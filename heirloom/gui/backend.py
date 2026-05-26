import os
import shutil
import subprocess
import threading
from configparser import ConfigParser
from pathlib import Path
from urllib.parse import urlparse

import requests
from PySide6.QtCore import (
    QAbstractListModel,
    QObject,
    QModelIndex,
    Property,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
)

from ..config import get_config
from ..database_functions import (
    NOT_INSTALLED,
    delete_game_record,
    init_games_db,
    read_game_record,
    refresh_game_installation_status,
    write_game_record,
)
from ..heirloom import Heirloom
from ..integrations import add_installed_game_integrations
from ..password_functions import decrypt_password, encrypt_password, get_encryption_key, set_encryption_key


CONFIG_DIR = Path('~/.config/heirloom/').expanduser()
CONFIG_FILE = CONFIG_DIR / 'config.ini'
CACHE_DIR = CONFIG_DIR / 'artwork'


class GamesModel(QAbstractListModel):
    TitleRole = Qt.UserRole + 1
    UuidRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    CoverArtRole = Qt.UserRole + 4
    InstalledRole = Qt.UserRole + 5
    InstallDirRole = Qt.UserRole + 6
    ExecutableRole = Qt.UserRole + 7
    SizeRole = Qt.UserRole + 8

    def __init__(self):
        super().__init__()
        self._games = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._games)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._games):
            return None
        game = self._games[index.row()]
        if role == self.TitleRole:
            return game.get('game_name', '')
        if role == self.UuidRole:
            return game.get('installer_uuid', '')
        if role == self.DescriptionRole:
            return game.get('game_description', '')
        if role == self.CoverArtRole:
            return game.get('coverart_local', '') or game.get('game_coverart', '')
        if role == self.InstalledRole:
            return game.get('install_dir') != NOT_INSTALLED
        if role == self.InstallDirRole:
            return game.get('install_dir', NOT_INSTALLED)
        if role == self.ExecutableRole:
            return game.get('executable', NOT_INSTALLED)
        if role == self.SizeRole:
            return game.get('game_installed_size', '')
        return None

    def roleNames(self):
        return {
            self.TitleRole: b'title',
            self.UuidRole: b'uuid',
            self.DescriptionRole: b'description',
            self.CoverArtRole: b'coverArt',
            self.InstalledRole: b'installed',
            self.InstallDirRole: b'installDir',
            self.ExecutableRole: b'executable',
            self.SizeRole: b'installedSize',
        }

    def game_by_uuid(self, uuid):
        return next((game for game in self._games if game.get('installer_uuid') == uuid), None)

    def set_games(self, games):
        self.beginResetModel()
        self._games = list(games)
        self.endResetModel()


class GamesFilterModel(QSortFilterProxyModel):
    filterChanged = Signal()

    def __init__(self, source_model):
        super().__init__()
        self._query = ''
        self._mode = 'all'
        self.setSourceModel(source_model)
        self.setDynamicSortFilter(True)

    @Slot(str)
    def setQuery(self, query):
        self._query = query.strip().lower()
        self.invalidateFilter()
        self.filterChanged.emit()

    @Slot(str)
    def setMode(self, mode):
        self._mode = mode
        self.invalidateFilter()
        self.filterChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        installed = bool(self.sourceModel().data(index, GamesModel.InstalledRole))
        if self._mode == 'installed' and not installed:
            return False
        if self._mode == 'notInstalled' and installed:
            return False
        if not self._query:
            return True
        title = (self.sourceModel().data(index, GamesModel.TitleRole) or '').lower()
        description = (self.sourceModel().data(index, GamesModel.DescriptionRole) or '').lower()
        return self._query in title or self._query in description


