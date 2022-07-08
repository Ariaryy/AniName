import json
import os
import re
import utils
from icecream import ic 
from rich import print

os.system('cls')

print("Please Make sure you have renamed your season/name folder(s) with the MAL ID of the Anime.\n")

#directory = input("Path of the parent Anime folder of the Anime to be renamed: ")
directory = r'C:\Users\hmjoisa\Downloads\Media\Anime\TV\Haikyuu!! (2014-20)'

class Anime:

    def __init__(self, path):

        self.noSeasons = False

        dirscan = os.scandir(path)

        subdirs = [i.name for i in dirscan if i.is_dir()]

        season_re = re.compile(r'^[0-9]+[Ss][0-9]+')
        self.filtered_subdirs = sorted([i for i in subdirs if season_re.match(i)])

        if (len(self.filtered_subdirs) == 0):
            mal_ids = []
            mal_ids = [os.path.basename(directory).split("S")[0]]
            self.noSeasons = True
        else:
            mal_ids = [i.upper().split("S")[0] for i in self.filtered_subdirs]
            self.seasons = [i.upper().split("S")[1] for i in self.filtered_subdirs]

        print(mal_ids)
        self.mal_ids = mal_ids

        self.file_titles = {}
        self.anime_titles = []

        if (self.noSeasons == True):
            title = utils.format_season(utils.anime_title(self.mal_ids[0]))
            self.anime_titles.append(title)
            self.file_titles.update({self.mal_ids[0]:title})
        else:
            for i, id in enumerate(self.filtered_subdirs):
                season, *part = self.seasons[i].split("P")
                part = 0 if part == [] else part[0]
                ic(season, part)
                anime_title = utils.anime_title(mal_ids[i])
                file_title = utils.format_season(anime_title, int(season), int(part))
                self.anime_titles.append(anime_title)
                self.file_titles.update({id:file_title})

    def get_kitsu(self, title):
        utils.anime_episodes_kitsu(title)

    def get_episodes(self, malid, title):
        self.episodes = {malid:{}}
        ep_nos = []
        ep_titles = []
        ep_nos, ep_titles = (utils.anime_episodes_kitsu(title)) #utils.extract_episodes
        for i, ep_no in enumerate(ep_nos):
            self.episodes[malid].update({utils.format_zeros(ep_no, len(ep_nos)): ep_titles[i]})
        #utils.clear()

anime = Anime(directory)

if anime.noSeasons == True:
    paths = [directory]

else:
    paths = [os.path.join(directory, i) for i in anime.filtered_subdirs]

ic(anime.anime_titles)
ic(anime.file_titles)

#anime.get_kitsu(anime.anime_titles[0])

for i, path in enumerate(paths):
    anime.get_episodes(anime.mal_ids[i], anime.anime_titles[i])
    #ic(anime.anime_titles[i])
    #anime.get_kitsu(anime.anime_titles[i])
    #ic(anime.episodes)
    print(json.dumps((anime.episodes), indent=4, sort_keys=True))
    utils.rename(path, r'*.mkv', anime.episodes[anime.mal_ids[i]], anime.file_titles[anime.filtered_subdirs[i]])