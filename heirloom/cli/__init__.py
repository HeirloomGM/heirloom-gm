import atexit
import base64
import json
import os
import sqlite3
import shutil
from enum import Enum

import keyring
import rich
import typer
from cryptography.fernet import Fernet
from InquirerPy import prompt
from typing_extensions import Annotated

from ..heirloom import Heirloom


class InstallationMethod(str, Enum):
    wine = 'wine'
    sevenzip = '7zip'
    

def get_config():
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
    config_file = config_dir + 'config.json'
    if not os.path.isfile(config_file) or os.path.getsize(config_file) == 0:
        console.print(f'Configuration file not found: [yellow]{config_file}[/yellow]')
        console.print('Please enter your login credentials for Legacy Games.')
        questions = [
            {
                'type': 'input',
                'name': 'user',
                'message': 'Enter username or email: '
            },
            {
                'type': 'password',
                'name': 'password',
                'message': 'Enter password: '
            },
            {
                'type': 'input',
                'name': 'base_install_dir',
                'default': os.path.expanduser('~/Games/LegacyGames/'),
                'message': 'Enter base installation folder: '
            },
            {
                'type': 'input',
                'name': 'wine_path',
                'message': 'Path to Wine executable: ',
                'default': shutil.which('wine') or '/usr/bin/wine'
            },
            {
                'type': 'input',
                'name': '7zip_path',
                'message': 'Path to 7zip executable: ',
                'default': shutil.which('7z') or '/usr/bin/7z'
            }
        ]
        answers = prompt(questions)
        questions = [
            {
                'type': 'confirm',
                'name': 'save_config_file',
                'message': f'Save configuration file to {os.path.expanduser(config_file)}?'
            }
        ]
        save_file = prompt(questions)
        if save_file['save_config_file']:
            answers['password'] = encrypt_password(answers['password']).decode('utf-8')
            with open(os.path.expanduser(config_file), 'w') as cf:
                cf.write(json.dumps(answers, indent=4))
            with open(os.path.expanduser(config_file), 'r') as f:
                config_data = json.loads(f.read())
                config_data['password'] = decrypt_password(config_data['password']).decode('utf-8')
        else:
            config_data = answers
    else:
        with open(os.path.expanduser(config_file), 'r') as f:
            config_data = json.loads(f.read())
            config_data['password'] = decrypt_password(config_data['password']).decode('utf-8')
    return config_data


def init_games_db():
    existing = True if os.path.isfile(config_dir + 'games.db') else False
    db = sqlite3.connect(config_dir + 'games.db')
    if not existing:
        sql = 'CREATE TABLE games(name, uuid, install_dir);'
        cursor = db.cursor()
        cursor.execute(sql)
    return db


def set_encryption_key():
    key = Fernet.generate_key()
    keyring.set_password('system', 'heirloom-encryption-key', base64.b64encode(key).decode('utf-8'))

def get_encryption_key():
    key = keyring.get_password('system', 'heirloom-encryption-key')
    if key:
        return base64.b64decode(key.encode('utf-8'))
    else:
        return None

def encrypt_password(password):
    key = get_encryption_key()
    f = Fernet(key)
    token = f.encrypt(password.encode('utf-8'))
    return token

def decrypt_password(password):
    key = get_encryption_key()
    f = Fernet(key)
    token = f.decrypt(password.encode('utf-8'))
    return token


def select_from_games_list():
    heirloom.refresh_games_list()
    choices = [{'name': g['game_name'], 'value': g['game_name']} for g in heirloom.games]
    question = [
        {
            'type': 'list',
            'name': 'game',
            'message': 'Select a game: ',
            'choices': choices
        }
    ]
    game = prompt(question)['game']
    return game


console = rich.console.Console()
app = typer.Typer(rich_markup_mode='rich')


@app.command('list')
def list_games():
    """
    Lists games in your Legacy Games library.
    """
    heirloom.refresh_games_list()
    table = rich.table.Table(title='Legacy Games')
    table.add_column("Game Name", justify="left", style="yellow")
    table.add_column("UUID", justify="center", style="green")
    table.add_column("Installed?", justify="right", style="red")
    for g in heirloom.games:
        table.add_row(g['game_name'], g['installer_uuid'], "Unknown")
    console.print(table)
    

@app.command('download')
def download(game: Annotated[str, typer.Option(help='Game name to download, will be prompted if not provided')] = None,
             uuid: Annotated[str, typer.Option(help='UUID of game to download, will be prompted for game name if not provided')] = None):
    """
    Downloads a game from the Legacy Games library and saves the installation file to the current folder.
    """
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    fn = heirloom.download_game(game, output_dir='./')
    console.print(f'Successfully downloaded [bold blue]{game}[/bold blue] setup executable as [green]{fn}[/green]')


@app.command('install')
def install(game: Annotated[str, typer.Option(help='Game name to download, will be prompted if not provided')] = None,
            uuid: Annotated[str, typer.Option(help='UUID of game to download, will be prompted for game name if not provided')] = None,
            install_method: Annotated[InstallationMethod, typer.Option(case_sensitive=False)] = None):
    """
    Installs a game from the Legacy Games library.    
    """
    while not config.get('base_install_dir'):
        config['base_install_dir'] = input('Enter base installation folder: ')
    if not os.path.isdir(os.path.expanduser(config['base_install_dir'])):
        os.makedirs(os.path.expanduser(config['base_install_dir']))
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    if install_method:
        result = heirloom.install_game(game, installation_method=install_method.value)
    else:
        result = heirloom.install_game(game)
    if result.get('status') == 'success':
        console.print(f'Installation to [green]{result["install_path"]}[/green] successful! :grin:')
        if result.get('executable_files') and len(result.get('executable_files')) == 1:
            console.print(f'To start game, run: [yellow]{config["wine_path"]} {config["base_install_dir"]}{result["executable_files"][0]}[/yellow]')
        elif result.get('executable_files') and len(result.get('executable_files')) > 1:
            console.print(f':exclamation: Ambiguous executable detected; game may be any one of: {result.get("executable_files")}')
    else:
        console.print(result)
        console.print(f'[bold]Installation [red italic]unsuccessful[/red italic]! :frowning:')


@app.command('info')
def info(game: Annotated[str, typer.Option(help='Game name to download, will be prompted if not provided')] = None,
         uuid: Annotated[str, typer.Option(help='UUID of game to download, will be prompted for game name if not provided')] = None):
    """
    Prints a JSON blob representing a game from the Legacy Games API.
    """
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    rich.pretty.pprint(heirloom.dump_game_data(game))


@app.command('uninstall')
def uninstall():
    pass


config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()
if not encryption_key:
    set_encryption_key()
    encryption_key = get_encryption_key()
config = get_config()
config['db'] = init_games_db()
heirloom = Heirloom(**config)
with console.status('Logging in to Legacy Games...'):
    user_id = heirloom.login()
with console.status('Refreshing games list...'):
    heirloom.refresh_games_list()


@atexit.register
def cleanup_temp_dir():
    if os.path.isdir(heirloom._tmp_dir):
        shutil.rmtree(heirloom._tmp_dir)
        

def main():
    app()
