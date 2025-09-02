from sqlmodel import create_engine

DEBUG = True
DB_URL = "sqlite:///data/db/database"
engine = create_engine(DB_URL, echo=DEBUG)
