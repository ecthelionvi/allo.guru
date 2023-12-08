from config import engine
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Define models for tables
class ServiceStatus(Base):
    __tablename__ = "service_status"

    id = Column(Integer, primary_key=True)
    status = Column(String(255), default="online", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    encrypted_email = Column(String(255), unique=True, nullable=False)  # Field name changed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)
