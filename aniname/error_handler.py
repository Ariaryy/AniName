"""
Contains a class with static methods to print respective error messages on the screen.
"""

from rich.console import Console

console = Console()


def pause() -> None:
    """
    Pauses program until the Enter key is pressed
    """

    input("Press the Enter key to continue . . .")


class HandleError:
    """
    A class with static methods to print errors.
    """

    @staticmethod
    def no_matching_dir() -> None:
        """
        Prints an error message when no directories matching the scan format were found.
        """

        console.print(
            """[b][red]No directories matching the scan format were found.
[yellow]Learn more about directory formatting: \
[blue]https://github.com/Ariaryy/AniName#anime-folder-formatting\n"""
        )

        pause()
        exit()

    @staticmethod
    def config_parsing_error(exception: Exception) -> None:
        """
        Prints an error message when there's an error parsing the config file.
        """

        console.print(
            f"""[red][b]There was an error while parsing the config file (conf.ini)
        
Error:
{type(exception).__name__} - {exception}

[yellow]Resolve the error or delete the conf.ini file and try again.\n"""
        )

        pause()
        exit()

    @staticmethod
    def config_key_error(exception: Exception) -> None:
        """
        Prints an error message when there's a missing key in the config file.
        """

        console.print(
            f"""[red][b]A variable seems to be missing in the config file (conf.ini)
            
        
Error:
{type(exception).__name__} - {exception}

[yellow]Resolve the error or delete the conf.ini file and try again.\n"""
        )

        pause()
        exit()

    @staticmethod
    def restore_not_found(dir_path: str, json_file: str) -> None:
        """
        Prints an error message when the restore directory does not exist.
        """

        console.print(
            f"""
[b][red]The directory of the files whose names are to be restored does not exist.
        
[yellow]Please make sure the following path exists:
[u]{str(dir_path)}[not u]
        
[yellow]Alternatively, you can try editing the path in the [u]{json_file}.json[not u] file to fix the issue.\n"""
        )

        pause()
        exit()
