from datetime import datetime
from uuid import uuid4

from sqlmodel import Relationship, SQLModel, Field

from common.db.models import Model


def generate_uuid_str() -> str:
    return str(uuid4())


class User(SQLModel, table=True):
    # I'd rather use UUID, but sqlite can't really manage UUIDs
    id: str = Field(default_factory=generate_uuid_str, primary_key=True)
    email: str = Field(max_length=255)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    birthdate: datetime
    address: str = Field(max_length=255)

    participations: list["Participation"] = Relationship(back_populates="user")


class Organization(Model, table=True):
    name: str = Field(max_length=255)

    events: list["Event"] = Relationship(back_populates="organization")
