

from flask import Flask, render_template, request, redirect
import os
import run_backend
import time
import sqlite3 as sql
import json
from dotenv import dotenv_values
import shutil


config = dotenv_values(".env")

app = Flask(__name__)

class User:
    def __init__(self, username, db_name):
        self.username = username
        self.db_name = db_name

    def new_user(self, username):
        self.username = username
        self.db_name = username + ".db"

user = User("", "")
# with open("users\\{}\\user.json".format(username), "r") as data_file:
#     user_info = json.load(data_file)

if config["ENV"] == 'dev':
    if "users" not in os.listdir():
        os.mkdir("users")

class Video:
    def __init__(self, video_id, title, thumbnail,score):
        self.video_id = video_id
        self.title = title
        self.thumbnail = thumbnail
        self.score = score

def get_list_queries(queries):
    list_queries = []
    for query in queries:
        if query != '':
            list_queries.append(query.lower().replace(" ", "+"))

    return list_queries

def login_data(username, user_info=None):
    if username in os.listdir("users"):
        with open("users\\{}\\user.json".format(username), "r") as data_file:
            user_info = json.load(data_file)
    
    else:
        os.mkdir("users\\" + username)
        os.mkdir("users\\" + username + "\\models")
        with open("users\\{}\\user.json".format(username), "w") as input:
            json.dump(user_info, input)

        db_name = username + ".db"
        with sql.connect("users\\{}\\{}".format(username, db_name)) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE videos
                        (title text, thumbnail text, score real, video_id text, upload_date real)''')
            conn.commit()
            c.execute('''CREATE TABLE feedback
                        (video_id text, label integer)''')
            conn.commit()

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
    print("username", user.username)
    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        lines = []
        for line in c.execute("SELECT * FROM videos"):
            lines.append(line)
        if len(lines) == 0:
            run_backend.update_db(user)
        
        videos = get_data_from_db(c)          

        last_update = videos[-1]['upload_date']
        if time.time() - last_update > (24*3600): # approximately 1 day
            run_backend.update_db(user)
            videos = get_data_from_db(c) 
        
    predictions = []
    for video in videos:
        predictions.append(Video(video["video_id"], 
                    video["title"], 
                    video["thumbnail"], 
                    round(video["score"], 2)))

        
    predictions = sorted(predictions, key = lambda x: x.score, reverse=True)[:30]
    return predictions, int((time.time() - last_update)/(60 * 60))

@app.route('/')
def main_page():
    if user.username == '':
        username = request.args.get('username')
        if username == None:
            return redirect('/login')
        else:
            user.new_user(username)

    if user.username not in os.listdir("users\\"):
        name = request.args.get('name')
        profile_url = request.args.get('profile_url')
        subject1 = request.args.get('subject1')
        subject2 = request.args.get('subject2')
        subject3 = request.args.get('subject3')
        subject4 = request.args.get('subject4')
        subject5 = request.args.get('subject5')
        queries = get_list_queries([subject1, subject2, subject3, subject4, subject5])
        info = {
            "name": name,
            "url_photo_profile": profile_url,
            "queries": queries
        }
        user_info = login_data(user.username, info)
        return redirect('/new_user')
    
    else:
        user_info = login_data(user.username)
        
    preds, last_update = get_predictions()

    return render_template("table.html", title="Video Recommender", 
                                         videos=preds, 
                                         last_update =last_update,
                                         user_name=user_info["name"],
                                         user_id=user.username)

@app.route('/new_user')
def new_user():
    run_backend.get_videos_to_train(user)
    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        videos = get_data_from_db(c)
    
    user_info = login_data(user.username)
    return render_template("vote.html", title="Video Recommender", 
                                         videos=videos, 
                                         last_update =0,
                                         user_name=user_info["name"],
                                         user_id=user.username)


@app.route('/background_process_button', methods=['POST'])
def background_process_botton():
    preds, _ = get_predictions()
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

    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM feedback WHERE video_id='{}'".format(feedback['video_id']))
        conn.commit()
        c.execute("INSERT INTO feedback VALUES ('{video_id}', '{label}')".format(**feedback))
        conn.commit()
    return redirect('/')

@app.route('/get_feedbacks')
def get_feedbacks():
    feedbacks = {}
    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        for line in c.execute("SELECT * FROM feedback"):
            feedbacks[line[0]] = line[1]
    
    return feedbacks

@app.route('/login')
def login():
    user.new_user('')
    return render_template('login.html')

@app.route('/subscription')
def subscription():
    username = request.args.get('username')
    print("login:", username)
    if username not in os.listdir("users"):
        return render_template('subscription.html')
    
    return redirect('/?username=' + username)

@app.route('/delete_account')
def delete():
    if request.args.get('account') == user.username:
        shutil.rmtree("users/" + user.username)

        return redirect('/login')
    else:
        return redirect('/')

@app.route('/background_process_button_vote', methods=['POST'])
def background_process_botton_vote():
    preds, _ = get_predictions()
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

    with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM feedback WHERE video_id='{}'".format(feedback['video_id']))
        conn.commit()
        c.execute("INSERT INTO feedback VALUES ('{video_id}', '{label}')".format(**feedback))
        conn.commit()
        with sql.connect("users\\{}\\{}".format(user.username, user.db_name)) as conn:
            c = conn.cursor()
            
        videos = get_data_from_db(c)
    
        user_info = login_data(user.username)
    return render_template("vote.html", title="Video Recommender", 
                                         videos=videos, 
                                         last_update =0,
                                         user_name=user_info["name"],
                                         user_id=user.username)

@app.route('/active_learning', methods=['POST'])
def active_learning():
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    