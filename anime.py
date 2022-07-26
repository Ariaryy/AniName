import os, re, sys
import utils
from rich.console import Console

console = Console()

class Anime:

    """
    Extracts Anime information from a directory containing Anime Seasons/Episodes
    """

    def __init__(self, path):

        self.noSeasons = False
        self.anime_display_titles = {}
        self.anime_titles = []
        self.mal_ids = []
        self.seasons = []
        self.season_nos = []
        self.part_nos = []
        self.full_paths = []

        self.full_paths = utils.ani_parse_dir(path, True)

        if len(self.full_paths) == 0:
            console.print(
            """[b][red]No directories matching the scan format were found.\n[yellow]Learn more about directory formatting: [blue]https://github.com/AbhiramH427/AniName\n""")
            os.system('pause')
            sys.exit()

        self.anime_dirs = [os.path.basename(i) for i in self.full_paths]

        for i in self.full_paths:
            mal_id, season_no, part_no = utils.parse_dir(os.path.basename(i))
            self.mal_ids.append(mal_id)
            self.seasons.append(f'{season_no}{part_no}')

        #Fetching Anime Titles
        for i, id in enumerate(self.anime_dirs):
            season = re.search(r'(?<=^[Ss])([0-9]+)', self.seasons[i])
            part = re.search(r'(?<=[Pp])([0-9]+)', self.seasons[i])

            season = 0 if season == None else season.group(1)
            part = 0 if part == None else part.group(1)

            self.season_nos.append(utils.format_zeros(str(season)))
            self.part_nos.append(utils.format_zeros(str(part)))

            anime_title = utils.anime_title(self.mal_ids[i])
            
            anime_display_title = utils.format_season(anime_title, int(season), int(part), True)

            self.anime_titles.append(anime_title)
            self.anime_display_titles.update({id:anime_display_title})

    def get_episodes(self, mal_id):

        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        self.episodes = {mal_id:{}}

        ep_nos = []
        ep_titles = []

        ep_nos, ep_titles = (utils.anime_episodes(mal_id))

        for i, ep_no in enumerate(ep_nos):
            self.episodes[mal_id].update({utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]})