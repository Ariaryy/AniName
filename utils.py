import json
import glob, os, pathlib
import re
import copy

import asyncio
import httpx
from http import HTTPStatus
from aiolimiter import AsyncLimiter

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import anitopy
import settings

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text
from rich.progress import track

console = Console()

rate_limit = AsyncLimiter(3, 1.6)


def parse_dir(dir_basename):

    var = re.search(r"^([\d]+)$|^([\d]+)([Ss][\d]+)([Pp][\d]+)?$", dir_basename)

    if var != None:

        var = [i for i in var.groups() if i != None]

        if len(var) == 1:
            var.append(["", ""])

        if len(var) == 2:
            var.append("")

        return var[0], var[1], var[2]

    return None


async def jikan_fetch(request_client, base_url):

    """
    Returns data from get request.
    Rate Limit: 3 calls per second.
    """

    await rate_limit.acquire()
    async with rate_limit:

        r = await request_client.get(base_url)

        if r.status_code == HTTPStatus.OK:

            if "type" in r.json()["data"]:
                if not r.json()["data"]["type"] == "TV":
                    return

            return r.json()

        elif r.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            console.print(
                "\n[b][red]The rate limit has been exceeded. Please try again later.\n"
            )
            os.system("pause")
            os._exit(1)

        elif r.status_code == HTTPStatus.NOT_FOUND:
            console.print(
                "\n[b][red]An error occured while fetching the Anime. Please ensure that the MyAnimeList ID provided is valid.\n"
            )
            os.system("pause")
            os._exit(1)

        else:
            console.print("[b][red]The API request failed due to an error.\n")
            os.system("pause")
            os._exit(1)


async def anime_title(mal_ids: list):

    request_client = httpx.AsyncClient()

    """
    Returns Anime Title(s) using MyAnimeList ID.
    """

    season_lang = copy.deepcopy(settings.season_lang)

    if season_lang == "romanji":
        season_lang = "title"
    elif season_lang == "japanese":
        season_lang = "title_japanese"
    else:
        season_lang = "title_english"

    tasks = []
    for mal_id in mal_ids:
        url = f"https://api.jikan.moe/v4/anime/{mal_id}"
        tasks.append(asyncio.create_task(jikan_fetch(request_client, url)))

    # total_tasks = len(tasks)
    # titles = [await f for f in track(asyncio.as_completed(tasks), description="Fetching Anime(s):", total=total_tasks, complete_style="yellow", finished_style="green", transient=True)]
    titles = await asyncio.gather(*tasks, return_exceptions=False)

    titles = [title["data"][season_lang] for title in titles if title != None]

    return titles


async def anime_episodes(mal_id, page=1, episode_list=[]):

    request_client = httpx.AsyncClient()

    """
    Returns list of episode numbers and titles of an Anime using MyAnimeList ID.
    """

    r = await (
        jikan_fetch(
            request_client,
            f"https://api.jikan.moe/v4/anime/{mal_id}/episodes?page{page}",
        )
    )

    last_visible_page = r["pagination"]["last_visible_page"]

    episode_list.append(r)

    if last_visible_page > 1:

        tasks = []
        for x in range(2, last_visible_page + 1):
            url = f"https://api.jikan.moe/v4/anime/{mal_id}/episodes?page={x}"
            tasks.append(asyncio.create_task(jikan_fetch(request_client, url)))

        #total_tasks = len(tasks)

        # episode_list_2 = [await f for f in track(asyncio.as_completed(tasks), description="Fetching Episodes:", total=total_tasks, complete_style="yellow", finished_style="green", transient=True)]
        episode_list_2 = await asyncio.gather(*tasks, return_exceptions=False)
        episode_list = episode_list + episode_list_2

    episode_list = [i["data"] for i in episode_list]

    return extract_episodes(episode_list)


def format_zeros(number, max_number=1):

    """
    Adds an appropriate number of leading zeros to a number based on the max number.
    """

    if number == None:
        return None

    if max_number < 10:
        max_number *= 10
    return str(number).zfill(len(str(max_number)))


def format_punctuations(string):

    """
    Returns string with punctuations appropriate for Windows file name.
    """

    string = re.sub(":", " ", str(string))
    string = re.sub(r'["\/<>\?\\\| +]+', " ", str(string))

    return string


def extract_episodes(episodes_data):

    episode_lang = copy.deepcopy(settings.episode_lang)

    if episode_lang == "romanji":
        episode_lang = "title_romanji"
    elif episode_lang == "japanese":
        episode_lang = "title_japanese"
    else:
        episode_lang = "title"

    """
    Returns a dictionary containing Episode Numbers and the respective Episode Title from the data fetched using anime_episodes()
    """
    ep_no = []
    ep_title = []

    last_episode = episodes_data[len(episodes_data) - 1][
        len(episodes_data[len(episodes_data) - 1]) - 1
    ]["mal_id"]

    for page in episodes_data:
        for ep in page:
            epn = format_zeros(str(ep["mal_id"]), last_episode)
            ept = format_punctuations(ep[episode_lang])
            ep_no.append(epn)
            ep_title.append(ept)

    return ep_no, ep_title


