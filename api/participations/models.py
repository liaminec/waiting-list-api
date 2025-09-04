from datetime import datetime
from uuid import UUID

from sqlmodel import Field, Relationship

from common.db.models import Model
from events.models import Representation, Offer
from users.models import User


class Participation(Model, table=True):
    confirmed: bool = Field(default=False)
    pending: bool = Field(default=False)
    wait_list: bool = Field(default=False)
    quantity: int
    confirmed_at: datetime | None = Field(default=None)
    pending_at: datetime | None = Field(default=None)
    waiting_at: datetime | None = Field(default=None)

    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="participations")
    offer_id: str = Field(foreign_key="offer.id")
    offer: Offer = Relationship(back_populates="participations")
    representation_id: str = Field(foreign_key="representation.id")
    representation: Representation = Relationship(back_populates="participations")
