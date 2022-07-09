import requests
import json
import glob, os, pathlib, sys
import re
#from thefuzz import fuzz
from icecream import ic
import copy
from ratelimit import limits, sleep_and_retry

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text

global all_episodes
global all_ep_no
all_ep_no = []
all_episodes = []

@sleep_and_retry
@limits(calls=3, period=4)
def fetch_url(base_url, params=None):

    """
    Returns data from get request.
    Rate Limit: 3 calls per second.
    """

    r = requests.get(base_url, params=params) if params == None else requests.get(base_url)
    return r

def anime_search(title):

    """
    Returns MyAnimeList ID using Title of Anime.
    """

    r = fetch_url("https://api.jikan.moe/v4/anime", {"q": title, "limit": 5, "type": "tv", "order_by": "title"})

    try:
        mal_id = ((r.json())['data'][0]['mal_id'])
    except Exception as e:
        print(json.dumps((r.json()), indent=4, sort_keys=True))
        print("\n")
        print(e)
    anime_title = ((r.json())['data'][0]['title'])
    return mal_id, anime_title

def format_season(anime, season=0, part=0):

    """
    Formats Anime season titles in the following format: Season Part Title
    Example: S01P01 - Season-Title
    """

    if(season < 1):
        season_name = f'{anime}'
    elif (season >= 1):
        season_name = f'S{format_zeros(str(season))} - {anime}'

    if (part >= 1):
        season_name = f'S{format_zeros(str(season))}P{format_zeros(str(part))} - {anime}'

    return season_name

def anime_title(mal_id):

    """
    Returns Anime Title using MyAnimeList ID.
    """

    r = fetch_url(f"https://api.jikan.moe/v4/anime/{mal_id}")
    return ((r.json())['data']['title'])

def anime_episodes(mal_id, title, page=1):

    """
    Returns a dictonary of episodes of an Anime using MyAnimeList ID.
    On failure, fetches episodes from Kitsu API using Anime Title.
    """

    r = fetch_url(f"https://api.jikan.moe/v4/anime/{mal_id}/episodes", {"page": page})

    try:
        if not bool((r.json())['data']):
            print("\n")
            print("DATA EMPTY, FALLING BACK TO KITSU API")
            print("\n")
            return anime_episodes_kitsu(title)
        all_episodes.append((r.json())['data'])
        #print(json.dumps((r.json()), indent=4, sort_keys=True))
    except Exception as e:
        print(json.dumps((r.json()), indent=4, sort_keys=True))
        print("\n")
        print(e)

    if (r.json())['pagination']['has_next_page'] == True:
        page += 1
        anime_episodes(mal_id, page)

    final_all_eps = copy.deepcopy(all_episodes) 
    del all_episodes[:]
    return extract_episodes(final_all_eps) 

def anime_episodes_kitsu(title, next=None):

    """
    Returns all episodes of an Anime using Anime title.
    """

    ic(title)

    if next == None:
        URL = f"https://kitsu.io/api/edge/anime?filter[text]={title}"
        r = requests.get(url = URL)
        #ic((r.json())['data'][0])
        URL = (r.json())['data'][0]['relationships']['episodes']['links']['related']

        r = requests.get(url = f'{URL}?page%5Blimit%5D=20')
    else:
        #URL = (r.json())['data'][0]['relationships']['episodes']['links']['related']
        r = requests.get(url = next)

    #print(json.dumps(r.json(), indent=4, sort_keys=True))

    for eps in (r.json())['data']:
        all_episodes.append(eps['attributes']['canonicalTitle'])
        all_ep_no.append(str(eps['attributes']['number']))

    if 'next' in (r.json())['links'].keys():
        anime_episodes_kitsu(title, (r.json())['links']['next'])

    final_all_eps = copy.deepcopy(all_episodes) 
    final_ep_no = copy.deepcopy(all_ep_no) 

    del all_episodes[:]
    del all_ep_no[:]

    return final_ep_no, final_all_eps
    #print(json.dumps((r.json())['data'][0]['attributes']['canonicalTitle'], indent=4, sort_keys=True))

def format_zeros(number, max_number=1):

    """
    Adds an appropriate number of leading zeros to a number based on the max number.
    """

    if max_number < 10:
        max_number *= 10
    return number.zfill(len(str(max_number)))

def format_punctuations(string):

    """
    Returns string with punctuations appropriate for Windows file name.
    """

    string = string.replace(':', ' -')
    punctuation = ['\\', '/', '?', '<', '>', '|', '"']
    for p in punctuation:
        string = string.replace(p, '')
    return string

def extract_episodes(episodes_data):

    """
    Returns a dictionary containing Episode Numbers and the respective Episode Title from the data fetched using anime_episodes()
    """
    ep_no = []
    ep_title = []

    for page in episodes_data:
        for ep in (page):   
            epn = format_zeros(str(ep['mal_id']), page[len(page)-1]['mal_id'])
            ept = format_punctuations(ep['title'])
            ep_no.append(epn)         
            ep_title.append(ept)

    return ep_no, ep_title

