from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename

import pymysql.cursors

import os

app = Flask(__name__)
app.secret_key = 'notyourbussiness'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

connection = pymysql.connect(host='43.228.85.107',
                             user='root',
                             password='kbu123',
                             database='ict_awrad',
                             cursorclass=pymysql.cursors.DictCursor,
                             connect_timeout=100)

global test_person
test_person = ''
@app.route('/')
def index():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    global test_person
    if not request.method == 'POST':
        return redirect('/')
    
    datas = request.form

    sql = f'''
        select id 
        from personnel 
        where frist_name = '{datas['username']}' and last_name = '{datas['password']}'
    '''

    with connection.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result[0]['id'])
        test_person = result[0]['id']
    # connection.close()

    return redirect('/personal')

@app.route('/personal')
def personal():
    global test_person
    
    sql = f'''
        select personnel.frist_name, personnel.last_name, personnel.code_per,
        department.value_name
        from personnel
        join department on personnel.department_id = department.id
        where personnel.id = {test_person} 
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
        # print(result)
    # connection.close()

    base_ = {
        'firstname': result[0]['frist_name'],
        'lastname': result[0]['last_name'],
        'code': result[0]['code_per'],
        'department': result[0]['value_name']
    }

    return render_template("personal.html", base_=base_)

@app.route('/progress', methods=['POST'])
def personal_progress():

    if not request.method == 'POST':
        return redirect('/')

    datas = request.form
    file = request.files['picture']

    print(datas)

    if file:
        filename = secure_filename(file.filename)
        person_dir = f"{datas['firstname']}_{datas['lastname']}"
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], person_dir)
        os.makedirs(save_dir, exist_ok=True)
        file.save(os.path.join(save_dir, filename))

    return redirect('/personal')

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)