import atexit
import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path

import rich
import typer
from InquirerPy import inquirer
from typing_extensions import Annotated

from ..config import *
from ..database_functions import *
from ..heirloom import Heirloom
from ..password_functions import *


console = rich.console.Console()
app = typer.Typer(rich_markup_mode='rich')

config_dir = os.path.expanduser('~/.config/heirloom/')
config_file = Path(config_dir).expanduser() / 'config.ini'
config = None
heirloom = None


class InstallationMethod(str, Enum):
    wine = 'wine'
    sevenzip = '7zip'


def reset_runtime_context():
    global config, heirloom
    if config and config.get('db'):
        config['db'].close()
    config = None
    heirloom = None


def reset_configuration():
    reset_runtime_context()
    if config_file.is_file():
        config_file.unlink()
        console.print(f'Removed configuration file: [yellow]{config_file}[/yellow]')
    else:
        console.print(f'No configuration file found at [yellow]{config_file}[/yellow].')


@app.callback(invoke_without_command=True)
def configure_app(
    ctx: typer.Context,
    reconfigure: Annotated[
        bool,
        typer.Option(
            '--reconfigure',
            help='Delete the saved configuration and prompt for Legacy Games credentials and install settings.',
        ),
    ] = False,
):
    """
    Manage Legacy Games from Linux.
    """
    if not reconfigure:
        return

    reset_configuration()
    get_context(refresh=False)
    console.print('[green]Configuration updated successfully.[/green]')
    if ctx.invoked_subcommand is None:
        raise typer.Exit()


def get_context(refresh=True):
    global config, heirloom
    if config and heirloom:
        return config, heirloom

    if not get_encryption_key():
        set_encryption_key()

    configparser = get_config(config_dir)
    config = dict(configparser['HeirloomGM'])
    heirloom = Heirloom(**config)

    try:
        with console.status('Logging in to Legacy Games...'):
            heirloom.login()
    except Exception as e:
        console.print(':exclamation: Unable to log in to Legacy Games!')
        console.print(e)
        raise

    if refresh:
        refresh_library()
    else:
        config['db'] = init_games_db(config_dir, [])
    return config, heirloom


def refresh_library():
    get_context(refresh=False)
    with console.status('Refreshing games list...'):
        heirloom.refresh_games_list()
    with console.status('Initializing database...'):
        existing_db = config.get('db')
        if existing_db:
            existing_db.close()
        config['db'] = init_games_db(config_dir, heirloom.games)
    refresh_game_installation_status(config['db'])
    merge_game_data_with_db()


def select_from_games_list(installed_only=False):
    refresh_library()
    games = heirloom.games
    if installed_only:
        choices = [g['game_name'] for g in games if g.get('install_dir') != NOT_INSTALLED]
    else:
        choices = [g['game_name'] for g in games]
    if not choices:
        raise typer.BadParameter('No matching games found.')
    return inquirer.select(message='Select a game: ', choices=choices).execute()


def merge_game_data_with_db():
    get_context(refresh=False)
    for each_game in heirloom.games:
        record = read_game_record(config['db'], uuid=each_game['installer_uuid'])
        if not record:
            record = read_game_record(config['db'], name=each_game['game_name'])
        each_game['install_dir'] = record.get('install_dir', NOT_INSTALLED) if record else NOT_INSTALLED
        each_game['executable'] = record.get('executable', NOT_INSTALLED) if record else NOT_INSTALLED


@app.command('list')
def list_games(installed: Annotated[bool, typer.Option('--installed', help='Only list installed games')] = False,
               not_installed: Annotated[bool, typer.Option('--not-installed', help='Only list games that are NOT installed')] = False):
    """
    Lists games in your Legacy Games library.
    """
    get_context()
    if installed and not_installed:
        installed = False
        not_installed = False

    table = rich.table.Table(title='Legacy Games', box=rich.box.ROUNDED, show_lines=True)
    table.add_column('Game Name', justify='left', style='yellow')
    table.add_column('UUID', justify='center', style='green')
    table.add_column('Installed?', justify='center')
    table.add_column('Description', justify='left', style='white bold')

    for game_record in heirloom.games:
        is_installed = game_record.get('install_dir') != NOT_INSTALLED
        if installed and not is_installed:
            continue
        if not_installed and is_installed:
            continue
        table.add_row(
            game_record['game_name'],
            game_record['installer_uuid'],
            'Yes' if is_installed else 'No',
            game_record.get('game_description', ''),
        )
    console.print(table)


