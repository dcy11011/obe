from email.policy import default
from enum import unique
from lib2to3.pgen2.token import ERRORTOKEN
import math
from flask import g
from exts import db
from log import *
import datetime
from sqlalchemy import ForeignKey, false, func, and_, true
import uuid

UUID_LEN = 40


MAXLEN_USERNAME     = 12
MAXLEN_USERSIG      = 40
MAXLEN_PASSWD       = 18
MAXLEN_MAIL         = 50
MAXLEN_TITLE        = 40
MAXLEN_CONTENT      = 500

# Type of resources
RES_JPG     = 1
RES_MP4     = 2
RES_MP3     = 3
RES_TYPE_LIST = [RES_JPG, RES_MP4, RES_MP3]

# Error code for insert_user
ERROR_QUERY_DB      = -1
ERROR_USERNAME      = -2
ERROR_MAIL          = -3
ERROR_TEL           = -4
TYPE_ERROR_QUERY    = type(ERROR_QUERY_DB)

# Error code for login
ERROR_NO_USER       = -1
ERROR_PASSWD        = -2


# Misc Error code
ERROR_DB_EXECUTE    = -1
ERROR_UNAUTHORIZED  = -2
ERROR_NOTEXIST      = -3
DB_SUCCESS          = 0
ERROR_NO_POST       = -2

# Reply
MAX_REPLY_GET   = 30

# Posts query type
POST_QUERY_NEW      = 0
POST_QUERY_HOT      = 1
POST_QUERY_FOLLOW   = 2


#########
# Valid #
#########
class Valid:
    valid_dict = dict()
    def __init__(self) -> None:
        pass
    def insert(content:str, code:int):
        Valid.valid_dict[content] = code
    def get_code(content):
        return Valid.valid_dict.get(content, None)



##############
# User Table #
##############
class Users(db.Model):
    __tablename__ = "users"
    uid = db.Column(db.Integer, primary_key = True, autoincrement=True)
    uuid = db.Column(db.String(UUID_LEN), unique=True) # for identifing new data when inserting. See Users.insert().
    name = db.Column(db.String(MAXLEN_USERNAME), unique=True)
    sig = db.Column(db.String(MAXLEN_USERSIG))
    mail = db.Column(db.String(100), unique=True)
    tel = db.Column(db.String(20), unique=True)
    img_res_id = db.Column(db.Integer)
    md5_passwd = db.Column(db.String(250))
    addtime = db.Column(db.DateTime())

    def __init__(self, name, mail, tel, md5_passwd):
        self.uid = None
        self.uuid = str(uuid.uuid4())
        self.name, self.mail, self.tel, self.md5_passwd = name, mail, tel, md5_passwd
        self.sig, self.img_res_id = None, None
        self.addtime = datetime.datetime.now()


    @staticmethod
    def get_max_uid():
        if g.get("max_uid", -1) < 0:
            try:
                g.max_uid = int(db.session.query(func.max(Users.uid)).one()[0])
            except Exception as e:
                logDE(e)
                g.max_uid = 0
        return g.max_uid


    @staticmethod
    def insert(name:str, passwd:str, valid_type:str, valid_content:str) -> int:
        # Check if username already exist
        if db.session.query(Users).filter(Users.name == name).first() is not None:
            return ERROR_USERNAME

        new_uid = -1
        # Try create and insert a new user to database
        try:
            user_uuid = None
            if(valid_type == "mail"):
                if db.session.query(Users).filter(Users.mail == valid_content).first() is not None:
                    return ERROR_MAIL
                new_user = Users(name, valid_content, None, passwd)
                user_uuid = new_user.uuid
                db.session.add(new_user)
            elif(valid_type == "tel"):
                if db.session.query(Users).filter(Users.tel == valid_content).first() is not None:
                    return ERROR_TEL
                new_user = Users(name, None, valid_content, passwd)
                user_uuid = new_user.uuid
                db.session.add(new_user)
            else:
                raise Exception("Unexpected validation type")
            db.session.commit()
            new_uid = int(db.session.query(Users.uid).filter(Users.uuid == user_uuid).one()[0])
        except Exception as e:
            logDE(e)
            return -1
        logD(f"New User: id={new_uid:06d}, name={name}")
        return new_uid


    @staticmethod
    def get_by_id(uid):
        usr = db.session.query(Users).filter(Users.uid == uid).first()
        return usr


    @staticmethod
    def get_by_login(username, passwd):
        usr = db.session.query(Users).filter(and_(Users.name == username)).first()
        if usr is None:
            return ERROR_NO_USER
        if usr.md5_passwd != passwd:
            return ERROR_PASSWD
        return usr.uid



