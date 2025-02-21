import requests
import time
from datetime import datetime
import logging
from ratelimit import limits, sleep_and_retry
from typing import Dict, List
import os


class FootballDataCollector:
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.headers = {
            'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        self.base_url = 'https://api-football-v1.p.rapidapi.com/v3'
        self.stats_cache = {}  # Cache per le statistiche
        self.daily_calls = 0
        self.MAX_DAILY_CALLS = 300
        self.team_stats_cache = {}  # Cache per statistiche squadre
        self.fixtures_cache = {}  # Cache per partite recenti

        # Lista delle leghe da monitorare
        self.monitored_leagues = {
            # Europa Top 5 (Prima e Seconda Divisione)
            'Premier League': 39,
            'Championship': 40,
            'La Liga': 140,
            'La Liga 2': 141,
            'Bundesliga': 78,
            '2. Bundesliga': 79,
            'Serie A': 135,
            'Serie B': 136,
            'Ligue 1': 61,
            'Ligue 2': 62,

            # Altri campionati europei (Prima e Seconda Divisione)
            'Eredivisie': 88,  # Olanda 1
            'Eerste Divisie': 89,  # Olanda 2
            'Primeira Liga': 94,  # Portogallo 1
            'Liga Portugal 2': 95,  # Portogallo 2
            'Super Lig': 203,  # Turchia 1
            '1. Lig': 204,  # Turchia 2
            'Super League': 207,  # Svizzera 1
            'Challenge League': 208,  # Svizzera 2
            'Pro League': 144,  # Belgio 1
            'Challenger Pro League': 145,  # Belgio 2

            # Principali campionati extra-europei (Solo Prima Divisione)
            'Serie A Brazil': 71,  # Brasile
            'Primera Division': 128,  # Argentina
            'MLS': 253,  # USA
            'J1 League': 98,  # Giappone
            'A-League': 188,  # Australia
            'Saudi Pro League': 307  # Arabia Saudita
        }

    @sleep_and_retry
    @limits(calls=1, period=2)  # Max 1 chiamata ogni 2 secondi
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        if self.daily_calls >= self.MAX_DAILY_CALLS:
            raise Exception("Limite giornaliero raggiunto")

        for attempt in range(3):  # 3 tentativi
            try:
                response = requests.get(
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                self.daily_calls += 1
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # Ultimo tentativo
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def get_team_stats(self, team_id: int, league_id: int) -> Dict:
        cache_key = f"{team_id}_{league_id}"
        if cache_key in self.team_stats_cache:
            return self.team_stats_cache[cache_key]

    def get_team_stats_batch(self, teams: List[tuple]) -> Dict:
        """Recupera statistiche per multiple squadre in una volta sola"""
        results = {}
        for team_id, league_id in teams:
            cache_key = f"{team_id}_{league_id}"
            if cache_key not in self.team_stats_cache:
                results[cache_key] = self.get_team_stats(team_id, league_id)
        return results

    def get_league_stats(self, league_id: int) -> Dict:
        """Recupera le statistiche di un'intera lega in una volta"""
        cache_key = f"league_{league_id}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        stats = self._make_request("leagues", {
            "id": league_id,
            "season": 2024
        })
        self.stats_cache[cache_key] = stats
        return stats



    def get_team_recent_form(self, team_id: int, league_id: int) -> Dict:
        """Recupera le ultime 4 partite di una squadra"""
        cache_key = f"team_form_{team_id}_{league_id}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        # Usiamo l'endpoint fixtures invece di teams/statistics
        stats = self._make_request("fixtures", {
            "team": team_id,
            "league": league_id,
            "season": 2024,
            "last": 4
        })
        self.stats_cache[cache_key] = stats
        return stats

    def get_team_stats(self, team_id: int, league_id: int) -> Dict:
        """Recupera le statistiche di una squadra specifica"""
        cache_key = f"team_{team_id}_{league_id}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        stats = self._make_request("teams/statistics", {
            "team": team_id,
            "league": league_id,
            "season": 2024
        })
        self.stats_cache[cache_key] = stats
        return stats

    def get_matches(self, date: str) -> List[Dict]:
        """Recupera solo le partite delle leghe monitorate"""
        matches = self._make_request("fixtures", {
            "date": date,
            "timezone": "Europe/Rome"
        })

        # Filtra le partite per le leghe monitorate
        filtered_matches = {
            "get": matches["get"],
            "parameters": matches["parameters"],
            "errors": matches["errors"],
            "results": matches["results"],
            "response": [
                match for match in matches["response"]
                if match["league"]["id"] in self.monitored_leagues.values()
            ]
        }

        print(f"Trovate {len(matches['response'])} partite totali")
        print(f"Filtrate {len(filtered_matches['response'])} partite dei campionati monitorati")

        return filtered_matches