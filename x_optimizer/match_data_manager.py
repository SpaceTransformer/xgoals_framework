import json
import os
from datetime import datetime
from typing import Dict, List
from api_client import FootballDataCollector


class MatchDataManager:
    def __init__(self, api_client: FootballDataCollector):
        self.api_client = api_client
        self.data_dir = "../match_data"
        self.ensure_data_directory()

    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📂 Directory '{self.data_dir}' creata.")
        else:
            print(f"📂 Directory '{self.data_dir}' già esistente.")

    def save_match_data(self, match_data: Dict, date: str):
        """Salva i dati della partita in un file JSON"""
        filename = f"match_{date}_{match_data['fixture']['id']}.json"
        filepath = os.path.join(self.data_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(match_data, f, ensure_ascii=False, indent=4)
            print(f"💾 File salvato: {filepath}")

    def collect_match_data(self, date: str) -> List[Dict]:
        """Raccoglie e salva i dati completi delle partite per una data"""
        print(f"\nRaccolta dati per {date}...")

        # Controlla dati esistenti
        existing_matches = []
        for filename in os.listdir(self.data_dir):
            if filename.startswith(f"match_{date}_"):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        match_data = json.load(f)
                        existing_matches.append(match_data)
                except json.JSONDecodeError:
                    print(f"File corrotto: {filename}, verrà ricreato")
                    os.remove(filepath)

        if existing_matches:
            print(f"Trovati {len(existing_matches)} match già salvati per {date}")
            return existing_matches

        # Recupero nuovi dati
        try:
            matches = self.api_client.get_matches(date)
            collected_data = []

            total_matches = len(matches['response'])
            print(f"Trovate {total_matches} partite da elaborare")

            for i, match in enumerate(matches['response'], 1):
                match_id = match['fixture']['id']
                try:
                    print(
                        f"Elaborazione partita {i}/{total_matches}: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")

                    # Recupero dati in sequenza
                    home_stats = self.api_client.get_team_stats(
                        match['teams']['home']['id'],
                        match['league']['id']
                    )
                    away_stats = self.api_client.get_team_stats(
                        match['teams']['away']['id'],
                        match['league']['id']
                    )
                    match_statistics = self.api_client.get_match_statistics(match_id)
                    match_events = self.api_client.get_match_events(match_id)
                    match_lineups = self.api_client.get_match_lineups(match_id)

                    # Nuova chiamata per i dati meteo con città e timestamp
                    city = match['fixture']['venue']['city']
                    timestamp = match['fixture']['timestamp']
                    match_weather = self.api_client.get_match_weather(match_id, city, timestamp)

                    # Componi il dizionario completo
                    match_data = {
                        'fixture': match['fixture'],
                        'league': match['league'],
                        'teams': match['teams'],
                        'goals': match['goals'],
                        'home_stats': home_stats['response'],
                        'away_stats': away_stats['response'],
                        'match_statistics': match_statistics,
                        'match_events': match_events,
                        'lineups': match_lineups,
                        'weather': match_weather
                    }

                    # Verifica la completezza dei dati
                    if all(v is not None for v in match_data.values()):
                        self.save_match_data(match_data, date)
                        collected_data.append(match_data)
                        print(f"✓ Dati completi salvati per la partita {i}/{total_matches}")
                    else:
                        print(f"⚠ Dati incompleti per la partita {i}/{total_matches}")

                except Exception as e:
                    print(f"Errore nell'elaborazione della partita {match_id}: {str(e)}")
                    continue

            success_rate = (len(collected_data) / total_matches) * 100
            print(f"Raccolti dati per {len(collected_data)}/{total_matches} partite ({success_rate:.1f}% completato)")
            return collected_data

        except Exception as e:
            print(f"Errore nella raccolta dati: {str(e)}")
            return self.load_matches_for_date(date)

    def load_matches_for_date(self, date: str) -> List[Dict]:
        """Carica le partite salvate per una specifica data"""
        matches = []
        for filename in os.listdir(self.data_dir):
            if filename.startswith(f"match_{date}_"):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)
                    matches.append(match_data)
        return matches

    def load_all_matches(self) -> List[Dict]:
        """Carica tutti i dati delle partite salvati"""
        all_matches = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)
                    all_matches.append(match_data)
        print(f"Caricati dati per {len(all_matches)} partite")
        return all_matches