from datetime import datetime

from sqlmodel import SQLModel, Field


class Model(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class ItemModel(SQLModel):
    id: str = Field(primary_key=True)


class TimedModel(Model):
    created_at: datetime = Field(default=datetime.now)
    updated_at: datetime = Field(default=datetime.now)


class ItemTimedModel(ItemModel):
    created_at: datetime = Field(default=datetime.now)
    updated_at: datetime = Field(default=datetime.now)
