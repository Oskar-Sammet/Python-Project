from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

def create_table():
    Base.metadata.create_all(bind=engine)