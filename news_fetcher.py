"""
News Fetcher Module for Jarvis HR Agent
Uses NewsAPI to fetch top articles by keyword.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_news(self, keyword: str, top_n: int = 3) -> list:
        """
        Fetch top N news articles for a given keyword.

        Returns:
            List of dicts with 'title' and 'url'
        """
        params = {
            "q": keyword,
            "apiKey": self.api_key,
            "pageSize": top_n,
            "sortBy": "publishedAt",
            "language": "en",
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            return [{"title": a["title"], "url": a["url"]} for a in articles[:top_n]]
        except requests.exceptions.RequestException as e:
            logger.error(f"News fetch error: {e}")
            return []
