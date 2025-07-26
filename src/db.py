import json
import os.path
import sqlite3

db_file = 'data.db'

def commit_exists(bvid: str):
    with sqlite3.connect(db_file) as conn:
        c = conn.execute('select * from commit_history where bvid = ?', (bvid,))
        return c.fetchone() is not None

def insert_commit(bvid: str, data: any, up_id: int, up_name: str):
    with sqlite3.connect(db_file) as conn:
        conn.execute('insert into commit_history (bvid, json_data,up_id, up_name) values (?, ?, ?, ?)', (bvid, json.dumps(data,ensure_ascii=False), up_id, up_name))


def init():
    if not os.path.exists(db_file):
        with sqlite3.connect(db_file) as conn:
            conn.execute("""create table commit_history
                         (
                             id        integer primary key autoincrement,
                             bvid      text,
                             json_data TEXT,
                             up_id     integer,
                             up_name   text
                         )""")