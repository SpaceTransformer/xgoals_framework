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
        if not self.api_key:
            raise ValueError("❌ RAPIDAPI_KEY non trovata nelle variabili d'ambiente. Controlla il file .env.")

        self.headers = {
            'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        self.base_url = 'https://api-football-v1.p.rapidapi.com/v3'
        self.stats_cache = {}  # Cache per le statistiche
        self.daily_calls = 0
        self.MAX_DAILY_CALLS = 7500  # Aggiornato per piano Pro
        self.team_stats_cache = {}  # Cache per statistiche squadre
        self.fixtures_cache = {}  # Cache per partite recenti

        # Lista delle leghe da monitorare
        self.monitored_leagues = {
            # Competizioni UEFA
            'Champions League': 2,
            'Europa League': 3,
            'Conference League': 848,

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

    def clean_city_name(self, city: str) -> str:
        """Pulisce il nome della città rimuovendo informazioni aggiuntive"""
        # Dizionario delle sostituzioni per casi specifici
        city_replacements = {
            "Ciudad de Córdoba, Provincia de Córdoba": "Cordoba,Argentina",
            "Capital Federal, Ciudad de Buenos Aires": "Buenos Aires,Argentina",
            "Junín, Provincia de Buenos Aires": "Junin,Argentina",
            "La Plata, Provincia de Buenos Aires": "La Plata,Argentina"
        }

        # Controlla se la città è nel dizionario delle sostituzioni
        if city in city_replacements:
            return city_replacements[city]

        # Se non è nel dizionario, prendi solo la prima parte (prima della virgola)
        if "," in city:
            return city.split(",")[0].strip()

        return city

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

    def get_team_recent_form(self, team_id: int, league_id: int) -> Dict:
        """Recupera le ultime 4 partite di una squadra"""
        cache_key = f"team_form_{team_id}_{league_id}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        stats = self._make_request("fixtures", {
            "team": team_id,
            "league": league_id,
            "season": 2024,
            "last": 4
        })
        self.stats_cache[cache_key] = stats
        return stats

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

    def get_match_statistics(self, fixture_id: int) -> Dict:
        """Recupera statistiche dettagliate della partita"""
        return self._make_request("fixtures/statistics", {
            "fixture": fixture_id
        })

    def get_match_events(self, fixture_id: int) -> Dict:
        """Recupera eventi della partita (goals, cards, subs)"""
        return self._make_request("fixtures/events", {
            "fixture": fixture_id
        })

    def get_match_lineups(self, fixture_id: int) -> Dict:
        """Recupera formazioni e info giocatori"""
        return self._make_request("fixtures/lineups", {
            "fixture": fixture_id
        })

    def get_match_weather(self, fixture_id: int, city: str, match_timestamp: int) -> Dict:
        """Recupera le condizioni meteorologiche dalla API di Open-Meteo usando la città"""

        def get_weather_description(weather_code):
            weather_codes = {
                0: "Cielo sereno",
                1: "Prevalentemente sereno",
                2: "Parzialmente nuvoloso",
                3: "Cielo coperto",
                45: "Nebbia",
                48: "Nebbia con brina",
                51: "Pioggerella leggera",
                53: "Pioggerella moderata",
                55: "Pioggerella intensa",
                61: "Pioggia leggera",
                63: "Pioggia moderata",
                65: "Pioggia intensa",
                71: "Neve leggera",
                73: "Neve moderata",
                75: "Neve intensa",
                77: "Neve a chicchi",
                80: "Acquazzoni leggeri",
                81: "Acquazzoni moderati",
                82: "Acquazzoni violenti",
                85: "Nevicate leggere",
                86: "Nevicate intense",
                95: "Temporale",
                96: "Temporale con grandine leggera",
                99: "Temporale con grandine intensa"
            }
            return weather_codes.get(weather_code, "Condizioni meteo non classificate")

        try:
            # Pulisci il nome della città
            clean_city = self.clean_city_name(city)

            # Converti il timestamp in data/ora
            match_date = datetime.fromtimestamp(match_timestamp)

            # Prima otteniamo le coordinate della città
            print(f"Recupero coordinate per la città: {clean_city} (originale: {city})")
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=1"
            geocoding_response = requests.get(geocoding_url)
            location_data = geocoding_response.json()

            if not location_data.get("results"):
                print(f"Città non trovata: {clean_city}")
                return {}

            lat = location_data["results"][0]["latitude"]
            lon = location_data["results"][0]["longitude"]

            # Ora prendiamo i dati meteo
            print(f"Recupero dati meteo per {clean_city} ({lat}, {lon}) del {match_date}")
            weather_url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": match_date.strftime("%Y-%m-%d"),
                "end_date": match_date.strftime("%Y-%m-%d"),
                "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
                "timezone": "Europe/Rome"
            }

            weather_response = requests.get(weather_url, params=params)
            weather_data = weather_response.json()

            # Estrai i dati dell'ora della partita
            match_hour = match_date.hour

            weather_code = weather_data["hourly"]["weathercode"][match_hour]
            weather_info = {
                "city": city,
                "temperature": weather_data["hourly"]["temperature_2m"][match_hour],
                "precipitation": weather_data["hourly"]["precipitation"][match_hour],
                "wind_speed": weather_data["hourly"]["windspeed_10m"][match_hour],
                "weather_code": weather_code,
                "weather_description": get_weather_description(weather_code),
                "timestamp": match_timestamp
            }

            print(f"Dati meteo recuperati con successo per {clean_city}")
            return weather_info

        except Exception as e:
            print(f"Errore nel recupero dati meteo per {fixture_id} ({city}): {str(e)}")
            return {}

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