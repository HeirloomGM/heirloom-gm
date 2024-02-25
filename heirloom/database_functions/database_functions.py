import os
import sys
import sqlite3
from rich.console import Console

from ..path_functions import *


def init_games_db(config_dir: str, games_list: list):
    existing = True if os.path.isfile(config_dir + 'games.db') else False
    db = sqlite3.connect(config_dir + 'games.db')
    if not existing:
        cursor = db.cursor()
        sql = '''
        CREATE TABLE games(
            name TEXT, 
            uuid TEXT PRIMARY KEY UNIQUE, 
            install_dir TEXT,
            executable TEXT    
        )
        '''
        cursor.execute(sql)
        db.commit()
        sql = '''INSERT INTO games VALUES(?, ?, ?, ?)'''
        for each_game in games_list:
            cursor.execute(sql, (each_game['game_name'], each_game['installer_uuid'], 'Not Installed', 'Not Installed'))
            db.commit()
    return db


def write_game_record(db, name=None, uuid=None, install_dir=None, executable=None):
    sql = "INSERT INTO games VALUES(?, ?, ?, ?) ON CONFLICT(uuid) DO UPDATE SET name=excluded.name, install_dir=excluded.install_dir, executable=excluded.executable" 
    cursor = db.cursor()    
    cursor.execute(sql, (name, uuid, install_dir, executable))
    db.commit()
 

def read_game_record(db, name=None, uuid=None):
    if name:
        sql = f"SELECT * FROM games WHERE name='{name}'"
    if uuid:
        sql = f"SELECT * FROM games WHERE uuid='{uuid}'"
    if not sql:
        Console().print(f':exclamation: Must specify name or UUID for game!')
        sys.exit(1)
    cursor = db.cursor()
    result = cursor.execute(sql)
    record = result.fetchone()
    return dict(zip(('name', 'uuid', 'install_dir', 'executable'), record)) if record else None
   

def delete_game_record(db, name=None, uuid=None):
    if uuid:
        sql = f"DELETE FROM games WHERE uuid='{uuid}'"
    elif name:
        sql = f"DELETE FROM games WHERE name='{name}'"
    else:
        Console().print(':exclamation: Must specify name or UUID for game!')
        sys.exit(1)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()


def refresh_game_status(db):
    """
    This function is used to detect manual uninstallations. If the installation directory isn't found,
    set the install_dir to "Not Installed".
    """
    sql = "SELECT * FROM games WHERE install_dir != 'Not Installed'"
    cursor = db.cursor()
    result = [{'name': name, 'uuid': uuid, 'install_dir': install_dir, 'executable': executable} for (name, uuid, install_dir, executable) in cursor.execute(sql).fetchall()]
    for each in result:
        if not os.path.exists(convert_to_unix_path(each['install_dir'])):
            sql = f"UPDATE games SET install_dir = 'Not Installed' WHERE uuid = '{each['uuid']}'"
            result = cursor.execute(sql)
            db.commit()
