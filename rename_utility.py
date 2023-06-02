"""
The main application to rename episode filenames.
"""

import os
import sys
from pathlib import Path
from tkinter import filedialog

from rich import box
from rich import print as rprint
from rich.columns import Columns
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from src import AnimeList, Config, utils

os.system("cls||clear")

if getattr(sys, "frozen", False):
    APP_PATH = Path(sys.executable).parent
else:
    APP_PATH = Path(__file__).parent

console = Console()
config = Config()


def pause() -> None:
    """
    Pauses program until the Enter key is pressed
    """

    input("Press the Enter key to continue . . .")


config.init(APP_PATH / "conf.ini")

console.print(
    """[b]Make sure to follow the instructions on \
https://github.com/Ariaryy/AniName before you proceed.\n"""
)

INPUT_DIR = Prompt.ask(
    "[b][u]Press Enter to select the Anime Directory (or paste the path)"
)

print()

if not Path(INPUT_DIR).exists() or INPUT_DIR == "":
    INPUT_DIR = filedialog.askdirectory(title="Select the Anime Directory")

INPUT_DIR = Path(INPUT_DIR)

anime_list = AnimeList()

lang_options = {
    "ep_title_lang": config.ep_title_lang,
    "anime_title_lang": config.anime_title_lang,
}

anime_list.get_animes(INPUT_DIR, lang_options)

table = Table(
    title="[b][yellow]Anime(s) Found", box=box.ROUNDED, show_lines=True, highlight=True
)

table.add_column("Title", style="white")
table.add_column("MAL ID")

new_dirs = []

for i, anime in enumerate(anime_list.animes):
    anime_info_dict = {"sn": anime.season, "pn": anime.part, "st": anime.title}
    new_dirs.append(
        anime.dir_path.parent
        / Config.config_format_parse(config.anime_title_format, anime_info_dict)
    )
    table.add_row(
        new_dirs[i].name,
        f"[b][blue][link https://myanimelist.net/anime/{anime.mal_id}]{anime.mal_id}",
    )

console.print(table)

print()

CHOICE = Confirm.ask("[green]Proceed?")

if CHOICE is False:
    sys.exit()

for i, anime in enumerate(anime_list.animes):
    console.print(f"\n[h1][b][u][yellow]Renaming: {anime.title}\n")
    anime.get_episodes(config.ep_title_lang)

    if (new_dirs[i]).exists():
        new_dirs[i] = new_dirs[i].parent / utils.path_fix_exisiting(
            new_dirs[i].name, new_dirs[i].parent
        )

    anime.rename_episodes(INPUT_DIR, new_dirs[i].name, config.ep_title_format)

    console.print(Columns(anime.rename_log))

print()

for directory in new_dirs:
    tree = Tree(
        f":open_file_folder: [link {directory.as_uri()}]{directory}",
        guide_style="bold bright_blue",
    )
    utils.walk_directory(directory, tree)
    print()
    rprint(tree)

oldfilespath = INPUT_DIR.parent / "ORIGINAL_EPISODE_FILENAMES"
console.print(
    f"""
[b][yellow]The original episode filenames are backed up in the following folder:
[link {oldfilespath.as_uri()}]{oldfilespath}[/link {oldfilespath.as_uri()}]

If you wish to restore the orignal episode filenames, use the restore utility.
\n"""
)

pause()
