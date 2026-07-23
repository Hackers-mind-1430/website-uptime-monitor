from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router

app = FastAPI(title="Uptime Monitor")
app.include_router(api_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
