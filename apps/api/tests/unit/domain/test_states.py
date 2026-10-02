"""State vocabulary and explicit unknown/absence semantics."""

import pytest

from app.domain.states import (
    DecisionEffect,
    ProcessingState,
    ReviewApprovalState,
    RuleStatus,
    ScreeningDecision,
)


STATE_VALUES = [
    (ProcessingState, {"RECEIVED", "QUARANTINED", "QUEUED", "PROCESSING", "NEEDS_INPUT", "FAILED_RETRYABLE", "FAILED_FINAL", "COMPLETED"}),
    (ScreeningDecision, {"PASS", "REVIEW", "HOLD"}),
    (ReviewApprovalState, {"NOT_REQUIRED", "OPEN", "ASSIGNED", "AWAITING_INFORMATION", "APPROVED", "DECLINED", "RESOLVED", "CANCELLED"}),
    (RuleStatus, {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE", "ERROR"}),
    (DecisionEffect, {"NONE", "REVIEW", "HOLD"}),
]


@pytest.mark.parametrize("enum_type,expected", STATE_VALUES)
def test_exact_specification_vocabulary(enum_type, expected):
    assert {state.value for state in enum_type} == expected
    assert all(enum_type(value).value == value for value in expected)


@pytest.mark.parametrize("enum_type", [item[0] for item in STATE_VALUES])
@pytest.mark.parametrize("invalid", ["INVALID", False, 0, None])
def test_invalid_or_absent_state_is_not_coerced(enum_type, invalid):
    with pytest.raises(ValueError):
        enum_type(invalid)


@pytest.mark.parametrize("invalid", ["REJECT", "APPROVE", "APPROVED", "FAIL"])
def test_screening_has_no_human_approval_or_rejection_alias(invalid):
    with pytest.raises(ValueError):
        ScreeningDecision(invalid)


@pytest.mark.parametrize("other", [False, 0, None, RuleStatus.PASS, RuleStatus.FAIL, RuleStatus.NOT_APPLICABLE, RuleStatus.ERROR])
def test_unknown_remains_distinct(other):
    assert RuleStatus.UNKNOWN != other


def test_lifecycle_dimensions_do_not_compare_equal_by_shared_text():
    assert RuleStatus.PASS != ScreeningDecision.PASS
    assert DecisionEffect.REVIEW != ScreeningDecision.REVIEW
    assert all(ReviewApprovalState.APPROVED != decision for decision in ScreeningDecision)


@pytest.mark.parametrize("state", [state for enum_type, _ in STATE_VALUES for state in enum_type])
def test_state_truthiness_cannot_stand_in_for_success(state):
    with pytest.raises(TypeError, match="explicit state comparison"):
        bool(state)


@pytest.mark.parametrize("state", list(RuleStatus))
def test_pass_requires_explicit_pass_member(state):
    assert (state is RuleStatus.PASS) == (state.value == "PASS")
    assert RuleStatus(state.value) is state
