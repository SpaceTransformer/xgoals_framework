import autogen
import os
from dotenv import load_dotenv
import json
import datetime
from typing import Dict, List, Tuple, Optional
import logging
from formula_evaluator import FormulaEvaluator, FormulaParameters
from api_client import FootballDataCollector
from match_data_manager import MatchDataManager


class AlgorithmSaver:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.logger = logging.getLogger('AlgorithmSaver')

    def get_next_version(self) -> float:
        """Determina la prossima versione disponibile del file"""
        base_name = "algoritmo_xgoals"
        version = 1.0

        while True:
            file_name = f"{base_name}_v{version:.1f}.py"
            if not os.path.exists(os.path.join(self.base_dir, file_name)):
                return version
            version += 0.1

    def generate_algorithm_file(self, formula: str, parameters: Dict) -> str:
        """
        Genera un nuovo file Python contenente l'algoritmo di xGoals

        Args:
            formula: La formula matematica da implementare
            parameters: I parametri ottimizzati dell'algoritmo

        Returns:
            str: Il percorso del file generato
        """
        version = self.get_next_version()
        file_name = f"algoritmo_xgoals_v{version:.1f}.py"
        file_path = os.path.join(self.base_dir, file_name)

        # Template del codice con documentazione estesa
        code_template = f'''"""
xGoals Algorithm Version {version:.1f}
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Questo algoritmo calcola gli Expected Goals (xG) per le partite di calcio
basandosi su statistiche di gioco e condizioni ambientali.

Parametri ottimizzati attraverso machine learning su dati storici.
"""

from typing import Dict, Tuple


class XGoalsCalculator:
    def __init__(self):
        # Parametri ottimizzati
        self.parameters = {parameters}

        # Metadata
        self.version = {version:.1f}
        self.generated_date = "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def calculate_xgoals(self, match_data: Dict) -> Tuple[float, float]:
        """
        Calcola gli Expected Goals per una partita

        Args:
            match_data: Dict contenente:
                - home_stats (Dict): Statistiche squadra casa
                - away_stats (Dict): Statistiche squadra trasferta
                - weather (Dict): Condizioni meteo
                - match_statistics (List): Statistiche partita

        Returns:
            Tuple[float, float]: (home_xg, away_xg)
        """
        try:
            # Estrai statistiche
            home_stats = match_data.get('home_stats', {{}})
            away_stats = match_data.get('away_stats', {{}})
            weather = match_data.get('weather', {{}})
            match_stats = match_data.get('match_statistics', [])

            # Formula implementata
            {formula}

            return home_xg, away_xg

        except Exception as e:
            logging.error(f"Errore nel calcolo xG: {{str(e)}}")
            return 0.0, 0.0

    def get_metadata(self) -> Dict:
        """Restituisce i metadata dell'algoritmo"""
        return {{
            "version": self.version,
            "generated_date": self.generated_date,
            "parameters": self.parameters
        }}


if __name__ == "__main__":
    # Test dell'algoritmo
    calculator = XGoalsCalculator()

    # Esempio di utilizzo
    test_match = {{
        "home_stats": {{}},
        "away_stats": {{}},
        "weather": {{}},
        "match_statistics": []
    }}

    home_xg, away_xg = calculator.calculate_xgoals(test_match)
    print(f"Test Results:")
    print(f"Home xG: {{home_xg:.2f}}")
    print(f"Away xG: {{away_xg:.2f}}")
    print("\\nAlgorithm Metadata:")
    print(json.dumps(calculator.get_metadata(), indent=2))
'''

        # Salva il file
        try:
            with open(file_path, 'w') as f:
                f.write(code_template)
            self.logger.info(f"Algoritmo salvato in: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio dell'algoritmo: {str(e)}")
            return ""


