from abc import abstractmethod

from sqlmodel import Session

from synda.database import engine
from synda.model.node import Node


class InputLoader:
    @abstractmethod
    def load(self) -> list[Node]:
        pass

    @staticmethod
    def persist_nodes(nodes: list[Node]) -> list[Node]:
        with Session(engine) as session:
            for node in nodes:
                session.add(node)

            session.commit()

            for node in nodes:
                session.refresh(node)

            return nodes
