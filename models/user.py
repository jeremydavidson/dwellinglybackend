import datetime
from db import db
from models.base_model import BaseModel


class UserModel(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    role = db.Column(db.String(20))
    firstName = db.Column(db.String(80))
    lastName = db.Column(db.String(80))
    fullName = db.column_property(firstName + ' ' + lastName)
    phone = db.Column(db.String(25))
    password = db.Column(db.String(128))
    archived = db.Column(db.Boolean)
    lastActive = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, firstName, lastName, email, password, phone, role, archived):
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.phone = phone
        self.password = password
        self.role = role if role else 'pending'
        self.archived = False
        self.lastActive = datetime.datetime.utcnow()

    def update_last_active(self):
        self.lastActive = datetime.datetime.utcnow()
        db.session.commit()

    def json(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'archived': self.archived,
            'lastActive': self.lastActive.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        }

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_role(cls, role):
        return cls.query.filter_by(role=role).all()
