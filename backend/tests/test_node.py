"""
Unit tests for LangGraph nodes.
Tests each node in isolation using mocks.
"""
import pytest
from unittest.mock import patch, MagicMock


# ========== TEST 1: Indexer Success ==========
@patch("backend.src.graph.nodes.VideoIntelligenceService")
def test_indexer_success(mock_service_class):
    """Test that indexer returns correct data on success."""
    from backend.src.graph.nodes import index_video_node

    # Setup mock
    mock_service = MagicMock()
    mock_service.download_youtube_video.return_value = "temp.mp4"
    mock_service.upload_to_gcs.return_value = "gs://bucket/video.mp4"
    mock_service.analyze_video.return_value = MagicMock()
    mock_service.extract_data.return_value = {
        "transcript": "Buy this product now",
        "ocr_text": ["#ad", "sponsored"],
        "video_metadata": {"platform": "youtube"},
    }
    mock_service_class.return_value = mock_service

    # Execute
    state = {"video_url": "https://youtu.be/test123", "video_id": "vid_test", "retry_count": 0}
    result = index_video_node(state)

    # Assert
    assert result["indexer_success"] is True
    assert result["transcript"] == "Buy this product now"
    assert len(result["ocr_text"]) == 2


# ========== TEST 2: Indexer Failure ==========
@patch("backend.src.graph.nodes.VideoIntelligenceService")
def test_indexer_failure(mock_service_class):
    """Test that indexer handles errors and sets retry flag."""
    from backend.src.graph.nodes import index_video_node

    mock_service = MagicMock()
    mock_service.download_youtube_video.side_effect = Exception("Network error")
    mock_service_class.return_value = mock_service

    state = {"video_url": "https://youtu.be/test123", "video_id": "vid_test", "retry_count": 0}
    result = index_video_node(state)

    assert result["indexer_success"] is False
    assert result["retry_count"] == 1
    assert "Network error" in result["errors"][0]


# ========== TEST 3: Auditor with no transcript ==========
def test_auditor_no_transcript():
    """Test that auditor skips when no transcript is available."""
    from backend.src.graph.nodes import audit_content_node

    state = {"transcript": "", "ocr_text": []}
    result = audit_content_node(state)

    assert result["final_status"] == "FAIL"
    assert "No transcript" in result["final_report"]
