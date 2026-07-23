from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    service_status = [
        {"name": "API Gateway", "status": "online", "url": "https://api.example.com"},
        {"name": "Database", "status": "online", "url": "sqlite://"},
        {"name": "Scheduler", "status": "online", "url": "internal"},
    ]
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "service_status": service_status},
    )
