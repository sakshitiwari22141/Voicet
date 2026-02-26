from flask_login import UserMixin
from . import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), unique=True, nullable=False)
    posts = db.relationship('Videos',backref='user', lazy=True)

class Videos(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    youtube_url = db.Column(db.String(200), nullable=True)
    file_name = db.Column(db.String(200), nullable=True)
    file_extension = db.Column(db.String(10) )
    file_path = db.Column(db.String(200))
    original_filename = db.Column(db.String(200))
    # Field to track Celery tasks
    task_id = db.Column(db.String(100), nullable=True)
    translate_to_languge = db.Column(db.String(200))
    translate_to_gender = db.Column(db.String(200))
    video_processed = db.Column(db.Integer, default=0) # 0: Original/Pending, 1: Processed
    percent_processed = db.Column(db.Integer, default=0)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Restore FK but keep as String because the app currently stores 'current_user.name' here
    posted_by = db.Column(db.String(1000), db.ForeignKey('user.name'), nullable=False)
