from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/personal')
def personal():
    return render_template("personal.html")

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)