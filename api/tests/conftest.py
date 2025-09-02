from datetime import datetime

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, text, create_engine

from app import app
from events.models import Event, Representation
from users.models import User, Organization


@pytest.fixture
def test_engine() -> Engine:
    return create_engine("sqlite:///data/db/test-database", echo=True)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def users(test_engine: Engine) -> list[User]:
    with Session(test_engine) as session:
        user1 = User(
            email="user1@test.com",
            firstname="User1",
            lastname="Test",
            birthdate=datetime(1994, 1, 1),
            address="test"
        )
        user2 = User(
            email="user2@test.com",
            firstname="User2",
            lastname="Test",
            birthdate=datetime(1994, 2, 1),
            address="test"
        )
        session.add(user1)
        session.add(user2)
        session.commit()
        return [user1, user2]


@pytest.fixture
def organization(test_engine: Engine) -> Organization:
    with Session(test_engine) as session:
        organization = Organization(name="BILLY")
        session.add(organization)
        session.commit()
        return organization


@pytest.fixture
def events(test_engine: Engine, organization: Organization) -> list[Event]:
    with Session(test_engine) as session:
        event1 = Event(
            id="ev_001",
            title="Jazz Festival 2025",
            description="Annual jazz festival featuring world-class musicians",
            thumbnail_url="https://example.com/jazz.jpg",
            organization_id=organization.id,
            venue_name="Olympia",
            venue_address="48 Rue de l'olympia",
            timezone="Europe/Paris"
        )
        event2 = Event(
            id="ev_002",
            title="Rock Concert",
            description="High-energy rock performance",
            thumbnail_url="https://example.com/rock.jpg",
            organization_id=organization.id,
            venue_name="Le Zénith",
            venue_address="15 rue de la fiesta",
            timezone="Europe/Paris"
        )
        event3 = Event(
            id="ev_003",
            title="Classical Evening",
            description="Elegant classical music concert",
            thumbnail_url="https://example.com/classical.jpg",
            organization_id=organization.id,
            venue_name="Paris MK2",
            venue_address="7 quai de la Loire",
            timezone="Europe/Paris"
        )
        session.add(event1)
        session.add(event2)
        session.add(event3)
        session.commit()
        return [event1, event2, event3]


@pytest.fixture
def representations(test_engine: Engine, events: list[Event]) -> list[Representation]:
    event1, event2, event3 = events
    with Session(test_engine) as session:
        representation1 = Representation(
            id="rep_001",
            event_id=event1.id,
            start_datetime=datetime(2025, 7, 15, 20),
            end_datetime=datetime(2025, 7, 15, 23)
        )
        representation2 = Representation(
            id="rep_002",
            event_id=event1.id,
            start_datetime=datetime(2025, 7, 16, 20),
            end_datetime=datetime(2025, 7, 16, 23)
        )
        representation3 = Representation(
            id="rep_003",
            event_id=event1.id,
            start_datetime=datetime(2025, 7, 17, 20),
            end_datetime=datetime(2025, 7, 17, 23)
        )
        representation4 = Representation(
            id="rep_004",
            event_id=event2.id,
            start_datetime=datetime(2025, 8, 10, 19, 30),
            end_datetime=datetime(2025, 8, 10, 22, 30)
        )
        representation5 = Representation(
            id="rep_005",
            event_id=event2.id,
            start_datetime=datetime(2025, 8, 11, 19, 30),
            end_datetime=datetime(2025, 8, 11, 22, 30)
        )
        representation6 = Representation(
            id="rep_006",
            event_id=event3.id,
            start_datetime=datetime(2025, 9, 5, 19),
            end_datetime=datetime(2025, 9, 5, 21, 30)
        )
        session.add(representation1)
        session.add(representation2)
        session.add(representation3)
        session.add(representation4)
        session.add(representation5)
        session.add(representation6)
        session.commit()
        return [
            representation1,
            representation2,
            representation3,
            representation4,
            representation5,
            representation6,
        ]


@pytest.fixture(autouse=True)
def clear_db(test_engine: Engine) -> None:
    yield
    with Session(test_engine) as session:
        session.execute(text("DELETE FROM participation"))
        session.execute(text("DELETE FROM inventory"))
        session.execute(text("DELETE FROM offer"))
        session.execute(text("DELETE FROM offer_type"))
        session.execute(text("DELETE FROM representation"))
        session.execute(text("DELETE FROM event"))
        session.execute(text("DELETE FROM organization"))
        session.execute(text("DELETE FROM user"))