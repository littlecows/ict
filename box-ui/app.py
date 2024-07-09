from flask import Flask, render_template, request, redirect, session
import requests

import cv2
import numpy as np
import os
import threading

import pymysql.cursors


app = Flask(__name__)
app.secret_key = 'n0ty0urbuss1ness'

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

global faceDetect, grayFrame, frame
faceDetect = []
grayFrame = []

haarFile = './hrs/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(haarFile)

def start():
    global t

    t = threading.Thread(target=detectProcess)
    t.start()

def stop():
    global running
    global t

    running = False

    t.join()

def detectProcess():
    global faceDetect, grayFrame, running, faceCascade
    running = True

    while running:
        if len(grayFrame) > 0:
            faceDetect = faceCascade.detectMultiScale(grayFrame, 1.1, 6, minSize=(30, 30))

def cameraCapture():
    global faceDetect, grayFrame

    camera = cv2.VideoCapture(0)

    while True:
        _, frame = camera.read()
        
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if len(faceDetect) > 0:
            for (x, y, w, h) in faceDetect:
                try:
                    faces = cv2.resize(grayFrame[y:y+h, x:x+w], (196, 196))
                    label, confidence = recognizer.predict(faces)
                    conf = "{0}".format(round(100-confidence))
                    print(conf)
                except:
                    print("Wait")
                
                try:
                    name = label_map[label]
                    if int(conf) > 50:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "Who", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                except:
                    print("Wait")
        
        cv2.imshow("MOCKING", frame)


        if cv2.waitKey(5) & 0xFF == 27:
            break

        if cv2.getWindowProperty("MOCKING", cv2.WND_PROP_VISIBLE) < 1:
            cv2.destroyAllWindows()
            break
    
    camera.release()
    cv2.destroyAllWindows()


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

@app.route('/camera', methods=['GET', 'POST'])
def camera():

    if 'event' not in session and 'model' not in session:
        return redirect('/event')
    
    load_model(session['model'])

    if request.method == 'POST':
        global result, label_map, recognizer

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(f"./facemodel/{session['model']}.yml")
        label_map = ''
        with open(f"./facemodel/{session['model']}.txt", 'r') as f:
            label_map = {int(line.split(',')[0]): line.split(',')[1].strip() for line in f.readlines()}
        
        start()
        try:
            result = cameraCapture()
        finally:
            stop()

    return render_template('camera.html')
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)