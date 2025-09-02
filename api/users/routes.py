from fastapi import APIRouter
from sqlmodel import Session, select

from config import engine
from users.models import User

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[User])
def get_users():
    with Session(engine) as session:
        results = session.exec(select(User)).all()
        return results
