from app.models.health_check import HealthCheck
from app.models.monitor import Monitor


def build_monitor_chart_dataset(db, monitor: Monitor):
    latest = (
        db.query(HealthCheck)
        .filter(HealthCheck.monitor_id == monitor.id)
        .order_by(HealthCheck.checked_at.desc())
        .first()
    )

    return {
        "monitor_name": monitor.name,
        "status": "up" if latest and latest.is_up else "down" if latest else "unknown",
        "response_time": latest.response_time if latest and latest.response_time is not None else 0,
        "last_checked": latest.checked_at.isoformat() if latest else None,
    }
