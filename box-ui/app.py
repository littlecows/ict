from flask import Flask, render_template, request, redirect, session
import requests

import cv2
import numpy as np

import pymysql.cursors

app = Flask(__name__)
app.secret_key = 'notyourbussiness'

connection = pymysql.connect(host='43.228.85.107',
                             user='root',
                             password='kbu123',
                             database='ict_awrad',
                             cursorclass=pymysql.cursors.DictCursor,
                             connect_timeout=100)

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
    print(data)

    return redirect('/event')

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)