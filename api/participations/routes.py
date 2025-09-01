from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, exists, select, delete, func

from api.common.db.utils import create
from api.config import engine
from api.events.models import Inventory
from api.participations.models import Participation
from api.participations.serializers import ParticipationPostSerializer, \
    WaitingListRankSerializer

router = APIRouter(prefix="participations")


@router.post("join-waiting-list")
def join_waiting_list(data: ParticipationPostSerializer):
    data_dict = data.dict()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    with Session(engine) as session:
        # Checking that the user is not already taking part in the event
        existing_participations = session.exec(
            exists().where(
                Participation.user_id == data_dict["user_id"],
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id
            )
        )
        if existing_participations:
            raise HTTPException(
                status_code=500,
                detail="Your participation has already been acknowledged"
            )
        available_stock = session.exec(
            select(Inventory.available_stock).where(
                Inventory.offer_id == offer_id,
                Inventory.representation_id == representation_id
            )
        )
        if available_stock > 0:
            raise HTTPException(
                status_code=403,
                detail=(
                    "The waiting list for this product is not open yet, "
                    f"there are still {available_stock} units available"
                )
            )
        participation = Participation(
            wait_list=True, wating_at=datetime.now(), **data_dict
        )
        create(participation, session)
        return Response(
            "The user has successfully been added to the waiting list", status_code=201
        )


@router.post("leave-waiting-list")
def leave_waiting_list(data: ParticipationPostSerializer):
    data_dict = data.dict()
    with Session(engine) as session:
        try:
            session.exec(
                delete(Participation).where(
                    Participation.user_id == data_dict["user_id"],
                    Participation.representation_id == data_dict["representation_id"],
                    Participation.offer_id == data_dict["offer_id"],
                    Participation.wait_list == True
                )
            )
        except NoResultFound:
            raise HTTPException(
                status_code=404, detail="You are not in the waiting list"
            )
    return Response(
        "The user has successfully been removed from the waiting list", status_code=204
    )


@router.post("check-waiting-status")
def check_waiting_status(data: ParticipationPostSerializer):
    data_dict = data.dict()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    with Session(engine) as session:
        # Fetching the waiting list participation
        try:
            participation = session.exec(
                select(Participation).where(
                    Participation.representation_id == representation_id,
                    Participation.offer_id == offer_id,
                    Participation.user_id == data_dict["user_id"],
                    Participation.wait_list == True
                )
            )
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail="You are not in the waiting list for this product"
            )
        # Get the position
        total, position = session.query(
            select(
                func.count(Participation).filter(
                    Participation.wait_list == True,
                    Participation.representation_id == representation_id,
                    Participation.offer_id == offer_id
                ),
                func.count(Participation).filter(
                    Participation.wait_list == True,
                    Participation.representation_id == representation_id,
                    Participation.offer_id == offer_id,
                    Participation.waiting_at >= participation.waiting_at
                )
            )
        ).scalar()
        return Response(
            WaitingListRankSerializer(
                user=participation.user,
                representation=participation.representation,
                offer=participation.offer,
                position=position,
                total=total
            ).dict(),
            status_code=200
        )
