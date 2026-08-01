from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.database import Base, engine
from app.models.health_check import HealthCheck
from app.services.scheduler import start_scheduler, stop_scheduler
from app.models.monitor import Monitor
from app.models.alert import Alert

ROOT_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Website Uptime Monitor",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(ROOT_DIR / "static")),
    name="static"
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()