import tempfile
import unittest
from pathlib import Path

from heirloom.database_functions.database_functions import (
    NOT_INSTALLED,
    delete_game_record,
    init_games_db,
    read_game_record,
    refresh_game_installation_status,
    write_game_record,
)


class DatabaseFunctionsTest(unittest.TestCase):
    def test_init_games_db_preserves_install_state_when_catalog_refreshes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            games = [{'game_name': 'Original Name', 'installer_uuid': 'uuid-1'}]
            db = init_games_db(tmpdir, games)
            try:
                write_game_record(db, 'Original Name', 'uuid-1', 'Z:\\Games\\Original', 'Z:\\Games\\Original\\Game.exe')

                refreshed_games = [{'game_name': 'Updated Name', 'installer_uuid': 'uuid-1'}]
                refreshed_db = init_games_db(tmpdir, refreshed_games)
                refreshed_db.close()

                record = read_game_record(db, uuid='uuid-1')
                self.assertEqual(record['name'], 'Updated Name')
                self.assertEqual(record['install_dir'], 'Z:\\Games\\Original')
                self.assertEqual(record['executable'], 'Z:\\Games\\Original\\Game.exe')
            finally:
                db.close()

    def test_read_game_record_uses_bound_parameters_for_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = init_games_db(tmpdir, [{'game_name': "Bob's Game", 'installer_uuid': 'uuid-1'}])
            try:
                record = read_game_record(db, name="Bob's Game")

                self.assertEqual(record['uuid'], 'uuid-1')
            finally:
                db.close()

    def test_delete_game_record_marks_game_not_installed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = init_games_db(tmpdir, [{'game_name': 'Game', 'installer_uuid': 'uuid-1'}])
            try:
                write_game_record(db, 'Game', 'uuid-1', 'Z:\\Games\\Game', 'Z:\\Games\\Game\\Game.exe')

                delete_game_record(db, uuid='uuid-1')

                record = read_game_record(db, uuid='uuid-1')
                self.assertEqual(record['install_dir'], NOT_INSTALLED)
                self.assertEqual(record['executable'], NOT_INSTALLED)
            finally:
                db.close()

    def test_refresh_game_installation_status_clears_missing_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_install = Path(tmpdir) / 'Installed'
            existing_install.mkdir()
            db = init_games_db(tmpdir, [{'game_name': 'Game', 'installer_uuid': 'uuid-1'}])
            try:
                write_game_record(db, 'Game', 'uuid-1', str(existing_install), str(existing_install / 'Game.exe'))

                existing_install.rmdir()
                refresh_game_installation_status(db)

                record = read_game_record(db, uuid='uuid-1')
                self.assertEqual(record['install_dir'], NOT_INSTALLED)
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()
