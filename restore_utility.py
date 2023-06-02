"""
The main application to restore episode filenames from backup.
"""

import json
import os
from pathlib import Path
from tkinter import filedialog

from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from src import HandleError
from src.utils import walk_directory

os.system("cls||clear")

console = Console()


def pause() -> None:
    """
    Pauses program until the Enter key is pressed
    """

    input("Press the Enter key to continue . . .")


INPUT_DIR = Prompt.ask(
    "[b][u]Press Enter to select the folder containing the backup files (or paste the path)"
)

if not Path(INPUT_DIR).exists() or INPUT_DIR == "":
    INPUT_DIR = filedialog.askdirectory(title="Select the Anime Directory")

INPUT_DIR = Path(INPUT_DIR)

json_file_paths = sorted(list(INPUT_DIR.glob(r"*.json")))

anime_list = [i.stem for i in json_file_paths]

table = Table()
table.add_column("S. No", style="cyan")
table.add_column("Anime", style="yellow")

for i, anime in enumerate(anime_list):
    table.add_row(str(i + 1), anime)

console.print(table)

SELECTION = int(Prompt.ask("\n[b][u]Select a Backup File")) - 1

failed = False

with open(json_file_paths[SELECTION], encoding='utf-8') as f:
    f = json.load(f)

    rename_path = Path(list(f.keys())[0])

    if not rename_path.exists():
        HandleError.restore_not_found(str(rename_path), anime_list[SELECTION])

    new_titles = f[list(f.keys())[0]]

    tree = Tree(
        "[b][yellow]The selected backup file contains the following episode titles",
        style="bold",
    )
    for title in new_titles:
        tree.add(new_titles[title])

    print()
    print(tree)
    print()

    CHOICE = Confirm.ask("[green]Proceed to restore filename?")

    if CHOICE is False:
        exit()

    print()

    tree = Tree(
        "[b][red]The following files were not found and hence they couldn't be renamed",
        style="bold",
    )
    console.print("[b][u]Restoring File Names\n")

    for title in new_titles:
        if (rename_path / title).exists():
            (rename_path / title).rename(rename_path / new_titles[title])

            renderables = [Panel(f"[b]{title}\n\n[green]{new_titles[title]}")]
            console.print(Columns(renderables))
        else:
            failed = True
            tree.add(title)

if failed is True:
    print()
    print(tree)
    print()

tree = Tree(
    f":open_file_folder: [link {rename_path.as_uri()}]{rename_path}",
    guide_style="bold bright_blue",
)
walk_directory(rename_path, tree)
print()
print(tree)
print()
pause()
