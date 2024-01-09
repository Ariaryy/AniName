import os
from pathlib import Path

from appdirs import user_config_dir

from .config import Config

config_dir = Path(user_config_dir("AniName", False, roaming=True))

os.makedirs(config_dir, exist_ok=True)

conf_file_path = config_dir / "conf.ini"

conf = Config(conf_file_path)
