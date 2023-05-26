import json
import glob, os, pathlib
import copy

import aniparse
import regex
import src.settings as settings

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text

console = Console()


def parse_dir(dir_basename):
    var = regex.search(r"^([\d]+)$|^([\d]+)([Ss][\d]+)([Pp][\d]+)?$", dir_basename)

    if var != None:
        var = [i for i in var.groups() if i != None]

        if len(var) == 1:
            var.append(["", ""])

        if len(var) == 2:
            var.append("")

        return var[0], var[1], var[2]

    return None


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

    string = regex.sub(":", " ", str(string))
    string = regex.sub(r'["\/<>\?\\\| +]+', " ", str(string))

    return string.strip()


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


def foldername_fix_existing(foldername, dirname):
    names = [x for x in os.listdir(dirname) if x.startswith(foldername)]
    suffixes = [x.replace(foldername, "") for x in names]
    suffixes = [x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")]
    indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return "%s (%d)" % (foldername, idx)


def rename(dir, rename_dir, pattern, episodes, dir_title):
    """
    Renames files using path, file pattern and episodes fetched using anime_episodes()
    """

    pathAndFilenameList = sorted(list(glob.iglob(os.path.join(rename_dir, pattern))))

    renderables = []

    anitomy_options = {"allowed_delimiters": " -_.&+,|"}

    regexp = regex.compile(r"([Pp][\d]+)")

    # Removes part number so that Anitomy doesn't fail
    anitomy_dict = [
        os.path.basename(regex.sub(regexp, "", i)) for i in pathAndFilenameList
    ]

    anitomy_dict = [(aniparse.parse(i, options=anitomy_options)) for i in anitomy_dict]

    for i, file in enumerate(pathAndFilenameList):
        anitomy_dict[i]["file_name"] = os.path.basename(file)

    anitomy_dict = [i for i in anitomy_dict if "episode_number" in i]

    dir_title = format_punctuations(dir_title)

    if os.path.exists(os.path.join(os.path.dirname(rename_dir), dir_title)):
        dir_title = foldername_fix_existing(dir_title, os.path.dirname(rename_dir))

    old_new = {os.path.join(os.path.dirname(rename_dir), dir_title): {}}

    for anitomy in anitomy_dict:
        pathAndFilename = os.path.join(rename_dir, anitomy["file_name"])

        title, ext = os.path.splitext(os.path.basename(pathAndFilename))

        ep_no = format_zeros(anitomy["episode_number"], len(episodes))

        episodeName = episodes[ep_no]

        ep_title_prefs = copy.deepcopy(settings.ep_prefs)

        ep_title_prefs.update({"en": ep_no, "et": episodeName})

        rename_string = (
            config_format_parse(settings.episode_format, ep_title_prefs) + ext
        )

        if (
            os.path.exists(os.path.join(rename_dir, rename_string))
            and os.path.join(rename_dir, rename_string) != pathAndFilename
        ):
            rename_string = filename_fix_existing(rename_string, rename_dir)

        try:
            os.rename(pathAndFilename, os.path.join(rename_dir, rename_string))
            renderables.append(Panel(f"[b]{title}\n\n[green]{rename_string}"))

            old_new[os.path.join(os.path.dirname(rename_dir), dir_title)].update(
                {f"{rename_string}": f"{title}{ext}"}
            )
        except:
            renderables.append(Panel(f"[b]{title}\n\n[red]Failed to rename"))

    console.print(Columns(renderables))

    try:
        os.rename(
            rename_dir,
            os.path.join(os.path.dirname(rename_dir), format_punctuations(dir_title)),
        )
    except:
        pass

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
    format_split = regex.split(r"{((?:[^{}]|(?R))*)}", format)

    format_split = list(filter(None, format_split))

    for i, arg in enumerate(format_split[:]):
        arg_split = regex.split(r"([\\+]|[\&+]|[\|]|[\s+])", arg)

        default = ""

        if arg_split[len(arg_split) - 2] == "|":
            default = arg_split[len(arg_split) - 1]
            arg_split = arg_split[:-2]

        arg_split = list(filter(None, arg_split))

        new_arg_split = []

        for j, sub_arg in enumerate(arg_split):
            if sub_arg == "\\":
                pass
            elif sub_arg == "&":
                if arg_split[j - 1] == "\\":
                    new_arg_split.append(sub_arg)
            elif str(sub_arg) in args:
                if args[sub_arg] == None:
                    new_arg_split = [default]
                    break
                new_arg_split.append(args[arg_split[j]])
            else:
                new_arg_split.append(sub_arg)

        format_split[i] = "".join(new_arg_split)

    format_split = list(filter(None, format_split))

    while True:
        if format_split[0].startswith("{") and format_split[0].endswith("}"):
            del format_split[0]
            if len(format_split) == 0:
                break
        else:
            break

    for i, arg in enumerate(format_split[:]):
        if arg.startswith("{") and arg.endswith("}"):
            format_split[i] = str(format_split[i])[1:-1]

    if len(format_split) == 0:
        format_split.append("Episode name not found")

    return format_punctuations("".join(format_split))
