from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.monitor import Monitor
from app.models.health_check import HealthCheck
from app.services.checker import check_website

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):

    monitors = db.query(Monitor).all()

    latest_checks = {}

    for monitor in monitors:
        latest = (
            db.query(HealthCheck)
            .filter(HealthCheck.monitor_id == monitor.id)
            .order_by(HealthCheck.checked_at.desc())
            .first()
        )

        latest_checks[monitor.id] = latest

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "title": "Website Uptime Monitor",
            "monitors": monitors,
            "latest_checks": latest_checks,
        },
    )


@router.get("/add")
def add_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_monitor.html",
        context={"request": request, "title": "Add Website"},
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
    monitor = Monitor(
        name=name,
        url=url,
        expected_status=expected_status,
        check_interval=check_interval,
        email=email,
    )

    db.add(monitor)
    db.commit()

    return RedirectResponse("/", status_code=303)


@router.get("/check/{monitor_id}")
def run_check(monitor_id: int, db: Session = Depends(get_db)):

    monitor = db.get(Monitor, monitor_id)

    if monitor:
        check_website(db, monitor)

    return RedirectResponse("/", status_code=303)


@router.get("/delete/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):

    monitor = db.get(Monitor, monitor_id)

    if monitor:
        db.delete(monitor)
        db.commit()

    return RedirectResponse("/", status_code=303)