from flask import Flask, render_template, request, redirect, session, flash
import requests

import cv2
import numpy as np
import os
import threading

import pymysql.cursors


app = Flask(__name__)
app.secret_key = 'n0ty0urbuss1ness'

def db_connect():
    connection = pymysql.connect(host='141.98.17.127',
                                port=33309,
                                user='root',
                                password='ZXCasdQWE$%^123',
                                database='Ict_award',
                                cursorclass=pymysql.cursors.DictCursor,
                                connect_timeout=100)
    return connection


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

    # download_url = 'http://43.228.85.107:8080/api/download'
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

def draw_checkmark(img, position, color=(0, 255, 0), thickness=2, length=20):
    x, y = position
    cv2.line(img, (x, y), (x + length, y + length), color, thickness)
    cv2.line(img, (x + length, y + length), (x + 2*length, y - length), color, thickness)

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
            faceDetect = faceCascade.detectMultiScale(grayFrame, 1.2, 6, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

def cameraCapture():
    global faceDetect, grayFrame

    camera = cv2.VideoCapture(0)
    status = ''
    checkmark_symbol = "\u2713"
    while True:
        _, frame = camera.read()
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if len(faceDetect) > 0:
            for (x, y, w, h) in faceDetect:
                try:
                    faces = cv2.resize(grayFrame[y:y+h, x:x+w], (196, 196))
                    label, confidence = recognizer.predict(faces)
                    conf = "{0}".format(round(100-confidence))
                    print(label, conf)
                except:
                    print("Wait")
                
                try:
                    name = label_map[label]
                    if int(conf) > 30:
                        id_ = str(name).split('_')
                        # connect = db_connect()
                        # with connect.cursor() as cursor:
                        #     connect.commit()
                        #     sql = f'''
                        #     select event_id, personnel_id
                        #     from list_in_events 
                        #     where event_id = {session["event"]} and personnel_id = {id_[-1]}
                        #     '''

                        #     cursor.execute(sql)
                        #     result = cursor.fetchall()
                            
                        #     if not result:
                        #         sql = f'''
                        #             select id
                        #             from personnel
                        #             where code_per = {id_[-1]}
                        #         '''
                        #         cursor.execute(sql)
                        #         personnel_id = cursor.fetchall()

                        #         sql = f'''
                        #             insert into list_in_events(event_id, personnel_id)
                        #             values({session["event"]}, {personnel_id[0]["id"]})
                        #         '''
                        #         cursor.execute(sql)
                        #         connect.commit()
                        #         status = 'signed'
                        #     else:
                        #         status = 'already signed'

                        # connect.close()
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
                        cv2.putText(frame, f"{name}", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        draw_checkmark(frame, (x + 125, y-15), color=(0, 255, 0), thickness=6, length=15)
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "Who", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                except:
                    a = None
        
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
    connect = db_connect()
    with connect.cursor() as cursor:
        connect.commit()
        department = '''
            select id, value_code
            from department
        '''
        cursor.execute(department)
        departments = cursor.fetchall()

        event = '''
            select events_host.id, events_host.title, events_host.adress, events_host.department_id,
            department.value_code
            from events_host
            join department on department.id = events_host.department_id
            where del_flg = 0
        '''
        cursor.execute(event)
        events = cursor.fetchall()
    connect.close()
    
    return render_template('event.html', model_=departments, event_=events)

@app.route('/newevent', methods=['POST'])
def newevent():

    if not request.method == 'POST':
        return redirect('/event')
    
    data = request.form
    department = str(data['model']).split('/')
    
    connect = db_connect()
    with connect.cursor() as cursor:
        sql = f'''
        INSERT INTO events_host (title, department_id)
        VALUES (%s, {department[1]})
        '''
        values = (data["newevent"])
        cursor.execute(sql, values)
        connect.commit()
    connect.close()

    return redirect('/event')

@app.route('/progress', methods=['POST'])
def progress():
    if not request.method == 'POST':
        return redirect('/event')
    
    data = request.form
    department = [data['depart_name'], data['depart_id']]

    session['event'] = data['event']
    session['model'] = department[0]
    session['department'] = department[1]

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
            flash("กำลังเตรียมความพร้อมระบบ โปรดรอ", "info")
            return redirect('/event')

    return render_template('camera.html')
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)