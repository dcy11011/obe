import os

DEBUG = True

basedir = os.getcwd()

DB_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = DEBUG

JSON_AS_ASCII = False

# IMPORTANT! better not to hardcode this key
SECRET_KEY = "WoXiangWangZiYou,WoYaoTanLianAi,WoRiLeGouLe,WoZhaoBuDaoDuiXiang."

MAX_POST_REQUEST = 50
MAX_REPLY_REQUEST = 50

MAIL_SERVER = 'smtp.yeah.net'
MAIL_PORT = 465
MAIL_USERNAME = 'dcy11011@yeah.net'
MAIL_PASSWORD = 'UYQACHVLVXIRCDIK'
MAIL_USE_SSL = True
