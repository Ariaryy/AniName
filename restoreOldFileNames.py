
import glob, os, json

from icecream import ic

from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns


os.system('cls')

console = Console()

dir = r'C:\Users\hmjoisa\Downloads\Media\Anime\TV\Haikyuu!! (2014-20)\Old Episode Titles'

pathAndFilenameList = (sorted(list(glob.iglob(os.path.join(dir, r'*.json')))))

anime_list = [os.path.splitext(os.path.basename(i))[0] for i in pathAndFilenameList]

console.print("[b][u]Select a Backup File\n")

table = Table()
table.add_column("S. No", style="cyan")
table.add_column("Anime", style="yellow")

for i, anime in enumerate(anime_list):
    table.add_row(str(i+1), anime)

console.print(table)

print()
selection = int(input())-1
print()


with open(pathAndFilenameList[selection]) as f:

    f = json.load(f)

    rename_path = list(f.keys())[0]
    new_titles = f[rename_path]

    console.print("[b][u]Restoring File Names\n")

    for title in new_titles:
        #os.rename(os.path.join(rename_path, f"{title}"), os.path.join(rename_path, f"{new_titles[title]}"))
        renderables = [Panel(f"[b]{title}\n\n[green]{new_titles[title]}")]
        console.print(Columns(renderables))


