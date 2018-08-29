#coding:utf-8
from flask import Flask
from flask import request
import requests
from WXBizDataCrypt import WXBizDataCrypt

import lib.mysql_connector

app = Flask(__name__)
g_db = None

# personal account: shuai.ma@philips.com
appId = 'your appid' 
secret = 'your secret'


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
    print result
    global sessionKey
    sessionKey = r.json()['session_key']
    openId = r.json()['openid']
    print sessionKey
    return openId

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

@app.route('/privacy', methods=['GET', 'POST'])
def privacy():
    if not request.json or not 'agreed' in request.json:
        abort(400)

    agreed  = request.json['agreed']
    openid = request.json['openid']

    #TODO: store agree status and user openid into DB
    print openid, int(agreed)
    sql_cmd = 'INSERT INTO shuai_test.miniapp_test (wechat_openid, privacy_agreed) values (%s, %d)' % (openid, int(agreed))
    print sql_cmd
    lib.mysql_connector.insertdb(g_db, sql_cmd)   

    return str(agreed)

@app.route('/user_reg_info', methods=['GET', 'POST'])
def user_reg_info():
    if not request.json or not 'mrn' in request.json or not 'full_name' in request.json:
        abort(400)
    print request.json

    mrn  = request.json['mrn']
    full_name = request.json['full_name']
    print mrn.encode('utf-8'), full_name.encode('utf-8')
    return mrn+' '+full_name

if __name__ == "__main__":
    print 'connecting db ...'
    g_db = lib.mysql_connector.connectdb()    # 连接MySQL数据库
    print 'starting web service ...'
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0')


