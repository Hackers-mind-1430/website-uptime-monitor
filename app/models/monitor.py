from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    url = Column(String(300), nullable=False)

    expected_status = Column(Integer, default=200)

    check_interval = Column(Integer, default=5)

    email = Column(String(255))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    health_checks = relationship(
        "HealthCheck",
        backref="monitor",
        cascade="all, delete-orphan"
    )