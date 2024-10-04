import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = "postgresql://admin:admin@db:5432/server"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zxczxc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
