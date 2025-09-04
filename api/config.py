import os
from dotenv import load_dotenv

from sqlmodel import create_engine

from exceptions import UnsetVarError

load_dotenv()

DEBUG = True
try:
    DB_URL = os.environ["DB_URL"]
except KeyError as kerr:
    raise UnsetVarError(
        "You must set the DB_URL env variable (see .env file)"
    ) from kerr

engine = create_engine(DB_URL, echo=DEBUG)
