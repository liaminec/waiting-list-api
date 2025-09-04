from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, exists, select, func

from common.db.utils import get_instance_by_id
from common.db.utils import create
from common.dependencies import get_session
from events.models import Inventory, Offer, Representation
from participations.models import Participation
from participations.serializers import (
    ParticipationPostSerializer,
    WaitingListRankSerializer,
    ParticipationSerializer,
    CheckWaitingListRankSerializer,
    ParticipationPostLightSerializer,
)

router = APIRouter(prefix="/participations")


def participation_check(
    user_id: UUID,
    offer_id: str,
    representation_id: str,
    quantity: int,
    session: Session,
) -> tuple[Offer, Representation]:
    """
    Check that a participation for the given data has not already been created,
    then checks the existence of the requested offer and representation, and that the
    desired quantity does not exceed the limit per offer.
    :param user_id: Id of the user for whom the participation should be added
    :param offer_id: Id for the offer to purchase
    :param representation_id: Id of the representation for which a prestation is bought
    :param quantity: Number of items desired
    :param session: An active session to a database
    :return: The offer and the representation for which a participation is desired
    """
    existing_participations = session.query(
        exists(Participation).where(
            Participation.user_id == user_id,
            Participation.representation_id == representation_id,
            Participation.offer_id == offer_id,
        )
    ).scalar()
    if existing_participations:
        raise HTTPException(
            status_code=500, detail="Your participation has already been acknowledged"
        )
    offer = get_instance_by_id(Offer, offer_id, session)
    if not offer:
        raise HTTPException(
            status_code=404, detail="The requested offer does not exist"
        )
    representation = get_instance_by_id(Representation, representation_id, session)
    if not representation:
        raise HTTPException(
            status_code=404, detail="The requested representation does not exist"
        )
    if offer.event_id != representation.event_id:
        raise HTTPException(
            status_code=500,
            detail=(
                "The requested offer does not apply to the requested representation, "
                "they are not part of the same event"
            ),
        )
    if quantity > offer.max_quantity_per_order:
        raise HTTPException(
            status_code=500,
            detail=(
                "Your order exceeds the maximum quantity allowed for this item\n"
                f"Maximum quantity per order: {offer.max_quantity_per_order}"
            ),
        )
    return offer, representation


# WAITING LIST


