import os, re, sys
import utils
from rich.console import Console
from rich.progress import track
import asyncio
import settings

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

console = Console()


class Anime:

    """
    Extracts Anime information from a directory containing Anime Seasons/Episodes
    """

    def __init__(self, path):

        # Used for filenames and displaying on screen
        self.anime_display_titles = {}
        # Anime titles from MAL
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

        self.full_paths = utils.ani_parse_dir(path, True)

        if len(self.full_paths) == 0:
            console.print(
                """[b][red]No directories matching the scan format were found.\n[yellow]Learn more about directory formatting: [blue]https://github.com/Ariaryy/AniName#pre-requisite\n"""
            )
            os.system("pause")
            sys.exit()

        # Folder names from path
        self.anime_dirs = [os.path.basename(i) for i in self.full_paths]

        # Parse folder names
        for i in self.full_paths:
            mal_id, season_no, part_no = utils.parse_dir(os.path.basename(i))
            self.mal_ids.append(mal_id)
            self.seasons.append(f"{season_no}{part_no}")

        anime_titles = asyncio.run(utils.anime_title(self.mal_ids))

        # Fetching Anime Titles
        for i, id in enumerate(self.anime_dirs):

            season = re.search(r"(?<=^[Ss])([0-9]+)", self.seasons[i])
            part = re.search(r"(?<=[Pp])([0-9]+)", self.seasons[i])

            season = None if season == None else season.group(1)
            part = None if part == None else part.group(1)

            self.season_nos.append(utils.format_zeros(season))
            self.part_nos.append(utils.format_zeros(part))

            format_args = {"sn": season, "pn": part, "st": anime_titles[i]}

            anime_display_title = utils.config_format_parse(
                settings.season_display_format, format_args
            )

            self.anime_titles.append(anime_titles[i])
            self.anime_display_titles.update({id: anime_display_title})

    def get_episodes(self, mal_id):

        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        self.episodes = {mal_id: {}}

        ep_nos = []
        ep_titles = []

        ep_nos, ep_titles = asyncio.run(utils.anime_episodes(mal_id))

        for i, ep_no in enumerate(ep_nos):
            self.episodes[mal_id].update(
                {utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]}
            )
