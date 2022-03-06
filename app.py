

from flask import Flask, render_template, request, redirect
import os
import run_backend
import time
import sqlite3 as sql
import json
from dotenv import dotenv_values


config = dotenv_values(".env")

app = Flask(__name__)

username = "jonysalgado"

db_name = username + ".db"
with open("users\\{}\\user.json".format(username), "r") as data_file:
    user_info = json.load(data_file)

if config["ENV"] == 'dev' and db_name not in os.listdir("users\\" + username):
    with sql.connect("users\\{}\\{}".format(username, db_name)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE videos
                     (title text, thumbnail text, score real, video_id text, upload_date real)''')
        conn.commit()
        c.execute('''CREATE TABLE feedback
                     (video_id text, label integer)''')
        conn.commit()

    if "users" not in os.listdir():
        os.mkdir("users")

class Video:
    def __init__(self, video_id, title, thumbnail,score):
        self.video_id = video_id
        self.title = title
        self.thumbnail = thumbnail
        self.score = score

def login_data(username, user_info=None):
    if username in os.listdir("users"):
        with open("users\\{}\\user.json".format(username), "r") as data_file:
            user_info = json.load(data_file)
    
    else:
        os.mkdir("users\\" + username)
        os.mkdir("users\\" + username + "\\models")
        with open("users\\{}\\user.json".format(username), "w") as input:
            json.dump(user_info, input)
    return user_info


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
    
    with sql.connect("users\\{}\\{}".format(username, db_name)) as conn:
        c = conn.cursor()
        lines = []
        for line in c.execute("SELECT * FROM videos"):
            lines.append(line)
        if len(lines) == 0:
            run_backend.update_db(username)
        
        videos = get_data_from_db(c)          

        last_update = videos[-1]['upload_date']
        if time.time() - last_update > (24*3600): # approximately 1 day
            run_backend.update_db(username)
            videos = get_data_from_db(c) 
        
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
    username = request.args.get('username')
    if username == None:
        return redirect('/login')

    if username not in os.listdir("users\\"):
        name = request.args.get('name')
        profile_url = request.args.get('profile_url')
        subject1 = request.args.get('subject1')
        subject2 = request.args.get('subject2')
        subject3 = request.args.get('subject3')
        subject4 = request.args.get('subject4')
        subject5 = request.args.get('subject5')
        info = {
            "name": name,
            "url_photo_profile": profile_url,
            "queries": [subject1, subject2, subject3, subject4, subject5]
        }
        user_info = login_data(username, info)
    
    else:
        user_info = login_data(username)
        


    return render_template("table.html", title="Video Recommender", 
                                         videos=preds, 
                                         last_update =last_update,
                                         user_name=user_info["name"])

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

    with sql.connect("users\\{}\\{}".format(username, db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM feedback WHERE video_id='{}'".format(feedback['video_id']))
        conn.commit()
        c.execute("INSERT INTO feedback VALUES ('{video_id}', '{label}')".format(**feedback))
        conn.commit()
    return redirect('/')

@app.route('/get_feedbacks')
def get_feedbacks():
    feedbacks = {}
    with sql.connect("users\\{}\\{}".format(username, db_name)) as conn:
        c = conn.cursor()
        for line in c.execute("SELECT * FROM feedback"):
            feedbacks[line[0]] = line[1]
    
    return feedbacks

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/subscription')
def subscription():
    username = request.args.get('username')
    print("login:", username)
    if username not in os.listdir("users"):
        return render_template('subscription.html')
    
    return redirect('/?username=' + username)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    