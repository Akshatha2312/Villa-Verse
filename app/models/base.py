from datetime import datetime, timezone
from app.extensions import db

class BaseModel(db.Model):
    """
    Abstract Base Model for all VillaVerse database entities.
    Provides standard audit timestamps and serialization helper.
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    def to_dict(self) -> dict:
        """Serialize model attributes into a standard Python dictionary."""
        result = {}
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[column.name] = val
        return result
