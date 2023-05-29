import asyncio
import os
import sys
from pathlib import Path

import regex
from rich.console import Console
from rich.progress import track

import src.mal as mal
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
        self.full_paths = []
        # Anime data from MAL
        self.anime_data = []

        self.full_paths = utils.ani_parse_dir(path, True)

        if len(self.full_paths) == 0:
            console.print(
                """[b][red]No directories matching the scan format were found.\n[yellow]Learn more about directory formatting: [blue]https://github.com/Ariaryy/AniName#anime-folder-formatting\n"""
            )
            os.system("pause")
            sys.exit()

        # Folder names from path
        self.anime_dirs = [i.name for i in self.full_paths]

        # Parse folder names
        for i in self.full_paths:
            mal_id, season_no, part_no = utils.parse_dir(i.name)
            self.mal_ids.append(mal_id)
            self.seasons.append(f"{season_no}{part_no}")

        self.anime_data = asyncio.run(mal.fetch_animes(self.mal_ids))

        # Fetching Anime Titles
        for i, id in enumerate(self.anime_dirs):
            season = regex.search(r"(?<=^[Ss])([0-9]+)", self.seasons[i])
            part = regex.search(r"(?<=[Pp])([0-9]+)", self.seasons[i])

            season = None if season == None else season.group(1)
            part = None if part == None else part.group(1)

            self.season_nos.append(utils.format_zeros(season))
            self.part_nos.append(utils.format_zeros(part))

            title = self.anime_data[i][self.mal_ids[i]][settings.season_lang]

            format_args = {"sn": season, "pn": part, "st": title}

            anime_display_title = utils.config_format_parse(
                settings.season_display_format, format_args
            )

            self.anime_titles.append(title)
            self.anime_display_titles.update({id: anime_display_title})

    def get_episodes(self, anime_data):
        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        mal_id = list(anime_data[0].keys())[0]

        self.episodes = {mal_id: {}}

        ep_nos = []
        ep_titles = []

        episodes = (asyncio.run(mal.fetch_episodes(anime_data)))[0]

        episodes = episodes[list(episodes.keys())[0]][settings.episode_lang]

        (*ep_nos,) = episodes
        (*ep_titles,) = episodes.values()

        for i, ep_no in enumerate(ep_nos):
            self.episodes[mal_id].update(
                {utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]}
            )
