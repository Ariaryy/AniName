"""
The main application to restore episode filenames from backup.
"""

import json
import os
from pathlib import Path
from tkinter import filedialog

from rich import box, print
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from . import utils
from .error_handler import HandleError

os.system("cls||clear")

CONSOLE = Console()


def print_divider(message: str) -> None:
    """Prints a divider with the provided message."""

    print()
    CONSOLE.rule(message, style="white")
    print()


def initialize() -> Path:
    input_dir = Prompt.ask(
        "[b][u]Press Enter to select the folder containing the backup files (or paste the path)"
    )

    if not Path(input_dir).exists() or input_dir == "":
        input_dir = filedialog.askdirectory(title="Select the Anime Directory")

    return Path(input_dir)


def print_backup_files(json_paths: list[Path]) -> None:
    table = Table(
        title="\n[b][yellow]Backup File(s) Found",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )

    table.add_column("S. No", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Anime", style="white")
    table.add_column("Season")
    table.add_column("Part")
    table.add_column("Total Episodes")
    table.add_column("MAL ID")

    for i, json_path in enumerate(json_paths, 1):
        with open(json_path, encoding="utf-8") as f:
            f = json.load(f)
            table.add_row(
                str(i),
                json_path.stem,
                f["title"],
                f["season"] or "-",
                f["part"] or "-",
                str(f["rename_count"]),
                f"[b][blue][link https://myanimelist.net/anime/{f['mal_id']}]{f['mal_id']}",
            )

    CONSOLE.print(table, justify="center")


def restore(input_dir: Path = None):
    if input_dir is None:
        input_dir = initialize()

    json_paths = sorted(list(input_dir.glob(r"*.json")))

    if len(json_paths) == 0:
        raise NoBackupsFound

    print_backup_files(json_paths)

    json_list = [i.stem for i in json_paths]

    INPUT = Prompt.ask("\n[b][u]Select Backup Files (separated by spaces)")
    CHOICES = [int(i) - 1 for i in INPUT.split()]

    print_divider("[b]Reverting[/b]")

    rename_paths = []

    for choice in CHOICES:
        failed = False

        with open(json_paths[choice], encoding="utf-8") as f:
            f = json.load(f)

            rename_path = Path(f["dir_path"])

            CONSOLE.print(
                Align(f"\n[h1][b][u][yellow]Reverting: {f['title']}\n", "center")
            )
            
            if not rename_path.exists():
                HandleError.restore_not_found(str(rename_path), json_list[choice])
                continue


            rename_paths.append(rename_path)

            new_titles = f["restore"]

            tree = Tree(
                "[b][red]The following files were not found and hence they couldn't be renamed",
                style="bold",
            )

            for title in new_titles:
                if (rename_path / title).exists():
                    (rename_path / title).rename(rename_path / new_titles[title])

                    renderables = [Panel(f"[b]{title}\n\n[green]{new_titles[title]}")]
                    CONSOLE.print(Align(Columns(renderables), "center"))

                else:
                    failed = True
                    tree.add(title)

        if failed is True:
            print()
            print(tree)
            print()

    if len(rename_paths) == 0:
        return

    print_divider("[b]Overview[/b]")

    for rename_path in rename_paths:
        tree = Tree(
            f":open_file_folder: [link {rename_path.as_uri()}]{rename_path}",
            guide_style="bold bright_blue",
        )
        utils.walk_directory(rename_path, tree)
        print()
        print(tree)
        print()


class NoBackupsFound(Exception):
    """Raised when no episode backup files found."""

    def __init__(self) -> None:
        HandleError.no_backup_found()
