import os
import sys
from pathlib import Path
from tkinter import filedialog

from rich import box
from rich import print as rprint
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

import src.settings as settings
import src.utils as utils
from src.anime import Anime

os.system("cls")

if getattr(sys, "frozen", False):
    application_path = Path(sys.executable).parent
elif __file__:
    application_path = Path(__file__).parent

settings.init(application_path / "conf.ini")

console = Console()

console.print(
    "[b]Make sure to follow the instructions on https://github.com/Ariaryy/AniName before you proceed.\n"
)

directory = Prompt.ask(
    "[b][u]Press Enter to select the Anime Directory (or paste the path)"
)
print()

if not Path(directory).exists() or directory == "":
    directory = filedialog.askdirectory(title="Select the Anime Directory")

directory = Path(directory)

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
    anime_display_title = utils.format_punctuations(
        anime.anime_display_titles[anime.anime_dirs[i]]
    )

    if (path.parent / anime_display_title).exists():
        anime_display_title = utils.foldername_fix_existing(
            anime_display_title, path.parent
        )

    ep_prefs_data = {
        "sn": season_number,
        "pn": season_part,
        "st": season_title,
    }

    settings.set_ep_prefs(ep_prefs_data)

    new_dirs.append(path.parent / anime_display_title)

    utils.rename(directory, path, episodes, anime_display_title)

print()

for dirs in new_dirs:
    tree = Tree(
        f":open_file_folder: [link {dirs.as_uri()}]{dirs}",
        guide_style="bold bright_blue",
    )
    utils.walk_directory(dirs, tree)
    print()
    rprint(tree)

oldfilespath = directory.parent / "ORIGINAL_EPISODE_FILENAMES"
console.print(
    f"""
[b][yellow]The original episode filenames are backed up in the following folder:
[link {oldfilespath.as_uri()}]{oldfilespath}[/link {oldfilespath.as_uri()}]

If you wish to restore the orignal episode filenames, use the restore utility.
\n"""
)

os.system("pause")
