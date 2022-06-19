from email.mime import base
import os

DEBUG = False
DEBUG_ERROR = False

basedir = os.getcwd()

DB_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

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


# Path to save user uploaded files
UPLOAD_PATH  = os.path.join(basedir, "userdata")
ALLOWED_EXTENTIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'aac', 'mp3', 'wav', 'flac', 'mp4', 'mov', 'avi', 'mpeg', 'amr']
FILE_TYPE = {
    'jpg':'IMG',
    'jpeg':'IMG',
    'png':'IMG',
    'gif':'IMG',
    'webp':'IMG',
    'aac':'AUD',
    'mp3':'AUD',
    'flac':'AUD',
    'amr':'AUD',
    'mp4':'VID',
    'avi':'VID',
    'mpeg':'VID',
}

