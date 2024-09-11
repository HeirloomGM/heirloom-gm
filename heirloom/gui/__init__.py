import os

import dearpygui.dearpygui as dpg

from ..heirloom import Heirloom
from ..password_functions import *
from ..path_functions import *
from ..database_functions import *
from ..config import *


class Tile:
    def __init__(self, image_path, title, description):
        self.image_path = image_path
        self.title = title
        self.description = description


def create_tiles():
    tiles = [
        Tile("image1.png", "Image 1", "Description for Image 1"),
        Tile("image2.png", "Image 2", "Description for Image 2"),
        Tile("image3.png", "Image 3", "Description for Image 3")
    ]
    return tiles


def create_tile_widgets(tiles):
    for tile in tiles:
        with dpg.handler_registry():
            with dpg.group(horizontal=True):
                dpg.add_image(tile.image_path, width=100, height=100)
                dpg.add_text(tile.title)
                dpg.add_text(tile.description)


def merge_game_data_with_db():
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


def main():
    dpg.create_context()
    dpg.create_window(title="Tile GUI")
    tiles = create_tiles()
    create_tile_widgets(tiles)
    dpg.show_toolbars()
    dpg.show_metrics()
    dpg.show_debug()


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

main()