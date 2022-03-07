from ml_utils import *
import youtube_dl as ytdl
import time
from dotenv import dotenv_values
import sqlite3 as sql


config = dotenv_values(".env")
queries = ["machine+learning", "data+science", "learn+italian", "valorant"]

def update_db(user):
    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM videos")
        conn.commit()
        ydl = ytdl.YoutubeDL({"ignoreerrors": True})
        # with open("new_videos.json", "w+") as output:
        with open("users\\{}\\user.json".format(user.username) , "r") as data_file:
            user_info = json.load(data_file)
        for query in user_info["queries"]:
            r = ydl.extract_info("ytsearch{}:{}".format(config["NUMBER_VIDEOS"], query), download=False) # Change to 50 after
            for entry in r['entries']:
                if entry is not None:
                    p = compute_prediction(entry, user.username)
                    data_front = {
                        'title': entry['title'].replace("'", ""),
                        'thumbnail': entry["thumbnails"][-1]['url'],
                        'score': float(p),
                        'video_id': entry['webpage_url'],
                        'upload_date': time.time()
                    }
                    c.execute("INSERT INTO videos VALUES ('{title}', '{thumbnail}', '{score}', '{video_id}', '{upload_date}')".format(**data_front))
                    conn.commit()
    return True

def get_videos_to_train(user):
    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        ydl = ytdl.YoutubeDL({"ignoreerrors": True})
        with open("users\\{}\\user.json".format(user.username) , "r") as data_file:
            user_info = json.load(data_file)
        for query in user_info["queries"]:
            r = ydl.extract_info("ytsearch{}:{}".format(config["NUMBER_VIDEOS"], query), download=False) # Change to 50 after
            for entry in r['entries']:
                if entry is not None:
                    data_front = {
                        'title': entry['title'].replace("'", ""),
                        'thumbnail': entry["thumbnails"][-1]['url'],
                        'score': -1,
                        'video_id': entry['webpage_url'],
                        'upload_date': time.time()
                    }
                    c.execute("INSERT INTO videos VALUES ('{title}', '{thumbnail}', '{score}', '{video_id}', '{upload_date}')".format(**data_front))
                    conn.commit()
    return True