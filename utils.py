import requests
import json
import glob, os, pathlib
import re
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

console = Console()

global all_episodes
global all_ep_no
all_ep_no = []
all_episodes = []

def parse_folder(folder_name):

    var = re.search(r'^([0-9]+)$|^([0-9]+)([Ss][0-9]+)([Pp][0-9]+)?$', folder_name)

    if var != None:

        var = [i for i in var.groups() if i != None]

        if len(var) == 1:
            var.append(['', ''])

        if len(var) == 2:
            var.append('')

        return var[0], var[1], var[2]

    console.print("[b][red]Invalid folder formatting.\n[yellow]Learn more about folder formatting: [blue]https://github.com/AbhiramH427/AniName")
    quit()

@sleep_and_retry
@limits(calls=3, period=4)
def fetch_url(base_url, params=None):

    """
    Returns data from get request.
    Rate Limit: 3 calls per second.
    """

    r = requests.get(base_url, params=params) if params == None else requests.get(base_url)

    if not r.status_code == 200:
        console.print('[b][red]The provided the MyAnimeList ID is invalid.')
        quit()

    return r.json()

def anime_search(title):

    """
    Returns MyAnimeList ID using Title of Anime.
    """

    r = fetch_url("https://api.jikan.moe/v4/anime", {"q": title, "limit": 5, "type": "tv", "order_by": "title"})

    try:
        mal_id = (r['data'][0]['mal_id'])
    except Exception as e:
        print(json.dumps(r, indent=4, sort_keys=True))
        print("\n")
        print(e)
    anime_title = (r['data'][0]['title'])
    return mal_id, anime_title

def format_season(anime_title, format, season_metadata, season=0, part=0):

    """
    Formats Anime season titles in the format provided in the config file.
    """

    season_metadata['season_title'] = anime_title

    if (int(season) < 1):
        season_metadata['season_prefix'] = ''
        season_metadata['seperator'] = ''

    """
    season_metadata = {
        'season_prefix': season_prefix,
        'part_prefix': part_prefix,
        'seperator': seperator,
        'season_number': '',
        'season_title': '',
        'part_number': '',
    }
    """

    if (int(part) < 1):
        season_metadata['part_prefix'] = ''

    if (int(season) >= 1):
        season_metadata['season_number'] = format_zeros(str(season))

    if (int(part) >= 1):
        season_metadata['season_number'] = format_zeros(str(season))
        season_metadata['part_number'] = format_zeros(str(part))
    
    season_name = format.format(**season_metadata)

    return season_name

def anime_title(mal_id, language):

    """
    Returns Anime Title using MyAnimeList ID.
    """

    if language == 'romanji':
        language = 'title'
    elif language == 'japanese':
        language = 'title_japanese'
    else:
        language = 'title_english'

    r = fetch_url(f"https://api.jikan.moe/v4/anime/{mal_id}")

    if not 'data' in r:
        console.print(f'[b][red]There was an error while fetching the Anime title. Double check the provided MyAnimeList ID: {mal_id}')
        quit()

    if not r['data']['type'] == "TV":
        console.print('[b][red]Anime types except TV are not supported.')
        quit()

    title = (r['data'][language])

    return title

def anime_episodes(mal_id, episode_lang, page=1):

    """
    Returns a dictonary of episodes of an Anime using MyAnimeList ID.
    On failure, fetches episodes from Kitsu API using Anime Title.
    """

    r = (fetch_url(f"https://api.jikan.moe/v4/anime/{mal_id}/episodes", {"page": page}))

    if not 'data' in r:
        console.print(f'[b][red]There was an error while fetching the episodes. Double check the provided MyAnimeList ID {mal_id}')
        quit()

    all_episodes.append(r['data'])

    if r['pagination']['has_next_page'] == True:
        page += 1
        anime_episodes(mal_id, episode_lang, page)

    final_all_eps = copy.deepcopy(all_episodes) 
    del all_episodes[:]

    return extract_episodes(final_all_eps, episode_lang) 

def anime_episodes_kitsu(title, next=None):

    """
    Returns all episodes of an Anime using Anime title.
    """

    if next == None:
        URL = f"https://kitsu.io/api/edge/anime?filter[text]={title}"
        r = (requests.get(url = URL)).json()
        URL = r['data'][0]['relationships']['episodes']['links']['related']

        r = requests.get(url = f'{URL}?page%5Blimit%5D=20')
    else:
        r = requests.get(url = next)

    for eps in r['data']:
        all_episodes.append(eps['attributes']['canonicalTitle'])
        all_ep_no.append(str(eps['attributes']['number']))

    if 'next' in r['links'].keys():
        anime_episodes_kitsu(title, r['links']['next'])

    final_all_eps = copy.deepcopy(all_episodes) 
    final_ep_no = copy.deepcopy(all_ep_no) 

    del all_episodes[:]
    del all_ep_no[:]

    return final_ep_no, final_all_eps

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

    string = re.sub(':', ' ', str(string))
    string = re.sub(r'["\/<>\?\\\| +]+', ' ', str(string))

    return string

def extract_episodes(episodes_data, episode_lang):

    if episode_lang == 'romanji':
        episode_lang = 'title_romanji'
    elif episode_lang == 'japanese':
        episode_lang = 'title_japanese'
    else:
        episode_lang = 'title'

    """
    Returns a dictionary containing Episode Numbers and the respective Episode Title from the data fetched using anime_episodes()
    """
    ep_no = []
    ep_title = []

    for page in episodes_data:
        for ep in (page):   
            epn = format_zeros(str(ep['mal_id']), page[len(page)-1]['mal_id'])
            ept = format_punctuations(ep[episode_lang])
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


def rename(dir, pattern, episodes, dir_title, episode_format, title_metadata):

    """
    Renames files using path, file pattern and episodes fetched using anime_episodes()
    """

    pathAndFilenameList = (sorted(list(glob.iglob(os.path.join(dir, pattern)))))

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

        title_metadata.update({'episode_number': ep_no, 'episode_title': episodeName})

        rename_string = episode_format.format(**title_metadata)

        
        old_new[os.path.join(os.path.dirname(dir), dir_title)].update({f'{rename_string}{ext}':f'{title}{ext}'})
        
        os.rename(pathAndFilename, os.path.join(dir, f"{rename_string}{ext}"))

        renderables.append(Panel(f"[b]{title}\n\n[green]{rename_string}"))

    console.print(Columns(renderables))
    oldfilespath = os.path.join(os.path.dirname(dir), 'Episode Titles Backup')

    if not os.path.exists(oldfilespath):
        os.makedirs(oldfilespath)

    os.rename(dir, os.path.join(os.path.dirname(dir), format_punctuations(dir_title)))

    with open(os.path.join(oldfilespath, filename_fix_existing(f"{format_punctuations(dir_title)}.json", oldfilespath)), "w", encoding="utf-8") as f:
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