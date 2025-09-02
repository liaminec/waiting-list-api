from sqlmodel_serializers import SQLModelSerializer

from users.models import User


class UserSerializer(SQLModelSerializer):
    class Meta:
        model = User
        omit = ("created_at", "updated_at")


class UserLightSerializer(SQLModelSerializer):
    class Meta:
        model = User
        fields = ("id", "firstname", "lastname")
