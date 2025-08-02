import datetime
import json
import os.path
import sqlite3

from loguru import logger

from src.utils import get_now_str

db_file = 'data.db'

def commit_exists(bvid: str):
    with sqlite3.connect(db_file) as conn:
        c = conn.execute('select * from commit_history where bvid = ?', (bvid,))
        return c.fetchone() is not None

def insert_commit(bvid: str, data: any, up_id: int, up_name: str):
    commit_time = get_now_str()
    with sqlite3.connect(db_file) as conn:
        conn.execute('insert into commit_history (bvid, json_data,up_id, up_name,commit_time) values (?, ?, ?, ?, ?)', (bvid, json.dumps(data,ensure_ascii=False), up_id, up_name,commit_time))


def init():
    if not os.path.exists(db_file):
        with sqlite3.connect(db_file) as conn:
            logger.info('init sqlite, create table commit_history')
            conn.execute("""create table commit_history
                         (
                             id        integer primary key autoincrement,
                             bvid      text,
                             json_data TEXT,
                             up_id     integer,
                             up_name   text,
                             commit_time text
                         )""")
    with sqlite3.connect(db_file) as conn:
        c = conn.execute("select * from sqlite_master where type = 'view' and name = 'up_summary'")
        if c.fetchone() is None:
            logger.info('init sqlite, create view up_summary')
            conn.execute("""CREATE VIEW up_summary as 
            SELECT up_id, up_name, 
            SUM(CASE WHEN json_extract(json_data, '$.haveAd') IS TRUE THEN 1 ELSE 0 END) AS ad_count, 
            SUM(CASE WHEN json_extract(json_data, '$.haveAd') IS NOT TRUE THEN 1 ELSE 0 END) AS not_ad_count, 
                   count(*) as total_count 
            FROM commit_history GROUP BY up_id, up_name order by total_count desc
            """)