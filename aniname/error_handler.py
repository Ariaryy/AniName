"""
Contains a class with static methods to print appropriate error messages and exit.
"""

import asyncio
import sys

from rich.console import Console

from . import http_session, utils

CONSOLE = Console()

NO_MATCHING_DIR = """[b][red]No directories matching the scan format were found.
[yellow]Learn more about directory formatting: \
[blue]https://github.com/Ariaryy/AniName#anime-folder-formatting\n"""

CONFIG_PARSE_ERROR = """[red][b]There was an error while parsing the config file (conf.ini)
        
Error:
{exception}

[yellow]Resolve the error or delete the conf.ini file and try again.\n"""

CONFIG_KEY_ERROR = """[red][b]A variable seems to be missing in the config file (conf.ini)
            
        
Error:
{exception}

[yellow]Resolve the error or delete the conf.ini file and try again.\n"""

RESTORE_NOT_FOUND = """
[b][red]The directory of the files whose names are to be restored does not exist.
        
[yellow]Please make sure the following path exists:
[u]{dir_path}[not u]
        
[yellow]Alternatively, you can try editing the path in the [u]{json_file}.json[not u] file to fix the issue.\n"""

NO_BACKUP_FOUND = """[b][red]No backup files were found."""


class HandleError:
    """
    A class with static methods to print errors.
    """

    @staticmethod
    def print_exit(error_message: str, exit: bool=True) -> None:
        CONSOLE.print(error_message)

        if (exit):
            asyncio.create_task(http_session.close_client_session())
            utils.pause()
            sys.exit()

    @staticmethod
    def no_matching_dir() -> None:
        """
        Prints an error message when no directories matching the scan format were found.
        """

        HandleError.print_exit(NO_MATCHING_DIR)

    @staticmethod
    def config_parsing_error(exception: Exception) -> None:
        """
        Prints an error message when there's an error parsing the config file.
        """

        HandleError.print_exit(
            CONFIG_PARSE_ERROR.format(
                exception=f"{type(exception).__name__} - {exception}"
            )
        )

    @staticmethod
    def config_key_error(exception: Exception) -> None:
        """
        Prints an error message when there's a missing key in the config file.
        """

        HandleError.print_exit(
            CONFIG_KEY_ERROR.format(
                exception=f"{type(exception).__name__} - {exception}"
            )
        )

    @staticmethod
    def restore_not_found(dir_path: str, json_file: str) -> None:
        """
        Prints an error message when the restore directory does not exist.
        """

        HandleError.print_exit(
            RESTORE_NOT_FOUND.format(dir_path=str(dir_path), json_file=json_file), exit=False
        )

    @staticmethod
    def no_backup_found() -> None:
        """
        Prints an error message when no directories matching the scan format were found.
        """

        HandleError.print_exit(NO_BACKUP_FOUND)