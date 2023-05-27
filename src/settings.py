import configparser, sys, os
from rich.console import Console


def init(conf_path):
    """
    Initializes the data in the conf file as global variables.
    """

    try:
        with open(conf_path, "x") as f:
            f.write(
                """# Guide: https://github.com/AbhiramH427/AniName#config-file
            
[preferences]
                        
season_title_language = english 
episode_title_language = english

[formatting]

episode_format = {S&sn|}{P&pn|}{E&en|}{{ - }}{et|}
season_format = {S&sn|}{P&pn|}{{ - }}{st|}"""
            )
    except:
        pass

    config_file = configparser.ConfigParser()
    config_file.read(conf_path, encoding="utf8")

    global episode_format, episode_lang, season_format, season_lang, season_metadata_format, season_display_format

    try:
        episode_format = config_file["formatting"]["episode_format"]
        episode_lang = config_file["preferences"]["season_title_language"]

        season_format = config_file["formatting"]["season_format"]
        season_lang = config_file["preferences"]["season_title_language"]
    except Exception as e:
        console = Console()
        console.print(
            f"[red][b]There seems be an error in the config file (conf.ini)\n\nError:\n{type(e).__name__} - {e}\n\n[yellow]Resolve the error or delete the conf.ini file and try again.\n"
        )
        os.system("pause")
        sys.exit()

    season_display_format = r"{S&sn|}{P&pn|}{{ - }}{st|}"

    season_metadata_format = {
        "sn": None,
        "pn": None,
        "st": None,
    }


def set_ep_prefs(ep_prefs_data):
    """
    Sets the episode preferencess as a global variable that varies from anime to anime.
    """

    global ep_prefs
    ep_prefs = ep_prefs_data
