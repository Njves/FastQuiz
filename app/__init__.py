from flask import Flask
from flask_admin import Admin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import MetaData
from config import Config

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=convention))
migrate = Migrate()
login_manager = LoginManager()
admin_app = Admin(name='FastQuiz', template_mode='bootstrap3')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    db.init_app(app)
    admin_app.init_app(app)
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)
    return app

from app import models