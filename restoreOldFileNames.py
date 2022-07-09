
import glob, os, json, pathlib
import utils

from icecream import ic

from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree

os.system('cls')

console = Console()

console.print("[b][u]Path of the folder conatining old episode titles backup files:\n")
dir = input()
#dir = r'C:\Users\hmjoisa\Downloads\Media\Anime\TV\Haikyuu!! (2014-20)\Old Episode Titles'

pathAndFilenameList = (sorted(list(glob.iglob(os.path.join(dir, r'*.json')))))

anime_list = [os.path.splitext(os.path.basename(i))[0] for i in pathAndFilenameList]

console.print("\n[b][u]Select a Backup File\n")

table = Table()
table.add_column("S. No", style="cyan")
table.add_column("Anime", style="yellow")

for i, anime in enumerate(anime_list):
    table.add_row(str(i+1), anime)

console.print(table)

print()
selection = int(input())-1
print()

utils.user_input()

failed = False

with open(pathAndFilenameList[selection]) as f:

    f = json.load(f)

    rename_path = list(f.keys())[0]
    new_titles = f[rename_path]
    tree = Tree("[b][red]The following files were not found and hence they couldn't be renamed", style="bold")
    console.print("[b][u]Restoring File Names\n")

    for title in new_titles:
        if os.path.exists(os.path.join(rename_path, title)):
            os.rename(os.path.join(rename_path, title), os.path.join(rename_path, new_titles[title]))
            renderables = [Panel(f"[b]{title}\n\n[green]{new_titles[title]}")]
            console.print(Columns(renderables))
        else:
            failed = True
            tree.add(title)

if failed == True:
    print()
    print(tree)
    print()

try:
    directory = os.path.abspath(rename_path)
except IndexError:
    print("[b]Usage:[/] python tree.py <DIRECTORY>")
else:
    tree = Tree(
        f":open_file_folder: [link file://{directory}]{directory}",
        guide_style="bold bright_blue",
    )
    utils.walk_directory(pathlib.Path(directory), tree)
    print()
    print(tree)