def filename_fix_existing(filename, dirname):

    """
    Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """

    name, ext = filename.rsplit('.', 1)
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit('.', 1)[0] for x in names]
    suffixes = [x.replace(name, '') for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes
                   if x.startswith(' (') and x.endswith(')')]
    indexes  = [int(x) for x in suffixes
                   if set(x) <= set('0123456789')]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return '%s (%d).%s' % (name, idx, ext)


def rename(dir, pattern, episodes, dir_title):

    """
    Renames files using path, file pattern and episodes fetched using anime_episodes()
    """

    pathAndFilenameList = (sorted(list(glob.iglob(os.path.join(dir, pattern)))))

    console = Console()
    renderables = []

    ep_re = re.compile(r'([Ee][0-9]+)|([Ss][0-9]+[Ee][0-9]+)|([0-9]+)')
    last_no_re = re.compile(r'(\d+)[^\d]*$')
    first_ep = os.path.basename(pathAndFilenameList[0])
    last_ep = os.path.basename(pathAndFilenameList[len(pathAndFilenameList)-1])
    
    ep_range = [re.search(last_no_re ,(re.search(ep_re, first_ep).group())).group(), re.search(last_no_re, (re.search(ep_re, last_ep).group())).group()]
    ep_range = [format_zeros(i, len(pathAndFilenameList)) for i in ep_range]
    
    episodes_ar = sorted({i for i in episodes if int(i) >= int(ep_range[0]) and int(i) <= int(ep_range[1])})
    
    old_new = {os.path.join(os.path.dirname(dir), dir_title): {}}

    for i, ep_no in enumerate(episodes_ar):
        
        pathAndFilename = pathAndFilenameList[i]
        
        title, ext = os.path.splitext(os.path.basename(pathAndFilename))
        episodeName = episodes[ep_no]
        
        renderables.append(Panel(f"[b]{title}\n\n[green]E{ep_no} - {episodeName}"))

        #print (f"From: {title}\nTo:   E{ep_no} - {episodeName}\n")

        old_new[os.path.join(os.path.dirname(dir), dir_title)].update({f'E{ep_no} - {episodeName}{ext}':f'{title}{ext}'})
        os.rename(pathAndFilename, os.path.join(dir, f"E{ep_no} - {episodeName}{ext}"))

    console.print(Columns(renderables))
    oldfilespath = os.path.join(os.path.dirname(dir), 'Episode Titles Backup')

    if not os.path.exists(oldfilespath):
        os.makedirs(oldfilespath)

    os.rename(dir, os.path.join(os.path.dirname(dir), format_punctuations(dir_title)))

    with open(os.path.join(oldfilespath, filename_fix_existing(f"{dir_title}.json", oldfilespath)), "w", encoding="utf-8") as f:
        f.write(json.dumps(old_new, indent = 4))

def walk_directory(directory: pathlib.Path, tree: Tree) -> None:
    """Recursively build a Tree with directory contents."""
    # Credits: https://github.com/Textualize/rich/blob/master/examples/tree.py
    # Sort dirs first then by filename
    paths = sorted(
        pathlib.Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            branch = tree.add(
                f"[bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}",
                style=style,
                guide_style=style,
            )
            walk_directory(path, branch)
        else:
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            icon = "📺 " if path.suffix == ".mkv" else "📄 "
            tree.add(Text(icon) + text_filename)

def user_input():

    console = Console()

    yes = {'yes','y'}
    no = {'no','n'}

    valid = False

    console.print("\n[green]Proceed? (Y/N): ")

    while (valid == False):

        choice = input().lower()

        if choice in yes:
            valid = True
        elif choice in no:
            quit()
        else:
            console.print("\n[red]Please provide a valid input (Y/N): ")

# def rename(dir, pattern, episodesList, epNo):

#     iteration = 0
#     count = 0
#     pathAndFilenameList = (sorted(list(glob.iglob(os.path.join(dir, pattern)))))
#     pathAndFilename = pathAndFilenameList[iteration]

#     while((iteration <= len(pathAndFilenameList)-1) or (count <= (len(episodesList)-1))):
#         pathAndFilename = pathAndFilenameList[iteration]

#         title, ext = os.path.splitext(os.path.basename(pathAndFilename))

#         print(episodesList[count])

#         episodeName = episodesList[count]
#         epRenameNo = epNo[count]

#         #Rename the EP if the EP is present (determined by EP No. of original file name)

#         #fuzzy = fuzz.ratio(title, f"E{epRenameNo}")

#         fuzzy=100

#         if (fuzzy > 50):
#             os.rename(pathAndFilename, os.path.join(dir, f"E{epRenameNo} - {episodeName}{ext}"))
#             iteration = iteration + 1
#             print (f"From: {title}\nTo:   E{epRenameNo} - {episodeName}\n")

#         count = count + 1