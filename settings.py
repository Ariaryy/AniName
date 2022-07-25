def init():

    """
    Initializes the data in the conf file as global variables.
    """

    import configparser

    config_file = configparser.ConfigParser()
    config_file.read("conf.ini", encoding='utf8')

    global episode_format, episode_lang, episode_prefix, season_format, season_lang, season_prefix, part_prefix, seperator, season_metadata_format, season_display_format

    episode_format = config_file['formatting']['episode_format']
    episode_lang = config_file['preference']['episode_title']
    episode_prefix = config_file['preference']['episode_prefix']

    season_format = config_file['formatting']['season_format']
    season_lang = config_file['preference']['season_title']
    season_prefix = config_file['preference']['season_prefix']

    part_prefix = config_file['preference']['part_prefix']

    seperator = (config_file['preference']['seperator']).replace('"', '')

    season_display_format = "{season_prefix}{season_number}{part_prefix}{part_number}{seperator}{season_title}"

    season_metadata_format = {
    'season_prefix': season_prefix,
    'part_prefix': part_prefix,
    'seperator': seperator,
    'season_number': '',
    'season_title': '',
    'part_number': '',
}

def set_ep_prefs(ep_prefs_data):

    """
    Sets the episode preferences as a global variable that varies from anime to anime.
    """

    global ep_prefs
    ep_prefs = ep_prefs_data