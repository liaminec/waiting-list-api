from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Model(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class TimedModel(Model):
    created_at: datetime = Field(default=datetime.now)
    updated_at: datetime = Field(default=datetime.now)
