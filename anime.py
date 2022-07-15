import os
import utils
from icecream import ic
import re

class Anime:

    """
    Extracts Anime information from a directory containing Anime Seasons/Episodes
    """

    def __init__(self, path, season_lang, season_format, season_prefix, part_prefix, seperator):

        self.noSeasons = False
        self.file_titles = {}
        self.anime_titles = []
        self.mal_ids = []
        self.seasons = []
        self.season_nos = []
        self.part_nos = []
        self.full_paths = []

        #RegExp for filtering out Anime Folders
        anime_dir_re = re.compile(r'^[0-9]+[Ss][0-9]+')

        dirscan = os.scandir(path)
        subdirs = [i.name for i in dirscan if i.is_dir()]

        #Filtering out using RegExp
        self.anime_dirs = sorted([i for i in subdirs if anime_dir_re.match(i)])

        #len(anime_dirs) == 0 imples that the Anime does not have season folders
        if (len(self.anime_dirs) == 0):

            mal_id, season_no, part_no = utils.parse_folder(os.path.basename(path))

            self.anime_dirs = [os.path.basename(path)]
            self.mal_ids = [mal_id]
            self.noSeasons = True
            self.full_paths = [path]
        else:
            for i in self.anime_dirs:
                mal_id, season_no, part_no = utils.parse_folder(i)
                self.mal_ids.append(mal_id)
                self.seasons.append(f'{season_no}{part_no}')
                self.full_paths.append(os.path.join(path, i))

        #Fetching Anime Titles
        if (self.noSeasons == True):
            title = utils.anime_title(self.mal_ids[0], season_lang)
            title = utils.format_season(title, season_format)   

            self.anime_titles.append(title)
            self.file_titles.update({self.mal_ids[0]:title})

            self.season_nos.append(utils.format_zeros(str(0)))
            self.part_nos.append(utils.format_zeros(str(0)))

        else:
            for i, id in enumerate(self.anime_dirs):
                season = re.search(r'(?<=^[Ss])([0-9]+)', self.seasons[i]).group(1)
                part = re.search(r'(?<=[Pp])([0-9]+)', self.seasons[i])

                part = 0 if part == None else part.group(1)

                #anime_title = utils.anime_title(self.mal_ids[i])

                self.season_nos.append(utils.format_zeros(str(season)))
                self.part_nos.append(utils.format_zeros(str(part)))

                anime_title = utils.anime_title(self.mal_ids[i], season_lang)

                file_title = utils.format_season(anime_title, season_format, season_prefix, part_prefix, seperator, int(season), int(part))

                self.anime_titles.append(anime_title)
                self.file_titles.update({id:file_title})

    def get_episodes(self, mal_id, episode_lang):

        """
        Returns titles for all episodes in an Anime using MyAnimeList ID
        """

        self.episodes = {mal_id:{}}

        ep_nos = []
        ep_titles = []

        ep_nos, ep_titles = (utils.anime_episodes(mal_id, episode_lang))

        for i, ep_no in enumerate(ep_nos):
            self.episodes[mal_id].update({utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]})