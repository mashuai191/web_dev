#coding:utf-8
from flask import Flask, abort, request, json, jsonify, g
import os
import requests
import logging
from WXBizDataCrypt import WXBizDataCrypt
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

import lib.mysql_connector
import decimal

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# override the default json encoder

class MyJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return str(obj)
        return super(MyJSONEncoder, self).default(obj)

app = Flask(__name__)
g_db = None
app.json_encoder = MyJSONEncoder

app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
#dev env
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://shuai_test:P@ssw0rd1234@159.89.132.69:3306/shuai_test?charset=utf8'
#production env
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Philips@123@rm-uf6s5852kgoy3842v.mysql.rds.aliyuncs.com:3306/shuai_test?charset=utf8'
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()




class MiniappUserProfile(db.Model):
    """
    eg. fields: id, title
    """
    __tablename__ = 'miniapp_user_profile'
    #__table_args__ = {'autoload': True, 'schema': 'data', 'autoload_with': db.engine}
    __table_args__ = {'autoload': True, 'autoload_with': db.engine}

    def verify_password(self, password):
        #return pwd_context.verify(password, self.password_hash)
        return "not used password yet"

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'openid': self.wechat_openid})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = MiniappUserProfile.query.filter_by(wechat_openid=data['openid']).first()

        return user

# personal account: shuai.ma@philips.com
#appId = 'wx7bc211dcd940abde' 
#secret = 'a5f829109f0cf966c084e2e255304015'

# company account: simon
appId = 'wx5cb39f555c7238cf'
secret = 'ecec76ba7091fe78cdc95f098a80dc56'

#secret = '96fa56effc51f901aa10c2da5cca4421'

# check if input activation code is in code pool
def getActivationCodeInCodePool(activation_code):
    # 
    ret = -1
    #print activation_code, type(activation_code)
    sql_cmd = '''SELECT id_user_base FROM shuai_test.miniapp_user_base where activation_code='%s' ''' % (str(activation_code))
    result = lib.mysql_connector.querydb(g_db, sql_cmd)
    logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
    if result and result[0][0]:
        ret = result[0][0]

    return ret


@app.route('/')
def hello():
    return 'Hello, World'

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    #print request.headers
    #print 'username:', auth.username()
    #print 'data received :', username_or_token, password 
    user = MiniappUserProfile.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = MiniappUserProfile.query.filter_by(wechat_openid=username_or_token).first()
        #if not user or not user.verify_password(password):
        if not user:
            return False
    g.user = user
    return True

@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@app.route('/onlogin', methods=['GET', 'POST'])
def on_login():
    if request.method == 'POST':
        ret = ''
        if not request.json or not 'code' in request.json:
            abort(400)

        code = request.json['code']
    
        # call WeChat API with code to get session_key and openid 
        payload = {'appid': appId, 'secret': secret, 'js_code': code, 'grant_type': 'authorization_code'}
        url = 'https://api.weixin.qq.com/sns/jscode2session'
    
        r = requests.get(url=url, params=payload)

        if (u'errcode' in r.json().keys()):
            logger.error('%s', r.text)
            ret = r.json()['errmsg']
        else:
            logger.info('code:%s, result:%s, status_code:%d', code, r.text, r.status_code)
            sessionKey = r.json()['session_key']
            openid = r.json()['openid']
        
            sql_cmd = '''SELECT id_session_key, wechat_session_key FROM shuai_test.miniapp_session_key where wechat_openid='%s' ''' % (str(openid))  
            result = lib.mysql_connector.querydb(g_db, sql_cmd)
            logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
            if result:
    	        sql_cmd = '''UPDATE shuai_test.miniapp_session_key SET wechat_session_key = '%s' WHERE id_session_key ='%d' ''' % (str(sessionKey), int(result[0][0]))
                result = lib.mysql_connector.updatedb(g_db, sql_cmd)
                logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
                if result: ret = 'true'
            else:
                sql_cmd = '''INSERT INTO shuai_test.miniapp_session_key (wechat_openid, wechat_session_key) VALUES ('%s', '%s')''' % (str(openid), str(sessionKey))
                result = lib.mysql_connector.insertdb(g_db, sql_cmd)
                logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
                if result:
                    logger.info("user login successful!")
                else:
                    logger.error("user login failed!")
                    return 'false'
            ret = openid
        return ret
    elif request.method == 'GET':
        return 'Why GET request'