class GuiController(QObject):
    busyChanged = Signal()
    configuredChanged = Signal()
    statusMessageChanged = Signal()
    errorMessageChanged = Signal()
    settingsChanged = Signal()
    progressChanged = Signal()
    operationFinished = Signal()
    _gamesLoaded = Signal(list)
    _operationFailed = Signal(str)
    _operationStatus = Signal(str)
    _operationProgress = Signal(float, str)
    _operationDone = Signal()

    def __init__(self):
        super().__init__()
        self.games = GamesModel()
        self.filtered_games = GamesFilterModel(self.games)
        self._busy = False
        self._configured = CONFIG_FILE.is_file()
        self._status_message = 'Ready'
        self._error_message = ''
        self._config = {}
        self._config_user = ''
        self._config_base_install_dir = str(Path('~/Games/LegacyGames/').expanduser())
        self._config_wine_runner = 'native'
        self._config_wine_path = shutil.which('wine') or ''
        self._config_flatpak_path = shutil.which('flatpak') or 'flatpak'
        self._config_wine_flatpak_app = 'org.winehq.Wine'
        self._config_sevenzip_path = shutil.which('7z') or ''
        self._config_default_installation_method = '7zip'
        self._config_auto_add_steam = False
        self._config_auto_add_kde = False
        self._progress = -1.0
        self._progress_label = ''
        self._heirloom = None

        self._load_public_settings()
        self._gamesLoaded.connect(self._apply_games)
        self._operationFailed.connect(self._fail_operation)
        self._operationStatus.connect(self._set_status)
        self._operationProgress.connect(self._set_progress)
        self._operationDone.connect(self._finish_operation)

    def _get_busy(self):
        return self._busy

    def _set_busy(self, busy):
        if self._busy != busy:
            self._busy = busy
            self.busyChanged.emit()

    busy = Property(bool, _get_busy, notify=busyChanged)

    def _get_configured(self):
        return self._configured

    def _set_configured(self, configured):
        if self._configured != configured:
            self._configured = configured
            self.configuredChanged.emit()

    configured = Property(bool, _get_configured, notify=configuredChanged)

    def _get_status_message(self):
        return self._status_message

    def _set_status(self, message):
        if self._status_message != message:
            self._status_message = message
            self.statusMessageChanged.emit()

    statusMessage = Property(str, _get_status_message, notify=statusMessageChanged)

    def _get_error_message(self):
        return self._error_message

    def _set_error(self, message):
        if self._error_message != message:
            self._error_message = message
            self.errorMessageChanged.emit()

    errorMessage = Property(str, _get_error_message, notify=errorMessageChanged)

    def _get_config_user(self):
        return self._config_user

    configUser = Property(str, _get_config_user, notify=settingsChanged)

    def _get_config_base_install_dir(self):
        return self._config_base_install_dir

    configBaseInstallDir = Property(str, _get_config_base_install_dir, notify=settingsChanged)

    def _get_config_wine_path(self):
        return self._config_wine_path

    configWinePath = Property(str, _get_config_wine_path, notify=settingsChanged)

    def _get_config_wine_runner(self):
        return self._config_wine_runner

    configWineRunner = Property(str, _get_config_wine_runner, notify=settingsChanged)

    def _get_config_flatpak_path(self):
        return self._config_flatpak_path

    configFlatpakPath = Property(str, _get_config_flatpak_path, notify=settingsChanged)

    def _get_config_wine_flatpak_app(self):
        return self._config_wine_flatpak_app

    configWineFlatpakApp = Property(str, _get_config_wine_flatpak_app, notify=settingsChanged)

    def _get_config_sevenzip_path(self):
        return self._config_sevenzip_path

    configSevenZipPath = Property(str, _get_config_sevenzip_path, notify=settingsChanged)

    def _get_config_default_installation_method(self):
        return self._config_default_installation_method

    configDefaultInstallationMethod = Property(str, _get_config_default_installation_method, notify=settingsChanged)

    def _get_config_auto_add_steam(self):
        return self._config_auto_add_steam

    configAutoAddSteam = Property(bool, _get_config_auto_add_steam, notify=settingsChanged)

    def _get_config_auto_add_kde(self):
        return self._config_auto_add_kde

    configAutoAddKde = Property(bool, _get_config_auto_add_kde, notify=settingsChanged)

    def _get_progress(self):
        return self._progress

    progress = Property(float, _get_progress, notify=progressChanged)

    def _get_progress_label(self):
        return self._progress_label

    progressLabel = Property(str, _get_progress_label, notify=progressChanged)

    def _set_progress(self, value, label=''):
        value = max(-1.0, min(1.0, value))
        if self._progress != value or self._progress_label != label:
            self._progress = value
            self._progress_label = label
            self.progressChanged.emit()

    @Slot()
    def bootstrap(self):
        if not CONFIG_FILE.is_file():
            self._set_status('Configuration needed')
            self._set_configured(False)
            return
        self.refreshLibrary()

    @Slot(str)
    def setSearch(self, query):
        self.filtered_games.setQuery(query)

    @Slot(str)
    def setFilterMode(self, mode):
        self.filtered_games.setMode(mode)

    @Slot(str, str, str, str, str, str, str, str, str, bool, bool)
    def saveConfiguration(self, user, password, base_install_dir, wine_runner, wine_path, flatpak_path, wine_flatpak_app, sevenzip_path, install_method, auto_add_steam, auto_add_kde):
        if not user.strip():
            self._set_error('Username is required.')
            return
        existing_password = self._read_saved_password_token()
        if not password and not existing_password:
            self._set_error('Password is required.')
            return
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not get_encryption_key():
            set_encryption_key()

        parser = ConfigParser()
        parser.add_section('HeirloomGM')
        parser.set('HeirloomGM', 'user', user.strip())
        if password:
            parser.set('HeirloomGM', 'password', encrypt_password(password).decode('utf-8'))
        else:
            parser.set('HeirloomGM', 'password', existing_password)
        parser.set('HeirloomGM', 'base_install_dir', base_install_dir.strip() or str(Path('~/Games/LegacyGames/').expanduser()))
        parser.set('HeirloomGM', 'wine_runner', wine_runner or 'native')
        parser.set('HeirloomGM', 'wine_path', wine_path.strip() or shutil.which('wine') or '')
        parser.set('HeirloomGM', 'flatpak_path', flatpak_path.strip() or shutil.which('flatpak') or 'flatpak')
        parser.set('HeirloomGM', 'wine_flatpak_app', wine_flatpak_app.strip() or 'org.winehq.Wine')
        parser.set('HeirloomGM', '7zip_path', sevenzip_path.strip() or shutil.which('7z') or '')
        parser.set('HeirloomGM', 'default_installation_method', install_method or '7zip')
        parser.set('HeirloomGM', 'auto_add_steam', str(auto_add_steam))
        parser.set('HeirloomGM', 'auto_add_kde', str(auto_add_kde))
        with CONFIG_FILE.open('w') as config_file:
            parser.write(config_file)
        CONFIG_FILE.chmod(0o600)
        self._set_configured(True)
        self._heirloom = None
        self._load_public_settings()
        self._set_error('')
        self._set_status('Configuration saved')
        self.refreshLibrary()

    @Slot()
    def refreshLibrary(self):
        if self._busy:
            return
        self._set_busy(True)
        self._set_error('')
        self._set_progress(-1.0, '')
        self._set_status('Refreshing Legacy Games library...')
        self._run(self._refresh_library_worker)

    @Slot(str)
    def installGame(self, uuid):
        if self._busy:
            return
        game = self.games.game_by_uuid(uuid)
        if not game:
            self._set_error('Game not found.')
            return
        self._set_busy(True)
        self._set_error('')
        self._set_progress(-1.0, '')
        self._set_status(f'Installing {game["game_name"]}...')
        self._run(lambda: self._install_worker(uuid))

    @Slot(str)
    def uninstallGame(self, uuid):
        if self._busy:
            return
        game = self.games.game_by_uuid(uuid)
        if not game:
            self._set_error('Game not found.')
            return
        self._set_busy(True)
        self._set_error('')
        self._set_progress(-1.0, '')
        self._set_status(f'Uninstalling {game["game_name"]}...')
        self._run(lambda: self._uninstall_worker(uuid))

    @Slot(str)
    def launchGame(self, uuid):
        game = self.games.game_by_uuid(uuid)
        if not game:
            self._set_error('Game not found.')
            return
        db = init_games_db(str(CONFIG_DIR), [])
        try:
            record = read_game_record(db, uuid=uuid)
        finally:
            db.close()
        if not record or record['executable'] == NOT_INSTALLED:
            self._set_error(f'{game["game_name"]} does not have a launch executable recorded.')
            return
        heirloom = self._heirloom or Heirloom(**self._config, quiet=True)
        subprocess.Popen(heirloom.launch_command(record['executable']), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._set_status(f'Launched {game["game_name"]}.')

    def _run(self, target):
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _read_saved_password_token(self):
        if not CONFIG_FILE.is_file():
            return ''
        parser = ConfigParser()
        parser.read(CONFIG_FILE)
        if not parser.has_section('HeirloomGM'):
            return ''
        return parser.get('HeirloomGM', 'password', fallback='')

    def _load_public_settings(self):
        if not CONFIG_FILE.is_file():
            self.settingsChanged.emit()
            return
        parser = ConfigParser()
        parser.read(CONFIG_FILE)
        if not parser.has_section('HeirloomGM'):
            self.settingsChanged.emit()
            return
        section = parser['HeirloomGM']
        self._config_user = section.get('user', self._config_user)
        self._config_base_install_dir = section.get('base_install_dir', self._config_base_install_dir)
        self._config_wine_runner = section.get('wine_runner', self._config_wine_runner)
        self._config_wine_path = section.get('wine_path', self._config_wine_path)
        self._config_flatpak_path = section.get('flatpak_path', self._config_flatpak_path)
        self._config_wine_flatpak_app = section.get('wine_flatpak_app', self._config_wine_flatpak_app)
        self._config_sevenzip_path = section.get('7zip_path', self._config_sevenzip_path)
        self._config_default_installation_method = section.get('default_installation_method', self._config_default_installation_method)
        self._config_auto_add_steam = section.getboolean('auto_add_steam', fallback=self._config_auto_add_steam)
        self._config_auto_add_kde = section.getboolean('auto_add_kde', fallback=self._config_auto_add_kde)
        self.settingsChanged.emit()

    def _load_config(self):
        config_parser = get_config(str(CONFIG_DIR) + os.sep)
        self._config = dict(config_parser['HeirloomGM'])

    def _ensure_client(self):
        if not self._heirloom:
            self._load_config()
            self._heirloom = Heirloom(**self._config, quiet=True)
        return self._heirloom

    def _refresh_library_worker(self):
        try:
            heirloom = self._ensure_client()
            self._operationStatus.emit('Logging in...')
            heirloom.login()
            self._operationStatus.emit('Loading library...')
            heirloom.refresh_games_list()
            db = init_games_db(str(CONFIG_DIR), heirloom.games)
            try:
                refresh_game_installation_status(db)
                games = self._merge_database_records(db, heirloom.games)
            finally:
                db.close()
            self._operationStatus.emit('Preparing artwork...')
            self._cache_artwork(games)
            self._gamesLoaded.emit(games)
        except Exception as exc:
            self._operationFailed.emit(str(exc))

    def _install_worker(self, uuid):
        try:
            heirloom = self._ensure_client()
            game = next(game for game in heirloom.games if game.get('installer_uuid') == uuid)
            result = heirloom.install_game(game['game_name'], progress_callback=self._download_progress_callback(game['game_name']))
            if result.get('status') != 'success':
                raise RuntimeError(result.get('stderr') or 'Installation failed.')
            executable = self._select_executable(result.get('executable_files') or [], result['install_path'])
            ui_game = self.games.game_by_uuid(uuid) or {}
            db = init_games_db(str(CONFIG_DIR), heirloom.games)
            try:
                write_game_record(
                    db,
                    name=result['game'],
                    uuid=result['uuid'],
                    install_dir=result['install_path'],
                    executable=executable,
                )
            finally:
                db.close()
            self._operationStatus.emit(f'Installed {result["game"]}.')
            integrations = add_installed_game_integrations(
                result['game'],
                self._config,
                executable,
                install_dir=result.get('unix_install_path', ''),
                icon_path=ui_game.get('coverart_local', ''),
            )
            if integrations:
                labels = []
                if integrations.get('steam'):
                    labels.append('Steam')
                if integrations.get('kde'):
                    labels.append('KDE')
                if labels:
                    self._operationStatus.emit(f'Installed {result["game"]} and added it to {", ".join(labels)}.')
            self._refresh_library_worker()
        except Exception as exc:
            self._operationFailed.emit(str(exc))

    def _uninstall_worker(self, uuid):
        try:
            heirloom = self._ensure_client()
            game = next(game for game in heirloom.games if game.get('installer_uuid') == uuid)
            db = init_games_db(str(CONFIG_DIR), heirloom.games)
            try:
                record = read_game_record(db, uuid=uuid)
                if not record or record['install_dir'] == NOT_INSTALLED:
                    raise RuntimeError(f'{game["game_name"]} is not recorded as installed.')
                heirloom.uninstall_game(game['game_name'], record['install_dir'])
                delete_game_record(db, uuid=uuid)
            finally:
                db.close()
            self._operationStatus.emit(f'Uninstalled {game["game_name"]}.')
            self._refresh_library_worker()
        except Exception as exc:
            self._operationFailed.emit(str(exc))

    def _download_progress_callback(self, game_name):
        def callback(downloaded, total):
            if total:
                value = downloaded / total
                label = f'{downloaded / (1024 * 1024):.1f} MB of {total / (1024 * 1024):.1f} MB'
            else:
                value = -1.0
                label = f'{downloaded / (1024 * 1024):.1f} MB downloaded'
            self._operationStatus.emit(f'Downloading {game_name}...')
            self._operationProgress.emit(value, label)
        return callback

    def _merge_database_records(self, db, games):
        merged = []
        for game in games:
            record = read_game_record(db, uuid=game['installer_uuid'])
            if not record:
                record = read_game_record(db, name=game['game_name'])
            item = dict(game)
            item['install_dir'] = record.get('install_dir', NOT_INSTALLED) if record else NOT_INSTALLED
            item['executable'] = record.get('executable', NOT_INSTALLED) if record else NOT_INSTALLED
            merged.append(item)
        return merged

    def _cache_artwork(self, games):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        for game in games:
            source = game.get('game_coverart')
            game_id = game.get('game_id') or game.get('installer_uuid')
            if not source or not game_id:
                continue
            suffix = Path(urlparse(source).path).suffix or '.jpg'
            artwork_path = CACHE_DIR / f'{game_id}{suffix}'
            if not artwork_path.exists():
                response = session.get(source, timeout=30)
                response.raise_for_status()
                artwork_path.write_bytes(response.content)
            game['coverart_local'] = artwork_path.as_uri()

    def _select_executable(self, executable_files, install_path):
        if not executable_files:
            return NOT_INSTALLED
        preferred = sorted(
            executable_files,
            key=lambda path: (
                'launcher' not in Path(path).name.lower(),
                len(Path(path).parts),
                Path(path).name.lower(),
            ),
        )[0]
        return f'{install_path}\\{Path(preferred).name}'

    def _apply_games(self, games):
        self.games.set_games(games)
        self._finish_operation()

    def _finish_operation(self):
        self._set_busy(False)
        self._set_progress(-1.0, '')
        self._set_status(self._status_message if self._status_message else 'Ready')
        self.operationFinished.emit()

    def _fail_operation(self, message):
        self._set_busy(False)
        self._set_progress(-1.0, '')
        self._set_error(message)
        self._set_status('Something went wrong')
        self.operationFinished.emit()
