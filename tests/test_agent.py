import pytest
from unittest.mock import patch
from app.agent import (
    parse_json,
    call_llm,
    step_extract_actions,
    step_assign_owners,
    step_detect_deadlines,
    step_detect_risks,
    step_summarize,
    update_status
)
from app.models import MeetingJob


# ── parse_json tests ───────────────────────────────────────────

def test_parse_json_valid():
    """Test parsing a valid JSON array string."""
    response = '[{"action": "Update login page", "priority": "High"}]'
    result = parse_json(response)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["action"] == "Update login page"


def test_parse_json_with_extra_text():
    """Test parsing JSON when LLM adds extra text around it."""
    response = 'Here are the findings: [{"action": "Fix bug", "priority": "Low"}] Hope this helps.'
    result = parse_json(response)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["action"] == "Fix bug"


def test_parse_json_empty_array():
    """Test parsing empty array."""
    result = parse_json("[]")
    assert result == []


def test_parse_json_invalid_returns_empty():
    """Test that invalid JSON returns empty list."""
    result = parse_json("This is not JSON at all")
    assert result == []


def test_parse_json_malformed_returns_empty():
    """Test that malformed JSON returns empty list."""
    result = parse_json('[{"action": "broken json"')
    assert result == []


# ── step_extract_actions tests ─────────────────────────────────

def test_step_extract_actions_returns_list(sample_transcript):
    """Test that extract actions returns a list."""
    mock_response = '[{"action": "Update login page", "priority": "High"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_extract_actions(sample_transcript)
    assert isinstance(result, list)
    assert len(result) > 0


def test_step_extract_actions_has_required_fields(sample_transcript):
    """Test that each action item has action and priority fields."""
    mock_response = '[{"action": "Update login page", "priority": "High"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_extract_actions(sample_transcript)
    for item in result:
        assert "action" in item
        assert "priority" in item


def test_step_extract_actions_llm_fails_returns_empty(sample_transcript):
    """Test that LLM failure returns empty list gracefully."""
    with patch("app.agent.call_llm", return_value="[]"):
        result = step_extract_actions(sample_transcript)
    assert result == []


# ── step_assign_owners tests ───────────────────────────────────

def test_step_assign_owners_returns_list(
    sample_transcript,
    sample_action_items
):
    """Test that assign owners returns a list."""
    mock_response = '[{"action": "Update login page", "owner": "Sarah", "priority": "High"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_assign_owners(sample_transcript, sample_action_items)
    assert isinstance(result, list)


def test_step_assign_owners_has_owner_field(
    sample_transcript,
    sample_action_items
):
    """Test that each item has an owner field."""
    mock_response = '[{"action": "Update login page", "owner": "Sarah", "priority": "High"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_assign_owners(sample_transcript, sample_action_items)
    for item in result:
        assert "owner" in item


# ── step_detect_deadlines tests ────────────────────────────────

def test_step_detect_deadlines_returns_list(
    sample_transcript,
    sample_action_items_with_owners
):
    """Test that detect deadlines returns a list."""
    mock_response = '[{"action": "Update login page", "owner": "Sarah", "priority": "High", "deadline": "Friday"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_detect_deadlines(
            sample_transcript,
            sample_action_items_with_owners
        )
    assert isinstance(result, list)


def test_step_detect_deadlines_has_deadline_field(
    sample_transcript,
    sample_action_items_with_owners
):
    """Test that each item has a deadline field."""
    mock_response = '[{"action": "Update login page", "owner": "Sarah", "priority": "High", "deadline": "Friday"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_detect_deadlines(
            sample_transcript,
            sample_action_items_with_owners
        )
    for item in result:
        assert "deadline" in item


# ── step_detect_risks tests ────────────────────────────────────

def test_step_detect_risks_returns_list(sample_transcript):
    """Test that detect risks returns a list."""
    mock_response = '[{"risk": "Third party API unstable", "severity": "High", "mentioned_by": "Sarah"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_detect_risks(sample_transcript)
    assert isinstance(result, list)


def test_step_detect_risks_has_required_fields(sample_transcript):
    """Test that each risk has required fields."""
    mock_response = '[{"risk": "Third party API unstable", "severity": "High", "mentioned_by": "Sarah"}]'
    with patch("app.agent.call_llm", return_value=mock_response):
        result = step_detect_risks(sample_transcript)
    for risk in result:
        assert "risk" in risk
        assert "severity" in risk


def test_step_detect_risks_no_risks_returns_empty(sample_transcript):
    """Test that no risks returns empty list."""
    with patch("app.agent.call_llm", return_value="[]"):
        result = step_detect_risks(sample_transcript)
    assert result == []


# ── step_summarize tests ───────────────────────────────────────

def test_step_summarize_returns_tuple(
    sample_transcript,
    sample_action_items,
    sample_action_items_with_owners
):
    """Test that summarize returns a tuple of string and int."""
    mock_response = "SUMMARY: Good meeting with clear owners.\nSCORE: 75"
    with patch("app.agent.call_llm", return_value=mock_response):
        summary, score = step_summarize(
            sample_transcript,
            sample_action_items,
            []
        )
    assert isinstance(summary, str)
    assert isinstance(score, int)


def test_step_summarize_score_in_range(sample_transcript, sample_action_items):
    """Test that score is always between 0 and 100."""
    mock_response = "SUMMARY: Test summary.\nSCORE: 150"
    with patch("app.agent.call_llm", return_value=mock_response):
        summary, score = step_summarize(sample_transcript, sample_action_items, [])
    assert 0 <= score <= 100


def test_step_summarize_score_never_negative(
    sample_transcript,
    sample_action_items
):
    """Test that score never goes below 0."""
    mock_response = "SUMMARY: Test summary.\nSCORE: -50"
    with patch("app.agent.call_llm", return_value=mock_response):
        summary, score = step_summarize(sample_transcript, sample_action_items, [])
    assert score >= 0