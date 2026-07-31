
import json
from urllib.parse import urlparse

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.models.monitor import Monitor
from app.models.health_check import HealthCheck
from app.services.checker import check_website
from app.services.reports import build_monitor_chart_dataset
from app.services.scheduler import (
    schedule_monitor_job,
    remove_monitor_job,
    update_monitor_job,
)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

PAGE_SIZE = 10


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/")
def dashboard(
    request: Request,
    query: str = "",
    page: int = 1,
    message: str = "",
    message_type: str = "success",
    db: Session = Depends(get_db),
):
    page = max(page, 1)

    monitors_query = db.query(Monitor)

    if query:
        search_term = f"%{query}%"

        monitors_query = monitors_query.filter(
            or_(
                Monitor.name.ilike(search_term),
                Monitor.url.ilike(search_term),
            )
        )

    total_monitors = monitors_query.count()

    total_pages = max(
        1,
        (total_monitors + PAGE_SIZE - 1) // PAGE_SIZE,
    )

    if page > total_pages:
        page = total_pages

    monitors = (
        monitors_query
        .order_by(Monitor.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    latest_checks = {}
    chart_dataset = []

    for monitor in monitors:
        latest = (
            db.query(HealthCheck)
            .filter(
                HealthCheck.monitor_id == monitor.id
            )
            .order_by(
                HealthCheck.checked_at.desc()
            )
            .first()
        )

        latest_checks[monitor.id] = latest

        chart_dataset.append(
            build_monitor_chart_dataset(
                db,
                monitor,
            )
        )

    total_up = sum(
        1
        for check in latest_checks.values()
        if check and check.is_up
    )

    total_down = sum(
        1
        for check in latest_checks.values()
        if check and not check.is_up
    )

    total_never = (
        total_monitors
        - len(
            [
                check
                for check in latest_checks.values()
                if check
            ]
        )
    )

    response_values = [
        check.response_time
        for check in latest_checks.values()
        if check
        and check.response_time is not None
    ]

    avg_response = (
        round(
            sum(response_values)
            / len(response_values),
            3,
        )
        if response_values
        else 0.0
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "title": "Website Uptime Monitor",
            "monitors": monitors,
            "latest_checks": latest_checks,
            "page": page,
            "total_pages": total_pages,
            "query": query,
            "message": message,
            "message_type": message_type,
            "status_summary": {
                "up": total_up,
                "down": total_down,
                "unknown": total_never,
            },
            "avg_response": avg_response,
            "chart_dataset": json.dumps(chart_dataset),
        },
    )


# ============================================================
# ADD MONITOR
# ============================================================

@router.get("/add")
def add_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_monitor.html",
        context={
            "request": request,
            "title": "Add Website",
        },
    )


