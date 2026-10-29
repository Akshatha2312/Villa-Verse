from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Optional, List
from app.extensions import db

T = TypeVar("T")

class BaseService(ABC, Generic[T]):
    """
    Abstract Base Service defining common data operations and business interfaces.
    Demonstrates OOP Abstraction and Template Method patterns.
    """

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Fetch a single entity by its primary key."""
        pass

    @abstractmethod
    def list_all(self, **filters) -> List[T]:
        """Retrieve all matching entities based on filters."""
        pass

    def commit_or_rollback(self) -> None:
        """Helper to ensure transactional integrity across all service operations."""
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
