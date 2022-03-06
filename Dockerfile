FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        build-essential \
        gcc \
        g++
RUN pip install -r requirements.txt
RUN python db_starter.py
#CMD python ./app.py

CMD gunicorn --bind 0.0.0.0:$PORT wsgi
# CMD gunicorn --bind 0.0.0.0:80 wsgi

# Creating app... done, ⬢ afternoon-coast-45979
# https://afternoon-coast-45979.herokuapp.com/ | https://git.heroku.com/afternoon-coast-45979.git