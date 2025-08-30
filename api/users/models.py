from datetime import datetime

from sqlmodel import Relationship

from api.common.db.models import TimedModel


class User(TimedModel, table=True):
    firstname: str
    lastname: str
    birthdate: datetime
    address: str


class Organization(TimedModel, table=True):
    name: str

    events: list["Event"] = Relationship(back_populates="organization")
