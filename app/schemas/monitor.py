from pydantic import BaseModel, HttpUrl
from typing import Optional


class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl
    expected_status: int = 200
    check_interval: int = 5
    email: Optional[str] = None


class MonitorRead(MonitorCreate):
    id: int

    class Config:
        from_attributes = True