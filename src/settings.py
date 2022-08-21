def init():

    """
    Initializes the data in the conf file as global variables.
    """

    import configparser

    config_file = configparser.ConfigParser()
    config_file.read("conf.ini", encoding="utf8")

    global episode_format, episode_lang, season_format, season_lang, season_metadata_format, season_display_format

    episode_format = config_file["formatting"]["episode_format"]
    episode_lang = config_file["preferences"]["season_title_language"]

    season_format = config_file["formatting"]["season_format"]
    season_lang = config_file["preferences"]["season_title_language"]

    season_display_format = r"{[S]&sn&[P]&pn& - |}{st|}"

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
