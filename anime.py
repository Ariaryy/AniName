import os
import utils
from icecream import ic
import re

class Anime:

    """
    Extracts Anime information from a directory containing Anime Seasons/Episodes
    """

    def __init__(self, path):

        self.noSeasons = False
        self.file_titles = {}
        self.anime_titles = []
        self.mal_ids = []
        self.full_paths = []

        #RegExp for filtering out Anime Folders
        anime_dir_re = re.compile(r'^[0-9]+[Ss][0-9]+')

        dirscan = os.scandir(path)
        subdirs = [i.name for i in dirscan if i.is_dir()]

        #Filtering out using RegExp
        self.anime_dirs = sorted([i for i in subdirs if anime_dir_re.match(i)])

        #len(anime_dirs) == 0 imples that the Anime does not have season folders
        if (len(self.anime_dirs) == 0):
            self.anime_dirs = [os.path.basename(path)]
            self.mal_ids = [os.path.basename(path).split("S")[0]]
            self.noSeasons = True
            self.full_paths = [path]
        else:
            self.mal_ids = [i.upper().split("S")[0] for i in self.anime_dirs]
            self.seasons = [i.upper().split("S")[1] for i in self.anime_dirs]
            self.full_paths = [os.path.join(path, i) for i in self.anime_dirs]

        if (self.noSeasons == True):
            title = utils.format_season(utils.anime_title(self.mal_ids[0]))
            self.anime_titles.append(title)
            self.file_titles.update({self.mal_ids[0]:title})
        else:
            for i, id in enumerate(self.anime_dirs):
                season, *part = self.seasons[i].split("P")
                part = 0 if part == [] else part[0]
                anime_title = utils.anime_title(self.mal_ids[i])
                file_title = utils.format_season(anime_title, int(season), int(part))
                self.anime_titles.append(anime_title)
                self.file_titles.update({id:file_title})

    def get_episodes(self, mal_id, title):

        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        self.episodes = {mal_id:{}}

        ep_nos = []
        ep_titles = []

        ep_nos, ep_titles = (utils.anime_episodes(mal_id, title))

        for i, ep_no in enumerate(ep_nos):
            self.episodes[mal_id].update({utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]})