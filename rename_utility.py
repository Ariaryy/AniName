import os, pathlib
import utils
from anime import Anime

from rich import print as rprint
from rich.table import Table
from rich.console import Console
from rich.tree import Tree
from rich import box
from rich.prompt import Confirm

import configparser

config_file = configparser.ConfigParser()
config_file.read("conf.ini", encoding='utf8')

episode_format = config_file['formatting']['episode_format']
episode_lang = config_file['preference']['episode_title']
episode_prefix = config_file['preference']['episode_prefix']

season_format = config_file['formatting']['season_format']
season_lang = config_file['preference']['season_title']
season_prefix = config_file['preference']['season_prefix']

part_prefix = config_file['preference']['part_prefix']

seperator = (config_file['preference']['seperator']).replace('"', '')

os.system('cls')

console = Console()

console.print("[b]Please Make sure you follow the guide on https://github.com/AbhiramH427/AniName before using the rename utility!\n")

console.print("[b][u]Directory path of Anime:\n")
directory = input()
print()

if not os.path.exists(directory):
    console.print('[b][red]Directory does not exist. Please provide a valid directory.')
    quit()

season_metadata_format = {
    'season_prefix': season_prefix,
    'part_prefix': part_prefix,
    'seperator': seperator,
    'season_number': '',
    'season_title': '',
    'part_number': '',
}

anime = Anime(directory, season_lang, season_format, season_metadata_format)

#TODO: Do not use conf file for listing on screen and backup file
table = Table(title="[b][yellow]Anime(s) Found", box=box.ROUNDED, show_lines=True, highlight=True)

table.add_column("Title", style="white")
table.add_column("MAL ID")

for i, title in enumerate(anime.file_titles):
    table.add_row(anime.file_titles[title], f'[b][blue][link https://myanimelist.net/anime/{anime.mal_ids[i]}]{anime.mal_ids[i]}')

console.print(table)

print()
choice = Confirm.ask("[green]Proceed?")

if choice == False:
    quit()

for i, path in enumerate(anime.full_paths):

    season_title = anime.anime_titles[i]
    season_number = anime.season_nos[i]
    season_part = anime.part_nos[i]

    
    if int(season_part) < 1:
        season_part = ''
        part_prefix = ''

    if int(season_number) < 1:
        season_number = ''
        season_prefix = ''

    console.print(f"\n[h1][b][u][yellow]Renaming: {season_title}\n")
    anime.get_episodes(anime.mal_ids[i], episode_lang)

    episodes = anime.episodes[anime.mal_ids[i]]
    file_titles = anime.file_titles[anime.anime_dirs[i]]
    pattern = r'*.mkv'

    episode_meta_data_format = {
        'season_number': season_number,
        'part_number': season_part,
        'season_title': season_title,
        'season_prefix': season_prefix,
        'episode_prefix': episode_prefix,
        'part_prefix': part_prefix,
        'seperator': seperator
    }

    utils.rename(path, pattern, episodes, file_titles, episode_format, episode_meta_data_format)

print()

if anime.noSeasons == True:
    directory = os.path.join(os.path.dirname(directory), utils.format_punctuations(anime.file_titles[anime.anime_dirs[0]]))
directory = os.path.abspath(directory)

if not os.path.exists(directory):
    console.print('[b][red]There was an error in getting the path of the Episode Titles Backup folder.')
    quit()

tree = Tree(
    f":open_file_folder: [link file://{directory}]{directory}",
    guide_style="bold bright_blue",
)
utils.walk_directory(pathlib.Path(directory), tree)
print()
rprint(tree)

oldfilespath = os.path.join(os.path.dirname(path), 'Episode Titles Backup')
console.print(f'\n[b][yellow]Original file names are backed up in this folder\n[link file://{oldfilespath}]{oldfilespath}\n\nIf you wish to restore the orignal file names, use the restore utility.')