@router.post("/add")
def add_monitor(
    name: str = Form(...),
    url: str = Form(...),
    expected_status: int = Form(200),
    check_interval: int = Form(5),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    # Validate check interval
    if check_interval < 1:
        return RedirectResponse(
            "/?message=Check+interval+must+be+at+least+1+minute"
            "&message_type=danger",
            status_code=303,
        )

    # Validate HTTP status
    if expected_status < 100 or expected_status > 599:
        return RedirectResponse(
            "/?message=Invalid+HTTP+status+code"
            "&message_type=danger",
            status_code=303,
        )

    # Validate URL
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        return RedirectResponse(
            "/?message=Please+enter+a+valid+HTTP+or+HTTPS+URL"
            "&message_type=danger",
            status_code=303,
        )

    monitor = Monitor(
        name=name.strip(),
        url=url.strip(),
        expected_status=expected_status,
        check_interval=check_interval,
        email=email.strip(),
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    schedule_monitor_job(monitor)

    return RedirectResponse(
        "/?message=Website+added+successfully"
        "&message_type=success",
        status_code=303,
    )


# ============================================================
# MANUAL CHECK
# ============================================================

@router.get("/check/{monitor_id}")
def run_check(
    monitor_id: int,
    db: Session = Depends(get_db),
):
    monitor = db.get(Monitor, monitor_id)

    message = "Monitor not found"
    message_type = "danger"

    if monitor:
        health_check = check_website(
            db,
            monitor,
        )

        status = (
            "UP"
            if health_check.is_up
            else "DOWN"
        )

        message = (
            f"Manual check completed: "
            f"{monitor.name} is {status}."
        )

        message_type = (
            "success"
            if health_check.is_up
            else "danger"
        )

    return RedirectResponse(
        f"/?message={message.replace(' ', '+')}"
        f"&message_type={message_type}",
        status_code=303,
    )


# ============================================================
# MONITOR DETAILS
# ============================================================

@router.get("/monitor/{monitor_id}")
def monitor_details(
    monitor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    monitor = db.get(
        Monitor,
        monitor_id,
    )

    if not monitor:
        return RedirectResponse(
            "/?message=Monitor+not+found"
            "&message_type=danger",
            status_code=303,
        )

    health_checks = (
        db.query(HealthCheck)
        .filter(
            HealthCheck.monitor_id == monitor.id
        )
        .order_by(
            HealthCheck.checked_at.desc()
        )
        .limit(100)
        .all()
    )

    total_checks = len(health_checks)

    successful_checks = sum(
        1
        for check in health_checks
        if check.is_up
    )

    failed_checks = sum(
        1
        for check in health_checks
        if not check.is_up
    )

    response_times = [
        check.response_time
        for check in health_checks
        if check.response_time is not None
    ]

    average_response = (
        round(
            sum(response_times)
            / len(response_times),
            3,
        )
        if response_times
        else 0.0
    )

    fastest_response = (
        min(response_times)
        if response_times
        else 0.0
    )

    slowest_response = (
        max(response_times)
        if response_times
        else 0.0
    )

    uptime_percentage = (
        round(
            (
                successful_checks
                / total_checks
            )
            * 100,
            2,
        )
        if total_checks
        else 0.0
    )

    alerts = (
        db.query(Alert)
        .filter(
            Alert.monitor_id == monitor.id
        )
        .order_by(
            Alert.created_at.desc()
        )
        .limit(50)
        .all()
    )

    # JSON is prepared in Python.
    # The template should consume this as data,
    # not as raw JavaScript/Jinja syntax.
    chart_data = {
        "labels": [
            check.checked_at.strftime(
                "%d %b %H:%M"
            )
            for check in reversed(
                health_checks
            )
        ],
        "response_times": [
            check.response_time
            for check in reversed(
                health_checks
            )
        ],
        "statuses": [
            "UP"
            if check.is_up
            else "DOWN"
            for check in reversed(
                health_checks
            )
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="monitor_details.html",
        context={
            "request": request,
            "title": (
                f"{monitor.name} - "
                "Monitor Details"
            ),
            "monitor": monitor,
            "health_checks": health_checks,
            "alerts": alerts,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "average_response": average_response,
            "fastest_response": fastest_response,
            "slowest_response": slowest_response,
            "uptime_percentage": uptime_percentage,
            "chart_data": json.dumps(chart_data),
        },
    )


# ============================================================
# EDIT MONITOR
# ============================================================

@router.get("/edit/{monitor_id}")
def edit_monitor_page(
    monitor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    monitor = db.get(
        Monitor,
        monitor_id,
    )

    if not monitor:
        return RedirectResponse(
            "/?message=Monitor+not+found"
            "&message_type=danger",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="edit_monitor.html",
        context={
            "request": request,
            "title": f"Edit {monitor.name}",
            "monitor": monitor,
        },
    )


@router.post("/edit/{monitor_id}")
def edit_monitor(
    monitor_id: int,
    name: str = Form(...),
    url: str = Form(...),
    expected_status: int = Form(200),
    check_interval: int = Form(5),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    monitor = db.get(
        Monitor,
        monitor_id,
    )

    if not monitor:
        return RedirectResponse(
            "/?message=Monitor+not+found"
            "&message_type=danger",
            status_code=303,
        )

    # Validate check interval
    if check_interval < 1:
        return RedirectResponse(
            f"/edit/{monitor_id}"
            "?message=Check+interval+must+be+at+least+1+minute"
            "&message_type=danger",
            status_code=303,
        )

    # Validate HTTP status
    if expected_status < 100 or expected_status > 599:
        return RedirectResponse(
            f"/edit/{monitor_id}"
            "?message=Invalid+HTTP+status+code"
            "&message_type=danger",
            status_code=303,
        )

    # Validate URL
    parsed_url = urlparse(url)

    if parsed_url.scheme not in (
        "http",
        "https",
    ) or not parsed_url.netloc:
        return RedirectResponse(
            f"/edit/{monitor_id}"
            "?message=Please+enter+a+valid+HTTP+or+HTTPS+URL"
            "&message_type=danger",
            status_code=303,
        )

    # Update monitor
    monitor.name = name.strip()
    monitor.url = url.strip()
    monitor.expected_status = expected_status
    monitor.check_interval = check_interval
    monitor.email = email.strip()

    # Save database changes
    db.commit()
    db.refresh(monitor)

    # Replace scheduler job using new settings
    update_monitor_job(monitor)

    return RedirectResponse(
        "/?message=Monitor+updated+successfully"
        "&message_type=success",
        status_code=303,
    )


# ============================================================
# DELETE MONITOR
# ============================================================

@router.get("/delete/{monitor_id}")
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
):
    monitor = db.get(
        Monitor,
        monitor_id,
    )

    message = "Monitor not found"
    message_type = "danger"

    if monitor:
        remove_monitor_job(
            monitor.id
        )

        db.delete(monitor)
        db.commit()

        message = (
            f"Deleted {monitor.name} successfully"
        )

        message_type = "success"

    return RedirectResponse(
        f"/?message={message.replace(' ', '+')}"
        f"&message_type={message_type}",
        status_code=303,
    )


# ============================================================
# STATUS API
# ============================================================

@router.get("/api/status")
def dashboard_status(
    db: Session = Depends(get_db),
):
    monitors = (
        db.query(Monitor)
        .all()
    )

    data = []

    for monitor in monitors:
        latest = (
            db.query(HealthCheck)
            .filter(
                HealthCheck.monitor_id
                == monitor.id
            )
            .order_by(
                HealthCheck.checked_at.desc()
            )
            .first()
        )

        data.append(
            {
                "id": monitor.id,
                "name": monitor.name,
                "is_up": (
                    latest.is_up
                    if latest
                    else None
                ),
                "status_code": (
                    latest.status_code
                    if latest
                    else None
                ),
                "response_time": (
                    latest.response_time
                    if latest
                    else None
                ),
                "checked_at": (
                    latest.checked_at.strftime(
                        "%d %b %H:%M:%S"
                    )
                    if latest
                    else None
                ),
            }
        )

    return data


# ============================================================
# ANALYTICS API
# ============================================================

@router.get("/api/analytics")
def dashboard_analytics(
    db: Session = Depends(get_db),
):
    monitors = (
        db.query(Monitor)
        .all()
    )

    total_monitors = len(monitors)

    up = 0
    down = 0
    response_times = []

    for monitor in monitors:
        latest = (
            db.query(HealthCheck)
            .filter(
                HealthCheck.monitor_id
                == monitor.id
            )
            .order_by(
                HealthCheck.checked_at.desc()
            )
            .first()
        )

        if latest:
            if latest.is_up:
                up += 1
            else:
                down += 1

            if latest.response_time is not None:
                response_times.append(
                    latest.response_time
                )

    avg_response = (
        round(
            sum(response_times)
            / len(response_times),
            3,
        )
        if response_times
        else 0.0
    )

    return {
        "total": total_monitors,
        "up": up,
        "down": down,
        "average_response": avg_response,
    }


# ============================================================
# ALERT HISTORY
# ============================================================

@router.get("/alerts")
def alert_history(
    request: Request,
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(Alert)
        .order_by(
            Alert.created_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="alerts.html",
        context={
            "request": request,
            "title": "Alert History",
            "alerts": alerts,
        },
    )

