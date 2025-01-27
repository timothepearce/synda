from sqlmodel import SQLModel, Session, Field, select

from synda.database import engine


class Provider(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    api_key: str | None = Field(default=None, unique=True)

    @staticmethod
    def create(name: str, api_key: str | None = None) -> "Provider":
        with Session(engine) as session:
            provider = Provider(name=name, api_key=api_key)
            session.add(provider)
            session.commit()
            session.refresh(provider)
            return provider

    def update(self, **kwargs) -> "Provider":
        with Session(engine) as session:
            for field, value in kwargs.items():
                setattr(self, field, value)

            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    def delete(self) -> None:
        with Session(engine) as session:
            session.delete(self)
            session.commit()

    @staticmethod
    def get(name: str) -> "Provider":
        with Session(engine) as session:
            return session.exec(select(Provider).where(Provider.name == name)).one()
