from vibelimits.classifier import classify_rules
from vibelimits.schemas import EventType


def test_reset():
    result = classify_rules("We are resetting Codex usage limits for everyone today")
    assert result.relevant and result.event_type == EventType.QUOTA_RESET


def test_increase():
    result = classify_rules("We increased agent usage limits by 2x for all Pro users")
    assert result.relevant and result.event_type == EventType.QUOTA_INCREASE


def test_irrelevant_release():
    result = classify_rules("New model launched with faster coding performance")
    assert not result.relevant
