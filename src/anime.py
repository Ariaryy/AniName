import asyncio
import os
import sys
from pathlib import Path

import regex
from rich.console import Console

from src.mal import fetch_animes, fetch_episodes
import src.settings as settings
import src.utils as utils

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

console = Console()


class Anime:

    """
    Extracts Anime information from a directory containing Anime Seasons/Episodes
    """

    def __init__(self, path: Path):
        # Used for filenames and displaying on screen
        self.anime_display_titles = {}
        # Anime titles from anime_data
        self.anime_titles = []
        # MAL IDs from folder name
        self.mal_ids = []
        # Season Part from folder name
        self.seasons = []
        # Formatted season numbers
        self.season_nos = []
        # Formatted part numbers
        self.part_nos = []
        # Path of Anime(s)
        self.anime_dir_paths = []
        # Anime data from MAL
        self.anime_data = {}

        self.EP_TITLE_LANG = settings.episode_lang
        self.ANIME_TITLE_LANG = settings.season_lang

        self.anime_dir_paths = utils.ani_parse_dir(path)

        if len(self.anime_dir_paths) == 0:
            console.print(
                """[b][red]No directories matching the scan format were found.\n[yellow]Learn more about directory formatting: [blue]https://github.com/Ariaryy/AniName#anime-folder-formatting\n"""
            )
            os.system("pause")
            sys.exit()

        # Folder names from path
        self.anime_dir_names = [path.name for path in self.anime_dir_paths]

        # Parse folder names
        for path in self.anime_dir_paths:
            mal_id, season_no, part_no = utils.parse_dir(path.name)
            self.mal_ids.append(mal_id)
            self.seasons.append(f"{season_no}{part_no}")

        fetched_anime_data = asyncio.run(
            fetch_animes(self.mal_ids, self.ANIME_TITLE_LANG, self.EP_TITLE_LANG)
        )

        [self.anime_data.update(data) for data in fetched_anime_data]

        # Fetching Anime Titles
        for path, id in enumerate(self.anime_dir_names):
            season = regex.search(r"(?<=^[Ss])([0-9]+)", self.seasons[path])
            part = regex.search(r"(?<=[Pp])([0-9]+)", self.seasons[path])

            season = None if season == None else season.group(1)
            part = None if part == None else part.group(1)

            self.season_nos.append(utils.format_zeros(season))
            self.part_nos.append(utils.format_zeros(part))

            (
                self.anime_data[self.mal_ids[path]]["local_min_ep"],
                self.anime_data[self.mal_ids[path]]["local_max_ep"],
            ) = utils.get_local_ep_range(self.anime_dir_paths[path])

            title = self.anime_data[self.mal_ids[path]]["anime_title"]

            format_args = {"sn": season, "pn": part, "st": title}

            anime_display_title = utils.config_format_parse(
                settings.season_display_format, format_args
            )

            self.anime_titles.append(title)
            self.anime_display_titles.update({id: anime_display_title})

    def get_episodes(self, mal_id):
        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        if self.anime_data[mal_id]["local_max_ep"] <= 100:
            return

        ep_nos = []
        ep_titles = []

        episodes = asyncio.run(fetch_episodes(self.anime_data, self.EP_TITLE_LANG))

        (*ep_nos,) = episodes
        (*ep_titles,) = episodes.values()

        for i, ep_no in enumerate(ep_nos):
            self.anime_data[mal_id]["episode_titles"].update({ep_no: ep_titles[i]})