def filename_fix_existing(filename, dirname):

    """
    Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """

    name, ext = filename.rsplit(".", 1)
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit(".", 1)[0] for x in names]
    suffixes = [x.replace(name, "") for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")]
    indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return "%s (%d).%s" % (name, idx, ext)


def rename(dir, rename_dir, pattern, episodes, dir_title):

    """
    Renames files using path, file pattern and episodes fetched using anime_episodes()
    """

    pathAndFilenameList = sorted(list(glob.iglob(os.path.join(rename_dir, pattern))))

    renderables = []

    anitomy_options = {"allowed_delimiters": " -_.&+,|"}

    regexp = re.compile(r"([Pp][\d]+)")

    # Removes part number so that Anitomy doesn't fail
    anitomy_dict = [
        os.path.basename(re.sub(regexp, "", i)) for i in pathAndFilenameList
    ]
    anitomy_dict = [(anitopy.parse(i, options=anitomy_options)) for i in anitomy_dict]

    for i, file in enumerate(pathAndFilenameList):
        anitomy_dict[i]["file_name"] = os.path.basename(file)

    anitomy_dict = [i for i in anitomy_dict if "episode_number" in i]

    old_new = {os.path.join(os.path.dirname(rename_dir), dir_title): {}}

    for anitomy in anitomy_dict:

        pathAndFilename = os.path.join(rename_dir, anitomy["file_name"])

        title, ext = os.path.splitext(os.path.basename(pathAndFilename))

        ep_no = format_zeros(anitomy["episode_number"], len(anitomy_dict))

        episodeName = episodes[ep_no]

        ep_title_prefs = copy.deepcopy(settings.ep_prefs)

        ep_title_prefs.update({"en": ep_no, "et": episodeName})

        rename_string = config_format_parse(settings.episode_format, ep_title_prefs)
        # rename_string = settings.episode_format.format(**ep_title_prefs)

        old_new[os.path.join(os.path.dirname(rename_dir), dir_title)].update(
            {f"{rename_string}{ext}": f"{title}{ext}"}
        )

        renderables.append(Panel(f"[b]{title}\n\n[green]{rename_string}"))

        try:
            os.rename(
                pathAndFilename, os.path.join(rename_dir, f"{rename_string}{ext}")
            )
        except:
            pass

    os.rename(
        rename_dir,
        os.path.join(os.path.dirname(rename_dir), format_punctuations(dir_title)),
    )

    console.print(Columns(renderables))
    oldfilespath = os.path.join(os.path.dirname(dir), "ORIGINAL_EPISODE_FILENAMES")

    if not os.path.exists(oldfilespath):
        os.makedirs(oldfilespath)

    with open(
        os.path.join(
            oldfilespath,
            filename_fix_existing(
                f"{format_punctuations(dir_title)}.json", oldfilespath
            ),
        ),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(old_new, indent=4))


def walk_directory(directory: pathlib.Path, tree: Tree) -> None:

    """
    Recursively build a Tree with directory contents.
    """

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


def ani_parse_dir(
    directory: pathlib.Path, check_init_path=False, parsed_paths=[]
) -> None:

    """
    Recursively scans all sub directories to find the ones matching the required format.
    """

    paths = sorted(pathlib.Path(directory).iterdir())

    if check_init_path == True:
        if parse_dir(os.path.basename(directory)) != None:
            parsed_paths.append(directory)

    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        if path.is_dir():
            if parse_dir(path.name) != None:
                parsed_paths.append(path)
            ani_parse_dir(path, False, parsed_paths)

    return parsed_paths


def config_format_parse(format, args):

    format_split = re.findall(r"{[^}]*}|[\s\S]", format)

    for i, arg in enumerate(format_split):

        default = ""

        if str(arg).startswith("{") and str(arg).endswith("}"):

            arg = str(arg).strip("{}")
            arg_split = re.split(r"([\\+]|[\&+]|[\|]|[\s+])", arg)

            arg_split = [k for k in arg_split if k != ""]

            for j, sub_arg in enumerate(arg_split):

                if sub_arg == "&" and arg_split[j - 1] == "\\":
                    arg_split[j - 1 : j + 1] = ["".join(arg_split[j - 1 : j + 1])]

            match_count = 0

            for j, sub_arg in enumerate(arg_split):

                if (str(sub_arg) in args and arg_split[j - 1] == "&") or (
                    str(sub_arg) in args and j == 0
                ):
                    arg_split[j] = args[sub_arg]
                    match_count += 1

                if sub_arg == "|":
                    default = "".join(arg_split[j + 1 :])
                    del arg_split[j:]

            arg_split = [k for k in arg_split if k != "&" and k != "|"]
            arg_split = [k.strip("\\") if k == "\\&" else k for k in arg_split]

            none_count = len([k for k in arg_split if k == None])

            if None in arg_split and none_count == match_count:
                arg_split = [default]
            elif None in arg_split:
                for k, sub_arg in enumerate(arg_split):
                    if sub_arg == None:
                        arg_split[k] = default
                        if arg_split[k - 1].startswith("[") and arg_split[
                            k - 1
                        ].endswith("]"):
                            del arg_split[k - 1]
                        if arg_split[k + 1].startswith("(") and arg_split[
                            k + 1
                        ].endswith(")"):
                            del arg_split[k + 1]

            for k, sub_arg in enumerate(arg_split):
                if sub_arg.startswith(("[", "(")) and arg_split[k - 1] != "\\":
                    sub_arg = sub_arg.strip("[(")
                    arg_split[k] = sub_arg

                if sub_arg.startswith(("[", "(")) and arg_split[k - 1] == "\\":
                    del arg_split[k - 1]

                if (
                    sub_arg.endswith(("]", ")"))
                    and not sub_arg.startswith(("[", "("))
                    and arg_split[k - 1] != "\\"
                ):
                    sub_arg = sub_arg.strip("])")
                    arg_split[k] = sub_arg

                if (
                    not sub_arg.startswith(("[", "("))
                    and sub_arg.endswith(("]", ")"))
                    and arg_split[k - 1] == "\\"
                ):
                    del arg_split[k - 1]

            arg = arg_split

        format_split[i] = "".join(arg)

    return format_punctuations("".join(format_split))