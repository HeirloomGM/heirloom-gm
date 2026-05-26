import requests
import base64
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote
from rich.progress import Progress
from rich.console import Console

from .password_functions import *
from .path_functions import *
from .integrations import build_wine_command


class Heirloom(object):
    def __init__(self, user, password, base_install_dir, **kwargs) -> None:
        self._session = requests.Session()
        self._request_timeout = kwargs.get('request_timeout', 30)
        self._encoded_password = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('utf-8')
        self._headers = {
            'accept': 'application/json',
            'accept-encoding': 'gzip,deflate',
            'authorization': '?token?',
            'content-type': 'application/json',
            'usertoken': f'Basic {self._encoded_password}',
        }
        self._api_url = 'https://api.legacygames.com'
        self._login_url = self._api_url + '/users/login'
        self._giveaway_catalog_url = self._api_url + '/users/getgiveawaycatalogbyemail'
        self._giveaway_download_url = self._api_url + '/products/giveawaydownload'
        self._product_catalog_url = self._api_url + '/products/catalog'
        self._purchased_games_url = self._api_url + '/users/downloads'
        self._purchase_download_url = self._api_url + '/products/download'
        self._profile_url = self._api_url + '/users/profile'
        self._user_id = None
        self._base_install_dir = Path(base_install_dir).expanduser()
        self._base_install_wine_path = convert_to_wine_path(self._base_install_dir.as_posix())
        self._wine_path = kwargs.get('wine_path', shutil.which('wine'))
        self._wine_runner = kwargs.get('wine_runner', 'native')
        self._flatpak_path = kwargs.get('flatpak_path', shutil.which('flatpak') or 'flatpak')
        self._wine_flatpak_app = kwargs.get('wine_flatpak_app', 'org.winehq.Wine')
        self._7zip_path = kwargs.get('7zip_path', shutil.which('7z'))
        self._default_installation_method = kwargs.get('default_installation_method', 'wine')
        self._quiet = kwargs.get('quiet', False)
        self._tmp_dir = Path(kwargs.get('temp_dir', '~/.heirloom.tmp/')).expanduser()
        self.games = []


    def _get_json(self, url, **kwargs):
        response = self._session.get(
            url,
            headers=kwargs.pop('headers', self._headers),
            timeout=self._request_timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()


    def _download_file(self, url, output_dir, description, progress_callback=None):
        output_path = Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)
        filename = unquote(Path(urlparse(url).path).name)
        if not filename:
            raise AssertionError(f'Unable to determine filename from URL: {url}')
        destination = output_path / filename
        response = self._session.get(url, stream=True, timeout=self._request_timeout)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 128
        downloaded = 0
        with destination.open('wb') as f:
            if not self._quiet:
                with Progress() as progress_bar:
                    download_task = progress_bar.add_task(description, total=total_size)
                    for data in response.iter_content(block_size):
                        if data:
                            downloaded += len(data)
                            progress_bar.update(download_task, advance=len(data))
                            f.write(data)
                            if progress_callback:
                                progress_callback(downloaded, total_size)
            else:
                for data in response.iter_content(block_size):
                    if data:
                        downloaded += len(data)
                        f.write(data)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
        return filename


    def _find_game(self, game_name):
        if not self.games:
            self.refresh_games_list()
        try:
            return next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}"')


    def _install_folder_name(self, installer_filename):
        folder_name = '_'.join(installer_filename.split('_')[:-1])
        return folder_name or Path(installer_filename).stem


    def _unix_install_dir(self, install_dir):
        return Path(convert_to_unix_path(str(install_dir))).expanduser()


    def _ensure_install_dir_is_safe(self, install_dir):
        base_dir = self._base_install_dir.resolve()
        target_dir = self._unix_install_dir(install_dir).resolve()
        if target_dir == base_dir or base_dir not in target_dir.parents:
            raise AssertionError(f'Refusing to uninstall outside configured install directory: {target_dir}')
        return target_dir


    def _wine_install_path(self, folder_name):
        base = self._base_install_wine_path.rstrip('\\/')
        return f'{base}\\{folder_name}'


    def _wine_config(self):
        return {
            'wine_runner': self._wine_runner,
            'wine_path': self._wine_path,
            'flatpak_path': self._flatpak_path,
            'wine_flatpak_app': self._wine_flatpak_app,
        }


    def _wine_command(self, *args):
        if self._wine_runner == 'flatpak':
            if not self._flatpak_path or not (shutil.which(self._flatpak_path) or os.path.exists(self._flatpak_path)):
                raise AssertionError('flatpak executable not found!')
            return [self._flatpak_path, 'run', self._wine_flatpak_app, *args]
        if not self._wine_path or not (shutil.which(self._wine_path) or os.path.exists(self._wine_path)):
            raise AssertionError('wine executable not found!')
        return [self._wine_path, *args]


    def launch_command(self, executable):
        return build_wine_command(self._wine_config(), executable)


    def login(self):
        response_json = self._get_json(self._login_url)
        if response_json.get('data') and type(response_json.get('data')) == dict and response_json['data'].get('userId'):
            self._user_id = response_json['data'].get('userId')
            return response_json['data'].get('userId')
        else:
            raise AssertionError('Did not find userId in login response!')
    
    
    def get_user_email(self):
        user_id = self._user_id or self.login()
        params = {
            'userId': user_id
        }
        response_json = self._get_json(self._profile_url, params=params)
        if response_json.get('data') and response_json['data'].get('email'):
            return response_json['data']['email']
        else:
            raise AssertionError(f'Could not get user profile for userId {user_id}!')

    
    def dump_game_data(self, game_name):
        return self._find_game(game_name)
    
    
    def get_game_from_uuid(self, uuid):
        if not self.games:
            self.refresh_games_list()
        try:
            game = next((g for g in self.games if g.get('installer_uuid').lower() == uuid.lower()))
            return game['game_name']
        except StopIteration:
            raise AssertionError(f'Unable to find game with UUID "{uuid}"')


    def get_uuid_from_name(self, game_name):
        if not self.games:
            self.refresh_games_list()
        try:
            game = next((g for g in self.games if g.get('game_name').lower() == game_name.lower()))
            return game['installer_uuid']
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}"')


    def get_purchased_games(self):
        if not self._user_id:
            self._user_id = self.login()
        product_catalog = self.get_product_catalog()
        params = {
            'userId': self._user_id
        }
        data = self._get_json(self._purchased_games_url, params=params).get('data')
        if data:
            purchased_games = [p for p in product_catalog if 'product_id' in p and p['product_id'] in [d['product_id'] for d in data]]
        else:
            purchased_games = []
        games = []
        for each_purchase in purchased_games:
            games += each_purchase['games']
        return games


    def get_product_catalog(self):
        if not self._user_id:
            self._user_id = self.login()
        return self._get_json(self._product_catalog_url)


    def get_giveaway_games(self):
        params = {
            'email': self.get_user_email()
        }
        response_json = self._get_json(self._giveaway_catalog_url, params=params)
        games = []
        for data in response_json['data']:
            existing_game_names = [g['game_name'] for g in games] if games else []
            for each_game in [d for d in data['games'] if d['game_name'] not in existing_game_names]:
                games.append(each_game)
        return games
        

    def refresh_games_list(self):
        giveaway_games = self.get_giveaway_games()
        for each in giveaway_games:
            each['amazonprime_giveaway'] = True
        purchased_games = self.get_purchased_games()
        for each in purchased_games:
            each['amazonprime_giveaway'] = False
        self.games = purchased_games + [g for g in giveaway_games if g['game_name'] not in [p['game_name'] for p in purchased_games]]


    def download_game(self, game_name, output_dir=None, progress_callback=None):
        if not output_dir:
            output_dir = self._tmp_dir
        game = self._find_game(game_name)
        if game['amazonprime_giveaway']:
            params = {
                'installerUuid': game['installer_uuid']
            }
            response_json = self._get_json(self._giveaway_download_url, params=params)
        else:
            product_catalog = self.get_product_catalog()
            params = {
                'userId': self._user_id
            }
            data = self._get_json(self._purchased_games_url, params=params).get('data')
            if data:
                purchased_games = [p for p in product_catalog if 'product_id' in p and p['product_id'] in [d['product_id'] for d in data]]
            else:
                purchased_games = []
            try:
                product = next((p for p in purchased_games if 'games' in p and game['game_name'] in [n['game_name'] for n in p['games']]))
            except StopIteration:
                raise AssertionError(f'Unable to find game with name "{game_name}"')
            params = {
                'productId': product['product_id'],
                'gameId': game['game_id']
            }
            response_json = self._get_json(self._purchase_download_url, params=params)
        if not response_json.get('data') or type(response_json.get('data')) != dict:
            raise AssertionError(f'Got invalid data back from download request!\n{response_json.get("data")}\nParams:\n{params}')
        cdn_url = response_json['data']['file']
        return self._download_file(
            cdn_url,
            output_dir,
            f'[green]Downloading[/green] [white italic]{game_name}[/white italic] ([yellow]{game["game_installed_size"]}[/yellow])',
            progress_callback=progress_callback,
        )


    def download_artwork(self, game_name, output_dir=None):
        if not output_dir:
            output_dir = self._tmp_dir
        game = self._find_game(game_name)
        coverart_url = game['game_coverart']
        return self._download_file(
            coverart_url,
            output_dir,
            f'[yellow]Downloading artwork for[/yellow] [white]{game_name}[/white]',
        )


    def install_game(self, game_name, installation_method=None, show_gui=False, progress_callback=None):
        if not installation_method:
            installation_method = self._default_installation_method
        if installation_method.lower() not in ('wine', '7zip'):
            raise AssertionError(f'Invalid installation method ("{installation_method}"); valid installation methods are: ["wine", "7zip"]')
        game = self._find_game(game_name)
        fn = self.download_game(game_name, progress_callback=progress_callback)
        folder_name = self._install_folder_name(fn)
        unix_install_path = self._base_install_dir / folder_name
        wine_install_path = self._wine_install_path(folder_name)
        installer_path = self._tmp_dir / fn
        if installation_method.lower() == 'wine':
            if not show_gui:
                cmd = self._wine_command('start', '/b', '/wait', '/unix', str(installer_path), '/S', f'/D={wine_install_path}')
            else:
                cmd = self._wine_command('start', '/b', '/wait', '/unix', str(installer_path), f'/D={wine_install_path}')
        elif installation_method.lower() == '7zip':
            if not self._7zip_path or not os.path.exists(self._7zip_path):
                raise AssertionError(f'7z executable not found!')
            cmd = [self._7zip_path, 'x', f'-o{unix_install_path}', '-y', str(installer_path)]
        self._base_install_dir.mkdir(parents=True, exist_ok=True)

        if not self._quiet:
            console = Console()
            console.print(f'[green]Installation method[/green] is [blue bold]{installation_method}[/blue bold]')
            with console.status(f'Running command: [yellow]{" ".join(cmd)}[/yellow]'):
                result = subprocess.run(cmd, timeout=300, capture_output=True)
        else:
            result = subprocess.run(cmd, timeout=300, capture_output=True)

        installed = unix_install_path.is_dir()
        install_dir = unix_install_path
        response = {
            'status': 'success' if installed else 'fail',
            'cmd': cmd,
            'stdout': result.stdout.decode('utf-8', errors='replace'),
            'stderr': result.stderr.decode('utf-8', errors='replace'),
            'install_path': wine_install_path,
            'unix_install_path': install_dir.as_posix(),
            'game': game['game_name'],
            'uuid': game['installer_uuid'],
        }
        if installed:
            response['executable_files'] = [
                g.as_posix()
                for g in install_dir.glob('**/*.exe')
                if 'uninstall' not in g.name.lower() and 'crashhandler' not in g.name.lower()
            ]
        return response


    def uninstall_game(self, game_name, install_dir):
        game = self._find_game(game_name)
        target_dir = self._ensure_install_dir_is_safe(install_dir)
        if not self._quiet:
            console = Console()
            with console.status(f'[green]Uninstalling[/green] [white italic]{game_name}[/white italic]'):
                if target_dir.exists():
                    shutil.rmtree(target_dir)
        else:
            if target_dir.exists():
                shutil.rmtree(target_dir)
        return {
            'status': 'success',
            'install_path': str(install_dir),
            'unix_install_path': target_dir.as_posix(),
            'game': game['game_name'],
            'uuid': game['installer_uuid'],
        }
