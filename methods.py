from cmath import log
from crypt import methods
from os import stat
from random import randint
from socket import INADDR_MAX_LOCAL_GROUP
from unittest.util import _MAX_LENGTH
from flask import Flask, request, jsonify, g
from matplotlib.pyplot import vlines
from requests import Response
import config
from flask_mail import Mail, Message
from exts import mail
from model import *
from tokens import *


def id_msg(id, message = ""):
    return jsonify({"id":id, "message":message})


def wrap_post(post: Posts, uid = None) -> dict:
    userinfo = Users.get_by_id(post.uid)
    if type(userinfo) is not Users:
        userinfo = Users("已注销用户","","","")
    replycount = Replies.count_by_pid(post.pid)
    if(replycount < 0 ):
        return None
    ret_list = {
        "pid":post.pid,
        "title":post.title,
        "content":post.content,
        "uid":post.uid,
        "pos":post.pos,
        "nreply" : replycount,
        "dianzan":post.dianzan,
        "restype":post.res_type,
        "resid":post.res_id,
        "datetime":post.addtime,
        "username":userinfo.name,
        "userimgid" : userinfo.img_res_id,
    }
    if uid is not None:
        if_zan = Dianzans.get(uid, post.pid)
        ret_list['if_zan'] = if_zan
    return ret_list


def wrap_post_list(post_list:list, uid = None)->dict:
    if type(post_list) is TYPE_ERROR_QUERY:
        return None
    ret_list = []
    max_pid = -1
    min_pid = -1
    for post in post_list:
        post_dict = wrap_post(post, uid)
        if post_dict is None:
            return None
        ret_list.append(post_dict)
        max_pid = int(max(max_pid, post.pid))
        min_pid = int(post.pid if min_pid < 0 else min(min_pid, post.pid))
    return {
        "posts":ret_list, "count":len(ret_list),
        "min":min_pid, "max":max_pid,
    }


def wrap_dict(data:dict)->tuple:
    if data is None:
        return 500, id_msg(-1, "server internal error")
    data['message'] = 'success'
    return 200, jsonify(data)


def user_login(username:str, passwd:str):
    uid = Users.get_by_login(username, passwd)
    if uid < 0:
        return 400, id_msg(-1, "login failed")
    token  = generate_token(uid)
    return 200, jsonify({"token": f'JWT {token:s}', "message":"success"})


def request_valid_code(content:str):
    
    code = randint(100000, 999999)
    Valid.insert(content, code)
    msg = Message(f'【草莓波球论坛】新用户注册验证', sender = config.MAIL_USERNAME, recipients=[content,])
    msg.body = f"【草莓波球论坛】欢迎注册草莓波球论坛！您的验证码为{code}, 请在5分钟内完成注册。如非本人操作请忽略此邮件。"
    logD(f"[EMAIL] sending email{code}")
    mail.send(msg)
    return 200, id_msg(0, "success")


def user_register(username:str, passwd:str, valid_type:str, valid_content:str, valid_code:int):
    # IMPORTANT remove this code when release!!
    if valid_code != 884888 and Valid.get_code(valid_content) != valid_code:
        return 400, id_msg(11, "wrong validation code")
    if type(username)!=str or len(username) > MAXLEN_USERNAME:
        return 400, id_msg(10, f"username should be shorter than {MAXLEN_USERNAME}")
    ret = Users.insert(username, passwd, valid_type, valid_content)
    if ret < 0:
        if ret == ERROR_USERNAME:
            return 400, id_msg(2, "username already exist")
        if ret == ERROR_MAIL:
            return 400, id_msg(3, "mailbox already exist")
        if ret == ERROR_TEL:
            return 400, id_msg(4, "telephone already exist")
        return 500, ""
    return 200, jsonify({"uid":ret, "message":"success"})


def user_getinfo(uid:int):
    usr = Users.get_by_id(uid)
    if type(usr) is not Users:
        return 404, id_msg(-1, "user not found")
    user_info_dict = {
        'uid'       : usr.uid,
        'username'  : usr.name,
        'sig'       : usr.sig,
        'mail'      : usr.mail,
        'tel'       : usr.tel,
        'imgid'    : usr.img_res_id,
        'message'   : "success"
    }
    return 200, jsonify(user_info_dict)


def post_get_n(uid:int, n:int, start:int, type:int = POST_QUERY_NEW):
    logD(f'    ##### type={type}')
    post_list = Posts.get_n_newest(g.uid, n, start, type)
    post_list_dict = wrap_post_list(post_list, uid)
    return wrap_dict(post_list_dict)


def post_get_detail(uid:int, pid:int):
    post = Posts.get(pid)
    if type(post) is not Posts:
        return 400, id_msg(-1, f"request post not found")
    
    return wrap_dict(wrap_post(post, uid))
    

def post_get_users(uid, n, start):
    post_list = Posts.get_n_newest_filter_uid(uid, n, start)
    post_list_dict = wrap_post_list(post_list, uid)
    post_list_dict["uid"] = uid
    return wrap_dict(post_list_dict)



