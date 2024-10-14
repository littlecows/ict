from flask import Flask, render_template, request, redirect, session, flash, jsonify
import requests
import cv2
import numpy as np
import os
import threading
import pymysql.cursors
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)
app.secret_key = 'n0ty0urbuss1ness'

# MQTT configuration
# broker = '141.98.17.127'
# port = 28813
# topic = 'ictkbu'
# usernameMQ = 'techlabs'  # เปลี่ยนเป็นชื่อผู้ใช้ของคุณ
# passwordMQ = 'ASDzxc!@#QwE123'  # เปลี่ยนเป็นรหัสผ่านของคุณ

# client = mqtt.Client()
# client.username_pw_set(usernameMQ, passwordMQ)
# client.connect(broker, port, 60)

    
def db_connect():
    connection = pymysql.connect(host='141.98.17.127',
                                port=33309,
                                user='root',
                                password='ZXCasdQWE$%^123',
                                database='Ict_award',
                                cursorclass=pymysql.cursors.DictCursor,
                                connect_timeout=100)
    return connection

# def call_mqtt():
#     client.publish(topic, "restart")

def load_model(model):
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

global faceDetect, grayFrame
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

def contact_db(id_, event_id):
    connect = db_connect()
    connect.commit()
    with connect.cursor() as cursor:
        sql = f'''
        select event_id, personnel_id
        from list_in_events 
        where event_id = {event_id} and personnel_id = {id_[-1]}
        limit 1
        '''

        cursor.execute(sql)
        result = cursor.fetchone()
        if bool(result):
            pass
        else:
            sql = f'''
                select id
                from personnel
                where code_per = {id_[-1]}
            '''
            cursor.execute(sql)
            personnel_id = cursor.fetchall()

            sql = f'''
                insert into list_in_events(event_id, personnel_id)
                values({event_id}, {personnel_id[0]["id"]})
            '''
            cursor.execute(sql)
            connect.commit()
            
    connect.close()

def detectProcess():
    global faceDetect, grayFrame, running, faceCascade
    running = True

    while running:
        if len(grayFrame) > 0:
            faceDetect = faceCascade.detectMultiScale(grayFrame, 1.2, 6, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

def cameraCapture():
    global faceDetect, grayFrame

    camera = cv2.VideoCapture(0)
    event_id = session.get('event') 
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
                except Exception as e:
                    print(f"Error in face recognition: {e}")
                    continue
                
                try:
                    name = label_map[label]
                    if int(conf) > 23 and int(conf) < 36:
                        id_ = str(name).split('_')
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
                        cv2.putText(frame, f"{name}", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        draw_checkmark(frame, (x + 125, y-15), color=(0, 255, 0), thickness=6, length=15)
                        threading.Thread(target=contact_db, args=(id_, event_id)).start()
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "Who", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                except Exception as e:
                    print(f"Error in processing detection: {e}")
        
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
    global id_
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
            # call_mqtt()
            return redirect('/event')

    return render_template('camera.html')

# done progress
@app.route('/event_done', methods=['POST'])
def event_done():
    if not request.method == 'POST':
        return redirect("/event")
    
    msg = {'status':None}
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        data = request.json
        
        try:
            connect = db_connect()
            with connect.cursor() as cursor:
                sql = 'UPDATE events_host SET del_flg = 1 WHERE id = %s'
                cursor.execute(sql, (data['event']))
                connect.commit()
            connect.close()
            msg['status'] = 'ok'
        except Exception as Error:
            print('Error subject:', Error)
            msg['status'] = 'failed'
            return jsonify(msg)
    
    return jsonify(msg)
    
    
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
