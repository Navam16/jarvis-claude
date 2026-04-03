"""
Feature Module for Jarvis HR Agent
Web deployment version:
  - Removed: eel, pyautogui, pyaudio, pywhatkit, hugchat, pvporcupine,
              os.startfile, subprocess (desktop actions)
  - Kept: weather, news, web search, HR actions, time/date
  - HR features route to Supabase via db.py
"""

import logging
import re
from datetime import datetime

from backend.command import speak
from backend.config import OPENWEATHERMAP_API_KEY, NEWS_API_KEY
from backend.db import (
    fetch_all_resumes,
    search_resumes_by_skills,
    insert_candidate,
    fetch_shortlisted_candidates,
    log_conversation,
)
from backend.feedback import StatusIndicator, Timer
from backend.helper import extract_city_from_query, extract_skills_from_query
from backend.nlp.command_parser import parse_command
from news_fetcher import NewsFetcher
from weather_fetcher import WeatherFetcher

logger = logging.getLogger(__name__)

# ── Lazy singletons ───────────────────────────────────────────────────────────
_weather_fetcher = None
_news_fetcher = None


def get_weather_fetcher():
    global _weather_fetcher
    if _weather_fetcher is None and OPENWEATHERMAP_API_KEY:
        try:
            _weather_fetcher = WeatherFetcher(OPENWEATHERMAP_API_KEY)
        except ValueError as e:
            logger.error(f"WeatherFetcher init failed: {e}")
    return _weather_fetcher


def get_news_fetcher():
    global _news_fetcher
    if _news_fetcher is None and NEWS_API_KEY:
        _news_fetcher = NewsFetcher(NEWS_API_KEY)
    return _news_fetcher


# ── Main dispatcher ───────────────────────────────────────────────────────────
async def handle_user_text(user_text: str, language: str = "en") -> str:
    """
    Parse the user command and execute the appropriate action.

    Args:
        user_text: Transcribed text from the user
        language: Detected language code from Whisper

    Returns:
        Response string to send back to the user
    """
    intent = parse_command(user_text)
    StatusIndicator.processing(f"Intent: {intent} | Input: {user_text}")

    if not intent:
        return speak("Sorry, I did not understand that. Please try again.")

    # ── Time & Date ───────────────────────────────────────────────────────────
    if intent == "get_time":
        now = datetime.now().strftime("%H:%M")
        return speak(f"The current time is {now}.")

    elif intent == "get_date":
        today = datetime.now().strftime("%B %d, %Y")
        return speak(f"Today's date is {today}.")

    # ── Weather ───────────────────────────────────────────────────────────────
    elif intent == "get_weather":
        city = extract_city_from_query(user_text)
        if not city:
            return speak("Please tell me which city you want the weather for.")
        return get_weather(city)

    # ── News ──────────────────────────────────────────────────────────────────
    elif intent == "get_news":
        keyword = re.sub(
            r'\b(news|about|latest|show|me|tell|the)\b', '', user_text, flags=re.IGNORECASE
        ).strip() or "top"
        return get_news(keyword)

    # ── HR: Shortlist ─────────────────────────────────────────────────────────
    elif intent == "hr_shortlist":
        skills = extract_skills_from_query(user_text)
        if not skills:
            return speak("Please specify the skills you want to filter candidates by.")
        return shortlist_candidates(skills)

    # ── HR: Schedule ──────────────────────────────────────────────────────────
    elif intent == "hr_schedule":
        return speak(
            "Scheduling agent is not yet connected. Please provide candidate name and preferred time."
        )

    # ── HR: Email ─────────────────────────────────────────────────────────────
    elif intent == "hr_email":
        return speak("Email agent is not yet connected. I will notify you when it is ready.")

    # ── HR: Red Flag ──────────────────────────────────────────────────────────
    elif intent == "hr_redflag":
        return check_red_flags()

    # ── HR: Summary ───────────────────────────────────────────────────────────
    elif intent == "hr_summary":
        return get_pipeline_summary()

    # ── HR: Upload Resume ─────────────────────────────────────────────────────
    elif intent == "hr_upload_resume":
        return speak("Please use the upload button in the interface to add a resume.")

    else:
        return speak("I understood your intent but this feature is not yet available.")


