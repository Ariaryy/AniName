"""
The main application to rename episode filenames.
"""

import asyncio
import os
import platform
import sys
from argparse import ArgumentParser
from pathlib import Path
from tkinter import filedialog

from rich import box
from rich import print as rprint
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree


def get_current_script_directory():
    if getattr(
        sys, "frozen", False
    ):  # Check if the script is running in a PyInstaller bundle
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(os.path.abspath(__file__))
    else:
        # Handle the case where neither sys.frozen nor __file__ is available
        raise RuntimeError("Unable to determine script directory.")


project_root_directory = os.path.dirname(get_current_script_directory())
sys.path.insert(0, project_root_directory)

from aniname import http_session, restore_utility, utils
from aniname.anime_list import AnimeList

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.system("cls||clear")

CONSOLE = Console()


def initialize() -> Path:
    """Prints instructions and takes user input."""

    print()

    CONSOLE.print(
        """[b]Make sure to follow the instructions on \
https://github.com/Ariaryy/AniName before you proceed.\n"""
    )

    INPUT_DIR = Prompt.ask(
        "[b][u]Press Enter to select the Anime Directory (or paste the path)"
    )

    print()

    if not Path(INPUT_DIR).exists() or INPUT_DIR == "":
        INPUT_DIR = filedialog.askdirectory(title="Select the Anime Directory")

    return Path(INPUT_DIR)


def print_anime_list(anime_list: AnimeList):
    """Prints the list of anime(s) in a table."""

    table = Table(
        title="[b][yellow]Anime(s) Found",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )

    table.add_column("Title", style="white")
    table.add_column("Season")
    table.add_column("Part")
    table.add_column("Rename Preview")
    table.add_column("MAL ID")

    for anime in anime_list.animes:
        table.add_row(
            anime.title,
            anime.season or "-",
            anime.part or "-",
            anime.new_dir_path.name,
            f"[b][blue][link https://myanimelist.net/anime/{anime.mal_id}]{anime.mal_id}",
        )

    print()
    CONSOLE.print(table, justify="center")
    print()


def print_rename_summary(anime_list: AnimeList):
    """Prints the rename log."""

    for anime in anime_list.animes:
        tree = Tree(
            f":open_file_folder: [link {anime.new_dir_path.as_uri()}]{anime.new_dir_path}",
            guide_style="bold bright_blue",
        )
        
        utils.walk_directory(anime.new_dir_path, tree)
        print()
        rprint(tree)

    print_divider("[b]Backup[/b]")

    old_files_path = anime_list.init_dir.parent / "ORIGINAL_EPISODE_FILENAMES"
    CONSOLE.print(
        f"""
[b][yellow]The original episode filenames are backed up in the following folder:
[link {old_files_path.as_uri()}]{old_files_path}[/link {old_files_path.as_uri()}]

If you wish to restore the orignal episode filenames, use the restore utility.
"""
    )

    print()


def print_divider(message: str) -> None:
    """Prints a divider with the provided message."""

    print()
    CONSOLE.rule(message, style="white")
    print()


async def user_confirmation() -> None:
    CONSOLE.print("[green]Proceed?", justify="center")
    CHOICE = Confirm.ask()

    if CHOICE is False:
        await http_session.close_client_session()
        sys.exit()


def offer_restore(anime_list: AnimeList) -> None:
    CONSOLE.print("[green]Do you wish to run the restore utility now?")
    CHOICE = Confirm.ask()

    if CHOICE:
        old_files_path = anime_list.init_dir.parent / "ORIGINAL_EPISODE_FILENAMES"
        return restore_utility.restore(old_files_path)


async def main():
    parser = ArgumentParser(
        prog="AniName",
        description="Batch rename Anime Episode files with customizable formatting.",
    )

    parser.add_argument(
        "-r", "--restore", help="Run the restore utility", action="store_true"
    )

    args = parser.parse_args()

    if args.restore:
        return restore_utility.restore()

    INPUT_DIR = initialize()
    anime_list = AnimeList(init_dir=INPUT_DIR)

    await anime_list.scan_animes()

    print_anime_list(anime_list=anime_list)

    await user_confirmation()

    print_divider("[b]Renaming[/b]")

    await anime_list.rename_animes()
    await http_session.close_client_session()

    print_divider("[b]Overview[/b]")
    print_rename_summary(anime_list)
    offer_restore(anime_list)

    utils.pause()


if __name__ == "__main__":
    asyncio.run(main())
