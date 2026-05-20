import os
import sqlite3
from pathlib import Path
from rich.console import Console

from ..path_functions import *


NOT_INSTALLED = 'Not Installed'


def init_games_db(config_dir: str, games_list: list):
    config_path = Path(config_dir).expanduser()
    config_path.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(config_path / 'games.db')
    db.execute('''
    CREATE TABLE IF NOT EXISTS games(
        name TEXT NOT NULL,
        uuid TEXT PRIMARY KEY UNIQUE,
        install_dir TEXT NOT NULL DEFAULT 'Not Installed',
        executable TEXT NOT NULL DEFAULT 'Not Installed'
    )
    ''')
    sql = '''
    INSERT INTO games(name, uuid, install_dir, executable)
    VALUES(?, ?, ?, ?)
    ON CONFLICT(uuid) DO UPDATE SET name=excluded.name
    '''
    db.executemany(
        sql,
        [
            (
                each_game['game_name'],
                each_game['installer_uuid'],
                NOT_INSTALLED,
                NOT_INSTALLED,
            )
            for each_game in games_list
            if each_game.get('game_name') and each_game.get('installer_uuid')
        ],
    )
    db.commit()
    return db


def write_game_record(db, name=None, uuid=None, install_dir=None, executable=None):
    sql = """
    INSERT INTO games(name, uuid, install_dir, executable)
    VALUES(?, ?, ?, ?)
    ON CONFLICT(uuid) DO UPDATE SET
        name=excluded.name,
        install_dir=excluded.install_dir,
        executable=excluded.executable
    """
    db.execute(sql, (name, uuid, install_dir or NOT_INSTALLED, executable or NOT_INSTALLED))
    db.commit()
 

def read_game_record(db, name=None, uuid=None):
    if name:
        sql = "SELECT name, uuid, install_dir, executable FROM games WHERE name = ?"
        params = (name,)
    elif uuid:
        sql = "SELECT name, uuid, install_dir, executable FROM games WHERE uuid = ?"
        params = (uuid,)
    else:
        Console().print(f':exclamation: Must specify name or UUID for game!')
        return None
    result = db.execute(sql, params)
    record = result.fetchone()
    return dict(zip(('name', 'uuid', 'install_dir', 'executable'), record)) if record else None
   

def delete_game_record(db, name=None, uuid=None):
    if uuid:
        sql = "UPDATE games SET install_dir = ?, executable = ? WHERE uuid = ?"
        params = (NOT_INSTALLED, NOT_INSTALLED, uuid)
    elif name:
        sql = "UPDATE games SET install_dir = ?, executable = ? WHERE name = ?"
        params = (NOT_INSTALLED, NOT_INSTALLED, name)
    else:
        Console().print(':exclamation: Must specify name or UUID for game!')
        return
    db.execute(sql, params)
    db.commit()


def refresh_game_installation_status(db):
    """
    This function is used to detect manual uninstallations. If the installation directory isn't found,
    set the install_dir to "Not Installed".
    """
    sql = "SELECT name, uuid, install_dir, executable FROM games WHERE install_dir != ?"
    cursor = db.cursor()
    result = [
        {'name': name, 'uuid': uuid, 'install_dir': install_dir, 'executable': executable}
        for (name, uuid, install_dir, executable) in cursor.execute(sql, (NOT_INSTALLED,)).fetchall()
    ]
    for each in result:
        if not os.path.exists(convert_to_unix_path(each['install_dir'])):
            sql = "UPDATE games SET install_dir = ?, executable = ? WHERE uuid = ?"
            cursor.execute(sql, (NOT_INSTALLED, NOT_INSTALLED, each['uuid']))
            db.commit()
