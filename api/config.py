from sqlmodel import create_engine

DEBUG = True
DB_URL = ""
engine = create_engine(DB_URL, echo=DEBUG)