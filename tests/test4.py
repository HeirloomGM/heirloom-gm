import os
from importlib.resources import files

import requests
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


def download_artwork():
    if not os.path.exists(heirloom._tmp_dir):
        os.makedirs(heirloom._tmp_dir)
    for g in heirloom.games:
        coverart_url = g.get('game_coverart')
        game_id = g.get('game_id')
        if not os.path.exists(heirloom._tmp_dir + os.path.sep + f'{game_id}.jpg'):
            r = requests.get(coverart_url)
            content = r.content
            if content:
                with open(heirloom._tmp_dir + os.path.sep + f'{game_id}.jpg', 'wb') as f:
                    f.write(content)


def create_tiles():
    tiles = []
    for g in heirloom.games:
        image_source = os.path.join(heirloom._tmp_dir, f'{g.get("game_id")}.jpg')
        game_name = g.get('game_name')
        game_description = g.get('game_description')
        tiles.append(Tile(image_source, game_name, game_description))
    return tiles


def create_tile_widgets(tiles):
    with dpg.font_registry():
        regular_font = files(__package__).joinpath('fonts', 'Roboto-Regular.ttf')
        bold_font = files(__package__).joinpath('fonts', 'Roboto-Bold.ttf')
        italic_font = files(__package__).joinpath('fonts', 'Roboto-Italic.ttf')
        bold_italic_font = files(__package__).joinpath('fonts', 'Roboto-BoldItalic.ttf')
        roboto_regular = dpg.add_font(regular_font, 18, default_font=True)
        roboto_bold = dpg.add_font(bold_font, 24)
        roboto_italic = dpg.add_font(italic_font, 18)
        roboto_bold_italic = dpg.add_font(bold_italic_font, 18)
    for tile in tiles:
        width, height, channels, data = dpg.load_image(tile.image_path)
        with dpg.texture_registry():
            dpg.add_static_texture(width=width, height=height, default_value=data, tag=tile.title)
        with dpg.group(horizontal=True):
            dpg.add_image(tile.title, width=200, height=200)
            with dpg.group():
                title = dpg.add_text(tile.title, wrap=600)
                dpg.bind_item_font(title, roboto_bold)
                desc = dpg.add_text(tile.description, wrap=600)
                dpg.bind_item_font(desc, roboto_regular)
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Install', callback=lambda: heirloom.install_game(tile.title))
                    dpg.add_button(label='Uninstall', callback=lambda: heirloom.uninstall_game(tile.title), show=False)


def merge_game_data_with_db():
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


def create_menu_bar():
    with dpg.viewport_menu_bar():
        with dpg.menu(label='File'):
            dpg.add_menu_item(label='Exit', callback=dpg.stop_dearpygui)
        with dpg.menu(label='Help'):
            dpg.add_menu_item(label='About', callback=lambda: dpg.show_tool('About'))


def main():
    download_artwork()
    dpg.create_context()
    dpg.create_viewport(title='Heirloom Games Manager', width=1280, height=800)
    create_menu_bar()
    
    with dpg.window(tag="Primary Window", autosize=True, no_resize=True, no_move=True, no_collapse=True):
        tiles = create_tiles()
        create_tile_widgets(tiles)
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()



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

