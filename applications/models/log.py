from flask_restful import fields

from applications.extensions import db
from .base import BaseModel


class LoggingModel(db.Model, BaseModel):
    __tablename__ = 'lg_logging'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(10))
    uid = db.Column(db.Integer, default=None)
    url = db.Column(db.String(255))
    desc = db.Column(db.Text)
    ip = db.Column(db.String(255))
    success = db.Column(db.Boolean, default=True)
    user_agent = db.Column(db.Text)

    @staticmethod
    def fields():
        return {
            'id': fields.Integer,
            'method': fields.String,
            'uid': fields.String,
            'url': fields.Url,
            'desc': fields.String,
            'ip': fields.String,
            'success': fields.Boolean,
            'user_agent': fields.String,
            'create_at': fields.DateTime,
        }