@router.post(
    "/join-waiting-list", response_model=ParticipationSerializer, status_code=201
)
def join_waiting_list(
    data: ParticipationPostSerializer, session: Session = Depends(get_session)
):
    """
    Api route to join the waiting list for a given user, offer, representation
    and quantity
    """
    data_dict = data.model_dump()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    quantity = data_dict["quantity"]
    offer, _ = participation_check(
        data_dict["user_id"], offer_id, representation_id, quantity, session
    )
    try:
        available_stock = session.exec(
            select(Inventory.available_stock).where(
                Inventory.offer_id == offer_id,
                Inventory.representation_id == representation_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail="The requested item is not available for this representation",
        )
    if available_stock > 0:
        raise HTTPException(
            status_code=403,
            detail=(
                "The waiting list for this product is not open yet, "
                f"there are still {available_stock} units available"
            ),
        )
    participation = Participation(
        wait_list=True, waiting_at=datetime.now(), **data_dict
    )
    participation = create(participation, session)
    return participation


@router.post("/leave-waiting-list")
def leave_waiting_list(
    data: ParticipationPostLightSerializer, session: Session = Depends(get_session)
):
    """
    Api route to leave the waiting list for a given user, offer and representation
    """
    data_dict = data.model_dump()
    try:
        participation = session.exec(
            select(Participation).where(
                Participation.user_id == data_dict["user_id"],
                Participation.representation_id == data_dict["representation_id"],
                Participation.offer_id == data_dict["offer_id"],
                Participation.wait_list == True,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="You are not in the waiting list")
    session.delete(participation)
    session.commit()
    return JSONResponse(
        content="The user has successfully been removed from the waiting list",
        status_code=200,
    )


@router.post(
    "/check-waiting-status", response_model=WaitingListRankSerializer, status_code=200
)
def check_waiting_status(
    data: CheckWaitingListRankSerializer, session: Session = Depends(get_session)
):
    """
    Api route to check the position of a user on the waiting list for a given offer
    and reprensation
    """
    data_dict = data.model_dump()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    # Fetching the waiting list participation
    try:
        participation = session.exec(
            select(Participation).where(
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id,
                Participation.user_id == data_dict["user_id"],
                Participation.wait_list == True,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail="You are not in the waiting list for this product",
        )
    # Get the total number of participations in the waiting list for the offer
    # and representation, and the user's position
    total = session.exec(
        select(func.count())
        .select_from(Participation)
        .where(
            Participation.wait_list == True,
            Participation.representation_id == representation_id,
            Participation.offer_id == offer_id,
        )
    ).one()
    position = session.exec(
        select(func.count())
        .select_from(Participation)
        .where(
            Participation.wait_list == True,
            Participation.representation_id == representation_id,
            Participation.offer_id == offer_id,
            Participation.waiting_at <= participation.waiting_at,
        )
    ).one()
    return WaitingListRankSerializer(
        user=participation.user,
        representation=participation.representation,
        offer=participation.offer,
        position=position,
        total=total,
    )


# REGULAR PARTICIPATION


@router.post("/join-event", response_model=ParticipationSerializer, status_code=201)
def join_event(
    data: ParticipationPostSerializer, session: Session = Depends(get_session)
):
    """
    API route to make a user join an event for a given offer and representation
    """
    data_dict = data.model_dump()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    quantity = data_dict["quantity"]
    offer, _ = participation_check(
        data_dict["user_id"], offer_id, representation_id, quantity, session
    )
    try:
        inventory = session.exec(
            select(Inventory).where(
                Inventory.offer_id == offer_id,
                Inventory.representation_id == representation_id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail="The requested item is not available for this representation",
        )
    if inventory.available_stock == 0:
        raise HTTPException(
            status_code=500,
            detail=(
                "This item is out of order for the chosen representation, "
                "try another offer or join the waiting list"
            ),
        )
    if inventory.available_stock < quantity:
        raise HTTPException(
            status_code=500,
            detail=(
                "There is not enough stock left for your order.\n"
                f"Number of items available: {inventory.available_stock}"
            ),
        )
    participation = Participation(
        confirmed=True, confirmed_at=datetime.now(), **data_dict
    )
    session.add(participation)
    inventory.available_stock = inventory.available_stock - quantity
    session.add(inventory)
    session.commit()
    ParticipationSerializer.model_validate(participation)
    return participation


@router.post("/cancel")
def cancel(
    data: ParticipationPostLightSerializer, session: Session = Depends(get_session)
):
    """
    API route to cancel the confirmed participation of a user to an event for a
    given offer and representation.
    Upon cancel, the inventory is replenished for the number of items associated with
    the participations and users on top of the waiting list wishing for an available
    quantity are set to pending (it will require validation within 1h or be canceled)
    """
    data_dict = data.model_dump()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    try:
        participation = session.exec(
            select(Participation).where(
                Participation.user_id == data_dict["user_id"],
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id,
                Participation.confirmed == True,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=(
                "No participation were found for this "
                "representation for this specific offer"
            ),
        )
    inventory = session.exec(
        select(Inventory).where(
            Inventory.offer_id == offer_id,
            Inventory.representation_id == representation_id,
        )
    ).one()
    quantity = participation.quantity
    session.delete(participation)
    #  Get the first in waiting list according to available stock
    #  and set his status to pending while tickets are still available for the
    # demands in the waiting list
    # A task triggered by an event sent to a queue would be better though
    now = datetime.now()
    while quantity > 0:
        first_waiting = session.exec(
            select(Participation)
            .where(
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id,
                Participation.quantity <= quantity,
                Participation.wait_list == True,
            )
            .order_by(Participation.waiting_at)
        ).first()
        if not first_waiting:
            break
        first_waiting.pending = True
        first_waiting.wait_list = False
        first_waiting.pending_at = now
        session.add(first_waiting)
        session.commit()
        # If not all the tickets are gone, we can still try to find if they
        # can still be sold to someone else on the waiting list
        quantity = quantity - first_waiting.quantity
        # Here there should be an email notification to the user
    if quantity > 0:
        inventory.available_stock += quantity
    session.commit()

    return JSONResponse(content="Your participation has been canceled", status_code=200)


# PENDING PARTICIPATION


@router.post("/confirm", response_model=ParticipationSerializer)
def confirm(
    data: ParticipationPostLightSerializer, session: Session = Depends(get_session)
):
    """
    API route to confirm a pending (i.e. that just got out of the waiting list)
    participation for a user, for a given offer and representation.
    If the delay between being set to pending and confirmation exceeds 1 hour, no
    confirmation is possible and the participation is canceled.
    Otherwise the participation is confirmed.
    """
    now = datetime.now()
    data_dict = data.model_dump()
    representation_id = data_dict["representation_id"]
    offer_id = data_dict["offer_id"]
    try:
        participation = session.exec(
            select(Participation).where(
                Participation.representation_id == representation_id,
                Participation.offer_id == offer_id,
                Participation.user_id == data_dict["user_id"],
                Participation.pending == True,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=(
                "You have no participation to confirm "
                "for this item on this representation"
            ),
        )
    # Let's say that the user has 1 hour to confirm his presence
    if (now - participation.pending_at).seconds / 3600 > 1:
        raise HTTPException(
            status_code=403,
            detail=(
                "You have exceeded the 1 hour confirmation window, "
                "you have lost your place in the waiting line"
            ),
        )
    participation.confirmed = True
    participation.pending = False
    participation.confirmed_at = now
    session.add(participation)
    session.commit()
    return participation
