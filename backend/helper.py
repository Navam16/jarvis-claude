"""
Helper utilities for Jarvis HR Agent
"""

import re


def extract_yt_term(command: str) -> str:
    """Extract the search term from a 'play X on youtube' command."""
    pattern = r"play\s+(.*?)\s+on\s+youtube"
    match = re.search(pattern, command, re.IGNORECASE)
    return match.group(1) if match else None


def remove_words(input_string: str, words_to_remove: list) -> str:
    """Remove specified words from a string."""
    words = input_string.split()
    filtered_words = [word for word in words if word.lower() not in words_to_remove]
    return " ".join(filtered_words)


def extract_city_from_query(query: str) -> str:
    """Extract city name from a weather query."""
    match = re.search(r'\b(?:in|for)\s+(.+)', query, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        for word in ["weather", "forecast", "please"]:
            city = re.sub(r'\b' + word + r'\b\s*$', '', city, flags=re.IGNORECASE).strip()
        return city

    # Fallback: strip common command words
    city = query
    for word in ["weather", "forecast", "what's", "what is", "the", "show", "me", "get"]:
        city = re.sub(r'\b' + word + r'\b', '', city, flags=re.IGNORECASE)
    return city.strip()


def extract_skills_from_query(query: str) -> list:
    """
    Extract skill keywords from an HR shortlisting command.
    E.g. 'shortlist candidates with Python and machine learning' -> ['Python', 'machine learning']
    """
    # Remove common HR command words
    stopwords = [
        "shortlist", "find", "show", "me", "candidates", "with",
        "skills", "having", "who", "know", "experience", "in", "and",
        "or", "the", "a", "an", "please", "jarvis"
    ]
    query_clean = query
    for word in stopwords:
        query_clean = re.sub(r'\b' + word + r'\b', '', query_clean, flags=re.IGNORECASE)

    # Split on commas or 'and'/'or' to get individual skills
    parts = re.split(r',|\band\b|\bor\b', query_clean, flags=re.IGNORECASE)
    skills = [p.strip() for p in parts if p.strip()]
    return skills
