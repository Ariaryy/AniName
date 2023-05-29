import copy
import json
from pathlib import Path

import aniparse
import regex
from rich.columns import Columns
from rich.console import Console
from rich.filesize import decimal
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

import src.settings as settings

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


def filename_fix_existing(filename: str, dir: Path) -> str:
    """
    Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """

    name, ext = filename.rsplit(".", 1)
    names = [x.name for x in dir.iterdir() if x.name.startswith(name)]
    names = [x.rsplit(".", 1)[0] for x in names]
    suffixes = [x.replace(name, "") for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")]
    indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return "%s (%d).%s" % (name, idx, ext)


def foldername_fix_existing(foldername: str, dir: Path) -> str:
    names = [x.name for x in dir.iterdir() if x.name.startswith(foldername)]
    suffixes = [x.replace(foldername, "") for x in names]
    suffixes = [x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")]
    indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return "%s (%d)" % (foldername, idx)


def rename(
    ani_scan_dir: Path,
    rename_dir: Path,
    ep_data: dict,
    new_dir_name: str,
    match_pattern=r"*.mkv",
):
    """
    Renames files using path, file pattern and episodes fetched using anime_episodes()
    """

    ep_file_paths = sorted(list((rename_dir).glob(match_pattern)))

    console_renderables = []

    anitomy_options = {"allowed_delimiters": " -_.&+,|"}

    # Removes part number so that Anitomy doesn't fail
    anitomy_dict = [regex.sub(r"([Pp][\d]+)", "", i.name) for i in ep_file_paths]

    anitomy_dict = [(aniparse.parse(i, options=anitomy_options)) for i in anitomy_dict]

    for i, ep_file in enumerate(ep_file_paths):
        anitomy_dict[i]["file_name"] = ep_file.name

    anitomy_dict = [i for i in anitomy_dict if "episode_number" in i]

    backup_ep_names = {str(rename_dir.parent / new_dir_name): {}}

    for anitomy in anitomy_dict:
        ep_file_path = rename_dir / anitomy["file_name"]

        old_ep_filename = ep_file_path.stem
        file_ext = ep_file_path.suffix

        ep_no = format_zeros(anitomy["episode_number"], len(ep_data))

        episode_title = ep_data[ep_no]

        ep_title_prefs = copy.deepcopy(settings.ep_prefs)

        ep_title_prefs.update({"en": ep_no, "et": episode_title})

        new_ep_filename = (
            config_format_parse(settings.episode_format, ep_title_prefs) + file_ext
        )

        if (
            rename_dir / new_ep_filename
        ).exists() and rename_dir / new_ep_filename != ep_file_path:
            new_ep_filename = filename_fix_existing(new_ep_filename, rename_dir)

        try:
            ep_file_path.rename(rename_dir / new_ep_filename)

            console_renderables.append(
                Panel(f"[b]{old_ep_filename + file_ext}\n\n[green]{new_ep_filename}")
            )

            backup_ep_names[str(rename_dir.parent / new_dir_name)].update(
                {f"{new_ep_filename}": f"{old_ep_filename}{file_ext}"}
            )
        except:
            console_renderables.append(
                Panel(f"[b]{old_ep_filename}\n\n[red]Failed to rename")
            )

    console.print(Columns(console_renderables))

    try:
        rename_dir.rename(rename_dir.parent / new_dir_name)
    except:
        pass

    backup_dir = ani_scan_dir.parent / "ORIGINAL_EPISODE_FILENAMES"

    if not backup_dir.exists():
        backup_dir.mkdir()

    with open(
        backup_dir / filename_fix_existing(f"{new_dir_name}.json", backup_dir),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(backup_ep_names, indent=4))


def walk_directory(directory: Path, tree: Tree) -> None:
    """
    Recursively build a Tree with directory contents.
    """

    # Credits: https://github.com/Textualize/rich/blob/master/examples/tree.py

    # Sort dirs first then by filename
    paths = sorted(
        directory.iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            branch = tree.add(
                f"[bold magenta]:open_file_folder: [link {path.as_uri()}]{escape(path.name)}",
                style=style,
                guide_style=style,
            )
            walk_directory(path, branch)
        else:
            text_filename = Text(path.name, "green")
            #text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link {path.as_uri()}")
            #file_size = path.stat().st_size
            #text_filename.append(f" ({decimal(file_size)})", "blue")
            icon = "📺 " if path.suffix == ".mkv" else "📄 "
            tree.add(Text(icon) + text_filename)


def ani_parse_dir(
    directory: Path, check_init_path=False, parsed_paths=[]
) -> list[Path]:
    """
    Recursively scans all sub directories to find the ones matching the required format.
    """

    paths = sorted(list(directory.iterdir()))

    if check_init_path == True:
        if parse_dir(directory.name) != None:
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
