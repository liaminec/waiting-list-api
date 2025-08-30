from datetime import datetime
from uuid import UUID

from sqlmodel import Field, Relationship

from api.common.db.models import TimedModel, Model
from api.users.models import Organization


class Event(TimedModel, table=True):
    title: str = Field(max_length=255)
    description: str = Field(max_length=500)
    thumbnail_url: str
    venue_name: str = Field(max_length=500)
    venue_address: str

    organization_id: UUID = Field(foreign_key="organization.id")
    organization: Organization = Relationship(back_populates="events")

