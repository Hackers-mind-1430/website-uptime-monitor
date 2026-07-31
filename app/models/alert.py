from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    monitor_id = Column(
        Integer,
        ForeignKey(
            "monitors.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    is_up = Column(
        Boolean,
        nullable=False,
    )

    status_code = Column(Integer)

    response_time = Column(Float)

    error_message = Column(
        String(500)
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    monitor = relationship(
        "Monitor",
        backref="alerts",
    )