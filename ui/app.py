from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/personal')
def personal():
    return render_template("personal.html")

@app.route('/progress', methods=['POST'])
def personal_progress():

    if not request.method == 'POST':
        return redirect('/')

    datas = request.form
    file = request.files['picture']

    if file:
        filename = secure_filename(file.filename)
        person_dir = f"{datas['firstname']}_{datas['lastname']}"
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], person_dir)
        os.makedirs(save_dir, exist_ok=True)
        file.save(os.path.join(save_dir, filename))

    return redirect('/personal')

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)