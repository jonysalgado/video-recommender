import run_backend
import sqlite3 as sql
from dotenv import dotenv_values

config = dotenv_values(".env")

if __name__ == '__main__':
    with sql.connect(config['DB_NAME']) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE videos
                     (title text, thumbnail text, score real, video_id text, upload_date real)''')
        conn.commit()
        c.execute('''CREATE TABLE feedback
                     (video_id text, label integer)''')
        conn.commit()

    run_backend.update_db()