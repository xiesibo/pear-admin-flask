from flask import Flask

from entrance.extend.orm import db
from entrance.extend.migrate import migrate


def init_extensions(app: Flask):
    db.init_app(app)
    migrate.init_app(app)