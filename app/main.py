from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.database import Base, engine

# Import ALL models before create_all()
from app.models.monitor import Monitor
from app.models.health_check import HealthCheck

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Website Uptime Monitor",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

app.include_router(router)