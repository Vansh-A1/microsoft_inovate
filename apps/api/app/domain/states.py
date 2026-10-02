"""Distinct processing, screening, review, and rule states from spec section 2.

UNKNOWN describes an unresolved check; None denotes an absent value. Neither
is false, monetary zero, FAIL, NOT_APPLICABLE, or PASS. Consumers must compare
enum members explicitly, rather than use truthiness to infer success.
"""

from enum import Enum


class _ExplicitState(Enum):
    def __bool__(self) -> bool:
        raise TypeError(f"{type(self).__name__} requires an explicit state comparison")


class ProcessingState(_ExplicitState):
    RECEIVED = "RECEIVED"
    QUARANTINED = "QUARANTINED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    NEEDS_INPUT = "NEEDS_INPUT"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    COMPLETED = "COMPLETED"


class ScreeningDecision(_ExplicitState):
    PASS = "PASS"
    REVIEW = "REVIEW"
    HOLD = "HOLD"


class ReviewApprovalState(_ExplicitState):
    NOT_REQUIRED = "NOT_REQUIRED"
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    AWAITING_INFORMATION = "AWAITING_INFORMATION"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class RuleStatus(_ExplicitState):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class DecisionEffect(_ExplicitState):
    NONE = "NONE"
    REVIEW = "REVIEW"
    HOLD = "HOLD"
