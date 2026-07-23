from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    status = Column(String(32), default="unknown")
    last_checked = Column(DateTime, default=datetime.utcnow)
