from datetime import datetime

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, text, create_engine

from app import app
from events.models import Event, Representation, OfferType, Offer, Inventory
from tests.utils import session_add
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
            address="test",
        )
        user2 = User(
            email="user2@test.com",
            firstname="User2",
            lastname="Test",
            birthdate=datetime(1994, 2, 1),
            address="test",
        )
        user3 = User(
            email="user3@test.com",
            firstname="User3",
            lastname="Test",
            birthdate=datetime(1994, 3, 1),
            address="test",
        )
        session.add(user1)
        session.add(user2)
        session.add(user3)
        session.commit()
        return [user1, user2, user3]


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
        session.add(organization)
        event1 = Event(
            id="ev_001",
            title="Jazz Festival 2025",
            description="Annual jazz festival featuring world-class musicians",
            thumbnail_url="https://example.com/jazz.jpg",
            organization_id=organization.id,
            venue_name="Olympia",
            venue_address="48 Rue de l'olympia",
            timezone="Europe/Paris",
        )
        event2 = Event(
            id="ev_002",
            title="Rock Concert",
            description="High-energy rock performance",
            thumbnail_url="https://example.com/rock.jpg",
            organization_id=organization.id,
            venue_name="Le Zénith",
            venue_address="15 rue de la fiesta",
            timezone="Europe/Paris",
        )
        event3 = Event(
            id="ev_003",
            title="Classical Evening",
            description="Elegant classical music concert",
            thumbnail_url="https://example.com/classical.jpg",
            organization_id=organization.id,
            venue_name="Paris MK2",
            venue_address="7 quai de la Loire",
            timezone="Europe/Paris",
        )
        session.add(event1)
        session.add(event2)
        session.add(event3)
        session.commit()
        return [event1, event2, event3]


@pytest.fixture
def representations(test_engine: Engine, events: list[Event]) -> list[Representation]:
    with Session(test_engine) as session:
        session_add(session, events)
        event1, event2, event3 = events
        representation1 = Representation(
            id="rep_001",
            event_id=event1.id,
            start_datetime=datetime(2025, 7, 15, 20),
            end_datetime=datetime(2025, 7, 15, 23),
        )
        representation2 = Representation(
            id="rep_002",
            event_id=event1.id,
            start_datetime=datetime(2025, 7, 16, 20),
            end_datetime=datetime(2025, 7, 16, 23),
        )
        representation3 = Representation(
            id="rep_003",
            event_id=event2.id,
            start_datetime=datetime(2025, 7, 17, 20),
            end_datetime=datetime(2025, 7, 17, 23),
        )
        session.add(representation1)
        session.add(representation2)
        session.add(representation3)
        session.commit()
        return [representation1, representation2, representation3]


@pytest.fixture
def offer_type(test_engine: Engine) -> OfferType:
    with Session(test_engine) as session:
        offer_type = OfferType(label="ticket")
        session.add(offer_type)
        session.commit()
        return offer_type


@pytest.fixture
def offers(
    test_engine: Engine, offer_type: OfferType, events: list[Event]
) -> list[Offer]:
    with Session(test_engine) as session:
        session.add(offer_type)
        session_add(session, events)
        event1, event2, event3 = events
        offer1 = Offer(
            id="off_001",
            event_id=event1.id,
            name="General Admission",
            type_id=offer_type.id,
            max_quantity_per_order=4,
            description="Standard entry to Jazz Festival",
        )
        offer2 = Offer(
            id="off_002",
            event_id=event1.id,
            name="VIP Package",
            type_id=offer_type.id,
            max_quantity_per_order=2,
            description="Standard entry to Jazz Festival",
        )
        offer3 = Offer(
            id="off_003",
            event_id=event2.id,
            name="Standard Ticket",
            type_id=offer_type.id,
            max_quantity_per_order=6,
            description="Standard entry to Jazz Festival",
        )
        session.add(offer1)
        session.add(offer2)
        session.add(offer3)
        session.commit()

        return [offer1, offer2, offer3]


@pytest.fixture
def inventories(
    test_engine: Engine, offers: list[Offer], representations: list[Representation]
) -> list[Inventory]:
    with Session(test_engine) as session:
        session_add(session, offers)
        session_add(session, representations)
        offer1, offer2, offer3 = offers
        (
            representation1,
            representation2,
            representation3,
        ) = representations
        inventory1 = Inventory(
            id="inv_001",
            offer_id=offer1.id,
            representation_id=representation1.id,
            total_stock=500,
            available_stock=0,
        )
        inventory2 = Inventory(
            id="inv_002",
            offer_id=offer1.id,
            representation_id=representation2.id,
            total_stock=500,
            available_stock=2,
        )
        inventory3 = Inventory(
            id="inv_003",
            offer_id=offer3.id,
            representation_id=representation3.id,
            total_stock=500,
            available_stock=5,
        )
        session.add(inventory1)
        session.add(inventory2)
        session.add(inventory3)
        session.commit()
        return [inventory1, inventory2, inventory3]


@pytest.fixture(autouse=True)
def keep_clear_db(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        session.execute(text("DELETE FROM participation"))
        session.execute(text("DELETE FROM inventory"))
        session.execute(text("DELETE FROM offer"))
        session.execute(text("DELETE FROM offertype"))
        session.execute(text("DELETE FROM representation"))
        session.execute(text("DELETE FROM event"))
        session.execute(text("DELETE FROM organization"))
        session.execute(text("DELETE FROM user"))
        session.commit()
    yield
    with Session(test_engine) as session:
        session.execute(text("DELETE FROM participation"))
        session.execute(text("DELETE FROM inventory"))
        session.execute(text("DELETE FROM offer"))
        session.execute(text("DELETE FROM offertype"))
        session.execute(text("DELETE FROM representation"))
        session.execute(text("DELETE FROM event"))
        session.execute(text("DELETE FROM organization"))
        session.execute(text("DELETE FROM user"))
        session.commit()
