from config import engine
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

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
