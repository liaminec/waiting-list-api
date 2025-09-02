from pydantic import BaseModel
from sqlmodel_serializers import SQLModelSerializer

from events.serializers import RepresentationLightSerializer, OfferLightSerializer
from participations.models import Participation
from users.serializers import UserLightSerializer


class ParticipationPostSerializer(SQLModelSerializer):
    class Meta:
        model = Participation
        fields = ("user_id", "representation_id", "offer_id")


class WaitingListRankSerializer(BaseModel):
    user: UserLightSerializer
    representation: RepresentationLightSerializer
    offer: OfferLightSerializer
    position: int
    total: int
