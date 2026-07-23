import time

import httpx
from sqlalchemy.orm import Session

from app.models.health_check import HealthCheck
from app.models.monitor import Monitor


def check_website(db: Session, monitor: Monitor):

    start_time = time.perf_counter()

    try:
        response = httpx.get(
            monitor.url,
            timeout=10,
            follow_redirects=True
        )

        response_time = round(
            time.perf_counter() - start_time,
            3
        )

        is_up = response.status_code == monitor.expected_status

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=is_up,
            status_code=response.status_code,
            response_time=response_time,
            error_message=None
        )

    except Exception as e:

        response_time = round(
            time.perf_counter() - start_time,
            3
        )

        health_check = HealthCheck(
            monitor_id=monitor.id,
            is_up=False,
            status_code=None,
            response_time=response_time,
            error_message=str(e)
        )

    db.add(health_check)
    db.commit()

    return health_check