@app.route('/decryption', methods=['GET', 'POST'])
def decryption():
    if not request.json or not 'encryptedData' in request.json or not 'iv' in request.json or not 'openid' in request.json:
        abort(400)

    encryptedData = request.json['encryptedData']
    iv = request.json['iv']
    openid = request.json['openid']

    sql_cmd = '''SELECT id_session_key FROM shuai_test.miniapp_session_key where wechat_openid='%s' ''' % (str(openid))  
    result = lib.mysql_connector.querydb(g_db, sql_cmd)
    logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
    if result:
        id_session_key = result[0][0]

        sql_cmd = '''SELECT wechat_session_key FROM shuai_test.miniapp_session_key where id_session_key='%s' ''' % (str(id_session_key))  
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
        if result:
            sessionKey = str(result[0][0])
            pc = WXBizDataCrypt(appId, sessionKey)
            ret = pc.decrypt(encryptedData, iv)
            return jsonify({"result":ret['stepInfoList']})
    return 'false'

@app.route('/privacy', methods=['GET', 'POST'])
def privacy():
    if request.method == 'POST':
        ret = 'false'
        if not request.json or not 'openid' in request.json:
            abort(400)
        #TODO: store agree status and user openid into DB
        openid = request.json['openid']
        agreed  = request.json['agreed']
        sql_cmd = '''SELECT 1 FROM shuai_test.miniapp_user_profile where wechat_openid='%s' limit 1''' % (str(openid))  
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
        if result and result[0][0] == 1:
    	    sql_cmd = '''UPDATE shuai_test.miniapp_user_profile SET privacy_agreed = '%s' WHERE wechat_openid='%s' ''' % (1, str(openid))
            result = lib.mysql_connector.updatedb(g_db, sql_cmd)
            logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
            if result: ret = 'true'
        else:
            sql_cmd = '''INSERT INTO shuai_test.miniapp_user_profile (wechat_openid, privacy_agreed) VALUES ('%s', %d)''' % (str(openid), int(agreed))
            result = lib.mysql_connector.insertdb(g_db, sql_cmd)
            logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
            if result:
                ret = 'true'
        return ret
    elif request.method == 'GET':
        ret = 'false'
        openid=request.args.get('openid')
        sql_cmd = '''SELECT privacy_agreed FROM shuai_test.miniapp_user_profile where wechat_openid='%s' ''' % (str(openid))  
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
        if result and result[0][0] == 1:
            ret = 'true'
        return ret


@app.route('/activation', methods=['GET', 'POST'])
def activation():
    ret = 'false'
    if request.method == 'POST':
    	if not request.json or not 'activation_code' in request.json or not 'LMP' or not 'openid' in request.json:
            abort(400)

    	openid = request.json['openid']
        activation_code  = request.json['activation_code']
    	LMP = request.json['LMP']
    	sql_cmd = '''SELECT id FROM shuai_test.miniapp_user_profile WHERE wechat_openid='%s' ''' % (str(openid))
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        id = result[0][0] if result else None
        if id:
            #check if the actiavation code is in pre-defined code pool
            id_user_base = getActivationCodeInCodePool(activation_code.encode('utf-8'))
            if id_user_base != -1:
                sql_cmd = '''UPDATE shuai_test.miniapp_user_profile SET activation_code = '%s', activation_code_id = '%d',  LMP = '%s', activated = '%d' WHERE id='%d' ''' % (activation_code.encode('utf-8'), int(id_user_base), LMP.encode('utf-8'), 1, id)
                result = lib.mysql_connector.updatedb(g_db, sql_cmd)
                logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
                if result: ret = 'true'

    elif request.method == 'GET':
        openid=request.args.get('openid')
        sql_cmd = '''SELECT activated FROM shuai_test.miniapp_user_profile where wechat_openid='%s' ''' % (str(openid))  
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
        if result and result[0][0] == 1:
            ret = 'true'

    return ret
        
