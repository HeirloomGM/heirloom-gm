import tempfile
import unittest
from pathlib import Path

from heirloom.integrations import (
    build_wine_command,
    read_shortcuts,
    steam_shortcut_fields,
    write_binary_vdf_object,
)


class IntegrationsTest(unittest.TestCase):
    def test_build_wine_command_supports_flatpak_runner(self):
        command = build_wine_command(
            {
                'wine_runner': 'flatpak',
                'flatpak_path': 'flatpak',
                'wine_flatpak_app': 'org.winehq.Wine',
            },
            'Z:\\Games\\Game\\Game.exe',
        )

        self.assertEqual(command, ['flatpak', 'run', 'org.winehq.Wine', 'Z:\\Games\\Game\\Game.exe'])

    def test_steam_shortcut_round_trip_preserves_fields(self):
        shortcut = steam_shortcut_fields(
            'Example Game',
            {'wine_runner': 'native', 'wine_path': '/usr/bin/wine'},
            'Z:\\Games\\Example\\Example.exe',
            start_dir='/home/deck/Games/Example',
            icon_path='/tmp/example.png',
        )
        data = {'shortcuts': {'0': shortcut}}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'shortcuts.vdf'
            path.write_bytes(write_binary_vdf_object(data))
            loaded = read_shortcuts(path)

        self.assertEqual(loaded['shortcuts']['0']['AppName'], 'Example Game')
        self.assertEqual(loaded['shortcuts']['0']['Exe'], '/usr/bin/wine')
        self.assertEqual(loaded['shortcuts']['0']['tags']['0'], 'Heirloom')


if __name__ == '__main__':
    unittest.main()
