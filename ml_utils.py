import pandas as pd
import joblib as jb
from scipy.sparse import hstack
import numpy as np
from sklearn.feature_extraction.text import  TfidfVectorizer
from sklearn.model_selection import train_test_split
import json

def compute_features(df, title_vec, dfval=None, is_train=False):

    title_vec_lgbm, title_vec_rf = title_vec

    features = ["views_per_day", "days_since_upload", "duration", "view_count"]
    df['upload_date'] = pd.to_datetime(df["upload_date"])
    df["days_since_upload"] = (pd.Timestamp.today() - df["upload_date"])/np.timedelta64(1, 'D')
    df["views_per_day"] = df["view_count"]/df["days_since_upload"] 

    if is_train==False:
        vectorized_title_lgbm = title_vec_lgbm.transform(df['title'])
        vectorized_title_rf = title_vec_rf.transform(df['title'])
        Xlgbm = hstack([df[features], vectorized_title_lgbm])
        Xrf = hstack([df[features], vectorized_title_rf])
        return Xlgbm, Xrf

    else:
        features = ["views_per_day", "days_since_upload", "duration", "view_count"]
        dfval['upload_date'] = pd.to_datetime(dfval["upload_date"])
        dfval["days_since_upload"] = (pd.Timestamp.today() - dfval["upload_date"])/np.timedelta64(1, 'D')
        dfval["views_per_day"] = dfval["view_count"]/dfval["days_since_upload"] 

        vectorized_title_lgbm = title_vec_lgbm.fit_transform(df['title'])
        vectorized_title_rf = title_vec_rf.fit_transform(df['title'])
        Xlgbm = hstack([df[features], vectorized_title_lgbm])
        Xrf = hstack([df[features], vectorized_title_rf])

        vectorized_title_lgbm_val = title_vec_lgbm.fit_transform(dfval['title'])
        vectorized_title_rf_val = title_vec_rf.fit_transform(dfval['title'])
        Xlgbm_val = hstack([dfval[features], vectorized_title_lgbm_val])
        Xrf_val = hstack([dfval[features], vectorized_title_rf_val])

        return Xlgbm, Xrf, Xlgbm_val, Xrf_val


def compute_prediction(data, user):

    title_vec_lgbm = jb.load("users\\{}\\models\\title_vec_lgbm.pkl.z".format(user))
    title_vec_rf = jb.load("users\\{}\\models\\title_vec_rf.pkl.z".format(user))

    title_vec = [title_vec_lgbm, title_vec_rf]
    df = pd.DataFrame([data.values()], columns=data.keys())
    Xlgbm, Xrf = compute_features(df, title_vec)

    mdl_rf = jb.load("users\\{}\\models\\rf.pkl.z".format(user))
    mdl_lgbm = jb.load("users\\{}\\models\\lgbm.pkl.z".format(user))

    if Xlgbm is None or Xrf is None:
        return 0


    p_rf = mdl_rf.predict_proba(Xrf)[0][1]
    p_lgbm = mdl_lgbm.predict_proba(Xlgbm)[0][1]

    p = 0.7*p_rf + 0.3*p_lgbm

    return p

def train_models(data, user):
    title_vec_lgbm = TfidfVectorizer(min_df=2, ngram_range=(1,4))
    title_vec_rf = TfidfVectorizer(min_df=2, ngram_range=(1,1))

    title_vec = [title_vec_lgbm, title_vec_rf]

    df = pd.DataFrame([data.values()], columns=data.keys())
    train, val = train_test_split(df, test_size=0.33, random_state=42)
    Xlgbm, Xrf = compute_features(train, title_vec, val, is_train=True)
    


def log_data(data, feature_array, p):

    video_id = data['webpage_url']
    data['prediction'] = p
    data['feature_array'] = feature_array.todense().tolist()
    print(video_id, json.dumps(data))







