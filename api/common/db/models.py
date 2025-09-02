from datetime import datetime

from sqlmodel import SQLModel, Field


class Model(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class ItemModel(SQLModel):
    id: str = Field(primary_key=True)
