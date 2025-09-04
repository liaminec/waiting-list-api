from sqlalchemy.exc import NoResultFound
from sqlmodel import SQLModel, Session

from common.db.models import ItemModel, Model


def create(instance: SQLModel, session: Session) -> SQLModel:
    session.add(instance)
    session.commit()
    return instance


def get_instance_by_id(
    model: ItemModel | Model, instance_id: str | int, session: Session
) -> ItemModel | Model | None:
    """
    Get an instance of a model
    :param model: The model of which we want an instance
    :param instance_id: The id of the instance
    :param session: An active session to a database
    :return: The instance of the given model for the given id if it exist, else None
    """
    try:
        instance = session.get(model, instance_id)
    except NoResultFound:
        return None
    return instance
