import os
import sys

from rich import print as rprint
from rich.table import Table
from rich.console import Console
from rich.tree import Tree
from rich import box
from rich.prompt import Confirm, Prompt

import src.settings as settings
from src.anime import Anime
import src.utils as utils

from tkinter import filedialog

os.system("cls")

settings.init(
    os.path.join(os.path.dirname(os.path.join(os.path.realpath(__file__))), "conf.ini")
)

console = Console()

console.print(
    "[b]Make sure to follow the instructions on https://github.com/Ariaryy/AniName before you proceed.\n"
)

directory = Prompt.ask(
    "[b][u]Press Enter to select the Anime Directory (or paste the path)"
)
print()

if not os.path.exists(directory):
    directory = filedialog.askdirectory(title="Select the Anime Directory")

anime = Anime(directory)

table = Table(
    title="[b][yellow]Anime(s) Found", box=box.ROUNDED, show_lines=True, highlight=True
)

table.add_column("Title", style="white")
table.add_column("MAL ID")

for i, title in enumerate(anime.anime_display_titles):
    table.add_row(
        anime.anime_display_titles[title],
        f"[b][blue][link https://myanimelist.net/anime/{anime.mal_ids[i]}]{anime.mal_ids[i]}",
    )

console.print(table)

print()
choice = Confirm.ask("[green]Proceed?")

if choice == False:
    sys.exit()

new_dirs = []

for i, path in enumerate(anime.full_paths):
    season_title = anime.anime_titles[i]
    season_number = anime.season_nos[i]
    season_part = anime.part_nos[i]

    console.print(f"\n[h1][b][u][yellow]Renaming: {season_title}\n")
    anime.get_episodes([anime.anime_data[i]])

    episodes = anime.episodes[anime.mal_ids[i]]
    anime_display_title = anime.anime_display_titles[anime.anime_dirs[i]]
    pattern = r"*.mkv"

    ep_prefs_data = {
        "sn": season_number,
        "pn": season_part,
        "st": season_title,
    }

    settings.set_ep_prefs(ep_prefs_data)

    new_dirs.append(
        os.path.join(
            os.path.dirname(path), utils.format_punctuations(anime_display_title)
        )
    )

    utils.rename(directory, path, pattern, episodes, anime_display_title)

print()

for dirs in new_dirs:
    tree = Tree(
        f":open_file_folder: [link file://{os.path.abspath(dirs)}]{dirs}",
        guide_style="bold bright_blue",
    )
    utils.walk_directory(dirs, tree)
    print()
    rprint(tree)

oldfilespath = os.path.join(os.path.dirname(directory), "ORIGINAL_EPISODE_FILENAMES")
console.print(
    f"""
[b][yellow]Original filenames are backed up in this folder
[link file://{os.path.abspath(oldfilespath)}]{oldfilespath}[/link file://{os.path.abspath(oldfilespath)}]

If you wish to restore the orignal file names, use the restore utility.
\n"""
)

os.system("pause")
