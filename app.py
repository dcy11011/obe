from crypt import methods
import json
from logging import makeLogRecord
from flask import Flask, request, make_response, send_file
import config
from exts import db, mail
from model import *
from methods import *
from flask_httpauth import HTTPTokenAuth
from tokens import *

app = Flask(__name__)
app.config.from_object('config')
app.app_context().push()
mail.init_app(app)
db.init_app(app)
db.create_all()
auth = HTTPTokenAuth(scheme='JWT')

@auth.verify_token
def verify_token(token):
    return valid_token(token)

@auth.error_handler
def auth_error_handler():
    return make_response(id_msg(-1, "client authorization failed"), 401)

def missing_element():
    return make_response(id_msg(-1, "Missing form element."), 400)

@app.route("/hello")
def hello_world():
    return "<p>Hello! This is a flask test text.</p>"

@app.route("/api/valid", methods=['GET'])
def ValidMail():
    mail = request.args.get('mail')
    tel = request.args.get('tel')
    code, data = request_valid_code(mail)
    return make_response(data, code)

@app.route("/api/register", methods=['POST'])
def Register():
    username = request.form.get('username')
    passwd = request.form.get('passwd')
    valid_type = request.form.get('valid_type')
    valid_content = request.form.get('valid_content')
    valid_code = request.form.get('code')
    
    if None in [username, passwd, valid_type, valid_content, valid_code]:
        return missing_element()
    
    try:
        valid_code = int(valid_code)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)

    code, data = user_register(username, passwd, valid_type, valid_content, valid_code)
    return make_response(data, code)


@app.route("/api/login", methods=['POST'])
def Login():
    username = request.form.get('username')
    passwd = request.form.get('passwd')
    
    if None in [username, passwd]:
        return missing_element()

    code, data = user_login(username, passwd)
    return make_response(data, code)


@app.route("/api/userinfo", methods=['GET'])
@auth.login_required
def UserInfo():
    uid = g.uid
    code, data = user_getinfo(uid)
    return make_response(data, code)


@app.route("/api/setprofile", methods = ['GET'])
@auth.login_required
def SetProfile():
    uid = g.uid
    res_id = request.args.get('resid')
    try:
        res_id = int(res_id)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = user_set_profile(uid, res_id)
    return make_response(data, code)


@app.route("/api/getpost", methods=['GET'])
@auth.login_required
def GetNPost():
    n = request.args.get('n', default=20)
    start = request.args.get('start')
    uid = g.uid
    type = request.args.get('order', default='new')
    invert_dict = {
        'new':POST_QUERY_NEW,
        'hot':POST_QUERY_HOT,
        'followednew':POST_QUERY_FOLLOW,
    }
    try:
        n = int(n)
        type = invert_dict[type]
        if start is not None:
            start = int(start)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = post_get_n(uid, n, start, type)
    if(n > config.MAX_POST_REQUEST):
        data['message'] = f"max request posts limited to {config.MAX_POST_REQUEST}"
    return make_response(data,code)


@app.route("/api/getuserpost", methods = ['GET'])
@auth.login_required
def GetUserPost():
    request_uid = request.args.get('uid')
    n = request.args.get('n',default=20)
    start = request.args.get('start', default=0)
    
    try:
        n = int(n)
        start = int(start)
        request_uid  = int(request_uid)
        
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = post_get_users(request_uid, n, start)
    if(n > config.MAX_POST_REQUEST):
        data['message'] = f"max request posts limited to {config.MAX_POST_REQUEST}"
    return make_response(data,code)    


@app.route("/api/post", methods=['POST'])
@auth.login_required
def NewPost():
    uid = g.uid
    title = request.form.get('title')
    content = request.form.get('content')
    res_type = request.form.get('res_type')
    res_content = request.form.get('res_content')
    pos = request.form.get('pos')
    if None in [title, content]:
        return missing_element()
    code, data = post_add(uid, title, content, res_type, res_content, pos)
    return make_response(data, code)


@app.route("/api/dianzanpost", methods=['GET'])
@auth.login_required
def DianzanPost():
    uid = g.uid
    pid = request.args.get('pid')
    try:
        pid = int(pid)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = post_dianzan(uid, pid)
    return make_response(data, code)


@app.route("/api/postdetail", methods=['GET'])
@auth.login_required
def GetPostDetail():
    pid = request.args.get('pid')
    uid = g.uid
    try:
        pid = int(pid)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = post_get_detail(uid, pid)
    return make_response(data,code)


@app.route("/api/removepost", methods=["GET"])
@auth.login_required
def RemovePost():
    uid = g.uid
    pid = request.args.get('pid')
    try:
        pid = int(pid)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = post_remove(uid, pid)
    return make_response(data, code)    


@app.route("/api/reply", methods=["POST"])
@auth.login_required
def NewReply():
    uid = g.uid
    pid = request.form.get('pid')
    content = request.form.get('content')
    res_type = request.form.get('res_type')
    res_content = request.form.get('res_content')
    pos = request.form.get('pos')
    if None in [pid, content]:
        return missing_element()
    code, data = reply_add(uid, pid, content, res_type, res_content, pos)
    return make_response(data, code)


@app.route("/api/getreply", methods=["GET"])
@auth.login_required
def GetNReply():
    uid = g.uid
    n = request.args.get('n',default=20)
    pid = request.args.get('pid')
    start = request.args.get('start', default=0)
    try:
        n = int(n)
        start = int(start)
        pid = int(pid)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = reply_get_n(pid, n,start)
    return make_response(data, code)


@app.route("/api/removereply", methods=["GET"])
@auth.login_required
def RemoveReply():
    uid = g.uid
    rid = request.args.get('rid')
    try:
        rid = int(rid)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = reply_remove(uid, rid)
    return make_response(data, code)


@app.route("/api/addfollow", methods=["GET"])
@auth.login_required
def AddFollow():
    uid = g.uid
    target = request.args.get('uid')
    try:
        target = int(target)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = follow_add(uid, target)
    return make_response(data, code)


@app.route("/api/removefollow", methods=["GET"])
@auth.login_required
def RemoveFollow():
    uid = g.uid
    target = request.args.get('uid')
    try:
        target = int(target)
    except:
        return make_response(jsonify({"message":"wrong parameter"}), 400)
    code, data = follow_remove(uid, target)
    return make_response(data, code)


@app.route("/api/followlist", methods=["GET"])
@auth.login_required
def FollowList():
    uid = g.uid
    code, data = follow_get_list(uid)
    return make_response(data, code)


@app.route("/api/upload", methods=['POST'])
@auth.login_required
def Upload():
    try:
        file = request.files['file']
    except Exception as e:
        logDE(e)
        return make_response(jsonify({"message":"ill data"}), 400)
    code, data = file_upload(file)
    return make_response(data, code)


@app.route("/api/download", methods=['GET'])
@auth.login_required
def Download():
    res_id = request.args.get('resid')
    file_path = file_get_path(res_id)
    if file_path is None:
        make_response(id_msg(-1, "File not exists"), 404)
    return send_file(file_path, as_attachment=True, max_age = 691200)
