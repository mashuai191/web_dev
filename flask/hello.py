from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route('/')
def index():
    app.logger.info('A value for debugging')
    app.logger.warning('A warning occurred (%d apples)', 42)
    app.logger.error('An error occurred')
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

# parameter and template
@app.route('/hello/<username>')
def hello_user(username=None):
    return render_template('hello.html', name=username)


app.logger.info('this is info msg')