class AgentProgress:
    def __init__(self, save_dir="agent_progress"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.current_session = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(save_dir, self.current_session)
        os.makedirs(self.session_dir, exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configura il sistema di logging"""
        logger = logging.getLogger('AgentProgress')
        logger.setLevel(logging.INFO)

        # Handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(os.path.join(self.session_dir, 'progress.log'))

        # Formatters
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        c_handler.setFormatter(logging.Formatter(log_format))
        f_handler.setFormatter(logging.Formatter(log_format))

        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def save_progress(self, iteration: int, formula: str, error: float,
                      chat_result: Optional[autogen.ChatResult]) -> None:
        """Salva il progresso di una singola iterazione"""
        try:
            progress_data = {
                'timestamp': str(datetime.datetime.now()),
                'iteration': iteration,
                'formula': formula,
                'error': error,
                'conversation': self._extract_conversation(chat_result)
            }

            filename = f"iteration_{iteration}.json"
            path = os.path.join(self.session_dir, filename)

            with open(path, 'w') as f:
                json.dump(progress_data, f, indent=2)

            self.logger.info(f"Progresso salvato per iterazione {iteration}")

        except Exception as e:
            self.logger.error(f"Errore nel salvataggio del progresso: {str(e)}")

    def _extract_conversation(self, chat_result: Optional[autogen.ChatResult]) -> List[Dict]:
        """Estrae i messaggi rilevanti dalla conversazione"""
        if not chat_result:
            return []

        messages = []
        try:
            for msg in chat_result.messages:
                messages.append({
                    'sender': msg.get('name', 'unknown'),
                    'content': msg.get('content', ''),
                    'role': msg.get('role', 'unknown')
                })
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione della conversazione: {str(e)}")

        return messages

    def load_best_progress(self) -> Tuple[Optional[str], float]:
        """Carica la migliore formula trovata finora"""
        best_error = float('inf')
        best_formula = None
        corrupted_files = []

        try:
            if not os.path.exists(self.save_dir):
                return None, float('inf')

            for session in os.listdir(self.save_dir):
                session_path = os.path.join(self.save_dir, session)
                if not os.path.isdir(session_path):
                    continue

                self.logger.info(f"Analisi sessione: {session}")

                for filename in os.listdir(session_path):
                    if not filename.startswith('iteration_'):
                        continue

                    file_path = os.path.join(session_path, filename)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)

                            if 'error' not in data or 'formula' not in data:
                                continue

                            if data['error'] < best_error:
                                best_error = data['error']
                                best_formula = data['formula']
                                self.logger.info(f"Nuova migliore formula trovata in {filename}")

                    except Exception as e:
                        self.logger.error(f"Errore nel file {file_path}: {str(e)}")
                        corrupted_files.append(file_path)

            if corrupted_files:
                self.logger.warning(f"Trovati {len(corrupted_files)} file corrotti")

            return best_formula, best_error

        except Exception as e:
            self.logger.error(f"Errore in load_best_progress: {str(e)}")
            return None, float('inf')


def create_sample_data_summary(match: Dict) -> Dict:
    """Crea un sommario minimale della struttura dati disponibile"""
    return {
        'teams': {
            'home': {'name': 'Example Home Team'},
            'away': {'name': 'Example Away Team'}
        },
        'stats_available': [
            'goals.for.average.home',
            'goals.against.average.home',
            'goals.for.average.away',
            'goals.against.average.away'
        ],
        'weather_available': [
            'temperature',
            'precipitation',
            'wind_speed',
            'weather_description'
        ],
        'match_stats_available': [
            'Shots on Goal',
            'Total Shots',
            'Possession'
        ]
    }


def setup_agents(historical_matches: List[Dict], progress_tracker: AgentProgress) -> List[autogen.AssistantAgent]:
    """Configura gli agenti per l'ottimizzazione"""
    config_list = [{"model": "gpt-4o-mini",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "temperature": 0.3,
                    "timeout": 600,
                    "cache_seed": 42
                    }]

    # Crea sommario dati
    data_summary = create_sample_data_summary(historical_matches[0])

    # Carica migliori risultati precedenti
    best_formula, best_error = progress_tracker.load_best_progress()
    previous_results = (
        f"\nMiglior formula precedente (errore: {best_error:.2f})"
        if best_formula else ""
    )

    # Template base per i messaggi di sistema
    base_system_template = """Ruolo: {role}

STRUTTURA DATI DISPONIBILE:
{data_summary}

FORMULE ESISTENTI:
{previous_results}

OBIETTIVI SPECIFICI:
{objectives}

IMPORTANTE:
- Lavora con le statistiche disponibili
- Proponi modifiche incrementali
- Considera l'impatto di tutti i fattori"""

    # Configurazioni specifiche per ogni agente
    agent_configs = {
        "data_analyst": {
            "name": "data_analyst",
            "role": "Analista Dati per Ottimizzazione xGoals",
            "objectives": [
                "Analizza le statistiche disponibili",
                "Valuta l'impatto delle condizioni meteo",
                "Proponi modifiche alle formule esistenti"
            ]
        },
        "statistical_expert": {
            "name": "statistical_expert",
            "role": "Esperto di Statistica Calcistica",
            "objectives": [
                "Analizza correlazioni tra statistiche e gol",
                "Proponi pesi ottimali per le variabili",
                "Valuta l'impatto del fattore casa"
            ]
        },
        "test_engineer": {
            "name": "test_engineer",
            "role": "Ingegnere di Test per Modelli Predittivi",
            "objectives": [
                "Verifica la robustezza delle formule",
                "Analizza gli errori estremi",
                "Proponi miglioramenti basati sui test"
            ]
        }
    }

    # Crea gli agenti
    agents = []
    for config in agent_configs.values():
        system_message = base_system_template.format(
            role=config["role"],
            data_summary=json.dumps(data_summary, indent=2),
            previous_results=previous_results,
            objectives="\n".join(f"- {obj}" for obj in config["objectives"])
        )

        agent = autogen.AssistantAgent(
            name=config["name"],
            system_message=system_message,
            llm_config={
                "config_list": config_list,
                "temperature": 0.3
            }
        )
        agents.append(agent)

    return agents


def prepare_match_data(match: Dict) -> Dict:
    """Prepara i dati della partita nel formato richiesto"""
    return {
        'teams': match['teams'],
        'goals': match['goals'],
        'home_stats': match['home_stats'],
        'away_stats': match['away_stats'],
        'match_statistics': match['match_statistics']['response'] if match['match_statistics']['response'] else [],
        'weather': match['weather']
    }


def main():
    # Inizializzazione
    load_dotenv()
    progress_tracker = AgentProgress()
    algorithm_saver = AlgorithmSaver()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('XGoalsOptimizer')

    try:
        # Inizializza il data manager
        data_manager = MatchDataManager(FootballDataCollector())
        logger.info("Data manager inizializzato")

        # Carica le partite
        historical_matches = data_manager.load_all_matches()
        if not historical_matches:
            logger.error("Nessuna partita trovata")
            return

        logger.info(f"Caricate {len(historical_matches)} partite per l'analisi")

        # Prepara i dati
        processed_matches = [prepare_match_data(match) for match in historical_matches]
        logger.info("Dati processati e preparati per l'analisi")

        # Setup degli agenti
        agents = setup_agents(historical_matches, progress_tracker)
        groupchat = autogen.GroupChat(agents=agents, messages=[], max_round=30)
        manager = autogen.GroupChatManager(groupchat=groupchat)

        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            code_execution_config={"use_docker": False},
            human_input_mode="NEVER"
        )

        best_overall_formula = None
        best_overall_error = float('inf')
        best_parameters = None

        # Iterazioni di ottimizzazione
        for iteration in range(5):
            logger.info(f"\nAvvio iterazione {iteration + 1}/5")

            # Messaggio iniziale per questa iterazione
            initial_message = f'''Iterazione {iteration + 1} di ottimizzazione xGoals.

Dati disponibili: {len(processed_matches)} partite complete con:
- Statistiche partita (tiri, possesso, ecc.)
- Statistiche stagionali squadre
- Dati meteo
- Risultati finali

Data Analyst, analizza le statistiche e proponi miglioramenti alla formula.'''

            try:
                # Avvia la conversazione
                chat_result = user_proxy.initiate_chat(manager, message=initial_message)

                # Estrai e valuta la formula proposta
                evaluator = FormulaEvaluator(processed_matches)
                formula_result = evaluator.test_formula2_detailed(FormulaParameters())
                current_error = formula_result['avg_error']

                # Aggiorna la migliore formula se necessario
                if current_error < best_overall_error:
                    best_overall_formula = evaluator.best_formula
                    best_overall_error = current_error
                    best_parameters = evaluator.parameters.__dict__

                    # Salva immediatamente la nuova migliore formula
                    logger.info(f"Nuova migliore formula trovata (errore: {best_overall_error:.2f})")
                    algorithm_saver.generate_algorithm_file(
                        formula=best_overall_formula,
                        parameters=best_parameters
                    )

                # Salva il progresso dell'iterazione
                progress_tracker.save_progress(
                    iteration + 1,
                    evaluator.best_formula,
                    current_error,
                    chat_result
                )

                logger.info(f"Risultati iterazione {iteration + 1}:")
                logger.info(f"Errore medio: {current_error:.2f}")
                logger.info(f"Distribuzione errori: {formula_result['error_distribution']}")

                # Verifica se abbiamo raggiunto un errore sufficientemente basso
                if current_error <= 0.5:
                    logger.info("Raggiunto errore target. Terminazione anticipata.")
                    break

            except Exception as e:
                logger.error(f"Errore durante l'iterazione {iteration + 1}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Errore durante l'ottimizzazione: {str(e)}")
    finally:
        # Salva l'algoritmo finale se abbiamo trovato una formula valida
        if best_overall_formula and best_parameters:
            final_algorithm_path = algorithm_saver.generate_algorithm_file(
                formula=best_overall_formula,
                parameters=best_parameters
            )
            logger.info(f"Algoritmo finale salvato in: {final_algorithm_path}")

        # Riepilogo finale
        logger.info("\nOttimizzazione completata!")
        logger.info(f"Risultati salvati in: {progress_tracker.session_dir}")
        logger.info(f"Miglior errore ottenuto: {best_overall_error:.2f}")


if __name__ == "__main__":
    main()