from datetime import datetime

from sqlmodel import Field, Relationship

from common.db.models import Model, ItemModel
from users.models import Organization


class Event(ItemModel, table=True):
    title: str = Field(max_length=255)
    description: str = Field(max_length=500)
    thumbnail_url: str
    venue_name: str = Field(max_length=255)
    venue_address: str = Field(max_length=255)
    timezone: str = Field(max_length=50)

    organization_id: int = Field(foreign_key="organization.id")
    organization: Organization = Relationship(back_populates="events")
    representations: list["Representation"] = Relationship(back_populates="event")
    offers: list["Offer"] = Relationship(back_populates="event")


class Representation(ItemModel, table=True):
    start_datetime: datetime
    end_datetime: datetime

    event_id: str = Field(foreign_key="event.id")
    event: Event = Relationship(back_populates="representations")
    inventories: list["Inventory"] = Relationship(back_populates="representation")
    participations: list["Participation"] = Relationship(
        back_populates="representation"
    )


class OfferType(Model, table=True):
    label: str = Field(max_length=128)

    offers: list["Offer"] = Relationship(back_populates="type")


class Offer(ItemModel, table=True):
    name: str = Field(max_length=255)
    max_quantity_per_order: int
    description: str = Field(max_length=500)

    event_id: str = Field(foreign_key="event.id")
    event: Event = Relationship(back_populates="offers")
    type_id: int = Field(foreign_key="offertype.id")
    type: OfferType = Relationship(back_populates="offers")
    inventories: list["Inventory"] = Relationship(back_populates="offer")
    participations: list["Participation"] = Relationship(back_populates="offer")


class Inventory(ItemModel, table=True):
    total_stock: int
    available_stock: int

    offer_id: str = Field(foreign_key="offer.id")
    offer: Offer = Relationship(back_populates="inventories")
    representation_id: str = Field(foreign_key="representation.id")
    representation: Representation = Relationship(back_populates="inventories")
