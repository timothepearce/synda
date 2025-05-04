import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine, Session

home_dir = Path.home()
synda_dir = home_dir / ".synda"
synda_dir.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{synda_dir}/synda.db"

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
