"""
Contains dataclass and methods required to use a config file.
"""

from configparser import ConfigParser, ParsingError
from dataclasses import dataclass, field
from pathlib import Path

import regex

from .error_handler import HandleError
from .utils import format_punctuations


@dataclass(slots=True)
class Config:
    """
    A dataclass containing options from the config file.
    """

    ep_title_format: str = field(init=False, default_factory=str)
    anime_title_format: str = field(init=False, default_factory=str)
    ep_title_lang: str = field(init=False, default_factory=str)
    anime_title_lang: str = field(init=False, default_factory=str)

    def init(self, conf_path: Path) -> None:
        """
        Initializes the data in the conf file to the object.
        """

        try:
            with open(conf_path, "x", encoding="utf-8") as file:
                file.write(
                    """# Guide: https://github.com/AbhiramH427/AniName#config-file
                
[preferences]
                        
season_title_language = english 
episode_title_language = english

[formatting]

episode_format = {S&sn|}{P&pn|}{E&en|}{{ - }}{et|}
season_format = {S&sn|}{P&pn|}{{ - }}{st|}"""
                )
        except FileExistsError:
            pass

        config_file = ConfigParser()

        try:
            config_file.read(conf_path, encoding="utf8")
        except ParsingError as exception:
            HandleError.config_parsing_error(exception)

        try:
            self.ep_title_format = config_file["formatting"]["episode_format"]
            self.ep_title_lang = config_file["preferences"]["season_title_language"]

            self.anime_title_format = config_file["formatting"]["season_format"]
            self.anime_title_lang = config_file["preferences"]["season_title_language"]
        except KeyError as exception:
            HandleError.config_key_error(exception)

    @staticmethod
    def config_format_parse(title_format: str, args: dict) -> str:
        """
        Parses config format and replaces variables with values.
        """

        format_split = regex.split(r"{((?:[^{}]|(?R))*)}", title_format)

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
                    if args[sub_arg] is None:
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