def post_add(uid, title, content, res_type, res_content, pos):
    if type(title) != str or len(title) > MAXLEN_TITLE or len(title) <=0:
        return 400, id_msg(2, f"request title format error(should be string shorter than {MAXLEN_TITLE})")
    if type(content) != str or len(content) > MAXLEN_CONTENT or len(content) <=0:
        return 400, id_msg(3, f"request content format error(should be string shorter than {MAXLEN_CONTENT})")
    if res_type not in RES_TYPE_LIST and res_type is not None:
        return 400, id_msg(4, f"request resource file type invalid")
    new_pid = Posts.insert(uid, title, content, res_type, res_content, pos) # FIX THIS WHEN ADDING RES TABLE
    if new_pid<0:
        return 500, id_msg(-1, "inserting failed")
    return 200, jsonify({"pid":new_pid, "message":"success"})
    

def post_dianzan(uid, pid):
    ret = Posts.zan(uid, pid)
    if type(ret) is TYPE_ERROR_QUERY:
        if ret == ERROR_NO_POST:
            return 404, id_msg(-1, "request post not found")
        return 500, id_msg(-1, "server internal error")
    return 200, jsonify({"ifzan":ret, "message":"success"})


def post_remove(uid, pid):
    status = Posts.remove_by_pid(uid, pid)
    if status == ERROR_UNAUTHORIZED:
        return 400, id_msg(2, "post not belong to request user")
    if status == ERROR_NOTEXIST:
        return 400, id_msg(3, "post not exist")
    if status < 0:
        return 400, id_msg(1, "fail")
    return 200, id_msg(0, "success")    


def reply_get_n(pid, n, start):
    reply_list = Replies.get_by_pid(pid,n,start)
    if type(reply_list) is TYPE_ERROR_QUERY:
        if reply_list == ERROR_NO_POST:
            return 404, id_msg(-1, "request post not found")
        return 500, id_msg(-1, "server internal error")
    ret_list = []
    max_rid = -1
    min_rid = -1
    for reply in reply_list:
        userinfo = Users.get_by_id(reply.uid)
        if type(userinfo) is not Users:
            userinfo = Users("未知发布者","","","")
        ret_list.append({
            "pid" : reply.pid,
            "rid" : reply.rid,
            "content" : reply.content,
            "restype" : reply.res_type,
            "resid" : reply.res_id,
            "username" : userinfo.name,
            "userimgid" : userinfo.img_res_id,
            "pos":reply.pos,
            "datetime":reply.addtime,
        })
        max_rid = max(max_rid, reply.rid)
        min_rid = reply.rid if min_rid < 0 else min(min_rid, reply.rid)
    return 200, jsonify({
        "reply":ret_list, "count":len(ret_list), "message":"success",
        "min":min_rid, "max":max_rid,
    })
    

def reply_add(uid, pid, content, res_type, res_content, pos):
    if type(content) != str or len(content) > MAXLEN_CONTENT or len(content) <=0:
        return 400, id_msg(3, f"request content format error(should be string shorter than {MAXLEN_CONTENT})")
    if res_type not in RES_TYPE_LIST and res_type is not None:
        return 400, id_msg(4, f"request resource file type invalid")
    if Posts.get(pid) is None:
        return 400, id_msg(5, f"request post not exist")
    new_rid = Replies.insert(uid, pid, content, res_type, res_content, pos) # FIX THIS WHEN ADDING RES TABLE
    if new_rid<0:
        if new_rid == ERROR_NO_POST:
            return 404, id_msg(-1, "request post not found")
        return 500, id_msg(-1, "inserting failed")
    return 200, jsonify({"rid":new_rid, "message":"success"})


def reply_remove(uid, rid):
    status = Replies.remove_by_rid(uid, rid)
    if status == ERROR_UNAUTHORIZED:
        return 400, id_msg(2, "reply not belong to request user")
    if status == ERROR_NOTEXIST:
        return 400, id_msg(3, "reply not exist")
    if status < 0:
        return 400, id_msg(1, "fail")
    return 200, id_msg(0, "success")


def follow_add(follower, follows):
    if None in [Users.get_by_id(follower), Users.get_by_id(follows)]:
        return 404, id_msg(-2, "One or more users not found")
    status = Follow.add(follower, follows)
    if not status:
        return 500, id_msg(-1, "server internal error")
    return 200, id_msg(0, "success")


def follow_remove(follower, follows):
    if None in [Users.get_by_id(follower), Users.get_by_id(follows)]:
        return 404, id_msg(-2, "One or more users not found")
    status = Follow.remove(follower, follows)
    if not status:
        return 500, id_msg(-1, "server internal error")
    return 200, id_msg(0, "success")


def follow_get_list(follower):
    if Users.get_by_id(follower) is None:
        return 404, id_msg(-2, "No such user")
    follows_list = Follow.get_list(follower)
    if follows_list is None:
        return 500, id_msg(-1, "server internal error")
    return 200, jsonify({
        'list':follows_list,
        'id':0,
        'message':'success',
    })