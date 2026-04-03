"""
NLP Command Parser for Jarvis HR Agent
Maps voice/text commands to intents using fuzzy matching.
Extended with HR-specific intents for web deployment.
"""

from rapidfuzz import fuzz, process


command_map = {
    # ── Time & Date ───────────────────────────────────────────────────────────
    "get_time": [
        "what time is it", "tell me the time", "time now",
        "current time", "what's the time", "show time",
    ],
    "get_date": [
        "what's the date", "what is the date", "tell me the date",
        "date today", "today's date", "current date",
    ],

    # ── Weather ───────────────────────────────────────────────────────────────
    "get_weather": [
        "what's the weather", "current weather", "weather report",
        "weather now", "tell me the weather", "how's the weather",
        "weather today", "weather forecast", "show weather",
    ],

    # ── News ──────────────────────────────────────────────────────────────────
    "get_news": [
        "news", "tell me the news", "what's the news", "news today",
        "latest news", "current news", "news headlines", "show me the news",
    ],

    # ── Search ────────────────────────────────────────────────────────────────
    "search_google": [
        "search for", "google search", "look up", "find on google",
        "google for", "search google", "can you search",
    ],

    # ── HR: Shortlisting ──────────────────────────────────────────────────────
    "hr_shortlist": [
        "shortlist candidates", "filter candidates", "find candidates",
        "shortlist resumes", "who has skills in", "candidates with skills",
        "show me candidates", "list candidates", "find me candidates",
        "shortlist people with", "find developers with", "find engineers with",
        "candidates with experience", "shortlist based on skills",
        "filter resumes", "search candidates",
    ],

    # ── HR: Schedule Interview ────────────────────────────────────────────────
    "hr_schedule": [
        "schedule interview", "book interview", "set up interview",
        "arrange interview", "schedule a meeting", "book a meeting",
        "schedule meeting with candidate", "set interview time",
        "schedule call with", "book a call",
    ],

    # ── HR: Send Email ────────────────────────────────────────────────────────
    "hr_email": [
        "send email", "send invite", "email candidate", "send interview invite",
        "notify candidate", "send mail", "email the shortlisted",
        "send rejection", "send offer", "mail candidate",
    ],

    # ── HR: Red Flag Detection ────────────────────────────────────────────────
    "hr_redflag": [
        "check red flags", "find red flags", "detect issues",
        "flag candidates", "check gaps", "employment gaps",
        "find suspicious", "check resume issues", "flag resume",
        "check for gaps in", "identify issues",
    ],

    # ── HR: Pipeline Summary ──────────────────────────────────────────────────
    "hr_summary": [
        "summarize pipeline", "pipeline summary", "hiring summary",
        "recruitment status", "how many candidates", "candidate summary",
        "show hiring status", "recruitment overview", "pipeline overview",
        "give me a summary", "today's pipeline", "what's our pipeline",
    ],

    # ── HR: Upload Resume ─────────────────────────────────────────────────────
    "hr_upload_resume": [
        "upload resume", "add resume", "add candidate", "upload cv",
        "add cv", "upload new resume", "ingest resume",
    ],
}

# Flatten for global matching
all_phrases = {
    phrase: intent
    for intent, phrases in command_map.items()
    for phrase in phrases
}


def parse_command(user_input: str) -> str:
    """
    Match user input to the most likely intent using fuzzy matching.

    Args:
        user_input: Raw text from user (voice or typed)

    Returns:
        Intent string or None if no confident match found
    """
    if not user_input:
        return None

    user_input = user_input.lower().strip()

    # ADDED THE UNDERSCORE HERE to catch the index value
    best_match, score, _ = process.extractOne(
        user_input, all_phrases.keys(), scorer=fuzz.token_sort_ratio
    )

    if score >= 60:
        return all_phrases[best_match]

    return None


def get_all_intents() -> list:
    """Return all available intent names."""
    return list(command_map.keys())


def get_phrases_for_intent(intent: str) -> list:
    """Return all phrases mapped to a given intent."""
    return command_map.get(intent, [])
