from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, exists, select, delete, func

from common.db.utils import create
from config import engine
from events.models import Inventory
from participations.models import Participation
from participations.serializers import (
    ParticipationPostSerializer,
    WaitingListRankSerializer,
)

router = APIRouter(prefix="/participations")


# WAITING LIST

@router.post("/join-waiting-list")
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


@router.post("/leave-waiting-list")
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


@router.post("/check-waiting-status")
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


# REGULAR PARTICIPATION

@router.post("/join-event", response_model=Participation)
def join_event(data: ParticipationPostSerializer):
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
        inventory = session.exec(
            select(Inventory).where(
                Inventory.offer_id == offer_id,
                Inventory.representation_id == representation_id
            )
        ).one()
        if inventory.available_stock == 0:
            raise HTTPException(
                status_code=403,
                detail=(
                    "This item is out of order for the chosen representation, "
                    f"try another offer or join the waiting list"
                )
            )
        participation = Participation(
            confirmed=True, confirmed_at=datetime.now(), **data_dict
        )
        session.add(participation)
        inventory.available_stock = inventory.available_stock - 1
        session.add(inventory)
        session.commit()
        return participation


@router.post("/cancel")
def cancel(data: ParticipationPostSerializer):
    data_dict = data.dict()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    with Session(engine) as session:
        try:
            session.exec(
                delete(Participation).where(
                    Participation.user_id == data_dict["user_id"],
                    Participation.representation_id == representation_id,
                    Participation.offer_id == offer_id,
                    Participation.confirmed == True
                )
            )
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No participation were found for this "
                    "representation for this specific offer"
                )
            )
        #  Get the first in waiting list and set his status to pending
        # An async task sent to a queue would be better
        first_waiting = session.exec(
            select(Participation)
            .where(
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id,
                Participation.wait_list == True
            )
            .order_by(Participation.waiting_at.desc())
        ).first()
        if first_waiting:
            first_waiting.pending = True
            first_waiting.waiting_list = False
            first_waiting.pending_at = datetime.now()
            session.add(first_waiting)
            session.commit()
            # Here there should be an email notification to the user
        return Response("Your participation has been canceled", status_code=204)


# PENDING PARTICIPATION

@router.post("/confirm", response_model=Participation)
def confirm(data: ParticipationPostSerializer):
    now = datetime.now()
    data_dict = data.dict()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    with Session(engine) as session:
        try:
            participation = session.exec(
                select(Participation)
                .where(
                    Participation.representation_id == representation_id,
                    Participation.offer_id == offer_id,
                    Participation.user_id == data_dict["user_id"],
                    Participation.pending == True
                )
            ).one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail=(
                    "You have no participation to confirm "
                    "for this item on this representation"
                )
            )
        # Let's say that the user has 1 hour to confirm his presence
        if (now - participation.pending_at)/3600 > 1:
            raise HTTPException(
                status_code=403,
                detail=(
                    "You have exceeded the 1 hour confirmation window, "
                    "you have lost your place in the waiting line"
                )
            )
        participation.confirmed = True
        participation.pending = False
        participation.confirmed_at = now
        session.add(participation)
        session.commit()
        return participation
