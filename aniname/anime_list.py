import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from . import conf_loader, utils
from .anime import Anime
from .error_handler import HandleError

ANIME_TITLE_LANG = conf_loader.conf.anime_title_lang
EP_TITLE_LANG = conf_loader.conf.ep_title_lang
AUTO_NAME = conf_loader.conf.auto_rename

from rich.console import Console

CONSOLE = Console()


@dataclass(slots=True)
class AnimeList:
    """
    A Dataclass that contains a list of objects of the Anime dataclass.
    """

    init_dir: Path = field(default_factory=Path)
    mal_id_list: list[int] = field(default_factory=list)
    animes: list[Anime] = field(default_factory=list)

    async def rename_animes(self):
        for anime in self.animes:
            with CONSOLE.status("Fetching Episodes", spinner="point"):
                await anime.fetch_episodes()
            anime.rename_episodes(init_dir=self.init_dir)

    async def scan_animes(self) -> None:
        """
        Find dir(s) matching format and fetch Anime data.
        """
        with CONSOLE.status("Scanning for Anime(s)", spinner="point"):
            anime_dir_paths: list[Path] = utils.find_formatted_subdir(self.init_dir)

        if len(anime_dir_paths) == 0:
            raise NoMatchingDir

        with CONSOLE.status("Fetching Anime data", spinner="point"):
            fetch_anime_tasks = []

            for path in anime_dir_paths:
                mal_id, season_no, part_no = utils.parse_dir_basename(path.name)
                local_ep_min, local_ep_max = utils.get_local_ep_range(path)
                self.mal_id_list.append(int(mal_id))
                anime = Anime(
                    mal_id=mal_id,
                    season=season_no,
                    part=part_no,
                    dir_path=path,
                    local_ep_range={"min": local_ep_min, "max": local_ep_max},
                )
                self.animes.append(anime)
                fetch_anime_tasks.append(asyncio.create_task(anime.fetch_anime()))

            await asyncio.gather(*fetch_anime_tasks)


class NoMatchingDir(Exception):
    """Raised when no directories matching the scan format were found."""

    def __init__(self) -> None:
        HandleError.no_matching_dir()