##############
# Post Table #
##############
class Posts(db.Model):
    __tablename__ = "posts"
    pid = db.Column(db.Integer, primary_key = True, autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid', ondelete='SET NULL'))
    uuid = db.Column(db.String(UUID_LEN), unique=True)
    addtime = db.Column(db.DateTime())
    title = db.Column(db.String(MAXLEN_TITLE))
    content  = db.Column(db.String(MAXLEN_CONTENT))
    res_id = db.Column(db.Integer)
    res_type = db.Column(db.Integer)
    pos = db.Column(db.String(200))
    dianzan = db.Column(db.Integer)

    def __init__(self, uid, title, content, res_type, res_id, pos):
        if res_type not in RES_TYPE_LIST and res_type is not None: 
            raise Exception(f"Unsupported resource type[{res_type}]")
        self.uuid = str(uuid.uuid4())
        self.uid, self.title, self.content, self.res_type, self.res_id, self.pos = uid, title, content, res_type, res_id, pos
        self.addtime = datetime.datetime.now()
        self.dianzan = 0

    
    @staticmethod
    def insert(uid, title, content, res_type=None, res_id=None, pos=None):
        new_pid = -1
        try:
            new_post = Posts(uid, title, content, res_type, res_id, pos)
            post_uuid = new_post.uuid
            db.session.add(new_post)
            db.session.commit()
            new_pid = int(db.session.query(Posts).filter(Posts.uuid == post_uuid).one().pid)
        except Exception as e:
            logDE(e)
            return -1
        return new_pid


    @staticmethod
    def get_max_pid():
        pid = 0
        try:
            pid = int(db.session.query(func.max(Posts.pid)).one()[0])
        except Exception as e:
            logDE(e)
            return -1
        return pid


    @staticmethod
    def get_n_newest(uid:int, n:int, start = None, type =  POST_QUERY_NEW) -> list:
        post_list = []
        try:
            temp = db.session.query(Posts)
            if type == POST_QUERY_NEW:
                if start is not None:
                    temp = temp.filter(Posts.pid.__le__(start))
                post_list = temp.order_by(Posts.pid.desc()).limit(n).all()
            if type == POST_QUERY_HOT:
                if start is not None:
                    temp = temp.filter(Posts.pid.__le__(start))
                post_list = temp.order_by(Posts.dianzan.desc()).limit(n).all()
            if type == POST_QUERY_FOLLOW:
                if start is not None:
                    temp = temp.filter(Posts.pid.__le__(start))
                post_list = temp.filter(Posts.uid.in_(Follow.get_list(uid))).order_by(Posts.dianzan.desc()).limit(n).all()
        except Exception as e:
            logDE(e)
            return ERROR_QUERY_DB        
        return post_list


    @staticmethod
    def get_n_newest_filter_uid(uid:int, n:int, start = None) -> list:
        post_list = []
        try:
            if start is not None:
                post_list = db.session.query(Posts).filter(and_(Posts.pid.__le__(start), Posts.uid == uid)).order_by(and_(Posts.pid.desc())).limit(n).all()
            else :
                post_list = db.session.query(Posts).order_by(Posts.pid.desc()).limit(n).all()
        except Exception as e:
            logDE(e)
            return ERROR_QUERY_DB        
        return post_list


    @staticmethod
    def get(pid:int):
        post = db.session.query(Posts).filter(Posts.pid == pid).first()
        return post

    
    @staticmethod
    def zan(uid:int, pid:int) -> bool:
        if Posts.get(pid) is None:
            return ERROR_NO_POST
        if_zaned = Dianzans.get(uid,pid)
        try:
            n_zan = db.session.query(Posts).filter(Posts.pid == pid).one().dianzan
            if if_zaned:
                n_zan -= 1
                Dianzans.remove(uid, pid)
            else:
                n_zan += 1
                Dianzans.add(uid, pid)
            
            db.session.query(Posts).filter(Posts.pid == pid).update({"dianzan":n_zan})
            db.session.commit()
        except Exception as e:
            logDE(e)
            return ERROR_QUERY_DB
        
        return not if_zaned


    @staticmethod 
    def remove_by_pid(uid:int, pid:int):
        try:
            post = db.session.query(Posts).filter(Posts.pid == pid)
            _post = post.one()
            if _post is None:
                return ERROR_NOTEXIST
            if _post.uid != uid:
                return ERROR_UNAUTHORIZED
            post.delete()
            db.session.commit()
        except Exception as e:
            logDE(e)
            return ERROR_DB_EXECUTE
        return DB_SUCCESS


        

###############
# Reply Table #
###############
class Replies(db.Model):
    __tablename__ = "replies"
    rid = db.Column(db.Integer, primary_key = True, autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid', ondelete='SET NULL'))
    pid = db.Column(db.Integer, db.ForeignKey('posts.pid', ondelete='CASCADE'))
    uuid = db.Column(db.String(UUID_LEN), unique=True)
    addtime = db.Column(db.DateTime())
    content  = db.Column(db.String(MAXLEN_CONTENT))
    res_id = db.Column(db.Integer)
    res_type = db.Column(db.Integer)
    pos = db.Column(db.String(200))

    def __init__(self, uid, pid, content, res_type=None, res_id=None, pos=None):
        if res_type not in RES_TYPE_LIST and res_type is not None: 
            raise Exception(f"Unsupported resource type[{res_type}]")
        self.uuid = str(uuid.uuid4())
        self.uid, self.pid, self.content, self.res_type, self.res_id, self.pos = uid, pid, content, res_type, res_id, pos
        self.addtime = datetime.datetime.now()


    @staticmethod
    def get_max_rid(pid):
        max_rid = 0
        try:
            max_rid = int(db.session.query(func.max(Replies.pid)).one()[0])
        except Exception as e:
            logDE(e)
            return -1        
        return max_rid


    @staticmethod
    def get_by_pid(pid:int, n:int = 20, start = None):
        if Posts.get(pid) is None:
            return ERROR_NO_POST
        reply_list = []
        try:
            if start is None:
                start = 0
            reply_list = db.session.query(Replies).filter(and_(Replies.pid == pid, Replies.rid.__ge__(start))).limit(n)
        except Exception as e:
            logDE(e)
            return ERROR_QUERY_DB        
        return reply_list

    
    @staticmethod
    def insert(uid, pid, content, res_type = None, res_id = None, pos = None):
        if Posts.get(pid) is None:
            return ERROR_NO_POST
        new_rid = -1
        try:
            new_reply = Replies(uid, pid, content, res_type, res_id, pos)
            reply_uuid = new_reply.uuid
            db.session.add(new_reply)
            db.session.commit()
            new_rid = int(db.session.query(Replies).filter(Replies.uuid == reply_uuid).one().rid)
        except Exception as e:
            logDE(e)
            return -1
        return new_rid


    @staticmethod
    def count_by_pid(pid):
        if Posts.get(pid) is None:
            return ERROR_NO_POST
        n_reply = 0
        try:
            n_reply = int(db.session.query(func.count(Replies.rid)).filter(Replies.pid == pid).one()[0])
        except Exception as e:
            logDE(e)
            return -1
        return n_reply


    @staticmethod
    def remove_by_rid(uid, rid):
        try:
            reply = db.session.query(Replies).filter(Replies.rid == rid)
            _reply = reply.one()
            if _reply is None:
                return ERROR_NOTEXIST
            if _reply.uid != uid:
                return ERROR_UNAUTHORIZED
            reply.delete()
            db.session.commit()
        except Exception as e:
            logDE(e)
            return ERROR_DB_EXECUTE
        return DB_SUCCESS


############
# Dianzans #
############
class Dianzans(db.Model):
    __tablename__ = "dianzans"
    uid = db.Column(db.Integer, db.ForeignKey('users.uid', ondelete='CASCADE'), primary_key = True)
    pid = db.Column(db.Integer, db.ForeignKey('posts.pid', ondelete='CASCADE'), primary_key = True)

    def __init__(self, uid, pid):
        self.uid, self.pid = uid, pid


    @staticmethod
    def add(uid, pid) -> bool:
        try:
            dianzan = Dianzans(uid,pid)
            db.session.add(dianzan)
            db.session.commit()
        except Exception as e:
            logDE(e)
            return False
        return True


    @staticmethod
    def remove(uid, pid):
        try:
            db.session.query(Dianzans).filter(and_(Dianzans.uid == uid, Dianzans.pid == pid)).delete()
            db.session.commit()
        except Exception as e:
            logDE(e)
            return False
        return True


    @staticmethod
    def get(uid, pid) ->bool:
        try:
            dianzan = db.session.query(Dianzans).filter(and_(Dianzans.uid == uid, Dianzans.pid == pid)).one()
            if dianzan is None:
                return False
            return True
        except Exception as e:
            logDE(e)
            return False



###########
# Follow  #
###########
class Follow(db.Model):
    __tablename__ = "follow"
    follower = db.Column(db.Integer, db.ForeignKey('users.uid', ondelete='CASCADE'), primary_key = True)
    follows  = db.Column(db.Integer, db.ForeignKey('users.uid', ondelete='CASCADE'), primary_key = True)

    def __init__(self, follower, follows):
        self.follower, self.follows = follower, follows

    @staticmethod
    def add(follower:int, follows:int) -> bool:
        try:
            follow = Follow(follower,follows)
            db.session.add(follow)
            db.session.commit()
        except Exception as e:
            logDE(e)
            return False
        return True


    @staticmethod
    def remove(follower:int, follows:int):
        try:
            db.session.query(Follow).filter(and_(Follow.follower == follower, Follow.follows == follows)).delete()
            db.session.commit()
        except Exception as e:
            logDE(e)
            return False
        return True


    @staticmethod
    def get_list(follower:int):
        follows_list = []
        try:
            ret = db.session.query(Follow).filter(and_(Follow.follower == follower)).all()
            follows_list = [r.follows for r in ret]
        except Exception as e:
            logDE(e)
            return None
        return follows_list