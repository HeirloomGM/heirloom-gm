import requests
import base64
import os
import shutil
import subprocess
from pathlib import Path
from rich.progress import Progress
from rich.console import Console

from .password_functions import *
from .path_functions import *


class Heirloom(object):
    def __init__(self, user, password, base_install_dir, **kwargs) -> None:
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
        self._base_install_dir = os.path.expanduser(base_install_dir)
        self._base_install_wine_path = convert_to_wine_path(self._base_install_dir)
        self._wine_path = kwargs.get('wine_path', shutil.which('wine'))
        self._7zip_path = kwargs.get('7zip_path', shutil.which('7z'))
        self._default_installation_method = kwargs.get('default_installation_method', 'wine')
        self._quiet = kwargs.get('quiet', False)
        self._tmp_dir = kwargs.get('temp_dir', os.path.expanduser('~/.heirloom.tmp/'))
        self.games = []


    def login(self):
        response = requests.get(self._login_url, headers=self._headers)
        response_json = response.json()
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
        response = requests.get(self._profile_url, headers=self._headers, params=params)
        response_json = response.json()
        if response_json.get('data') and response_json['data'].get('email'):
            return response_json['data']['email']
        else:
            raise AssertionError(f'Could not get user profile for userId {user_id}!')

    
    def dump_game_data(self, game_name):
        try:
            game = next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}"')
        return game
    
    
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
        response = requests.get(self._purchased_games_url, headers=self._headers, params=params)
        data = response.json().get('data')
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
        response = requests.get(self._product_catalog_url, headers=self._headers)
        product_catalog = response.json()
        return product_catalog


    def get_giveaway_games(self):
        params = {
            'email': self.get_user_email()
        }
        response = requests.get(self._giveaway_catalog_url, headers=self._headers, params=params)
        response_json = response.json()
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


    def download_game(self, game_name, output_dir=None):
        if not output_dir:
            output_dir = self._tmp_dir
        try:
            game = next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}')
        if game['amazonprime_giveaway']:
            params = {
                'installerUuid': game['installer_uuid']
            }
            response = requests.get(self._giveaway_download_url, headers=self._headers, params=params)
        else:
            product_catalog = self.get_product_catalog()
            params = {
                'userId': self._user_id
            }
            response = requests.get(self._purchased_games_url, headers=self._headers, params=params)
            data = response.json().get('data')
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
            response = requests.get(self._purchase_download_url, headers=self._headers, params=params)
        response_json = response.json()
        if not response_json.get('data') or type(response_json.get('data')) != dict:
            raise AssertionError(f'Got invalid data back from download request!\n{response_json.get("data")}\nParams:\n{params}')
        cdn_url = response_json['data']['file']
        response = requests.get(cdn_url, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024  # chunk size in bytes
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with open(output_dir + cdn_url.split('/')[-1], 'wb') as f:
            if not self._quiet:
                with Progress() as progress_bar:
                    download_task = progress_bar.add_task(f'[green]Downloading[/green] [white italic]{game_name}[/white italic] ([yellow]{game["game_installed_size"]}[/yellow])', total=total_size)
                    for data in response.iter_content(block_size):
                        progress_bar.update(download_task, advance=len(data))
                        f.write(data)
            else:
                for data in response.iter_content(block_size):
                    f.write(data)
        return cdn_url.split('/')[-1]


    def download_artwork(self, game_name, output_dir=None):
        if not output_dir:
            output_dir = self._tmp_dir
        try:
            game = next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}"')
        coverart_url = game['game_coverart']
        response = requests.get(coverart_url, headers=self._headers, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024  # chunk size in bytes
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with open(output_dir + coverart_url.split('/')[-1], 'wb') as f:
            with Progress() as progress_bar:
                download_task = progress_bar.add_task(f'[yellow]Downloading artwork for[/yellow] [white]{game_name}[/white]', total=total_size)
                for data in response.iter_content(block_size):
                    progress_bar.update(download_task, advance=len(data))
                    f.write(data)
        return coverart_url.split('/')[-1]


    def install_game(self, game_name, installation_method=None, show_gui=False):
        cmd = None
        if not installation_method:
            installation_method = self._default_installation_method
        if installation_method.lower() not in ('wine', '7zip'):
            raise AssertionError(f'Invalid installation method ("{installation_method}"); valid installation methods are: ["wine", "7zip"]')
        try:
            game = next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}')
        fn = self.download_game(game_name)
        folder_name = '_'.join(fn.split('_')[:-1])
        if installation_method.lower() == 'wine':
            if not self._wine_path or not os.path.exists(self._wine_path):
                raise AssertionError(f'wine executable not found!')
            if not show_gui:
                cmd = [self._wine_path, 'start', '/b', '/wait', '/unix', self._tmp_dir + fn, '/S', f'/D={self._base_install_wine_path}{folder_name}']
            else:
                cmd = [self._wine_path, 'start', '/b', '/wait', '/unix', self._tmp_dir + fn, f'/D={self._base_install_wine_path}{folder_name}']
        elif installation_method.lower() == '7zip':
            if not self._7zip_path or not os.path.exists(self._7zip_path):
                raise AssertionError(f'7z executable not found!')
            cmd = [self._7zip_path, 'x', f'-o{self._base_install_dir}{folder_name}', '-y', self._tmp_dir + fn]
        if not self._quiet:
            console = Console()
            console.print(f'[green]Installation method[/green] is [blue bold]{installation_method}[/blue bold]')
            with console.status(f'Running command: [yellow]{" ".join(cmd)}[/yellow]'):
                result = subprocess.run(cmd, timeout=300, capture_output=True)
                if os.path.isdir(self._base_install_dir + folder_name):
                    install_dir = Path(self._base_install_dir + folder_name)
                    executable_files = [g.as_posix() for g in install_dir.glob('**/*.exe') if 'uninstall' not in g.name.lower() and 'crashhandler' not in g.name.lower()]
                    return {'status': 'success', 'cmd': cmd, 'stdout': result.stdout.decode('utf-8'), 'stderr': result.stderr.decode('utf-8'), 'executable_files': executable_files, 'install_path': f'{self._base_install_wine_path}{folder_name}', 'game': game['game_name'], 'uuid': game['installer_uuid']}
                else:
                    return {'status': 'fail', 'cmd': cmd, 'stdout': result.stdout.decode('utf-8'), 'stderr': result.stderr.decode('utf-8'), 'install_path': f'{self._base_install_wine_path}{folder_name}', 'game': game['game_name'], 'uuid': game['installer_uuid']}
        else:
                result = subprocess.run(cmd, timeout=300, capture_output=True)
                if os.path.isdir(self._base_install_dir + folder_name):
                    install_dir = Path(self._base_install_dir + folder_name)
                    executable_files = [g.as_posix() for g in install_dir.glob('**/*.exe') if 'uninstall' not in g.name.lower() and 'crashhandler' not in g.name.lower()]
                    return {'status': 'success', 'cmd': cmd, 'stdout': result.stdout.decode('utf-8'), 'stderr': result.stderr.decode('utf-8'), 'executable_files': executable_files, 'install_path': f'{self._base_install_wine_path}{folder_name}', 'game': game['game_name'], 'uuid': game['installer_uuid']}
                else:
                    return {'status': 'fail', 'cmd': cmd, 'stdout': result.stdout.decode('utf-8'), 'stderr': result.stderr.decode('utf-8'), 'install_path': f'{self._base_install_wine_path}{folder_name}', 'game': game['game_name'], 'uuid': game['installer_uuid']}


    def uninstall_game(self, game_name, install_dir):
        try:
            game = next((g for g in self.games if g['game_name'].lower() == game_name.lower()))
        except StopIteration:
            raise AssertionError(f'Unable to find game with name "{game_name}"')
        if not self._quiet:
            console = Console()
            with console.status(f'[green]Uninstalling[/green] [white italic]{game_name}[/white italic]'):
                pass # do delete
        else:
            pass # do delete silently
