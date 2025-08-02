from datetime import datetime
import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    agents = db.relationship('LocalAgent', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    scheduled_jobs = db.relationship('ScheduledJob', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    preset_profiles = db.relationship('PresetProfile', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LocalAgent(db.Model):
    __tablename__ = 'local_agents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    api_key_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    last_seen = db.Column(db.DateTime)
    is_online = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_api_key(self, api_key):
        self.api_key_hash = generate_password_hash(api_key)
    
    def check_api_key(self, api_key):
        return check_password_hash(self.api_key_hash, api_key)
    
    def __repr__(self):
        return f'<LocalAgent {self.name}>'

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transcribed_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.id}>'

class ScheduledJob(db.Model):
    __tablename__ = 'scheduled_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_group_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    message_text = db.Column(db.Text, nullable=False)
    target_hwnd = db.Column(db.BigInteger, nullable=False)
    target_title_snapshot = db.Column(db.String(255))
    scheduled_time = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='PENDING')  # PENDING, SENT, FAILED, CANCELLED, EXPIRED
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime)
    
    # Index for efficient querying
    __table_args__ = (
        db.Index('idx_scheduled_jobs_status_time', 'status', 'scheduled_time'),
        db.Index('idx_scheduled_jobs_group', 'job_group_id'),
    )
    
    def __repr__(self):
        return f'<ScheduledJob {self.id} - {self.status}>'

class PresetProfile(db.Model):
    __tablename__ = 'preset_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10))  # Emoji icon
    start_delay_seconds = db.Column(db.Integer, nullable=False)
    repetitions = db.Column(db.Integer, nullable=False, default=1)
    interval_seconds = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PresetProfile {self.name}>'

class SystemStatus(db.Model):
    __tablename__ = 'system_status'
    
    id = db.Column(db.Integer, primary_key=True)
    rate_limited = db.Column(db.Boolean, default=False)
    reset_time = db.Column(db.DateTime(timezone=True))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_current_status(cls):
        status = cls.query.first()
        if not status:
            status = cls(rate_limited=False)
            db.session.add(status)
            db.session.commit()
        return status
    
    def __repr__(self):
        return f'<SystemStatus rate_limited={self.rate_limited}>'