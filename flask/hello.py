from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

# parameter and template
@app.route('/hello/<username>')
def hello_user(username=None):
    return render_template('hello.html', name=username)
