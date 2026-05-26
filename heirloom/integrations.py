import os
import shlex
import struct
import zlib
from pathlib import Path
from urllib.parse import urlparse


def truthy(value):
    return str(value).strip().lower() in ('1', 'yes', 'true', 'on')


def build_wine_command(config, executable):
    runner = config.get('wine_runner', 'native')
    if runner == 'flatpak':
        flatpak_path = config.get('flatpak_path') or 'flatpak'
        app_id = config.get('wine_flatpak_app') or 'org.winehq.Wine'
        return [flatpak_path, 'run', app_id, executable]
    return [config.get('wine_path') or 'wine', executable]


def desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def desktop_exec(command):
    return ' '.join(desktop_quote(part) if any(ch.isspace() or ch in '\\"' for ch in str(part)) else str(part) for part in command)


def icon_path_from_uri(value):
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme == 'file':
        return parsed.path
    return value


def slugify(value):
    cleaned = ''.join(ch.lower() if ch.isalnum() else '-' for ch in value)
    parts = [part for part in cleaned.split('-') if part]
    return '-'.join(parts) or 'game'


def write_kde_game_entry(game_name, config, executable, icon_path=''):
    desktop_dir = Path('~/.local/share/applications').expanduser()
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / f'heirloom-{slugify(game_name)}.desktop'
    command = build_wine_command(config, executable)
    desktop_file.write_text(
        '\n'.join(
            [
                '[Desktop Entry]',
                'Type=Application',
                f'Name={game_name}',
                f'Comment=Launch {game_name} with Heirloom Games Manager',
                f'Exec={desktop_exec(command)}',
                f'Icon={icon_path}' if icon_path else 'Icon=applications-games',
                'Terminal=false',
                'Categories=Game;',
                'StartupNotify=true',
                'X-HeirloomGame=true',
                '',
            ]
        )
    )
    desktop_file.chmod(0o644)
    return desktop_file


def steam_userdata_config_dirs():
    roots = [
        Path('~/.steam/steam/userdata').expanduser(),
        Path('~/.local/share/Steam/userdata').expanduser(),
        Path('~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata').expanduser(),
    ]
    dirs = []
    for root in roots:
        if not root.is_dir():
            continue
        for user_dir in root.iterdir():
            config_dir = user_dir / 'config'
            if user_dir.is_dir() and config_dir.is_dir():
                dirs.append(config_dir)
    return dirs


class BinaryVdfReader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def read_cstring(self):
        end = self.data.index(b'\x00', self.offset)
        value = self.data[self.offset:end].decode('utf-8', errors='replace')
        self.offset = end + 1
        return value

    def read_int(self):
        value = struct.unpack_from('<i', self.data, self.offset)[0]
        self.offset += 4
        return value

    def read_object(self):
        result = {}
        while self.offset < len(self.data):
            kind = self.data[self.offset]
            self.offset += 1
            if kind == 0x08:
                break
            key = self.read_cstring()
            if kind == 0x00:
                result[key] = self.read_object()
            elif kind == 0x01:
                result[key] = self.read_cstring()
            elif kind == 0x02:
                result[key] = self.read_int()
            else:
                raise ValueError(f'Unsupported binary VDF field type: {kind}')
        return result


def read_shortcuts(path):
    if not path.is_file() or path.stat().st_size == 0:
        return {'shortcuts': {}}
    try:
        reader = BinaryVdfReader(path.read_bytes())
        return reader.read_object()
    except Exception:
        backup = path.with_suffix('.vdf.heirloom-backup')
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        return {'shortcuts': {}}


def write_binary_vdf_object(items):
    output = bytearray()
    for key, value in items.items():
        encoded_key = str(key).encode('utf-8') + b'\x00'
        if isinstance(value, dict):
            output.extend(b'\x00' + encoded_key + write_binary_vdf_object(value))
        elif isinstance(value, int):
            output.extend(b'\x02' + encoded_key + struct.pack('<i', value))
        else:
            output.extend(b'\x01' + encoded_key + str(value).encode('utf-8') + b'\x00')
    output.extend(b'\x08')
    return bytes(output)


def signed_int32(value):
    value &= 0xFFFFFFFF
    if value >= 0x80000000:
        value -= 0x100000000
    return value


def shortcut_app_id(app_name, exe):
    return signed_int32(zlib.crc32((exe + app_name).encode('utf-8')) | 0x80000000)


def steam_shortcut_fields(game_name, config, executable, start_dir='', icon_path=''):
    runner = config.get('wine_runner', 'native')
    if runner == 'flatpak':
        exe = config.get('flatpak_path') or 'flatpak'
        launch_options = ' '.join(shlex.quote(part) for part in ['run', config.get('wine_flatpak_app') or 'org.winehq.Wine', executable])
    else:
        exe = config.get('wine_path') or 'wine'
        launch_options = shlex.quote(executable)
    return {
        'appid': shortcut_app_id(game_name, exe),
        'AppName': game_name,
        'Exe': exe,
        'StartDir': start_dir,
        'icon': icon_path,
        'ShortcutPath': '',
        'LaunchOptions': launch_options,
        'IsHidden': 0,
        'AllowDesktopConfig': 1,
        'AllowOverlay': 1,
        'OpenVR': 0,
        'Devkit': 0,
        'DevkitGameID': '',
        'LastPlayTime': 0,
        'tags': {'0': 'Heirloom'},
    }


def write_steam_shortcut(game_name, config, executable, start_dir='', icon_path=''):
    written = []
    for config_dir in steam_userdata_config_dirs():
        shortcuts_path = config_dir / 'shortcuts.vdf'
        data = read_shortcuts(shortcuts_path)
        shortcuts = data.setdefault('shortcuts', {})
        target = steam_shortcut_fields(game_name, config, executable, start_dir=start_dir, icon_path=icon_path)
        existing_key = None
        for key, shortcut in shortcuts.items():
            if shortcut.get('AppName') == game_name and shortcut.get('DevkitGameID', '') in ('', 'heirloom'):
                existing_key = key
                break
        if existing_key is None:
            existing_key = str(max([int(key) for key in shortcuts.keys() if str(key).isdigit()] or [-1]) + 1)
        shortcuts[existing_key] = target
        shortcuts_path.write_bytes(write_binary_vdf_object(data))
        written.append(shortcuts_path)
    return written


def add_installed_game_integrations(game_name, config, executable, install_dir='', icon_path=''):
    results = {}
    icon_path = icon_path_from_uri(icon_path)
    if truthy(config.get('auto_add_kde')):
        results['kde'] = [write_kde_game_entry(game_name, config, executable, icon_path=icon_path)]
    if truthy(config.get('auto_add_steam')):
        results['steam'] = write_steam_shortcut(game_name, config, executable, start_dir=install_dir, icon_path=icon_path)
    return results