@app.route('/weight', methods=['GET', 'POST'])
@auth.login_required
def weight():
    ret = 'false'
    if request.method == 'POST':
    	if not request.json or not 'weight'in request.json or not 'openid' in request.json:
            abort(400)
    	openid = request.json['openid']
        weight  = request.json['weight']
        for_date  = request.json['for_date']
        week_num = request.json['weekNum']
        # check if there is existing info for specific date
    	sql_cmd = '''SELECT id FROM shuai_test.miniapp_user_profile WHERE wechat_openid='%s' ''' % (str(openid))
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
    	if result:
            id = result[0][0]
            sql_cmd = '''SELECT id_weight FROM shuai_test.miniapp_weight_log WHERE user_profile_id='%s' AND for_date='%s'  ''' % (id, str(for_date))
            result_2 = lib.mysql_connector.querydb(g_db, sql_cmd)
            logger.info("sql_cmd=%s, result:%s", sql_cmd, result_2)
            id_weight = result_2[0][0] if result_2 else None
            if id_weight: 
            # if there is existing info, update weight
            #TODO: update weight for specific date
    	        sql_cmd = '''UPDATE shuai_test.miniapp_weight_log SET weight = '%.1f', for_date = '%s', week_num = '%d' WHERE id_weight=%d ''' % (float(weight), str(for_date), int(week_num), int(id_weight))
                result = lib.mysql_connector.updatedb(g_db, sql_cmd)
                logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
                ret = 'true'
            # if there is no existing info, add weight
            else:
                sql_cmd = '''INSERT INTO shuai_test.miniapp_weight_log (user_profile_id, weight, for_date, week_num) VALUES (%d,  %.1f, '%s', %d)''' % (int(id), float(weight), str(for_date), int(week_num))
                ret = lib.mysql_connector.insertdb(g_db, sql_cmd)
                logger.info("sql_cmd=%s", sql_cmd)
                if ret:
                    logger.info("insert succeed")
                    ret = 'true'
                else:
                    logger.error("insert failed")
        else:
            logger.error("user not existing!")

    elif request.method == 'GET':
        openid=request.args.get('openid')
        sql_cmd = '''SELECT id FROM shuai_test.miniapp_user_profile where wechat_openid='%s' ''' % (str(openid))  
        result = lib.mysql_connector.querydb(g_db, sql_cmd)
        # get the weekday list with long date format
        if result and result[0]:
            sql_cmd = '''SELECT for_date, weight FROM shuai_test.miniapp_weight_log where user_profile_id='%d' ''' % (int(result[0][0]))  
            result = lib.mysql_connector.querydb(g_db, sql_cmd)
            logger.info("sql_cmd=%s, result:%s", sql_cmd, result)
            return jsonify({"result":result})

    return ret


if __name__ == "__main__":

    # set the log path
    logger = logging.getLogger()
    #log_path = '/var/log/'+ appId + '/'
    log_path = '/var/log/'
    log_file = 'app.log' 
    if not os.path.exists(log_path):
        os.system(r"mkdir -p %s" % log_path)
    os.system(r"touch %s" % log_path + log_file)
    file_handler = logging.FileHandler(log_path + log_file)

    #file_handler = logging.FileHandler('./test.log')
    #logging_format = logging.Formatter('%(asctime)s - %(name)s - %(thread)d - %(levelname)s - %(message)s')
    logging_format = logging.Formatter('%(asctime)s %(levelname)s %(name)s Line:%(lineno)d - %(message)s')
    file_handler.setFormatter(logging_format)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    print "query existing tables", MiniappUserProfile.query.all()
    g_db = lib.mysql_connector.connectdb()    # 连接MySQL数据库

    logger.info("Starting web service ...")
    #app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0')
    app.run(host='0.0.0.0')





