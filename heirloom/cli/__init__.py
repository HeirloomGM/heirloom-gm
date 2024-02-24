import atexit
import base64
import json
import os
import sqlite3
import shutil
import sys
from enum import Enum

import keyring
import rich
import typer
from cryptography.fernet import Fernet
from InquirerPy import inquirer
from typing_extensions import Annotated

from ..heirloom import Heirloom


console = rich.console.Console()
app = typer.Typer(rich_markup_mode='rich')


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
        answers = {}
        answers['user'] = inquirer.text('Enter username or email: ').execute()
        answers['password'] = inquirer.secret('Enter password: ').execute()
        answers['base_install_dir'] = inquirer.filepath('Enter base installation folder: ', default=os.path.expanduser('~/Games/LegacyGames/')).execute()
        answers['wine_path'] = inquirer.text('Path to Wine executable: ', default=shutil.which('wine')).execute()
        answers['7zip_path'] = inquirer.text('Path to 7zip executable: ', default=shutil.which('7z')).execute()
        answers['default_installation_method'] = inquirer.select('Default installation method: ', choices=['7zip', 'wine'], default='7zip').execute()
        save_file = inquirer.confirm(f'Save configuration file to {os.path.expanduser(config_file)}?').execute()
        if save_file:
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
        sql = 'CREATE TABLE games(name text, uuid text primary key unique, install_dir text)'
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
    return db


def write_game_record(name=None, uuid=None, install_dir=None):
    if not config.get('db'):
        db = init_games_db()
    else:
        db = config.get('db')
    sql = "INSERT INTO games VALUES(?, ?, ?) ON CONFLICT(uuid) DO UPDATE SET install_dir=excluded.install_dir"
    cursor = db.cursor()    
    if not name:
        name = heirloom.get_name_from_uuid(uuid)
    if not uuid:
        uuid = heirloom.get_uuid_from_name(name)
    cursor.execute(sql, (name, uuid, install_dir))
    db.commit()
 

def read_game_record(name=None, uuid=None):
    if not config.get('db'):
        db = init_games_db()
    else:
        db = config.get('db')
    if name:
        sql = f"SELECT * FROM games WHERE name='{name}'"
    elif uuid:
        sql = f"SELECT * FROM GAMES WHERE uuidp'{uuid}'"
    else:
        console.print(':exclamation: Must specify name or UUID for game')
        sys.exit(1)
    cursor = db.cursor()
    result = cursor.execute(sql)
    record = result.fetchone()
    return dict(zip(('name', 'uuid', 'install_dir'), record)) if record else None
   

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
    game = inquirer.select(message='Select a game: ', choices=[g['game_name'] for g in heirloom.games]).execute()
    return game


def refresh_game_status():
    if not config.get('db'):
        config['db'] = init_games_db()
    db = config.get('db')
    sql = "SELECT * FROM games WHERE install_dir != 'Not Installed'"
    cursor = db.cursor()
    result = cursor.execute(sql).fetchall()
    for each in result:
        if not os.path.exists(each.get('install_dir')):
            sql = f"UPDATE games SET install_dir = 'Not Installed' WHERE uuid = '{each.get('uuid')}'"
            result = cursor.execute(sql)
            db.commit()


@app.command('list')
def list_games(installed: Annotated[bool, typer.Option('--installed', help='Only list installed games')] = False,
               not_installed: Annotated[bool, typer.Option('--not-installed', help='Only list games that are NOT installed')] = False):
    """
    Lists games in your Legacy Games library.
    """
    if installed and not_installed:  # Two negatives makes a positive!
        installed = False
        not_installed = False
    heirloom.refresh_games_list()
    table = rich.table.Table(title='Legacy Games', box=rich.box.ROUNDED, show_lines=True)
    table.add_column("Game Name", justify="left", style="yellow")
    table.add_column("UUID", justify="center", style="green")
    table.add_column('Description', justify="left", style="white bold")
    table.add_column("Installation Folder", justify="right", style="red")
    for g in heirloom.games:
        record = read_game_record(name=g['game_name'])
        if record:
            install_folder = record['install_dir']
            if not_installed:
                continue
        else:
            install_folder = 'Not installed'
            if installed:
                continue
        table.add_row(g['game_name'], g['installer_uuid'], g['game_description'], install_folder)
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
            executable_file = result.get('executable_files')[0].split('/')[-1]
            console.print(f'To start game, run: [yellow]{config["wine_path"]} \'{result.get("install_path")}\\{executable_file}\'')
            answer = f'{result.get("install_path")}\\{executable_file}'
        elif result.get('executable_files') and len(result.get('executable_files')) > 1:
            console.print(f':exclamation: Ambiguous executable detected!')
            answer = inquirer.select('Select the executable used to launch the game: ', choices=result.get('executable_files')).execute()
            executable_file = answer.split('/')[-1]
            console.print(f'To start game, run: [yellow]{config["wine_path"]} \'{result.get("install_path")}\\{executable_file}\'')
            answer = f'{result.get("install_path")}\\{executable_file}'
        write_game_record(game, uuid, answer)
    else:
        console.print(result)
        console.print(f'[bold]Installation was [red italic]unsuccessful[/red italic]! :frowning:')


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


def main():
    app()


config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()
if not encryption_key:
    set_encryption_key()
    encryption_key = get_encryption_key()
config = get_config()
config['db'] = init_games_db()
heirloom = Heirloom(**config)
try:
    with console.status('Logging in to Legacy Games...'):
        user_id = heirloom.login()
except Exception as e:
    console.print(f':exclamation: Unable to log in to Legacy Games!')
    console.print(e)
    sys.exit(1)
try:
    with console.status('Refreshing games list...'):
        heirloom.refresh_games_list()
        refresh_game_status()
except Exception as e:
    console.print(f':exclamation: Unable to refresh games list!')
    console.print(e)
    sys.exit(1)


@atexit.register
def cleanup_temp_dir():
    if os.path.isdir(heirloom._tmp_dir):
        shutil.rmtree(heirloom._tmp_dir)

