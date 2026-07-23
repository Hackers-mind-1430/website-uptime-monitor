from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)

    monitor_id = Column(
        Integer,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False
    )

    is_up = Column(Boolean, nullable=False)

    status_code = Column(Integer)

    response_time = Column(Float)

    checked_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    error_message = Column(String(500))