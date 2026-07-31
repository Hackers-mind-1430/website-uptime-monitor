import time

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

    except httpx.TimeoutException:
        response_time = round(time.perf_counter() - start_time, 3)

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message="Request timed out after 10 seconds.",
        )

    except httpx.ConnectError as exc:
        response_time = round(time.perf_counter() - start_time, 3)

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message=f"Connection failed: {str(exc)}",
        )

    except httpx.HTTPError as exc:
        response_time = round(time.perf_counter() - start_time, 3)

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message=f"HTTP error: {str(exc)}",
        )

    except Exception as exc:
        response_time = round(time.perf_counter() - start_time, 3)

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message=f"Unexpected error: {str(exc)}",
        )

    db.add(health_check)
    db.commit()
    db.refresh(health_check)

    if monitor.email:
        status_changed = (
            previous_check
            and previous_check.is_up != health_check.is_up
        )

        first_failed_check = (
            previous_check is None
            and not health_check.is_up
        )

        if status_changed or first_failed_check:
            send_email_alert(
                monitor,
                health_check.is_up,
                health_check.status_code,
                health_check.response_time,
                health_check.error_message,
            )

    return health_check