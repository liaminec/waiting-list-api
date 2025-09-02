from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Relationship, SQLModel, Field

from common.db.models import Model


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    birthdate: datetime
    address: str = Field(max_length=255)

    participations: list["Participation"] = Relationship(back_populates="user")


class Organization(Model, table=True):
    name: str = Field(max_length=255)

    events: list["Event"] = Relationship(back_populates="organization")
