from typing import Dict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.monitor import Monitor
from app.services.checker import check_website

scheduler = BackgroundScheduler()
job_registry: Dict[int, str] = {}


def _run_monitor_check(monitor_id: int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if monitor:
            check_website(db, monitor)
    finally:
        db.close()


def schedule_monitor_job(monitor: Monitor):
    job_id = f"monitor-{monitor.id}"
    trigger = IntervalTrigger(minutes=max(1, monitor.check_interval))

    scheduler.add_job(
        _run_monitor_check,
        trigger,
        args=[monitor.id],
        id=job_id,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=30,
    )
    job_registry[monitor.id] = job_id


def remove_monitor_job(monitor_id: int):
    job_id = job_registry.pop(monitor_id, None)
    if job_id and scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def sync_monitor_jobs():
    db = SessionLocal()
    try:
        monitors = db.query(Monitor).all()
    finally:
        db.close()

    current_ids = {monitor.id for monitor in monitors}
    existing_ids = set(job_registry.keys())

    for monitor in monitors:
        schedule_monitor_job(monitor)

    for monitor_id in existing_ids - current_ids:
        remove_monitor_job(monitor_id)


def start_scheduler():
    if not scheduler.running:
        scheduler.start(paused=True)
        sync_monitor_jobs()
        scheduler.resume()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
