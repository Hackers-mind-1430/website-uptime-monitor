from pydantic import BaseModel
from datetime import datetime


class MonitorBase(BaseModel):
    name: str
    url: str


class MonitorCreate(MonitorBase):
    pass


class MonitorRead(MonitorBase):
    id: int
    status: str
    last_checked: datetime

    class Config:
        orm_mode = True
