import pandas as pd
import joblib as jb
from scipy.sparse import hstack, csr_matrix
import numpy as np
import json

def compute_features(data, user):

    title_vec_lgbm = jb.load("users\\{}\\models\\title_vec_lgbm.pkl.z".format(user))
    title_vec_rf = jb.load("users\\{}\\models\\title_vec_rf.pkl.z".format(user))

    df = pd.DataFrame([data.values()], columns=data.keys())
    features = ["views_per_day", "days_since_upload", "duration", "view_count"]
    df['upload_date'] = pd.to_datetime(df["upload_date"])
    df["days_since_upload"] = (pd.Timestamp.today() - df["upload_date"])/np.timedelta64(1, 'D')
    df["views_per_day"] = df["view_count"]/df["days_since_upload"] 

    vectorized_title_lgbm = title_vec_lgbm.transform(df['title'])
    vectorized_title_rf = title_vec_rf.transform(df['title'])


    Xlgbm = hstack([df[features], vectorized_title_lgbm])
    Xrf = hstack([df[features], vectorized_title_rf])
    return Xlgbm, Xrf


def compute_prediction(data, user):
    Xlgbm, Xrf = compute_features(data, user)

    mdl_rf = jb.load("users\\{}\\models\\rf.pkl.z".format(user))
    mdl_lgbm = jb.load("users\\{}\\models\\lgbm.pkl.z".format(user))

    if Xlgbm is None or Xrf is None:
        return 0


    p_rf = mdl_rf.predict_proba(Xrf)[0][1]
    p_lgbm = mdl_lgbm.predict_proba(Xlgbm)[0][1]

    p = 0.7*p_rf + 0.3*p_lgbm

    return p

def log_data(data, feature_array, p):

    video_id = data['webpage_url']
    data['prediction'] = p
    data['feature_array'] = feature_array.todense().tolist()
    print(video_id, json.dumps(data))







