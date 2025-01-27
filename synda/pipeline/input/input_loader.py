from abc import abstractmethod

from sqlmodel import Session

from synda.model.node import Node


class InputLoader:
    @abstractmethod
    def load(self, session: Session) -> list[Node]:
        pass

    @staticmethod
    def persist_nodes(session: Session, nodes: list[Node]) -> list[Node]:
        for node in nodes:
            session.add(node)

        session.commit()

        for node in nodes:
            session.refresh(node)

        return nodes
