from sqlmodel import Session, SQLModel


def session_add(session: Session, instances: SQLModel | list[SQLModel]) -> None:
    if not isinstance(instances, list):
        session.add(instances)
        return
    for elt in instances:
        session.add(elt)
