import glob, os, json, pathlib, sys
import src.utils as utils

from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree
from rich.prompt import Confirm, Prompt

os.system("cls")

console = Console()

console.print("[b][u]Path of the folder conatining old episode titles backup files:\n")
dir = input()

pathAndFilenameList = sorted(list(glob.iglob(os.path.join(dir, r"*.json"))))

anime_list = [os.path.splitext(os.path.basename(i))[0] for i in pathAndFilenameList]

table = Table()
table.add_column("S. No", style="cyan")
table.add_column("Anime", style="yellow")

for i, anime in enumerate(anime_list):
    table.add_row(str(i + 1), anime)

console.print(table)

selection = int(Prompt.ask("\n[b][u]Select a Backup File")) - 1

failed = False

with open(pathAndFilenameList[selection]) as f:
    f = json.load(f)

    rename_path = list(f.keys())[0]

    if not os.path.exists(rename_path):
        console.print(
            f"""
[b][red]The directory of the files whose names are to be restored does not exist.
        
[yellow]Please make sure the following path exists:
[u]{rename_path}[not u]
        
[yellow]Alternatively, you can try editing the path in the [u]{anime_list[selection]}.json[not u] file to fix the issue.\n"""
        )
        os.system("pause")
        sys.exit()

    new_titles = f[rename_path]

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
        if os.path.exists(os.path.join(rename_path, title)):
            os.rename(
                os.path.join(rename_path, title),
                os.path.join(rename_path, new_titles[title]),
            )
            renderables = [Panel(f"[b]{title}\n\n[green]{new_titles[title]}")]
            console.print(Columns(renderables))
        else:
            failed = True
            tree.add(title)

if failed == True:
    print()
    print(tree)
    print()


directory = os.path.abspath(rename_path)
tree = Tree(
    f":open_file_folder: [link file://{directory}]{directory}",
    guide_style="bold bright_blue",
)
utils.walk_directory(pathlib.Path(directory), tree)
print()
print(tree)
print()
os.system("pause")
