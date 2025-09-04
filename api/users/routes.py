from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from common.dependencies import get_session
from users.models import User

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[User])
def get_users(session: Session = Depends(get_session)):
    results = session.exec(select(User)).all()
    return results
