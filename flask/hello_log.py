from flask import Flask
import logging


app = Flask(__name__)

@app.route('/')
def hello():
    app.logger.info('this is a info msg')
    app.logger.warning('this is warning msg')
    return 'Hello, World/n'

if __name__ == "__main__":
    logger = logging.getLogger()
    file_handler = logging.FileHandler('./test.log')
    logging_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(logging_format)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    app.run(ssl_context='adhoc', host='159.89.132.69', port='54321')
