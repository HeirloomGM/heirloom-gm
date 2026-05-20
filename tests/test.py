import os
from heirloom import Heirloom
from heirloom.password_functions import *
from heirloom.config import *
from heirloom.database_functions import *
from rich.pretty import pprint


def merge_game_data_with_db():
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()
if not encryption_key:
    set_encryption_key()
    encryption_key = get_encryption_key()
configparser = get_config(config_dir)
config = dict(configparser['HeirloomGM'])
heirloom = Heirloom(**config)
try:
    user_id = heirloom.login()
except Exception as e:
    raise(e)
try:
    heirloom.refresh_games_list()
    config['db'] = init_games_db(config_dir, heirloom.games)
    merge_game_data_with_db()
    refresh_game_installation_status(config['db'])
except Exception as e:
    raise(e)

for g in heirloom.games:
    pprint(g)