@app.command('download')
def download(game: Annotated[str, typer.Option(help='Game name to download, will be prompted if not provided')] = None,
             uuid: Annotated[str, typer.Option(help='UUID of game to download, will be prompted for game name if not provided')] = None):
    """
    Downloads a game from the Legacy Games library and saves the installation file to the current folder.
    """
    get_context()
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    fn = heirloom.download_game(game, output_dir='.')
    console.print(f'Successfully downloaded [bold blue]{game}[/bold blue] setup executable as [green]{fn}[/green]')


@app.command('install')
def install(game: Annotated[str, typer.Option(help='Game name to install, will be prompted if not provided')] = None,
            uuid: Annotated[str, typer.Option(help='UUID of game to install, will be prompted for game name if not provided')] = None,
            install_method: Annotated[InstallationMethod, typer.Option(case_sensitive=False)] = None):
    """
    Installs a game from the Legacy Games library.
    """
    get_context()
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

    if result.get('status') != 'success':
        console.print(result)
        console.print('[bold]Installation was [red italic]unsuccessful[/red italic]!')
        raise typer.Exit(1)

    console.print(f'Installation to [green]{result["install_path"]}[/green] successful!')
    executable = NOT_INSTALLED
    executable_files = result.get('executable_files') or []
    if len(executable_files) == 1:
        executable_file = executable_files[0].split('/')[-1]
        executable = f'{result.get("install_path")}\\{executable_file}'
    elif len(executable_files) > 1:
        console.print(':exclamation: Ambiguous executable detected!')
        answer = inquirer.select('Select the executable used to launch the game: ', choices=executable_files).execute()
        executable_file = answer.split('/')[-1]
        executable = f'{result.get("install_path")}\\{executable_file}'
    else:
        console.print(':warning: No launchable executable was detected.')

    if executable != NOT_INSTALLED:
        console.print(f'To start game, run: [yellow]{config["wine_path"]} {executable}[/yellow]')
    write_game_record(config['db'], name=game, uuid=uuid, install_dir=result['install_path'], executable=executable)


@app.command('info')
def info(game: Annotated[str, typer.Option(help='Game name to inspect, will be prompted if not provided')] = None,
         uuid: Annotated[str, typer.Option(help='UUID of game to inspect, will be prompted for game name if not provided')] = None):
    """
    Prints a JSON blob representing a game from the Legacy Games API.
    """
    get_context()
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list()
    console.print(heirloom.dump_game_data(game))


@app.command('uninstall')
def uninstall(game: Annotated[str, typer.Option(help='Game name to uninstall, will be prompted if not provided')] = None,
              uuid: Annotated[str, typer.Option(help='UUID of game to uninstall, will be prompted for game name if not provided')] = None,
              yes: Annotated[bool, typer.Option('--yes', '-y', help='Do not prompt before removing the install directory')] = False):
    """
    Uninstalls a game by removing its managed installation directory.
    """
    get_context()
    refresh_game_installation_status(config['db'])
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list(installed_only=True)
    if not uuid:
        uuid = heirloom.get_uuid_from_name(game)

    record = read_game_record(config['db'], uuid=uuid)
    if not record or record['install_dir'] == NOT_INSTALLED:
        console.print(f'[yellow]{game}[/yellow] is not recorded as installed.')
        raise typer.Exit(1)

    if not yes:
        confirmed = inquirer.confirm(f'Remove {record["install_dir"]}?', default=False).execute()
        if not confirmed:
            console.print('Uninstall cancelled.')
            raise typer.Exit()

    result = heirloom.uninstall_game(game, record['install_dir'])
    delete_game_record(config['db'], uuid=uuid)
    console.print(f'Uninstallation of [bold blue]{result["game"]}[/bold blue] successful.')


@app.command('launch')
def launch(game: Annotated[str, typer.Option(help='Game name to launch, will be prompted if not provided')] = None,
           uuid: Annotated[str, typer.Option(help='UUID of game to launch, will be prompted for game name if not provided')] = None):
    """
    Launches an installed game.
    """
    get_context()
    if uuid:
        game = heirloom.get_game_from_uuid(uuid)
    if not game:
        game = select_from_games_list(installed_only=True)
    if not uuid:
        uuid = heirloom.get_uuid_from_name(game)

    record = read_game_record(config['db'], uuid=uuid)
    if not record or record['executable'] == NOT_INSTALLED:
        console.print(f'[yellow]{game}[/yellow] does not have a recorded executable.')
        raise typer.Exit(1)

    cmd = [config['wine_path'], record['executable']]
    with console.status(f'Launching [yellow]{game}[/yellow]...'):
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    console.print(f'Launched [bold blue]{game}[/bold blue].')


def main():
    app()


@atexit.register
def cleanup_temp_dir():
    if heirloom and os.path.isdir(heirloom._tmp_dir):
        shutil.rmtree(heirloom._tmp_dir)
