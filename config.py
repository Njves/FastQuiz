import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    # SQLALCHEMY_DATABASE_URI = "postgresql://fastquiz_owner:stb6N7IJnzdB@ep-frosty-violet-a56hq90y.us-east-2.aws.neon.tech/fastquiz?sslmode=require"
    SQLALCHEMY_DATABASE_URI = "postgresql://admin:admin@localhost/server"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zxczxc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    JWT_KEY = 'test'
