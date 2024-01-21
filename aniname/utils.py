"""
Contains utility functions required by other modules.
"""

from pathlib import Path

import regex
from aniparse import parse as aniparse
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree

EP_ANITOMY_OPTIONS = {"allowed_delimiters": " -_.&+,|"}
ANI_ANITOMY_OPTIONS = {
    "allowed_delimiters": " -_.&+,|",
    "title_before_episode": "false",
}


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
            aniparse(remove_part_no(ep_path.stem), options=EP_ANITOMY_OPTIONS)[
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


def episode_anitomy_dict(ep_file_paths: list[Path]) -> list[dict]:
    """
    Creates a dictionary with parsed episode filenames.
    """

    anitomy_dict = [
        (aniparse(remove_part_no(path.name), options=EP_ANITOMY_OPTIONS))
        for path in ep_file_paths
    ]

    for i, ep_file in enumerate(ep_file_paths):
        anitomy_dict[i]["file_name"] = ep_file.name

    anitomy_dict = [anitomy for anitomy in anitomy_dict if "episode_number" in anitomy]

    return anitomy_dict


def anime_anitomy_dict(anime_file_paths: list[Path]) -> list[dict]:
    """
    Creates a dictionary with parsed anime titles.
    """

    anitomy_dict = [
        (aniparse(path.name, options=ANI_ANITOMY_OPTIONS)) for path in anime_file_paths
    ]

    for i, ani_dict in enumerate(anime_file_paths):
        anitomy_dict[i]["path"] = ani_dict

    return anitomy_dict


def format_punctuations(dir_basename: str) -> str:
    """
    Returns string with punctuations appropriate for Windows file name.
    """

    dir_basename = regex.sub(":", " ", str(dir_basename))
    dir_basename = regex.sub(r'["\/<>\?\\\| +]+', " ", str(dir_basename))

    return dir_basename.strip()


def path_fix_exisiting(new_path: Path) -> Path:
    """
    Expands name portion of file/folder name with numeric ' (x)' suffix to
    return name that doesn't exist already.
    """

    name = new_path.name
    dir_path = new_path.parent

    if not (dir_path / name).exists():
        return dir_path / name

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

    return dir_path / f"{name} ({idx}){ext}"


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


def find_formatted_subdir(dir_path: Path, match_pattern=r"*.mkv") -> list[Path]:
    """
    Scans all sub directories to find the ones having .mkv files and matching the required format.
    """

    scan_result: set[Path] = set()

    matching_paths = dir_path.rglob(match_pattern)
    for path in matching_paths:
        if parse_dir_basename(path.parent.name) is not None:
            scan_result.add(Path(path.parent))

    return list(scan_result)


def find_ani_subdir(dir_path: Path, match_pattern=r"*.mkv") -> list[Path]:
    """
    Scans all sub directories to find the ones having .mkv files.
    """

    scan_result: set[Path] = set()

    matching_paths = dir_path.rglob(match_pattern)
    for path in matching_paths:
        if parse_dir_basename(path.parent.name) is None:
            scan_result.add(path.parent)

    return list(scan_result)


def pause() -> None:
    """
    Pauses program until the Enter key is pressed
    """

    input("Press the Enter key to continue . . .")