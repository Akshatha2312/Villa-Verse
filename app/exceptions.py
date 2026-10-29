"""
Custom domain exceptions for the VillaVerse application.
Demonstrates Object-Oriented Exception Hierarchy and defensive programming.
"""

class VillaVerseError(Exception):
    """Base class for all domain exceptions in VillaVerse."""
    def __init__(self, message: str = "A community domain error occurred.", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code
        }


class EntityNotFoundError(VillaVerseError):
    """Raised when a requested domain entity is not found."""
    def __init__(self, entity_name: str, identifier: str | int):
        message = f"{entity_name} with identifier '{identifier}' was not found."
        super().__init__(message=message, status_code=404)
        self.entity_name = entity_name
        self.identifier = identifier


class VillaNotFoundError(EntityNotFoundError):
    """Raised specifically when a villa cannot be found."""
    def __init__(self, identifier: str | int):
        super().__init__(entity_name="Villa", identifier=identifier)


class MemberNotFoundError(EntityNotFoundError):
    """Raised when an owner or resident is not found."""
    def __init__(self, identifier: str | int):
        super().__init__(entity_name="Community Member", identifier=identifier)


class DuplicatePlotError(VillaVerseError):
    """Raised when attempting to register a plot number that is already taken."""
    def __init__(self, plot_number: str):
        message = f"Plot number '{plot_number}' is already registered in the community."
        super().__init__(message=message, status_code=409)
        self.plot_number = plot_number


class DuplicateVillaIdError(VillaVerseError):
    """Raised when a villa ID already exists."""
    def __init__(self, villa_id: str):
        message = f"Villa ID '{villa_id}' already exists in the registry."
        super().__init__(message=message, status_code=409)
        self.villa_id = villa_id


class InvalidStatusTransitionError(VillaVerseError):
    """Raised when an invalid state transition is attempted on a Villa or Maintenance Ticket."""
    def __init__(self, entity_name: str, current_status: str, target_status: str):
        message = f"Cannot transition {entity_name} from status '{current_status}' to '{target_status}'."
        super().__init__(message=message, status_code=422)
        self.current_status = current_status
        self.target_status = target_status


class ResidentAssignmentError(VillaVerseError):
    """Raised when a resident assignment violates occupancy constraints."""
    pass


class InvalidPaymentError(VillaVerseError):
    """Raised when a payment operation violates domain constraints (e.g., negative or exceeding balance)."""
    pass


class BusinessRuleViolationError(VillaVerseError):
    """General error for business rules violated in the domain."""
    pass
