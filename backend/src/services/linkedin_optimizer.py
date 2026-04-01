"""
LinkedIn Post Optimization Service using Claude AI.

Provides AI-powered content generation and optimization for LinkedIn posts,
including hooks, CTAs, hashtags, formatting, and A/B variant generation.
"""
import os
import logging
from typing import Optional

import anthropic

logger = logging.getLogger("linkedin-optimizer")

# Supported post types and industries
POST_TYPES = ["thought_leadership", "announcement", "tutorial", "success_story"]
INDUSTRIES = ["tech", "marketing", "sales", "finance", "healthcare", "education", "general"]

# Claude model to use
CLAUDE_MODEL = "claude-opus-4-5"


def _get_client() -> anthropic.Anthropic:
    """Return an Anthropic client, using ANTHROPIC_API_KEY from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(system: str, user: str, max_tokens: int = 1024) -> str:
    """Send a prompt to Claude and return the text response."""
    client = _get_client()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": user}],
        system=system,
    )
    return response.content[0].text.strip()


# ========== FEATURE 1: Post Generation ==========

def generate_post(
    topic: str,
    post_type: str = "thought_leadership",
    industry: str = "general",
    tone: str = "professional",
    target_audience: str = "professionals",
) -> str:
    """
    Generate an engaging LinkedIn post from a topic or keywords.

    Args:
        topic: The subject or keywords to base the post on.
        post_type: One of POST_TYPES (e.g. 'thought_leadership').
        industry: One of INDUSTRIES for domain-specific language.
        tone: Desired tone (e.g. 'professional', 'casual', 'inspirational').
        target_audience: Description of the intended reader.

    Returns:
        A fully formatted LinkedIn post as a string.
    """
    system = (
        "You are an expert LinkedIn content strategist who crafts highly engaging posts "
        "that drive maximum reach and interaction. You know LinkedIn's algorithm prefers "
        "posts that spark conversation, use white space well, and have a strong hook. "
        "Always write in first person, keep sentences short, and end with a question or CTA."
    )
    user = (
        f"Write a LinkedIn post about: {topic}\n\n"
        f"Post type: {post_type.replace('_', ' ')}\n"
        f"Industry: {industry}\n"
        f"Tone: {tone}\n"
        f"Target audience: {target_audience}\n\n"
        "Requirements:\n"
        "- Start with a strong hook (first line must grab attention)\n"
        "- Use short paragraphs (1-3 lines each) with blank lines between them\n"
        "- Include 2-3 relevant emojis naturally placed\n"
        "- End with an engaging question or clear CTA\n"
        "- Keep total length between 150-300 words\n"
        "- Do NOT use hashtags inside the body — add them at the end\n\n"
        "Return only the post text, ready to copy-paste."
    )
    logger.info(f"Generating LinkedIn post: topic='{topic}', type={post_type}")
    return _call_claude(system, user, max_tokens=600)


# ========== FEATURE 2: Content Optimization ==========

def optimize_post(
    post: str,
    optimize_for: str = "engagement",
    tone: Optional[str] = None,
    max_length: Optional[int] = None,
) -> str:
    """
    Refine an existing post for tone, length, and professional appeal.

    Args:
        post: The original LinkedIn post text.
        optimize_for: What to optimize for ('engagement', 'reach', 'clicks').
        tone: Optional target tone override.
        max_length: Optional word count limit.

    Returns:
        The optimized post text.
    """
    system = (
        "You are a LinkedIn content editor who refines posts to maximize "
        "professional impact and algorithmic reach. Preserve the author's voice "
        "while improving clarity, engagement, and formatting."
    )
    length_note = f"Keep it under {max_length} words." if max_length else "Aim for 150-300 words."
    tone_note = f"Adjust tone to be more {tone}." if tone else ""
    user = (
        f"Optimize this LinkedIn post for {optimize_for}:\n\n{post}\n\n"
        f"Instructions:\n"
        f"- Improve the hook if it's weak\n"
        f"- Ensure short paragraphs with white space\n"
        f"- Fix any grammar or awkward phrasing\n"
        f"- Strengthen the CTA or closing question\n"
        f"{tone_note}\n"
        f"{length_note}\n\n"
        "Return only the improved post text."
    )
    logger.info("Optimizing LinkedIn post")
    return _call_claude(system, user, max_tokens=600)


# ========== FEATURE 3: Hook Creation ==========

def generate_hooks(topic: str, count: int = 3) -> list[str]:
    """
    Generate multiple compelling opening lines for a LinkedIn post.

    Args:
        topic: The post subject or keywords.
        count: Number of hook variants to generate (1-5).

    Returns:
        List of hook strings.
    """
    count = max(1, min(count, 5))
    system = (
        "You are a copywriting expert specializing in LinkedIn hooks. "
        "A great LinkedIn hook stops the scroll in the first 1-2 lines. "
        "Use patterns like: bold claim, surprising statistic, personal story opener, "
        "contrarian take, or rhetorical question."
    )
    user = (
        f"Generate {count} different compelling hook lines for a LinkedIn post about: {topic}\n\n"
        "Each hook should use a different technique (bold claim, question, statistic, story, contrarian).\n"
        "Keep each hook to 1-2 sentences maximum.\n\n"
        f"Return exactly {count} hooks, one per line, numbered 1. 2. 3. etc."
    )
    logger.info(f"Generating {count} hooks for topic: '{topic}'")
    raw = _call_claude(system, user, max_tokens=400)
    hooks = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and ". " in line:
            hooks.append(line.split(". ", 1)[1].strip())
        elif line and not line[0].isdigit():
            hooks.append(line)
    return hooks[:count]


# ========== FEATURE 4: CTA Suggestions ==========

def generate_ctas(topic: str, goal: str = "engagement", count: int = 3) -> list[str]:
    """
    Generate call-to-action variations to maximize engagement.

    Args:
        topic: The post subject.
        goal: The desired action ('engagement', 'lead_gen', 'traffic', 'shares').
        count: Number of CTA variants to generate.

    Returns:
        List of CTA strings.
    """
    count = max(1, min(count, 5))
    system = (
        "You are a LinkedIn engagement expert. Great CTAs are specific, "
        "low-friction, and feel natural — not salesy. They invite conversation "
        "and make the reader feel their input is valued."
    )
    user = (
        f"Generate {count} different CTA (call-to-action) lines for a LinkedIn post about: {topic}\n"
        f"Optimization goal: {goal.replace('_', ' ')}\n\n"
        "Each CTA should use a different approach (question, directive, challenge, poll, resource offer).\n"
        f"Return exactly {count} CTAs, one per line, numbered 1. 2. 3. etc."
    )
    logger.info(f"Generating {count} CTAs for topic: '{topic}', goal: {goal}")
    raw = _call_claude(system, user, max_tokens=300)
    ctas = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and ". " in line:
            ctas.append(line.split(". ", 1)[1].strip())
        elif line and not line[0].isdigit():
            ctas.append(line)
    return ctas[:count]


# ========== FEATURE 5: Hashtag Optimization ==========

def suggest_hashtags(
    topic: str, industry: str = "general", count: int = 5
) -> list[str]:
    """
    Suggest relevant hashtags and mentions for maximum LinkedIn reach.

    Args:
        topic: The post subject or keywords.
        industry: Domain for context.
        count: Number of hashtag suggestions (3-10).

    Returns:
        List of hashtag strings (e.g. ['#AI', '#Leadership']).
    """
    count = max(3, min(count, 10))
    system = (
        "You are a LinkedIn SEO and discoverability expert. "
        "You know which hashtags have large engaged communities on LinkedIn "
        "vs. which are over-saturated or too niche."
    )
    user = (
        f"Suggest {count} optimal LinkedIn hashtags for a post about: {topic}\n"
        f"Industry context: {industry}\n\n"
        "Mix broad (high-volume) and niche (targeted) hashtags.\n"
        f"LinkedIn best practice: 3-5 hashtags is ideal, but provide {count} options.\n"
        f"Return exactly {count} hashtags, one per line, each starting with #."
    )
    logger.info(f"Suggesting hashtags for topic: '{topic}', industry: {industry}")
    raw = _call_claude(system, user, max_tokens=200)
    hashtags = [
        line.strip()
        for line in raw.splitlines()
        if line.strip().startswith("#")
    ]
    return hashtags[:count]


# ========== FEATURE 6: Formatting ==========

def format_post(post: str) -> str:
    """
    Apply LinkedIn best-practice formatting with bullet points and emojis.

    Args:
        post: The raw post text.

    Returns:
        Formatted post ready for LinkedIn.
    """
    system = (
        "You are a LinkedIn formatting specialist. You apply proven formatting "
        "techniques: short paragraphs, strategic line breaks, bullet points where "
        "appropriate, and tasteful emojis to improve readability and engagement."
    )
    user = (
        f"Format this LinkedIn post using best practices:\n\n{post}\n\n"
        "Apply these formatting rules:\n"
        "- Separate paragraphs with a blank line\n"
        "- Convert any list-like content to bullet points using '•'\n"
        "- Add 1-3 relevant emojis where they feel natural (not forced)\n"
        "- Ensure the first line stands alone as the hook (before 'see more')\n"
        "- Keep line length short for mobile readability\n\n"
        "Return only the formatted post text."
    )
    logger.info("Formatting LinkedIn post")
    return _call_claude(system, user, max_tokens=600)


# ========== FEATURE 7: A/B Testing ==========

def generate_ab_variants(
    topic: str,
    post_type: str = "thought_leadership",
    industry: str = "general",
    variants: int = 2,
) -> list[str]:
    """
    Create multiple post versions for A/B testing.

    Args:
        topic: The post subject.
        post_type: Type of LinkedIn post.
        industry: Industry context.
        variants: Number of variants to generate (2-3).

    Returns:
        List of complete post variants.
    """
    variants = max(2, min(variants, 3))
    system = (
        "You are a LinkedIn content strategist who creates multiple post variants "
        "for A/B testing. Each variant should feel distinctly different in hook style, "
        "structure, or angle — while covering the same core topic."
    )
    user = (
        f"Create {variants} distinct LinkedIn post variants about: {topic}\n"
        f"Post type: {post_type.replace('_', ' ')}\n"
        f"Industry: {industry}\n\n"
        f"Each variant must:\n"
        "- Use a completely different hook/opening style\n"
        "- Have a different structural approach (story vs. list vs. insight)\n"
        "- Be 150-300 words\n"
        "- End with a CTA or question\n"
        "- Include 3-5 hashtags at the end\n\n"
        f"Separate each variant with '---VARIANT---' on its own line.\n"
        f"Return exactly {variants} variants."
    )
    logger.info(f"Generating {variants} A/B variants for topic: '{topic}'")
    raw = _call_claude(system, user, max_tokens=1500)
    parts = [p.strip() for p in raw.split("---VARIANT---") if p.strip()]
    return parts[:variants]


# ========== FEATURE 8: Analytics Integration ==========

def predict_engagement(post: str) -> dict:
    """
    Predict engagement potential and get improvement recommendations.

    Args:
        post: The LinkedIn post text to analyze.

    Returns:
        Dictionary with score (0-100), grade, strengths, and recommendations.
    """
    system = (
        "You are a LinkedIn analytics expert who evaluates post quality based on "
        "known engagement signals: hook strength, readability, CTA clarity, "
        "emotional resonance, specificity, and formatting. Be honest and actionable."
    )
    user = (
        f"Analyze this LinkedIn post and predict its engagement potential:\n\n{post}\n\n"
        "Provide your analysis in this exact format:\n"
        "SCORE: [0-100]\n"
        "GRADE: [A/B/C/D/F]\n"
        "HOOK_STRENGTH: [Weak/Fair/Strong]\n"
        "READABILITY: [Weak/Fair/Strong]\n"
        "CTA_CLARITY: [Weak/Fair/Strong]\n"
        "STRENGTHS:\n"
        "- [strength 1]\n"
        "- [strength 2]\n"
        "IMPROVEMENTS:\n"
        "- [improvement 1]\n"
        "- [improvement 2]\n"
        "OPTIMAL_TIME: [Best day and time to post for maximum reach]"
    )
    logger.info("Predicting engagement for LinkedIn post")
    raw = _call_claude(system, user, max_tokens=500)

    result: dict = {
        "score": 0,
        "grade": "N/A",
        "hook_strength": "N/A",
        "readability": "N/A",
        "cta_clarity": "N/A",
        "strengths": [],
        "improvements": [],
        "optimal_posting_time": "Tuesday–Thursday, 8–10 AM or 12 PM (local time)",
        "raw_analysis": raw,
    }

    lines = raw.splitlines()
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                result["score"] = int(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        elif line.startswith("GRADE:"):
            result["grade"] = line.split(":", 1)[1].strip()
        elif line.startswith("HOOK_STRENGTH:"):
            result["hook_strength"] = line.split(":", 1)[1].strip()
        elif line.startswith("READABILITY:"):
            result["readability"] = line.split(":", 1)[1].strip()
        elif line.startswith("CTA_CLARITY:"):
            result["cta_clarity"] = line.split(":", 1)[1].strip()
        elif line.startswith("STRENGTHS:"):
            current_section = "strengths"
        elif line.startswith("IMPROVEMENTS:"):
            current_section = "improvements"
        elif line.startswith("OPTIMAL_TIME:"):
            result["optimal_posting_time"] = line.split(":", 1)[1].strip()
            current_section = None
        elif line.startswith("- ") and current_section in ("strengths", "improvements"):
            result[current_section].append(line[2:].strip())

    return result


# ========== CONVENIENCE: Full Optimization Pipeline ==========

def full_optimization(
    topic: str,
    post_type: str = "thought_leadership",
    industry: str = "general",
    tone: str = "professional",
    target_audience: str = "professionals",
) -> dict:
    """
    Run the complete LinkedIn post optimization pipeline.

    Generates a post, optimizes it, adds hashtags, and returns engagement
    predictions — all in one call.

    Args:
        topic: The post subject or keywords.
        post_type: Type of LinkedIn post.
        industry: Industry for domain-specific customization.
        tone: Desired tone.
        target_audience: Intended reader description.

    Returns:
        Dictionary with generated post, hooks, CTAs, hashtags,
        formatted post, A/B variants, and engagement prediction.
    """
    logger.info(f"Running full LinkedIn optimization for: '{topic}'")

    # 1. Generate base post
    post = generate_post(topic, post_type, industry, tone, target_audience)

    # 2. Generate hooks
    hooks = generate_hooks(topic, count=3)

    # 3. Generate CTAs
    ctas = generate_ctas(topic, goal="engagement", count=3)

    # 4. Suggest hashtags
    hashtags = suggest_hashtags(topic, industry, count=5)

    # 5. Format the post
    formatted_post = format_post(post)

    # 6. Generate A/B variants
    ab_variants = generate_ab_variants(topic, post_type, industry, variants=2)

    # 7. Predict engagement
    analytics = predict_engagement(formatted_post)

    return {
        "topic": topic,
        "post_type": post_type,
        "industry": industry,
        "generated_post": post,
        "formatted_post": formatted_post,
        "hooks": hooks,
        "ctas": ctas,
        "hashtags": hashtags,
        "ab_variants": ab_variants,
        "analytics": analytics,
    }
