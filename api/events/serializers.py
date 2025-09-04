from sqlmodel_serializers import SQLModelSerializer

from events.models import Event, Representation, Offer, OfferType


class EventLightSerializer(SQLModelSerializer):
    id: str

    class Meta:
        model = Event
        omit = ("organization_id", "organization", "created_at", "updated_at")


class RepresentationLightSerializer(SQLModelSerializer):
    id: str
    event: EventLightSerializer

    class Meta:
        model = Representation
        omit = ("inventories", "participations", "created_at", "updated_at", "event_id")


class OfferTypeLightSerializer(SQLModelSerializer):
    class Meta:
        model = OfferType
        fields = ("label",)


class OfferLightSerializer(SQLModelSerializer):
    id: str
    type: OfferTypeLightSerializer

    class Meta:
        model = Offer
        fields = ("id", "name", "type")
