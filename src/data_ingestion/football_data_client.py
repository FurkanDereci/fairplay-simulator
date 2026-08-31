import os
import requests
from typing import Dict, Any, Optional

class FootballDataClient:
    """Client for Football-Data.org API (Fixtures, Matches, Standings)."""
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY", "")
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

    def get_matches(self, competition_code: str = "PL") -> Dict[str, Any]:
        """Fetch scheduled/upcoming matches for a competition (e.g., 'PL', 'PD', 'SA', 'CL')."""
        if not self.api_key:
            raise ValueError("Football-Data.org API Key is required.")
        url = f"{self.BASE_URL}/competitions/{competition_code}/matches"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
