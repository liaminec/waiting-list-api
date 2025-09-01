from sqlmodel import SQLModel, Session


def create(instance: SQLModel, session: Session) -> SQLModel:
    session.add(instance)
    session.commit()
    return instance