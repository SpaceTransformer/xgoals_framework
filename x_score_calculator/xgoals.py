
class XGoalsCalculator:
    def __init__(self, api_client=None):
        self.api_client = api_client

    def calculate_xgoals(self, match):
        # Gestione sicura dell'accesso ai dati statistici
        try:
            # Verifica se le statistiche sono disponibili direttamente
            if 'statistics' in match:
                home_stats = self._find_team_stats(match['statistics'], 'home')
                away_stats = self._find_team_stats(match['statistics'], 'away')
            # Alternativa: verifica se sono nelle sotto-chiavi
            elif 'response' in match and len(match['response']) > 0 and 'statistics' in match['response'][0]:
                home_stats = self._find_team_stats(match['response'][0]['statistics'], 'home')
                away_stats = self._find_team_stats(match['response'][0]['statistics'], 'away')
            else:
                # Usa valori basati sui gol effettivi se le statistiche non sono disponibili
                return {'xgoals': match['goals']['home'] + match['goals']['away']}

            # Estrai i dati con gestione degli errori
            shots_home = self._safe_get(home_stats, 'shots_on_target', 0)
            shots_away = self._safe_get(away_stats, 'shots_on_target', 0)
            possession_home = self._safe_get(home_stats, 'possession', 50)
            possession_away = self._safe_get(away_stats, 'possession', 50)

            shots = shots_home + shots_away
            possession = (possession_home + possession_away) / 2

            return {'xgoals': 0.05 * shots + 0.02 * possession}

        except Exception as e:
            print(f"Errore nel calcolo degli xGoals: {e}")
            # Valore fallback basato sui gol effettivi
            return {'xgoals': match['goals']['home'] + match['goals']['away']}

    def _find_team_stats(self, statistics, team_type):
        # Cerca le statistiche della squadra home/away nella struttura dei dati
        # Se le statistiche sono una lista di elementi (es. API di Football-data)
        if isinstance(statistics, list):
            for stat_item in statistics:
                if 'team' in stat_item and 'type' in stat_item['team'] and stat_item['team']['type'] == team_type:
                    return stat_item
                elif 'type' in stat_item and stat_item['type'] == team_type:
                    return stat_item
        # Se le statistiche sono un dizionario con chiavi home/away
        elif isinstance(statistics, dict) and team_type in statistics:
            return statistics[team_type]

        # Se non troviamo nulla, restituiamo un dizionario vuoto
        return {}

    def _safe_get(self, stats_dict, key, default_value=0):
        # Estrae in modo sicuro un valore statistico, gestendo diversi formati di dati
        if isinstance(stats_dict, dict):
            # Cerca direttamente nella chiave
            if key in stats_dict:
                val = stats_dict[key]
            # Cerca nella struttura nidificata comune in alcune API
            elif 'statistics' in stats_dict:
                for stat in stats_dict['statistics']:
                    if isinstance(stat, dict) and 'type' in stat and stat['type'] == key:
                        val = stat.get('value', default_value)
                        if val is None:
                            return default_value
                        return self._parse_stat_value(val)
                return default_value
            else:
                return default_value

            return self._parse_stat_value(val)
        return default_value

    def _parse_stat_value(self, value):
        # Converte il valore della statistica in formato numerico
        if value is None:
            return 0

        # Gestisce valori percentuali (es. "56%")
        if isinstance(value, str):
            value = value.strip()
            if value.endswith('%'):
                try:
                    return float(value[:-1])
                except ValueError:
                    return 0
            try:
                return float(value)
            except ValueError:
                return 0

        return float(value) if isinstance(value, (int, float)) else 0
