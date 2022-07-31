def init():

    """
    Initializes the data in the conf file as global variables.
    """

    import configparser

    config_file = configparser.ConfigParser()
    config_file.read("conf.ini", encoding='utf8')

    global episode_format, episode_lang, episode_prefix, season_format, season_lang, season_prefix, part_prefix, separator, season_metadata_format, season_display_format

    episode_format = config_file['formatting']['episode_format']
    episode_lang = config_file['preferences']['episode_title']
    episode_prefix = config_file['preferences']['episode_prefix']

    season_format = config_file['formatting']['season_format']
    season_lang = config_file['preferences']['season_title']
    season_prefix = config_file['preferences']['season_prefix']

    part_prefix = config_file['preferences']['part_prefix']

    separator = (config_file['preferences']['separator']).replace('"', '')

    season_display_format = "{season_prefix}{season_number}{part_prefix}{part_number}{separator}{season_title}"

    season_metadata_format = {
    'season_prefix': season_prefix,
    'part_prefix': part_prefix,
    'separator': separator,
    'season_number': '',
    'season_title': '',
    'part_number': '',
}

def set_ep_prefs(ep_prefs_data):

    """
    Sets the episode preferencess as a global variable that varies from anime to anime.
    """

    global ep_prefs
    ep_prefs = ep_prefs_data