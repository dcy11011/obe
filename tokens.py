import imp
from operator import imod
from config import SECRET_KEY
from authlib.jose import jwt, JoseError
from flask import current_app, g
from log import *
from model import *

ERROR_TOKEN_VALIDATION = -1

def generate_token(uid):
    header = {'alg': 'HS256'}
    data = {'uid': uid}
    token = jwt.encode(header=header, payload=data, key=current_app.config['SECRET_KEY'])
    return str(token, 'utf-8')

def valid_token(token):
    key = current_app.config['SECRET_KEY']
    uid = 0
    logD(len(token))
    try:
        data = jwt.decode(token, key)
        uid = data['uid']
        logD(uid)
        if type(Users.get_by_id(uid)) == TYPE_ERROR_QUERY:
            return False
    except:
        return False
    g.uid = uid
    return True