"""
Contains dataclasses for storing data of Anime(s)
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from sys import platform

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel

from . import conf_loader, utils
from .config import Config
from .mal import fetch, parse_anime, parse_episodes

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

EP_TITLE_LANG = conf_loader.conf.ep_title_lang
EP_TITLE_FORMAT = conf_loader.conf.ep_title_format
ANIME_TITLE_FORMAT = conf_loader.conf.anime_title_format
MATCH_PATTERN = "*.mkv"

CONSOLE = Console()


@dataclass(slots=True)
class Anime:
    """
    Dataclass for an Anime
    """

    mal_id: int
    season: int
    part: int
    dir_path: Path
    local_ep_range: dict
    ep_pages: list = field(init=False, default=None)
    title: str = field(init=False, default_factory=str)
    type: str = field(init=False, default_factory=str)
    total_eps: int = field(init=False, default_factory=int)
    ep_titles: dict = field(init=False, default_factory=dict)
    rename_log: list[Panel] = field(init=False, default_factory=list)
    new_dir_path: Path = field(init=False, default_factory=Path)

    async def fetch_anime(self):
        """
        Fetches Anime data from MyAnimeList.
        """

        url = f"https://myanimelist.net/anime/{self.mal_id}/_/episode?offset=0"

        html = await fetch(url)

        parsed_anime = parse_anime(html, self.mal_id)

        self.title = parsed_anime["title"]
        self.total_eps = parsed_anime["total_eps"]
        self.type = parsed_anime["type"]
        self.ep_pages = parsed_anime["ep_pages"]
        self.ep_titles = parsed_anime["ep_titles"]

        anime_info_dict = {"sn": self.season, "pn": self.part, "st": self.title}
        formatted_dir_name = Config.config_format_parse(
            ANIME_TITLE_FORMAT, anime_info_dict
        )
        self.new_dir_path = utils.path_fix_exisiting(
            self.dir_path.parent / formatted_dir_name
        )

    async def fetch_episodes(self):
        """
        Fetches episode titles from MyAnimeList.
        """

        if self.local_ep_range["max"] <= 100:
            return

        tasks = []

        if self.local_ep_range["min"] <= 100:
            self.local_ep_range["min"] += 100
        min_ep_slice = (self.local_ep_range["min"] - 1) // 100
        max_ep_slice = ((self.local_ep_range["max"] - 1) // 100) + 1

        tasks = [
            asyncio.create_task(fetch(page, self.mal_id))
            for page in self.ep_pages[min_ep_slice:max_ep_slice]
        ]

        data = await asyncio.gather(*tasks)

        data_clean = {
            k: [d.get(k) for d in data if d.get(k) is not None]
            for k in set().union(*data)
        }

        episodes = [(parse_episodes(data_clean[id])) for id in data_clean]

        self.ep_titles.update(episodes[0])

    def rename_episodes(self, init_dir: Path) -> None:
        """
        Renames episode fileanmes using episode data.
        """

        CONSOLE.print(Align(f"\n[h1][b][u][yellow]Renaming: {self.title}\n", "center"))

        ep_file_paths = sorted(list(self.dir_path.glob(MATCH_PATTERN)))

        anitomy_dict = utils.episode_anitomy_dict(ep_file_paths)

        restore_dict = {
            "mal_id": self.mal_id,
            "title": self.title,
            "dir_path": str(self.new_dir_path),
            "season": self.season,
            "part": self.season,
            "rename_count": 0,
            "restore": {},
        }

        for anitomy in anitomy_dict:
            ep_file_path: Path = self.dir_path / anitomy["file_name"]

            old_ep_filename = ep_file_path.stem
            file_ext = ep_file_path.suffix

            ep_no = anitomy["episode_number"]

            episode_title = self.ep_titles[str(ep_no)]

            ep_title_dict = {
                "sn": self.season,
                "pn": self.part,
                "st": self.title,
                "en": utils.format_zeros(ep_no, self.local_ep_range["max"]),
                "et": episode_title,
            }

            new_ep_filename = (
                Config.config_format_parse(EP_TITLE_FORMAT, ep_title_dict) + file_ext
            )

            if self.dir_path / new_ep_filename != ep_file_path:
                new_ep_filename = utils.path_fix_exisiting(
                    self.dir_path / new_ep_filename
                ).name

            try:
                ep_file_path.rename(self.dir_path / new_ep_filename)

                self.rename_log.append(
                    Panel(
                        f"[b]{old_ep_filename + file_ext}\n\n[green]{new_ep_filename}"
                    )
                )

                restore_dict["restore"].update(
                    {f"{new_ep_filename}": f"{old_ep_filename}{file_ext}"}
                )

                restore_dict["rename_count"] += 1
            except Exception:
                self.rename_log.append(
                    Panel(f"[b]{old_ep_filename}\n\n[red]Failed to rename")
                )

        self.dir_path.rename(self.new_dir_path)

        backup_dir = init_dir.parent / "ORIGINAL_EPISODE_FILENAMES"

        if not backup_dir.exists():
            backup_dir.mkdir()

        with open(
            backup_dir
            / utils.path_fix_exisiting(backup_dir / f"{self.new_dir_path.name}.json"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(restore_dict, indent=4))

        CONSOLE.print(Align(Columns(self.rename_log), "center"))