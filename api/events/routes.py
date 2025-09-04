from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, or_

from common.db.utils import get_instance_by_id
from common.dependencies import get_session
from events.models import Event, Representation, Offer
from participations.models import Participation
from participations.serializers import ParticipationSerializer
from users.models import User

router = APIRouter(prefix="/events")


@router.get("/", response_model=list[Event])
def get_events(session: Session = Depends(get_session)):
    events = session.exec(select(Event)).all()
    return events


@router.get("/{pk}", response_model=Event)
def get_event_by_pk(pk: str, session: Session = Depends(get_session)):
    event = get_instance_by_id(Event, pk, session)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


@router.get("/{pk}/representations", response_model=list[Representation])
def get_representations_for_event(pk: str, session: Session = Depends(get_session)):
    representations = session.exec(
        select(Representation).where(Representation.event_id == pk)
    ).all()
    return representations


@router.get("/representations/{pk}", response_model=Representation)
def get_representation(pk: str, session: Session = Depends(get_session)):
    representation = get_instance_by_id(Representation, pk, session)
    if not representation:
        raise HTTPException(status_code=404, detail="Representation not found.")


@router.get("/{pk}/participations", response_model=list[ParticipationSerializer])
def get_event_participations(
    pk: str, list_filter: str | None = None, session: Session = Depends(get_session)
):
    if list_filter not in ("confirmed", "pending", "wait_list"):
        participations = session.exec(
            select(Participation, Offer, Representation, User)
            .join(Representation)
            .join(Offer)
            .where(
                Representation.event_id == pk,
            )
        ).all()
    else:
        participations = session.exec(
            select(Participation)
            .join(Representation)
            .join(Offer)
            .where(
                Representation.event_id == pk,
                or_(getattr(Participation, list_filter) == True),
            )
        ).all()
    return participations