# ── Weather ───────────────────────────────────────────────────────────────────
def get_weather(city_name: str) -> str:
    fetcher = get_weather_fetcher()
    if not fetcher:
        return speak("Weather API key is not configured.")

    with Timer(f"Weather fetch for {city_name}"):
        weather_data, error = fetcher.fetch_current_weather(city_name)

    if error:
        return speak(f"Sorry, I could not get weather for {city_name}. {error}")

    response = (
        f"Weather in {weather_data['city']}, {weather_data['country']}. "
        f"Temperature is {weather_data['temperature']} degrees Celsius, "
        f"feels like {weather_data['feels_like']} degrees. "
        f"Condition: {weather_data['condition']}. "
        f"Humidity is {weather_data['humidity']} percent."
    )
    return speak(response)


def get_weather_forecast(city_name: str, days: int = 5) -> str:
    fetcher = get_weather_fetcher()
    if not fetcher:
        return speak("Weather API key is not configured.")

    with Timer(f"Forecast for {city_name}"):
        forecast_data, error = fetcher.fetch_forecast(city_name, days)

    if error:
        return speak(f"Could not fetch forecast for {city_name}. {error}")

    first = forecast_data[0]
    last = forecast_data[-1]
    summary = (
        f"Here is the {days} day forecast for {city_name}. "
        f"First day: {first['temp_min']} to {first['temp_max']} degrees, {first['condition']}. "
        f"By day {days}: {last['temp_min']} to {last['temp_max']} degrees, {last['condition']}."
    )
    return speak(summary)


# ── News ──────────────────────────────────────────────────────────────────────
def get_news(keyword: str = "top") -> str:
    fetcher = get_news_fetcher()
    if not fetcher:
        return speak("News API key is not configured.")

    with Timer("News fetch"):
        articles = fetcher.fetch_news(keyword, top_n=3)

    if not articles:
        return speak("No news found at the moment.")

    titles = ". ".join([f"Article {i+1}: {a['title']}" for i, a in enumerate(articles)])
    return speak(f"Here are the top news articles about {keyword}. {titles}")


# ── HR: Shortlist Candidates ──────────────────────────────────────────────────
def shortlist_candidates(skills: list) -> str:
    StatusIndicator.processing(f"Searching resumes for skills: {skills}")
    try:
        with Timer("Resume search"):
            matches = search_resumes_by_skills(skills)

        if not matches:
            return speak(
                f"No candidates found with skills in {', '.join(skills)}. "
                "You may want to broaden the criteria."
            )

        names = [r.get("name", "Unknown") for r in matches[:5]]
        response = (
            f"I found {len(matches)} candidate{'s' if len(matches) > 1 else ''} "
            f"matching {', '.join(skills)}. "
            f"Top matches: {', '.join(names)}."
        )
        StatusIndicator.success(response)
        return speak(response)
    except Exception as e:
        logger.error(f"Shortlist error: {e}")
        return speak("There was an error searching the resume database.")


# ── HR: Red Flag Detection ────────────────────────────────────────────────────
def check_red_flags() -> str:
    StatusIndicator.processing("Checking resumes for red flags...")
    try:
        resumes = fetch_all_resumes()
        if not resumes:
            return speak("No resumes found in the database.")

        flagged = []
        for resume in resumes:
            flags = []
            exp = resume.get("experience_years", 0) or 0
            skills = resume.get("skills") or []

            if exp == 0:
                flags.append("no experience listed")
            if not skills:
                flags.append("no skills listed")
            if resume.get("raw_text") and len(resume["raw_text"]) < 100:
                flags.append("very short resume")

            if flags:
                flagged.append(f"{resume.get('name', 'Unknown')} ({', '.join(flags)})")

        if not flagged:
            return speak("No red flags detected across all resumes.")

        return speak(
            f"Found {len(flagged)} candidate{'s' if len(flagged) > 1 else ''} with potential issues: "
            + ". ".join(flagged[:5])
        )
    except Exception as e:
        logger.error(f"Red flag check error: {e}")
        return speak("There was an error checking for red flags.")


# ── HR: Pipeline Summary ──────────────────────────────────────────────────────
def get_pipeline_summary() -> str:
    StatusIndicator.processing("Generating pipeline summary...")
    try:
        all_resumes = fetch_all_resumes()
        shortlisted = fetch_shortlisted_candidates()

        response = (
            f"Current hiring pipeline: "
            f"{len(all_resumes)} total resume{'s' if len(all_resumes) != 1 else ''} in the database, "
            f"{len(shortlisted)} candidate{'s' if len(shortlisted) != 1 else ''} shortlisted."
        )
        return speak(response)
    except Exception as e:
        logger.error(f"Pipeline summary error: {e}")
        return speak("Could not fetch pipeline summary at this time.")
