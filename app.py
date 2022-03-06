

from flask import Flask, render_template, request, redirect
import os
import run_backend
import time
import sqlite3 as sql
from dotenv import dotenv_values


config = dotenv_values(".env")

app = Flask(__name__)

user_name = "jonysalgado"

db_name = user_name + ".db"

if config["ENV"] == 'dev' and db_name not in os.listdir("users\\" + user_name):
    with sql.connect("users\\{}\\{}".format(user_name, db_name)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE videos
                     (title text, thumbnail text, score real, video_id text, upload_date real)''')
        conn.commit()
        c.execute('''CREATE TABLE feedback
                     (video_id text, label integer)''')
        conn.commit()

class Video:
    def __init__(self, video_id, title, thumbnail,score):
        self.video_id = video_id
        self.title = title
        self.thumbnail = thumbnail
        self.score = score

def get_data_from_db(c):
    videos = []
    for line in c.execute("SELECT * FROM videos"):
        line_json = {
                        'title': line[0], 
                        'thumbnail': line[1], 
                        'score': line[2], 
                        'video_id': line[3],
                        'upload_date': line[4]
                    }
        videos.append(line_json)   

    return videos   

def get_predictions():
    
    with sql.connect("users\\{}\\{}".format(user_name, db_name)) as conn:
        c = conn.cursor()
        lines = []
        for line in c.execute("SELECT * FROM videos"):
            lines.append(line)
        if len(lines) == 0:
            run_backend.update_db(user_name)
        
        videos = get_data_from_db(c)          

        last_update = videos[-1]['upload_date']
        if time.time() - last_update > (24*3600): # approximately 1 day
            run_backend.update_db(user_name)
            videos = get_data_from_db(c) 
        
    # with open("new_videos.json", "r") as data_file:
    #     for line in data_file:
    #         line_json = json.loads(line)
    #         videos.append(line_json)
    predictions = []
    for video in videos:
        predictions.append(Video(video["video_id"], 
                    video["title"], 
                    video["thumbnail"], 
                    round(video["score"], 2)))

        
    predictions = sorted(predictions, key = lambda x: x.score, reverse=True)[:30]
    return predictions, int((time.time() - last_update)/(60 * 60))


preds, last_update = get_predictions()

@app.route('/')
def main_page():
    return render_template("table.html", title="Video Recommender", videos=preds, last_update=last_update)

@app.route('/background_process_button', methods=['POST'])
def background_process_botton():
    feedback = {}
    for pred in preds:

        if type(request.form.get(pred.video_id + "yes")) == str:
            feedback['video_id'] = pred.video_id
            feedback['label'] = 1
            print(pred.video_id, 1)
        elif type(request.form.get(pred.video_id + "no")) == str:
            feedback['video_id'] = pred.video_id
            feedback['label'] = 0
            print(pred.video_id, 0)

    with sql.connect("users\\{}\\{}".format(user_name, db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM feedback WHERE video_id='{}'".format(feedback['video_id']))
        conn.commit()
        c.execute("INSERT INTO feedback VALUES ('{video_id}', '{label}')".format(**feedback))
        conn.commit()
    print("ok")
    return redirect('/')

@app.route('/get_feedbacks')
def get_feedbacks():
    feedbacks = {}
    with sql.connect("users\\{}\\{}".format(user_name, db_name)) as conn:
        c = conn.cursor()
        for line in c.execute("SELECT * FROM feedback"):
            feedbacks[line[0]] = line[1]
    
    return feedbacks


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    