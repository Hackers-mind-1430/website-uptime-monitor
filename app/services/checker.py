import time
from app.models.alert import Alert
import httpx
from sqlalchemy.orm import Session

from app.models.health_check import HealthCheck
from app.models.monitor import Monitor
from app.services.email_alerts import send_email_alert


def check_website(db: Session, monitor: Monitor):
    previous_check = (
        db.query(HealthCheck)
        .filter(HealthCheck.monitor_id == monitor.id)
        .order_by(HealthCheck.checked_at.desc())
        .first()
    )

    start_time = time.perf_counter()

    try:
        response = httpx.get(
            monitor.url,
            timeout=10,
            follow_redirects=True,
        )

        response_time = round(time.perf_counter() - start_time, 3)
        is_up = response.status_code == monitor.expected_status

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=is_up,
            status_code=response.status_code,
            response_time=response_time,
            error_message=None,
        )
    except Exception as exc:
        response_time = round(time.perf_counter() - start_time, 3)
        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message=str(exc),
        )

    db.add(health_check)
    db.commit()
    db.refresh(health_check)

    if previous_check and previous_check.is_up != health_check.is_up:
        alert = Alert(
            monitor_id=monitor.id,
            is_up=health_check.is_up,
            status_code=health_check.status_code,
            response_time=health_check.response_time,
            error_message=health_check.error_message,
        )

        db.add(alert)
        db.commit()

        if monitor.email:
            send_email_alert(
                monitor,
                health_check.is_up,
                health_check.status_code,
                health_check.response_time,
                health_check.error_message,
            )
    elif previous_check is None and not health_check.is_up:
        alert = Alert(
            monitor_id=monitor.id,
            is_up=False,
            status_code=health_check.status_code,
            response_time=health_check.response_time,
            error_message=health_check.error_message,
        )

        db.add(alert)
        db.commit()

        if monitor.email:
            send_email_alert(
                monitor,
                False,
                health_check.status_code,
                health_check.response_time,
                health_check.error_message,
            )

    return health_check