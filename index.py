import os, pathlib
import utils
from icecream import ic 
from anime import Anime

from rich import print as rprint
from rich.table import Table
from rich.console import Console
from rich.tree import Tree
from rich import box

"""
TODO:

import configparser

config_file = configparser.ConfigParser()
config_file.read("conf.ini")

ep_format = config_file['Formatting']['episode_format']
season_format = config_file['Formatting']['season_format']
"""

os.system('cls')

console = Console()

console.print("[b]Please Make sure you follow the guide on https://github.com/AbhiramH427/Bulk-Anime-Renamer before using the rename utility!\n")

console.print("[b][u]Directory path of Anime:\n")
directory = input()
print()
#directory = r"C:\Users\hmjoisa\Downloads\Media\Anime\TV\Haikyuu!! (2014-20)"

anime = Anime(directory)

table = Table(title="[b][yellow]Anime(s) Found", box=box.ROUNDED, show_lines=True, highlight=True)

table.add_column("Title", style="white")
table.add_column("MAL ID")

for i, title in enumerate(anime.file_titles):
    table.add_row(anime.file_titles[title], f'[b][blue][link https://myanimelist.net/anime/{anime.mal_ids[i]}]{anime.mal_ids[i]}')

console.print(table)

utils.user_input()

print ("\033[A                             \033[A")
print ("\033[A                             \033[A")
print ("\033[A                             \033[A")

for i, path in enumerate(anime.full_paths):

    console.print(f"\n[h1][b][u][yellow]Renaming: {anime.anime_titles[i]}\n")
    anime.get_episodes(anime.mal_ids[i], anime.anime_titles[i])

    utils.rename(path, r'*.mkv', anime.episodes[anime.mal_ids[i]], anime.file_titles[anime.anime_dirs[i]])

print()

if anime.noSeasons == True:
    directory = os.path.abspath(os.path.join(os.path.dirname(directory), utils.format_punctuations(anime.file_titles[anime.mal_ids[0]])))

try:
    directory = os.path.abspath(directory)
except IndexError:
    print("[b]Usage:[/] python tree.py <DIRECTORY>")
else:
    tree = Tree(
        f":open_file_folder: [link file://{directory}]{directory}",
        guide_style="bold bright_blue",
    )
    utils.walk_directory(pathlib.Path(directory), tree)
    print()
    rprint(tree)

oldfilespath = os.path.join(os.path.dirname(path), 'Episode Titles Backup')
console.print(f'\n[b][yellow]Original file names are backed up in this folder\n[link file://{oldfilespath}]{oldfilespath}\n\nIf you wish to restore the orignal file names, use the restore utility.')