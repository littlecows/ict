from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify, flash
from flask_session import Session
from werkzeug.utils import secure_filename
import cv2
import numpy as np


import pymysql.cursors

import os

app = Flask(__name__)
app.secret_key = 'notyourbussiness'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

def db_connect():
    connection = pymysql.connect(host='141.98.17.127',
                                port=33309,
                                user='root',
                                password='ZXCasdQWE$%^123',
                                database='Ict_award',
                                cursorclass=pymysql.cursors.DictCursor,
                                connect_timeout=100)
    return connection


haarFile = './hrs/haarcascade_frontalface_default.xml'
cascade = cv2.CascadeClassifier(haarFile)

def remove_existing_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

eyeFile = './hrs/haarcascade_eye.xml'
eye_cascade = cv2.CascadeClassifier(eyeFile)


def is_valid_face(face_region, gray_frame):
    x, y, w, h = face_region

    # Size filtering (adjust thresholds as needed)
    if w < 50 or h < 50:
        return False

    # Aspect ratio filtering
    aspect_ratio = w / float(h)
    if aspect_ratio < 0.75 or aspect_ratio > 1.5:
        return False

    # Additional feature check (eyes detection)
    face_roi = gray_frame[y:y+h, x:x+w]
    eyes = eye_cascade.detectMultiScale(face_roi)
    if len(eyes) < 2:  # Usually, a valid face should have at least two eyes detected
        return False

    return True
    

def trainModel(base_path, paths, id_, department):
    count = 0
    for imageName in os.listdir(paths):
        imagePath = os.path.join(paths, imageName)

        image = cv2.imread(imagePath)
        resize = cv2.resize(image, (480, 640))
        image_np = np.array(resize)
        grayImage = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        face = cascade.detectMultiScale(grayImage, 1.2, 6, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

        for (x, y, w, h) in face:
            if is_valid_face((x, y, w, h), grayImage):
                newFace = resize[y:y+h, x:x+w]
                face = cv2.resize(newFace, (196, 196))
                while count < 15:
                    cv2.imwrite(f"{paths}/{id_}_{count}.jpg", face)
                    count += 1
        
        os.unlink(imagePath)
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces = []
    labels = []
    label_map = {}

    for idx, personName in enumerate(os.listdir(base_path)):
        label_map[idx] = personName
        person_dir = os.path.join(base_path, personName)

        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            faces.append(image)
            labels.append(idx)
    recognizer.train(faces, np.array(labels))
    recognizer.save(f"./uploads/facemodel/{department}.yml")

    with open(f"./uploads/facemodel/{department}.txt", 'w') as f:
        for idx, name in label_map.items():
            f.write(f"{idx},{name}\n")

# =====================
# ui code
# =====================
        
@app.route('/')
def index():
    if session.get('pid'):
        return redirect('/personal')
    else:
        return render_template("login.html")
    
    
# =====================
# login code
# =====================
@app.route('/login', methods=['POST'])
def login():
    if not request.method == 'POST':
        return redirect('/')
    
    datas = request.form

    connect = db_connect()

    with connect.cursor() as cursor:
        sql = f'''
            select id 
            from personnel 
            where frist_name = '{datas['username']}' and last_name = '{datas['password']}'
        '''
        cursor.execute(sql)
        result = cursor.fetchall()
        try:
            session['pid'] = result[0]['id']
        except:
            flash("ไม่พบชื่อผู้ใช้หรือรหัสผ่านผิด", "warning")
            return redirect('/')

    connect.close()
    return redirect('/personal')
# =====================
# end login code
# =====================

@app.route('/personal')
def personal():
    
    if not session.get('pid'):
        return redirect('/')
    
    connect = db_connect()
    connect.commit()
    with connect.cursor() as cursor:
        sql = f'''
            select personnel.frist_name, personnel.last_name, personnel.code_per,
            department.value_name, department.value_code
            from personnel
            join department on personnel.department_id = department.id
            where personnel.id = {session['pid']} 
        '''
        cursor.execute(sql)
        result = cursor.fetchall()
        # print(result)
    connect.close()

    base_ = {
        'firstname': result[0]['frist_name'],
        'lastname': result[0]['last_name'],
        'code': result[0]['code_per'],
        'department': result[0]['value_name'],
        'valcode': result[0]['value_code']
    }

    return render_template("personal.html", base_=base_)

@app.route('/progress', methods=['POST'])
def personal_progress():

    if not request.method == 'POST':
        return redirect('/')

    datas = request.form
    file = request.files['picture']

    # print(datas, file)
    connect = db_connect()
    with connect.cursor() as cur:
        sql = """
            UPDATE personnel
            SET frist_name = %s, last_name = %s
            WHERE code_per = %s
        """
        cur.execute(sql, (datas["firstname"], datas["lastname"], datas["code"]))
        connect.commit()
    connect.close()
    
    if file:
        filename = secure_filename(file.filename)
        base_path = os.path.join(app.config['UPLOAD_FOLDER'], datas['valcode'])
        person_dir = f"{datas['firstname']}_{datas['code']}"
        save_dir = os.path.join(base_path, person_dir)
        os.makedirs(save_dir, exist_ok=True)

        remove_existing_files(save_dir)

        file.save(os.path.join(save_dir, filename))

        trainModel(base_path, save_dir, datas['code'], datas['valcode'])

    flash("ดำเนินการเสร็จสิ้น", "success")
    return redirect('/personal')

@app.route('/api/download', methods=['POST'])
def download_file_api():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'message': 'No filename provided'}), 400
    
    filename = data['filename']
    path_ = f"facemodel/{filename}"

    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], path_)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], path_, as_attachment=True)
    else:
        return jsonify({'message': 'File not found'}), 404
    
@app.route('/logout')
def logout():
    session["pid"] = None
    return redirect('/')
# =====================
# end ui code
# =====================

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)