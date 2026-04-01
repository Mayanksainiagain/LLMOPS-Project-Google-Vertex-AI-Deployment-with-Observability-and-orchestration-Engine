"""
Unit tests for the LinkedIn Post Optimization Service.
Tests each feature in isolation using mocks to avoid real API calls.
"""
import pytest
from unittest.mock import patch, MagicMock


# ========== Helpers ==========

def _make_mock_client(text_response: str):
    """Return a mocked Anthropic client that returns text_response."""
    mock_content = MagicMock()
    mock_content.text = text_response
    mock_message = MagicMock()
    mock_message.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    return mock_client


# ========== TEST 1: generate_post ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_post_returns_string(mock_get_client):
    """generate_post should return a non-empty string from Claude."""
    mock_get_client.return_value = _make_mock_client("This is a LinkedIn post about AI.")
    from backend.src.services.linkedin_optimizer import generate_post

    result = generate_post(topic="AI in software engineering", post_type="thought_leadership")

    assert isinstance(result, str)
    assert len(result) > 0


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_post_passes_topic_to_claude(mock_get_client):
    """generate_post should include the topic in the Claude prompt."""
    mock_client = _make_mock_client("Post content")
    mock_get_client.return_value = mock_client
    from backend.src.services.linkedin_optimizer import generate_post

    generate_post(topic="machine learning trends")

    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "machine learning trends" in user_message


# ========== TEST 2: optimize_post ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_optimize_post_returns_string(mock_get_client):
    """optimize_post should return an optimized string."""
    mock_get_client.return_value = _make_mock_client("Improved LinkedIn post content.")
    from backend.src.services.linkedin_optimizer import optimize_post

    result = optimize_post(post="My original post text", optimize_for="engagement")

    assert isinstance(result, str)
    assert len(result) > 0


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_optimize_post_with_tone_and_max_length(mock_get_client):
    """optimize_post should include tone and length instructions when provided."""
    mock_client = _make_mock_client("Optimized post")
    mock_get_client.return_value = mock_client
    from backend.src.services.linkedin_optimizer import optimize_post

    optimize_post(post="Some post", optimize_for="reach", tone="casual", max_length=200)

    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "casual" in user_message
    assert "200" in user_message


# ========== TEST 3: generate_hooks ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_hooks_returns_list(mock_get_client):
    """generate_hooks should return a list of hook strings."""
    raw = "1. Are you ready to transform your career?\n2. Most people get this wrong about AI.\n3. I used to think success meant working harder."
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import generate_hooks

    hooks = generate_hooks(topic="career growth", count=3)

    assert isinstance(hooks, list)
    assert len(hooks) == 3
    assert all(isinstance(h, str) for h in hooks)


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_hooks_count_clamped(mock_get_client):
    """generate_hooks should clamp count between 1 and 5."""
    raw = "1. Hook one."
    mock_client = _make_mock_client(raw)
    mock_get_client.return_value = mock_client
    from backend.src.services.linkedin_optimizer import generate_hooks

    generate_hooks(topic="test", count=10)

    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "5" in user_message  # clamped to 5


# ========== TEST 4: generate_ctas ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_ctas_returns_list(mock_get_client):
    """generate_ctas should return a list of CTA strings."""
    raw = "1. What's your biggest challenge with AI adoption?\n2. Drop a comment below — I read every one.\n3. Tag someone who needs to see this."
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import generate_ctas

    ctas = generate_ctas(topic="AI adoption", goal="engagement", count=3)

    assert isinstance(ctas, list)
    assert len(ctas) == 3


# ========== TEST 5: suggest_hashtags ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_suggest_hashtags_returns_list(mock_get_client):
    """suggest_hashtags should return a list of hashtag strings."""
    raw = "#AI\n#MachineLearning\n#TechLeadership\n#FutureOfWork\n#Innovation"
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import suggest_hashtags

    hashtags = suggest_hashtags(topic="AI leadership", industry="tech", count=5)

    assert isinstance(hashtags, list)
    assert all(h.startswith("#") for h in hashtags)
    assert len(hashtags) == 5


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_suggest_hashtags_count_clamped(mock_get_client):
    """suggest_hashtags should clamp count between 3 and 10."""
    raw = "#AI\n#Tech\n#Leadership"
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import suggest_hashtags

    # Request 1 (below minimum), expect clamped to 3 in prompt
    suggest_hashtags(topic="test", count=1)
    call_kwargs = mock_get_client.return_value.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "3" in user_message


# ========== TEST 6: format_post ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_format_post_returns_string(mock_get_client):
    """format_post should return a formatted string."""
    mock_get_client.return_value = _make_mock_client("🚀 Formatted post\n\n• Bullet 1\n• Bullet 2")
    from backend.src.services.linkedin_optimizer import format_post

    result = format_post(post="Plain text post without formatting")

    assert isinstance(result, str)
    assert len(result) > 0


