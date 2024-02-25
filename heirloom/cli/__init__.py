import atexit
import os
import shutil
import subprocess
from enum import Enum

import rich
import typer
from InquirerPy import inquirer
from typing_extensions import Annotated

from ..heirloom import Heirloom
from ..password_functions import *
from ..path_functions import *
from ..database_functions import *
from ..config import *


console = rich.console.Console()
app = typer.Typer(rich_markup_mode='rich')


class InstallationMethod(str, Enum):
    wine = 'wine'
    sevenzip = '7zip'
    

def select_from_games_list(installed_only=False):
    heirloom.refresh_games_list()
    games = heirloom.games
    if not installed_only:
        game = inquirer.select(message='Select a game: ', choices=[g['game_name'] for g in games]).execute()
    else:
        game = inquirer.select(message='Select a game: ', choices=[g['game_name'] for g in games if g['install_dir'] != 'Not Installed']).execute()
    return game


def merge_game_data_with_db():
    games = heirloom.games
    for each_game in games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            console.print(f':exclamation: Unable to read game record for UUID [green]{each_game["installer_uuid"]}[/green]!')
            record = read_game_record(config['db'], name=each_game['game_name'])
            if not record:
                console.print(f':warning: Unable to read game record for game name [blue]{each_game["game_name"]}[/blue]!')
        each_game['install_dir'] = record.get('install_dir', 'Not Installed')
        each_game['executable'] = record.get('executable', 'Not Installed')
    heirloom.games = games


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
    refresh_game_status(config['db'])
    table = rich.table.Table(title='Legacy Games', box=rich.box.ROUNDED, show_lines=True)
    table.add_column("Game Name", justify="left", style="yellow")
    table.add_column("UUID", justify="center", style="green")
    table.add_column('Description', justify="left", style="white bold")
    for g in heirloom.games:
        record = read_game_record(config['db'], name=g['game_name'])
        if record and record['install_dir'] != 'Not Installed':
            if not_installed:
                continue
        elif record and record['install_dir'] == 'Not Installed':
            if installed:
                continue
        table.add_row(g['game_name'], g['installer_uuid'], g['game_description'])
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
    refresh_game_status(config['db'])
    merge_game_data_with_db()
    while not config.get('base_install_dir'):
        config['base_install_dir'] = input('Enter base installation folder: ')
    if not os.path.isdir(os.path.expanduser(config['base_install_dir'])):
        os.makedirs(os.path.expanduser(config['base_install_dir']))
    if not game and not uuid:
        game = select_from_games_list()
        uuid = heirloom.get_uuid_from_name(game)
    if uuid and not game:
        game = heirloom.get_game_from_uuid(uuid)
    if game and not uuid:
        uuid = heirloom.get_uuid_from_name(game)
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
        write_game_record(config['db'], name=game, uuid=uuid, install_dir=result['install_path'], executable=answer)
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
        merge_game_data_with_db()
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    rich.pretty.pprint(heirloom.dump_game_data(game))


@app.command('uninstall')
def uninstall(game: Annotated[str, typer.Option(help='Game name to uninstall, will be prompted if not provided')] = None,
              uuid: Annotated[str, typer.Option(help='UUID of game to uninstall, will be prompted for game name if not provided')] = None):
    """
    Uninstalls a game from the Legacy Games library.    
    """
    refresh_game_status(config['db'])
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list(installed_only=True)
    else:
        result = heirloom.uninstall_game(game)
    if result.get('status') == 'success':
        console.print(f'Uninstallation of {game} successful! :grin:')
        delete_game_record(config['db'], uuid=uuid)
    else:
        console.print(result)
        console.print(f'[bold]Installation was [red italic]unsuccessful[/red italic]! :frowning:')
        

@app.command('launch')
def launch(game: Annotated[str, typer.Option(help='Game name to uninstall, will be prompted if not provided')] = None,
           uuid: Annotated[str, typer.Option(help='UUID of game to uninstall, will be prompted for game name if not provided')] = None):
    """
    Launches an installed game.
    """
    if not game:
        game = select_from_games_list(installed_only=True)
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    else:
        uuid = heirloom.get_uuid_from_name(game)
    record = read_game_record(config['db'], uuid=uuid)
    cmd = [config['wine_path'], f"'{record['executable']}'"]
    with console.status(f"Running: [yellow]{' '.join(cmd)}[/yellow]"):
        result = subprocess.run(cmd, capture_output=True)
        console.print(result.stdout)
        
        
def main():
    app()


config_dir = os.path.expanduser('~/.config/heirloom/')
encryption_key = get_encryption_key()
if not encryption_key:
    set_encryption_key()
    encryption_key = get_encryption_key()
configparser = get_config(config_dir)
config = dict(configparser['HeirloomGM'])
heirloom = Heirloom(**config)
try:
    with console.status('Logging in to Legacy Games...'):
        user_id = heirloom.login()
except Exception as e:
    console.print(f':exclamation: Unable to log in to Legacy Games!')
    console.print(e)
    raise(e)
try:
    with console.status('Refreshing games list...'):
        heirloom.refresh_games_list()
    with console.status('Initializing database...'):
        config['db'] = init_games_db(config_dir, heirloom.games)
    with console.status('Merging database into game data...'):
        merge_game_data_with_db()
    refresh_game_status(config['db'])
except Exception as e:
    console.print(f':exclamation: Unable to refresh games list!')
    console.print(e)
    raise(e)


@atexit.register
def cleanup_temp_dir():
    if os.path.isdir(heirloom._tmp_dir):
        shutil.rmtree(heirloom._tmp_dir)

