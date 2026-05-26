import os
import shutil
from pathlib import Path
from rich.console import Console
from configparser import ConfigParser

from ..password_functions import *


def get_config(config_dir):
    console = Console()
    config_path = Path(config_dir).expanduser()
    config_path.mkdir(parents=True, exist_ok=True)
    config_file = config_path / 'config.ini'
    config_parser = ConfigParser()
    config_parser.add_section('HeirloomGM')
    if not config_file.is_file() or config_file.stat().st_size == 0:
        try:
            from InquirerPy import inquirer
        except ModuleNotFoundError as exc:
            raise RuntimeError('Configuration is missing and interactive CLI prompts are unavailable.') from exc
        console.print(f'Configuration file not found: [yellow]{config_file}[/yellow]')
        console.print('Please enter your login credentials for Legacy Games.')
        config_parser.set('HeirloomGM', 'user', inquirer.text('Enter username or email: ').execute())
        config_parser.set('HeirloomGM', 'password', inquirer.secret('Enter password: ').execute())
        config_parser.set('HeirloomGM', 'base_install_dir', inquirer.filepath('Enter base installation folder: ', default=os.path.expanduser('~/Games/LegacyGames/')).execute())
        config_parser.set('HeirloomGM', 'wine_runner', inquirer.select('Wine runner type: ', choices=['native', 'flatpak'], default='native').execute())
        config_parser.set('HeirloomGM', 'wine_path', inquirer.text('Path to Wine executable: ', default=shutil.which('wine') or '').execute())
        config_parser.set('HeirloomGM', 'flatpak_path', inquirer.text('Path to Flatpak executable: ', default=shutil.which('flatpak') or 'flatpak').execute())
        config_parser.set('HeirloomGM', 'wine_flatpak_app', inquirer.text('Wine Flatpak app ID: ', default='org.winehq.Wine').execute())
        config_parser.set('HeirloomGM', '7zip_path', inquirer.text('Path to 7zip executable: ', default=shutil.which('7z') or '').execute())
        config_parser.set('HeirloomGM', 'default_installation_method', inquirer.select('Default installation method: ', choices=['7zip', 'wine'], default='7zip').execute())
        config_parser.set('HeirloomGM', 'auto_add_steam', str(inquirer.confirm('Automatically add installed games to Steam?', default=False).execute()))
        config_parser.set('HeirloomGM', 'auto_add_kde', str(inquirer.confirm('Automatically add installed games to the KDE Games menu?', default=False).execute()))
        save_file = inquirer.confirm(f'Save configuration file to {config_file}?').execute()
        if save_file:
            config_parser.set('HeirloomGM', 'password', encrypt_password(config_parser.get('HeirloomGM', 'password')).decode('utf-8'))
            with config_file.open('w') as cf:
                config_parser.write(cf)
            config_file.chmod(0o600)
            with config_file.open('r') as cf:
                config_data = ConfigParser()
                config_data.read_file(cf)
                config_data.set('HeirloomGM', 'password', decrypt_password(config_data.get('HeirloomGM', 'password')).decode('utf-8'))
        else:
            config_data = config_parser
    else:
        with config_file.open('r') as cf:
            config_data = ConfigParser()
            config_data.read_file(cf)
            password = config_data.get('HeirloomGM', 'password')
            try:
                password = decrypt_password(password).decode('utf-8')
            except Exception:
                if password.startswith('gAAAA'):
                    raise RuntimeError(
                        'Stored password is encrypted, but the matching encryption key was not found. '
                        'Re-run configuration or restore the original keyring entry.'
                    )
                console.print(':warning: Stored password is not encrypted; using it as-is.')
            config_data.set('HeirloomGM', 'password', password)
    return config_data
