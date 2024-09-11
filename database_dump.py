import os
import sqlite3
import rich


db = sqlite3.connect(os.path.expanduser('~/.config/heirloom/games.db'))
cursor = db.cursor()
sql = 'SELECT * FROM games'
result = cursor.execute(sql).fetchall()
data = [r for r in result]
rich.print(data)

