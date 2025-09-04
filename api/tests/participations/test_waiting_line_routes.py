from datetime import datetime

import freezegun
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from events.models import Offer, Representation, Inventory
from participations.models import Participation
from tests.utils import session_add
from users.models import User


@pytest.mark.usefixtures("inventories")
@freezegun.freeze_time(datetime(2025, 1, 1))
def test_join_waiting_list_ok(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        offer = offers[0]
        representation = representations[0]
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "confirmed": False,
            "pending": False,
            "wait_list": True,
            "quantity": 1,
            "confirmed_at": None,
            "pending_at": None,
            "waiting_at": datetime(2025, 1, 1).isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
            },
            "representation": {
                "id": representation.id,
                "start_datetime": representation.start_datetime.isoformat(),
                "end_datetime": representation.end_datetime.isoformat(),
                "event": {
                    "id": representation.event.id,
                    "title": representation.event.title,
                    "description": representation.event.description,
                    "thumbnail_url": representation.event.thumbnail_url,
                    "venue_name": representation.event.venue_name,
                    "venue_address": representation.event.venue_address,
                    "timezone": representation.event.timezone,
                },
            },
            "offer": {
                "id": offer.id,
                "name": offer.name,
                "type": {"label": offer.type.label},
            },
        }
        participation = session.exec(
            select(Participation).where(
                Participation.user_id == user.id,
                Participation.representation_id == representation.id,
                Participation.offer_id == offer.id,
            )
        ).one()
        assert participation.wait_list
        assert not participation.confirmed
        assert not participation.pending
        assert participation.waiting_at == datetime(2025, 1, 1)
        assert not participation.confirmed_at
        assert not participation.pending_at
        assert participation.quantity == 1


def test_join_waitlist_stock_available(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
    inventories: list[Inventory],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        session_add(session, inventories)
        user = users[0]
        offer = offers[2]
        representation = representations[2]
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "The waiting list for this product is not open yet, "
            f"there are still {inventories[2].available_stock} units available"
        )


@pytest.mark.usefixtures("inventories")
def test_join_participation_already_exists(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        offer = offers[0]
        representation = representations[0]
        participation = Participation(
            user_id=user.id,
            offer_id=offer.id,
            representation_id=representation.id,
            confirmed=True,
            quantity=1,
        )
        session.add(participation)
        session.commit()
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 500
        assert response.json()["detail"] == (
            "Your participation has " "already been acknowledged"
        )
        session.refresh(participation)
        assert not participation.wait_list
        assert participation.confirmed


@pytest.mark.usefixtures("inventories")
def test_join_offer_does_not_exists(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        representation = representations[0]
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": "nonexistent",
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "The requested offer does not exist"
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == "nonexistent",
                    Participation.representation_id == representation.id,
                )
            ).one()


@pytest.mark.usefixtures("inventories")
def test_join_representation_does_not_exists(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        offer = offers[0]
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": "nonexistent",
                "quantity": 1,
            },
        )
        assert response.status_code == 404
        assert (
            response.json()["detail"] == "The requested representation does not exist"
        )
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == "nonexistent",
                )
            ).one()


def test_join_quantity_exceeds(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
    inventories: list[Inventory],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        session_add(session, inventories)
        user = users[0]
        offer = offers[0]
        representation = representations[0]
        response = client.post(
            "/participations/join-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 100,
            },
        )
        assert response.status_code == 500
        assert response.json()["detail"] == (
            "Your order exceeds the maximum quantity allowed for this item\n"
            f"Maximum quantity per order: {offer.max_quantity_per_order}"
        )
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == representation.id,
                )
            ).one()


@pytest.mark.usefixtures("inventories")
def test_leave_waiting_list_ok(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        offer = offers[0]
        representation = representations[0]
        participation = Participation(
            user_id=user.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime.now(),
            quantity=1,
        )
        session.add(participation)
        session.commit()
        response = client.post(
            "/participations/leave-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 200
        assert response.json() == (
            "The user has successfully been " "removed from the waiting list"
        )
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == representation.id,
                    Participation.wait_list == True,
                )
            ).one()


@pytest.mark.usefixtures("inventories")
def test_leave_waiting_list_not_in_list(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user = users[0]
        offer = offers[0]
        representation = representations[0]
        response = client.post(
            "/participations/leave-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "You are not in the waiting list"
        participation = Participation(
            user_id=user.id,
            offer_id=offer.id,
            representation_id=representation.id,
            confirmed=True,
            confirmed_at=datetime.now(),
            quantity=1,
        )
        session.add(participation)
        session.commit()
        response = client.post(
            "/participations/leave-waiting-list",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "You are not in the waiting list"


@pytest.mark.usefixtures("inventories")
def test_check_waiting_status(
    client: TestClient,
    test_engine: Engine,
    users: list[User],
    offers: list[Offer],
    representations: list[Representation],
) -> None:
    with Session(test_engine) as session:
        session_add(session, users)
        session_add(session, offers)
        session_add(session, representations)
        user1, user2, user3 = users
        offer = offers[0]
        representation = representations[0]
        participation0 = Participation(
            user_id=user1.id,
            offer_id=offer.id,
            representation_id=representation.id,
            confirmed=True,
            confirmed_at=datetime(2025, 1, 1),
            quantity=1,
        )
        participation1 = Participation(
            user_id=user2.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime(2025, 1, 2),
            quantity=1,
        )
        participation2 = Participation(
            user_id=user3.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime(2025, 1, 2, 10),
            quantity=1,
        )
        session.add(participation0)
        session.add(participation1)
        session.add(participation2)
        session.commit()
        # First in waiting list
        response = client.post(
            "/participations/check-waiting-status",
            json={
                "user_id": str(user2.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "user": {
                "id": str(user2.id),
                "email": user2.email,
                "firstname": user2.firstname,
                "lastname": user2.lastname,
            },
            "representation": {
                "id": representation.id,
                "start_datetime": representation.start_datetime.isoformat(),
                "end_datetime": representation.end_datetime.isoformat(),
                "event": {
                    "id": representation.event.id,
                    "title": representation.event.title,
                    "description": representation.event.description,
                    "thumbnail_url": representation.event.thumbnail_url,
                    "venue_name": representation.event.venue_name,
                    "venue_address": representation.event.venue_address,
                    "timezone": representation.event.timezone,
                },
            },
            "offer": {
                "id": offer.id,
                "name": offer.name,
                "type": {"label": offer.type.label},
            },
            "position": 1,
            "total": 2,
        }
        # Second in waiting list
        response = client.post(
            "/participations/check-waiting-status",
            json={
                "user_id": str(user3.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "user": {
                "id": str(user3.id),
                "email": user3.email,
                "firstname": user3.firstname,
                "lastname": user3.lastname,
            },
            "representation": {
                "id": representation.id,
                "start_datetime": representation.start_datetime.isoformat(),
                "end_datetime": representation.end_datetime.isoformat(),
                "event": {
                    "id": representation.event.id,
                    "title": representation.event.title,
                    "description": representation.event.description,
                    "thumbnail_url": representation.event.thumbnail_url,
                    "venue_name": representation.event.venue_name,
                    "venue_address": representation.event.venue_address,
                    "timezone": representation.event.timezone,
                },
            },
            "offer": {
                "id": offer.id,
                "name": offer.name,
                "type": {"label": offer.type.label},
            },
            "position": 2,
            "total": 2,
        }
        # Not in waiting list
        response = client.post(
            "/participations/check-waiting-status",
            json={
                "user_id": str(user1.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "You are not in the waiting " "list for this product"
        )
