"""
Contains utility functions required by other modules.
"""

from pathlib import Path

import regex
from aniparse import parse as aniparse
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree

ANITOMY_OPTIONS = {"allowed_delimiters": " -_.&+,|"}


def parse_dir_basename(dir_basename: str) -> tuple:
    """
    Parses folder name and returns MyAnimeList ID, Season number and Part number
    """

    basename_slice = regex.search(
        r"^([\d]+)$|^([\d]+)[Ss]([\d]+)(?:[Pp]([\d]+))?$", dir_basename
    )

    if basename_slice is None:
        return None

    basename_slice = list(filter(None, basename_slice.groups()))

    if len(basename_slice) == 1:
        basename_slice.extend([None, None])

    if len(basename_slice) == 2:
        basename_slice.append(None)

    return basename_slice[0], basename_slice[1], basename_slice[2]


def remove_part_no(dir_name: str) -> str:
    """
    Removes part number from episode filename.
    """

    return regex.sub(r"([Pp][\d]+)", "", dir_name)


def get_local_ep_range(ani_dir: Path, match_pattern=r"*.mkv") -> tuple[int]:
    """
    Gets the range of episodes files present in a directory.
    """

    ep_paths = list(ani_dir.glob(match_pattern))

    ep_no_list = [
        int(
            aniparse(remove_part_no(ep_path.stem), options=ANITOMY_OPTIONS)[
                "episode_number"
            ]
        )
        for ep_path in ep_paths
    ]

    return min(ep_no_list), max(ep_no_list)


def format_zeros(number: int, max_number=1) -> str:
    """
    Adds an appropriate number of leading zeros to a number based on the max number.
    """

    if number is None:
        return None

    if max_number < 10:
        max_number *= 10
    return str(number).zfill(len(str(max_number)))


def create_anitomy_dict(ep_file_paths: list[Path]) -> list[dict]:
    """
    Creates a dict with parsed episode filenames.
    """

    anitomy_dict = [
        (aniparse(remove_part_no(path.name), options=ANITOMY_OPTIONS))
        for path in ep_file_paths
    ]

    for i, ep_file in enumerate(ep_file_paths):
        anitomy_dict[i]["file_name"] = ep_file.name

    anitomy_dict = [anitomy for anitomy in anitomy_dict if "episode_number" in anitomy]

    return anitomy_dict


def format_punctuations(dir_basename: str) -> str:
    """
    Returns string with punctuations appropriate for Windows file name.
    """

    dir_basename = regex.sub(":", " ", str(dir_basename))
    dir_basename = regex.sub(r'["\/<>\?\\\| +]+', " ", str(dir_basename))

    return dir_basename.strip()


def path_fix_exisiting(name: str, dir_path: Path) -> str:
    """
    Expands name portion of file/folder name with numeric ' (x)' suffix to
    return name that doesn't exist already.
    """


    name_split = name.rsplit(".", 1)
    name = name_split[0]
    ext = "." + name_split[1] if len(name_split) == 2 else ""

    names = [x.name for x in dir_path.iterdir() if x.name.startswith(name)]
    names = [x.rsplit(".", 1)[0] for x in names]

    suffixes = [x.replace(name, "") for x in names]

    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes if x.startswith(" (") and x.endswith(")")]

    indexes = [int(x) for x in suffixes if set(x) <= set("0123456789")]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]

    return f"{name} ({idx}){ext}"


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
            # text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link {path.as_uri()}")
            # file_size = path.stat().st_size
            # text_filename.append(f" ({decimal(file_size)})", "blue")
            icon = "📺 " if path.suffix == ".mkv" else "📄 "
            tree.add(Text(icon) + text_filename)


def find_ani_subdir(dir_path: Path, match_pattern=r"*.mkv") -> list[Path]:
    """
    Scans all sub directories to find the ones matching the required format.
    """

    scan_result = []

    matching_paths = dir_path.rglob(match_pattern)
    for path in matching_paths:
        if (
            not path.parent in scan_result
            and parse_dir_basename(path.parent.name) is not None
        ):
            scan_result.append(path.parent)

    return scan_result
