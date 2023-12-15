from config import engine
from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class Superuser(Base):
    __tablename__ = "superusers"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ISPEndpoint(Base):
    __tablename__ = "isp_endpoints"

    id = Column(Integer, primary_key=True)
    address = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)


class ServiceStatus(Base):
    __tablename__ = "service_status"

    id = Column(Integer, primary_key=True)
    status = Column(String(255), default="online", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)


class EmailSubscription(Base):
    __tablename__ = "email_subscriptions"

    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    encrypted_email = Column(String(255), unique=True, nullable=False)
    email_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)


class SMSSubscription(Base):
    __tablename__ = "sms_subscriptions"

    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    encrypted_phone = Column(String(255), unique=True, nullable=False)
    phone_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)


# Create the tables
Base.metadata.create_all(bind=engine)
