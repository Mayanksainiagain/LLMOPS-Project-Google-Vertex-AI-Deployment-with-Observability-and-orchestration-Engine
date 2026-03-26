"""
Integration tests for the LangGraph workflow.
Tests the conditional routing logic.
"""
from backend.src.graph.workflow import should_continue_after_indexer


def test_routing_success():
    """When indexer succeeds, route to auditor."""
    state = {"indexer_success": True, "retry_count": 0}
    assert should_continue_after_indexer(state) == "auditor"


def test_routing_retry():
    """When indexer fails with retries left, route back to indexer."""
    state = {"indexer_success": False, "retry_count": 1}
    assert should_continue_after_indexer(state) == "indexer"


def test_routing_error_handler():
    """When indexer fails with no retries left, route to error handler."""
    state = {"indexer_success": False, "retry_count": 3}
    assert should_continue_after_indexer(state) == "error_handler"
