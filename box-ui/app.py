from flask import Flask, render_template, request, redirect, session
import requests

import cv2
import numpy as np
import os

import pymysql.cursors

app = Flask(__name__)
app.secret_key = 'notyourbussiness'

connection = pymysql.connect(host='43.228.85.107',
                             user='root',
                             password='kbu123',
                             database='ict_awrad',
                             cursorclass=pymysql.cursors.DictCursor,
                             connect_timeout=100)


def load_model(model):
    # clear model inside directory first
    directory = './facemodel'
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    download_url = 'http://127.0.0.1:5000/api/download'
    fileType = ['.yml', '.txt']
    for i_ in fileType:
        data = {'filename': f"{model}{i_}"}
        response = requests.post(download_url, json=data)

        if response.status_code == 200:
            with open(f"./facemodel/{data['filename']}", 'wb') as file:
                file.write(response.content)
        else:
            print(response.json())


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event')
def event():

    with connection.cursor() as cursor:
        department = '''
            select value_code
            from department
        '''
        cursor.execute(department)
        departments = cursor.fetchall()
        print(departments)

        event = '''
            select id, title, adress
            from events_host
            where del_flg = 0
        '''
        cursor.execute(event)
        events = cursor.fetchall()
        print(events)
    
    return render_template('event.html', model_=departments, event_=events)

@app.route('/progress', methods=['POST'])
def progress():
    if not request.method == 'POST':
        return redirect('/event')
    
    data = request.form
    session['event'] = data['event']
    session['model'] = data['model']

    return redirect('/camera')

@app.route('/camera')
def camera():

    if 'event' not in session and 'model' not in session:
        return redirect('/event')
    
    load_model(session['model'])

    return render_template('camera.html')
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)