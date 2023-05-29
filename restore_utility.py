import json
import os
import sys
from pathlib import Path
from tkinter import filedialog

from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

import src.utils as utils

os.system("cls")

console = Console()


dir = Prompt.ask(
    "[b][u]Press Enter to select the folder containing the backup files (or paste the path)"
)

if not Path(dir).exists() or dir == "":
    dir = filedialog.askdirectory(title="Select the Anime Directory")

dir = Path(dir)

json_file_paths = sorted(list(dir.glob(r"*.json")))

anime_list = [i.stem for i in json_file_paths]

table = Table()
table.add_column("S. No", style="cyan")
table.add_column("Anime", style="yellow")

for i, anime in enumerate(anime_list):
    table.add_row(str(i + 1), anime)

console.print(table)

selection = int(Prompt.ask("\n[b][u]Select a Backup File")) - 1

failed = False

with open(json_file_paths[selection]) as f:
    f = json.load(f)

    rename_path = Path(list(f.keys())[0])

    if not rename_path.exists():
        console.print(
            f"""
[b][red]The directory of the files whose names are to be restored does not exist.
        
[yellow]Please make sure the following path exists:
[u]{rename_path}[not u]
        
[yellow]Alternatively, you can try editing the path in the [u]{anime_list[selection]}.json[not u] file to fix the issue.\n"""
        )
        os.system("pause")
        sys.exit()

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

    choice = Confirm.ask("[green]Proceed to restore filename?")

    if choice == False:
        sys.exit()

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

if failed == True:
    print()
    print(tree)
    print()

tree = Tree(
    f":open_file_folder: [link {rename_path.as_uri()}]{rename_path}",
    guide_style="bold bright_blue",
)
utils.walk_directory(rename_path, tree)
print()
print(tree)
print()
os.system("pause")
