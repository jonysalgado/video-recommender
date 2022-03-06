from ml_utils import *
import youtube_dl as ytdl
import time
from dotenv import dotenv_values
import sqlite3 as sql


config = dotenv_values(".env")
queries = ["machine+learning", "data+science", "learn+italian", "valorant"]

def update_db(user):
    db_name = user + ".db"
    with sql.connect("users\\{}\\{}".format(user, db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM videos")
        conn.commit()
        ydl = ytdl.YoutubeDL({"ignoreerrors": True})
        # with open("new_videos.json", "w+") as output:
        for query in queries:
            r = ydl.extract_info("ytsearch{}:{}".format(config["NUMBER_VIDEOS"], query), download=False) # Change to 50 after
            for entry in r['entries']:
                if entry is not None:
                    p = compute_prediction(entry, user)
                    data_front = {
                        'title': entry['title'].replace("'", ""),
                        'thumbnail': entry["thumbnails"][-1]['url'],
                        'score': float(p),
                        'video_id': entry['webpage_url'],
                        'upload_date': time.time()
                    }
                    c.execute("INSERT INTO videos VALUES ('{title}', '{thumbnail}', '{score}', '{video_id}', '{upload_date}')".format(**data_front))
                    conn.commit()
                    # data_front = {
                    #     'title': entry['title'].replace("'", ""),
                    #     'thumbnail': entry["thumbnails"][-1]['url'],
                    #     'score': float(p),
                    #     'video_id': entry['webpage_url'],
                    #     'upload_date': time.time_ns()
                    # }
                    # output.write("{}\n".format(json.dumps(data_front)))
    return True