"""
Contains dataclasses for storing data of Anime(s)
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from sys import platform

from rich.panel import Panel

from src import utils

from .config import Config
from .error_handler import HandleError
from .mal import fetch_animes, fetch_episodes

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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

    def update_from_dict(self, new):
        """
        Update self using dictonary.
        """

        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_episodes(self, ep_title_lang):
        """
        Fetches episode titles.
        """

        if self.local_ep_range["max"] <= 100:
            return

        episodes = asyncio.run(
            fetch_episodes(
                self.mal_id,
                self.ep_pages,
                self.local_ep_range["min"],
                self.local_ep_range["max"],
                ep_title_lang,
            )
        )

        self.ep_titles.update(episodes[0])

    def rename_episodes(
        self,
        ani_scan_dir: Path,
        new_dir_name: str,
        ep_title_format: str,
        match_pattern=r"*.mkv",
    ) -> None:
        """
        Renames episode fileanmes using episode data.
        """

        ep_file_paths = sorted(list(self.dir_path.glob(match_pattern)))

        anitomy_dict = utils.create_anitomy_dict(ep_file_paths)

        backup_ep_names = {str(self.dir_path.parent / new_dir_name): {}}

        for anitomy in anitomy_dict:
            ep_file_path = self.dir_path / anitomy["file_name"]

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
                Config.config_format_parse(ep_title_format, ep_title_dict) + file_ext
            )

            if (
                self.dir_path / new_ep_filename
            ).exists() and self.dir_path / new_ep_filename != ep_file_path:
                new_ep_filename = utils.path_fix_exisiting(
                    new_ep_filename, self.dir_path
                )

            try:
                ep_file_path.rename(self.dir_path / new_ep_filename)

                self.rename_log.append(
                    Panel(
                        f"[b]{old_ep_filename + file_ext}\n\n[green]{new_ep_filename}"
                    )
                )

                backup_ep_names[str(self.dir_path.parent / new_dir_name)].update(
                    {f"{new_ep_filename}": f"{old_ep_filename}{file_ext}"}
                )
            except:
                self.rename_log.append(
                    Panel(f"[b]{old_ep_filename}\n\n[red]Failed to rename")
                )

        self.dir_path.rename(self.dir_path.parent / new_dir_name)

        backup_dir = ani_scan_dir.parent / "ORIGINAL_EPISODE_FILENAMES"

        if not backup_dir.exists():
            backup_dir.mkdir()

        with open(
            backup_dir / utils.path_fix_exisiting(f"{new_dir_name}.json", backup_dir),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(backup_ep_names, indent=4))


@dataclass(slots=True)
class AnimeList:
    """
    A Dataclass that contains a list of objects of the Anime dataclass.
    """

    mal_id_list: list[int] = field(default_factory=list)
    animes: list[Anime] = field(default_factory=list)

    def get_animes(self, parent_dir_path: Path, lang_options: dict) -> None:
        """
        Find dir(s) matching format and fetch Anime data.
        """

        anime_dir_paths = utils.find_ani_subdir(parent_dir_path)

        anime_title_lang = lang_options["anime_title_lang"]
        ep_title_lang = lang_options["ep_title_lang"]

        if len(anime_dir_paths) == 0:
            raise NoMatchingDir

        for path in anime_dir_paths:
            mal_id, season_no, part_no = utils.parse_dir_basename(path.name)
            local_ep_min, local_ep_max = utils.get_local_ep_range(path)
            self.mal_id_list.append(int(mal_id))
            self.animes.append(
                Anime(
                    mal_id=mal_id,
                    season=season_no,
                    part=part_no,
                    dir_path=path,
                    local_ep_range={"min": local_ep_min, "max": local_ep_max},
                )
            )

        fetched_anime_data = asyncio.run(
            fetch_animes(self.mal_id_list, anime_title_lang, ep_title_lang)
        )

        for i, data in enumerate(fetched_anime_data):
            self.animes[i].update_from_dict(data)


class NoMatchingDir(Exception):
    """Raised when no directories matching the scan format were found."""

    def __init__(self) -> None:
        HandleError.no_matching_dir()
