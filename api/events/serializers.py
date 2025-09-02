from sqlmodel_serializers import SQLModelSerializer

from events.models import Event, Representation, Offer


class EventLightSerializer(SQLModelSerializer):
    class Meta:
        model = Event
        omit = ("organization_id", "organization", "created_at", "updated_at")


class RepresentationLightSerializer(SQLModelSerializer):
    event: EventLightSerializer

    class Meta:
        model = Representation
        omit = ("inventories", "participations", "created_at", "updated_at")


class OfferLightSerializer(SQLModelSerializer):
    type_label: str

    class Meta:
        model = Offer
        fields = ("name", "description", "type_label")