# ========== TEST 7: generate_ab_variants ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_ab_variants_returns_list(mock_get_client):
    """generate_ab_variants should split response into separate variant strings."""
    raw = "Variant A: Here is the first post.\n---VARIANT---\nVariant B: Here is the second post."
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import generate_ab_variants

    variants = generate_ab_variants(topic="leadership", variants=2)

    assert isinstance(variants, list)
    assert len(variants) == 2
    assert "Variant A" in variants[0]
    assert "Variant B" in variants[1]


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_generate_ab_variants_count_clamped(mock_get_client):
    """generate_ab_variants should clamp variants to 2-3."""
    raw = "Post one.\n---VARIANT---\nPost two."
    mock_client = _make_mock_client(raw)
    mock_get_client.return_value = mock_client
    from backend.src.services.linkedin_optimizer import generate_ab_variants

    # Request 5 variants (above max of 3)
    generate_ab_variants(topic="test", variants=5)
    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "3" in user_message  # clamped to 3


# ========== TEST 8: predict_engagement ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_predict_engagement_returns_dict(mock_get_client):
    """predict_engagement should return a dict with required keys."""
    raw = (
        "SCORE: 82\n"
        "GRADE: B\n"
        "HOOK_STRENGTH: Strong\n"
        "READABILITY: Strong\n"
        "CTA_CLARITY: Fair\n"
        "STRENGTHS:\n"
        "- Great hook\n"
        "- Good use of emojis\n"
        "IMPROVEMENTS:\n"
        "- Add more specificity\n"
        "OPTIMAL_TIME: Tuesday, 9 AM"
    )
    mock_get_client.return_value = _make_mock_client(raw)
    from backend.src.services.linkedin_optimizer import predict_engagement

    result = predict_engagement(post="Some LinkedIn post text here")

    assert isinstance(result, dict)
    assert result["score"] == 82
    assert result["grade"] == "B"
    assert result["hook_strength"] == "Strong"
    assert result["readability"] == "Strong"
    assert result["cta_clarity"] == "Fair"
    assert "Great hook" in result["strengths"]
    assert "Add more specificity" in result["improvements"]
    assert "Tuesday" in result["optimal_posting_time"]


@patch("backend.src.services.linkedin_optimizer._get_client")
def test_predict_engagement_handles_malformed_response(mock_get_client):
    """predict_engagement should handle unexpected Claude output gracefully."""
    mock_get_client.return_value = _make_mock_client("Unexpected response format")
    from backend.src.services.linkedin_optimizer import predict_engagement

    result = predict_engagement(post="Some post")

    assert isinstance(result, dict)
    assert result["score"] == 0  # default when parsing fails
    assert isinstance(result["strengths"], list)
    assert isinstance(result["improvements"], list)


# ========== TEST 9: Missing API key ==========

def test_missing_api_key_raises_environment_error(monkeypatch):
    """_get_client should raise EnvironmentError when API key is missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from backend.src.services.linkedin_optimizer import _get_client

    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        _get_client()


# ========== TEST 10: full_optimization ==========

@patch("backend.src.services.linkedin_optimizer._get_client")
def test_full_optimization_returns_complete_dict(mock_get_client):
    """full_optimization should return a dict with all expected keys."""
    mock_get_client.return_value = _make_mock_client(
        "1. Hook one.\n2. Hook two.\n3. Hook three."  # reused for all calls
    )

    # Override each function with a targeted mock to avoid parsing issues
    with (
        patch("backend.src.services.linkedin_optimizer.generate_post", return_value="Generated post"),
        patch("backend.src.services.linkedin_optimizer.generate_hooks", return_value=["Hook 1", "Hook 2"]),
        patch("backend.src.services.linkedin_optimizer.generate_ctas", return_value=["CTA 1"]),
        patch("backend.src.services.linkedin_optimizer.suggest_hashtags", return_value=["#AI", "#Tech"]),
        patch("backend.src.services.linkedin_optimizer.format_post", return_value="Formatted post"),
        patch("backend.src.services.linkedin_optimizer.generate_ab_variants", return_value=["V1", "V2"]),
        patch("backend.src.services.linkedin_optimizer.predict_engagement", return_value={"score": 75, "grade": "B"}),
    ):
        from backend.src.services.linkedin_optimizer import full_optimization
        result = full_optimization(topic="AI in 2025")

    required_keys = {
        "topic", "post_type", "industry", "generated_post",
        "formatted_post", "hooks", "ctas", "hashtags", "ab_variants", "analytics",
    }
    assert required_keys.issubset(result.keys())
    assert result["topic"] == "AI in 2025"
    assert result["generated_post"] == "Generated post"
    assert result["hooks"] == ["Hook 1", "Hook 2"]
    assert result["analytics"]["score"] == 75
