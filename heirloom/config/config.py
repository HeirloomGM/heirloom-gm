import os
import shutil
from rich.console import Console
from InquirerPy import inquirer
from configparser import ConfigParser

from ..password_functions import *


def get_config(config_dir):
    console = Console()
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
    config_file = config_dir + 'config.ini'
    config_parser = ConfigParser(default_section='HeirloomGM')
    if not os.path.isfile(config_file) or os.path.getsize(config_file) == 0:
        console.print(f'Configuration file not found: [yellow]{config_file}[/yellow]')
        console.print('Please enter your login credentials for Legacy Games.')
        config_parser.set('HeirloomGM', 'user', inquirer.text('Enter username or email: ').execute())
        config_parser.set('HeirloomGM', 'password', inquirer.secret('Enter password: ').execute())
        config_parser.set('HeirloomGM', 'base_install_dir', inquirer.filepath('Enter base installation folder: ', default=os.path.expanduser('~/Games/LegacyGames/')).execute())
        config_parser.set('HeirloomGM', 'wine_path', inquirer.text('Path to Wine executable: ', default=shutil.which('wine')).execute())
        config_parser.set('HeirloomGM', '7zip_path', inquirer.text('Path to 7zip executable: ', default=shutil.which('7z')).execute())
        config_parser.set('HeirloomGM', 'default_installation_method', inquirer.select('Default installation method: ', choices=['7zip', 'wine'], default='7zip').execute())
        save_file = inquirer.confirm(f'Save configuration file to {os.path.expanduser(config_file)}?').execute()
        if save_file:
            config_parser.set('HeirloomGM', 'password', encrypt_password(config_parser.get('HeirloomGM', 'password')).decode('utf-8'))
            with open(os.path.expanduser(config_file), 'w') as cf:
                config_parser.write(cf)
            with open(os.path.expanduser(config_file), 'r') as cf:
                config_data = ConfigParser(default_section='HeirloomGM')
                config_data.read_file(cf)
                config_data.set('HeirloomGM', 'password', decrypt_password(config_data.get('HeirloomGM', 'password')).decode('utf-8'))
        else:
            config_data = config_parser['HeirloomGM']
    else:
        with open(os.path.expanduser(config_file), 'r') as cf:
            config_data = ConfigParser(default_section='HeirloomGM')
            config_data.read_file(cf)
            config_data.set('HeirloomGM', 'password', decrypt_password(config_data.get('HeirloomGM', 'password')).decode('utf-8'))
    return config_data
