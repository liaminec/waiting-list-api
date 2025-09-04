from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, or_

from common.db.utils import get_instance_by_id
from config import engine
from events.models import Event, Representation
from participations.models import Participation

router = APIRouter(prefix="/events")


@router.get("/", response_model=list[Event])
def get_events():
    with Session(engine) as session:
        events = session.exec(select(Event))
        return events


@router.get("/{pk}", response_model=Event)
def get_event_by_pk(pk: str):
    with Session(engine) as session:
        event = get_instance_by_id(Event, pk, session)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found.")
        return event


@router.get("/{pk}/representations", response_model=list[Representation])
def get_representations_for_event(pk: str):
    with Session(engine) as session:
        representations = session.exec(
            select(Representation).where(Representation.event_id == pk)
        )
        return representations


@router.get("/representations/{pk}", response_model=Representation)
def get_representation(pk: str):
    with Session(engine) as session:
        representation = get_instance_by_id(Representation, pk, session)
        if not representation:
            raise HTTPException(status_code=404, detail="Representation not found.")


@router.get("/{pk}/participations", response_model=list[Participation])
def get_event_participations(
    pk: str, confirmed: bool = True, pending: bool = False, wait_list: bool = False
):
    with Session(engine) as session:
        participations = session.exec(
            select(Participation).where(
                Participation.representation.event_id == pk,
                or_(
                    Participation.confirmed == confirmed,
                    Participation.pending == pending,
                    Participation.wait_list == wait_list,
                ),
            )
        )
        return participations
