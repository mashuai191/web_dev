#coding:utf-8
from flask import Flask
from flask import request
import requests
from WXBizDataCrypt import WXBizDataCrypt

app = Flask(__name__)

appId = 'wx7bc211dcd940abde'
secret = 'a5f829109f0cf966c084e2e255304015'
sessionKey = ''

@app.route('/')
def hello():
    return 'Hello, World'

@app.route('/onlogin', methods=['GET', 'POST'])
def on_login():
    if not request.json or not 'code' in request.json:
        abort(400)

    code = request.json['code']
    
    # call WeChat API with code to get session_key and openid 
    payload = {'appid': appId, 'secret': secret, 'js_code': code, 'grant_type': 'authorization_code'}
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    
    r = requests.get(url=url, params=payload)
    result = r.text
    global sessionKey
    sessionKey = r.json()['session_key']
    print sessionKey
    return result

@app.route('/decryption', methods=['GET', 'POST'])
def decryption():
    if not request.json or not 'encryptedData' in request.json:
        abort(400)

    encryptedData = request.json['encryptedData']
    iv = request.json['iv']
    #print 'appId',appId
    #print 'sessionKey', sessionKey
    #print 'encryptedData', encryptedData
    #print 'iv', iv

    pc = WXBizDataCrypt(appId, sessionKey)
    print pc.decrypt(encryptedData, iv)

    return 'This is the decrypted data!'

if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0')
