from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World/n'

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host='159.89.132.69', port='54321')
