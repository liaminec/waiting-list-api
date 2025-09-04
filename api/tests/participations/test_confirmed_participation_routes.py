from datetime import datetime

import freezegun
import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import NoResultFound, InvalidRequestError
from sqlmodel import Session, select
from starlette.testclient import TestClient

from events.models import Offer, Representation, Inventory
from participations.models import Participation
from tests.utils import session_add
from users.models import User


@freezegun.freeze_time(datetime(2025, 1, 1))
def test_join_event_ok(
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
        inventory = inventories[2]
        initial_available_stock = inventory.available_stock
        response = client.post(
            "/participations/join-event",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 3,
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "confirmed": True,
            "pending": False,
            "wait_list": False,
            "quantity": 3,
            "confirmed_at": datetime(2025, 1, 1).isoformat(),
            "pending_at": None,
            "waiting_at": None,
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
        session.refresh(inventory)
        assert inventory.available_stock == initial_available_stock - 3


@pytest.mark.usefixtures("inventories")
def test_join_event_no_more_stock(
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
            "/participations/join-event",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 3,
            },
        )
        assert response.status_code == 500
        assert response.json()["detail"] == (
            "This item is out of order for the chosen representation, "
            f"try another offer or join the waiting list"
        )
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == representation.id,
                )
            ).one()


def test_join_event_quantity_exceeds_stock(
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
        representation = representations[1]
        inventory = inventories[1]
        initial_available_stock = inventory.available_stock
        response = client.post(
            "/participations/join-event",
            json={
                "user_id": str(user.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
                "quantity": 3,
            },
        )
        assert response.status_code == 500
        assert response.json()["detail"] == (
            "There is not enough stock left for your order.\n"
            f"Number of items available: {initial_available_stock}"
        )
        session.refresh(inventory)
        assert inventory.available_stock == initial_available_stock
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == representation.id,
                )
            ).one()


def test_join_event_participation_already_exists(
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
        representation = representations[1]
        inventory = inventories[1]
        initial_available_stock = inventory.available_stock
        participation = Participation(
            user_id=user.id,
            offer_id=offer.id,
            representation_id=representation.id,
            pending=True,
            quantity=1,
        )
        session.add(participation)
        session.commit()
        response = client.post(
            "/participations/join-event",
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
        session.refresh(inventory)
        assert not participation.confirmed
        assert not participation.confirmed_at
        assert participation.pending
        assert inventory.available_stock == initial_available_stock


def test_join_event_offer_does_not_exist(
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
        representation = representations[1]
        inventory = inventories[1]
        initial_available_stock = inventory.available_stock
        response = client.post(
            "/participations/join-event",
            json={
                "user_id": str(user.id),
                "offer_id": "nonexistent",
                "representation_id": representation.id,
                "quantity": 1,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "The requested offer does not exist"
        session.refresh(inventory)
        assert inventory.available_stock == initial_available_stock
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == "nonexistent",
                    Participation.representation_id == representation.id,
                )
            ).one()


def test_join_event_representation_does_not_exists(
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
        inventory = inventories[1]
        initial_available_stock = inventory.available_stock
        response = client.post(
            "/participations/join-event",
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
        session.refresh(inventory)
        assert inventory.available_stock == initial_available_stock
        with pytest.raises(NoResultFound):
            session.exec(
                select(Participation).where(
                    Participation.user_id == user.id,
                    Participation.offer_id == offer.id,
                    Participation.representation_id == "nonexistent",
                )
            ).one()


@freezegun.freeze_time(datetime(2025, 1, 4))
def test_cancel_with_wait_list(
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
        user1, user2, user3 = users
        offer = offers[0]
        representation = representations[0]
        inventory = inventories[0]
        participation1 = Participation(
            user_id=user1.id,
            offer_id=offer.id,
            representation_id=representation.id,
            confirmed=True,
            confirmed_at=datetime(2025, 1, 1),
            quantity=4,
        )
        participation2 = Participation(
            user_id=user2.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime(2025, 1, 2),
            quantity=2,
        )
        participation3 = Participation(
            user_id=user3.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime(2025, 1, 3),
            quantity=1,
        )
        session_add(session, [participation1, participation2, participation3])
        session.commit()
        response = client.post(
            "/participations/cancel",
            json={
                "user_id": str(user1.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
            },
        )
        assert response.status_code == 200
        assert response.json() == "Your participation has been canceled"
        session.refresh(inventory)
        assert inventory.available_stock == 1
        with pytest.raises(InvalidRequestError):
            session.refresh(participation1)
        session.refresh(participation2)
        session.refresh(participation3)
        assert not participation2.wait_list
        assert participation2.pending
        assert participation2.pending_at == datetime(2025, 1, 4)
        assert not participation3.wait_list
        assert participation3.pending
        assert participation3.pending_at == datetime(2025, 1, 4)


def test_cancel_no_wait_list() -> None:
    @freezegun.freeze_time(datetime(2025, 1, 4))
    def test_cancel_with_wait_list(
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
            user1, user2, user3 = users
            offer = offers[0]
            representation = representations[0]
            inventory = inventories[0]
            participation1 = Participation(
                user_id=user1.id,
                offer_id=offer.id,
                representation_id=representation.id,
                confirmed=True,
                confirmed_at=datetime(2025, 1, 1),
                quantity=4,
            )
            session.add(participation1)
            session.commit()
            response = client.post(
                "/participations/cancel",
                json={
                    "user_id": str(user1.id),
                    "offer_id": offer.id,
                    "representation_id": representation.id,
                },
            )
            assert response.status_code == 200
            assert response.json() == "Your participation has been canceled"
            session.refresh(inventory)
            assert inventory.available_stock == 4
            with pytest.raises(InvalidRequestError):
                session.refresh(participation1)


def test_cancel_not_participating(
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
        user1, user2, user3 = users
        offer = offers[0]
        representation = representations[0]
        inventory = inventories[0]
        participation2 = Participation(
            user_id=user2.id,
            offer_id=offer.id,
            representation_id=representation.id,
            confirmed=True,
            confirmed_at=datetime(2025, 1, 2),
            quantity=2,
        )
        participation3 = Participation(
            user_id=user3.id,
            offer_id=offer.id,
            representation_id=representation.id,
            wait_list=True,
            waiting_at=datetime(2025, 1, 3),
            quantity=1,
        )
        session_add(session, [participation2, participation3])
        session.commit()
        response = client.post(
            "/participations/cancel",
            json={
                "user_id": str(user1.id),
                "offer_id": offer.id,
                "representation_id": representation.id,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "No participation were found for this "
            "representation for this specific offer"
        )
        session.refresh(inventory)
        assert inventory.available_stock == 0
        session.refresh(participation2)
        session.refresh(participation3)
        assert participation2.confirmed
        assert not participation2.pending
        assert participation3.wait_list
        assert not participation3.pending
