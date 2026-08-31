import os
import requests
from typing import Dict, Any, List, Optional

class OddsApiClient:
    """Client for The Odds API (odds-api.com) for betting odds feeds."""
    BASE_URL = "https://api.the-odds-api.com/v4/sports"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")

    def get_odds(self, sport_key: str = "soccer_epl", regions: str = "eu", markets: str = "h2h,totals") -> List[Dict[str, Any]]:
        """Fetch betting odds for a given sport (e.g., 'soccer_epl', 'soccer_spain_la_liga')."""
        if not self.api_key:
            raise ValueError("The Odds API Key is required.")
        url = f"{self.BASE_URL}/{sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
