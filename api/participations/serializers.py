from uuid import UUID

from pydantic import BaseModel, validator
from sqlmodel_serializers import SQLModelSerializer

from events.serializers import RepresentationLightSerializer, OfferLightSerializer
from participations.models import Participation
from users.serializers import UserLightSerializer


class ParticipationSerializer(SQLModelSerializer):
    user: UserLightSerializer | None = None
    offer: OfferLightSerializer
    representation: RepresentationLightSerializer

    class Meta:
        model = Participation
        omit = ("id", "offer_id", "representation_id", "user_id")


class ParticipationPostSerializer(SQLModelSerializer):
    class Meta:
        model = Participation
        fields = ("user_id", "representation_id", "offer_id", "quantity")

    @classmethod
    @validator("quantity")
    def validate_quantity_strict_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Quantity must be strictly positive")
        return value


class CheckWaitingListRankSerializer(SQLModelSerializer):
    class Meta:
        model = Participation
        fields = ("user_id", "representation_id", "offer_id")


class ParticipationPostLightSerializer(SQLModelSerializer):
    class Meta:
        model = Participation
        fields = ("user_id", "representation_id", "offer_id")


class WaitingListRankSerializer(BaseModel):
    user: UserLightSerializer
    representation: RepresentationLightSerializer
    offer: OfferLightSerializer
    position: int
    total: int
