import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, text

from config import engine


def load_data(file_path: str, table: str) -> None:
    data = pd.read_csv(file_path, index_col="id")
    data.to_sql(table, engine, if_exists="append")


if __name__ == "__main__":
    print("Loading data into the DB")
    try:
        load_data("data/files/users.csv", "user")
        load_data("data/files/organizations.csv", "organization")
        load_data("data/files/events.csv", "event")
        load_data("data/files/representations.csv", "representation")
        load_data("data/files/offer_types.csv", "offertype")
        load_data("data/files/offers.csv", "offer")
        load_data("data/files/inventory.csv", "inventory")
    except (IntegrityError, OperationalError):
        with Session(engine) as session:
            session.execute(text("DELETE FROM inventory"))
            session.execute(text("DELETE FROM offer"))
            session.execute(text("DELETE FROM offertype"))
            session.execute(text("DELETE FROM representation"))
            session.execute(text("DELETE FROM event"))
            session.execute(text("DELETE FROM organization"))
            session.execute(text("DELETE FROM user"))
            session.commit()
    print("The data was successfully loaded")
