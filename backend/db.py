"""
Database Module for Jarvis HR Agent
Replaces SQLite with Supabase (PostgreSQL)
"""

import logging
from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

# ── Supabase client ───────────────────────────────────────────────────────────
_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create the Supabase client (singleton)."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
            )
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialised.")
    return _supabase


# ── Conversations ─────────────────────────────────────────────────────────────
async def log_conversation(query: str, response: str, language: str = "en") -> None:
    """Log a user query and assistant response to Supabase."""
    try:
        db = get_supabase()
        db.table("conversations").insert({
            "query": query,
            "response": response,
            "language": language,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log conversation: {e}")


# ── Feedback ──────────────────────────────────────────────────────────────────
async def log_feedback(message: str, rating: Optional[int] = None) -> None:
    """Log user feedback to Supabase."""
    try:
        db = get_supabase()
        db.table("feedback").insert({
            "message": message,
            "rating": rating,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")


# ── Agent logs ────────────────────────────────────────────────────────────────
async def log_agent_action(
    session_id: str,
    agent_name: str,
    input_data: dict,
    output_data: dict,
    duration_ms: int = 0,
) -> None:
    """Log what each agent did and why."""
    try:
        db = get_supabase()
        db.table("agent_logs").insert({
            "session_id": session_id,
            "agent_name": agent_name,
            "input": input_data,
            "output": output_data,
            "duration_ms": duration_ms,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log agent action: {e}")


# ── Resumes ───────────────────────────────────────────────────────────────────
def fetch_all_resumes() -> list:
    """Fetch all resumes from Supabase."""
    try:
        db = get_supabase()
        result = db.table("resumes").select("*").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch resumes: {e}")
        return []


def search_resumes_by_skills(skills: list) -> list:
    """Search resumes that contain any of the given skills."""
    try:
        db = get_supabase()
        result = db.table("resumes").select("*").execute()
        resumes = result.data or []

        matched = []
        for resume in resumes:
            resume_skills = [s.lower() for s in (resume.get("skills") or [])]
            if any(skill.lower() in resume_skills for skill in skills):
                matched.append(resume)
        return matched
    except Exception as e:
        logger.error(f"Failed to search resumes: {e}")
        return []


def insert_resume(resume_data: dict) -> Optional[dict]:
    """Insert a parsed resume into Supabase."""
    try:
        db = get_supabase()
        result = db.table("resumes").insert(resume_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to insert resume: {e}")
        return None


# ── Candidates ────────────────────────────────────────────────────────────────
def insert_candidate(candidate_data: dict) -> Optional[dict]:
    """Insert a shortlisted candidate record."""
    try:
        db = get_supabase()
        result = db.table("candidates").insert(candidate_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to insert candidate: {e}")
        return None


def fetch_shortlisted_candidates() -> list:
    """Fetch all shortlisted candidates."""
    try:
        db = get_supabase()
        result = (
            db.table("candidates")
            .select("*, resumes(*)")
            .eq("status", "shortlisted")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch candidates: {e}")
        return []
