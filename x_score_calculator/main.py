import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import pandas as pd
from api_client import FootballDataCollector
from xgoals_old import XGoalsCalculator


def get_date_from_input() -> str:
    """
    Gestisce l'input della data in vari formati:
    - 'oggi' o 'today'
    - 'domani' o 'tomorrow'
    - 'gg/mm' per una data specifica del 2025
    """
    while True:
        date_input = input("\nInserisci data (oggi/domani o GG/MM): ").lower().strip()

        try:
            if date_input in ['oggi', 'today']:
                date = datetime.now()
            elif date_input in ['domani', 'tomorrow']:
                date = datetime.now() + timedelta(days=1)
            else:
                # Prova a parsare il formato GG/MM
                try:
                    day, month = map(int, date_input.split('/'))
                    date = datetime(2025, month, day)
                except:
                    print("Formato non valido. Usa 'oggi', 'domani' o 'GG/MM'")
                    continue

            return date.strftime("%Y-%m-%d")

        except Exception as e:
            print(f"Errore nel parsing della data: {e}")
            continue


def analyze_daily_matches(date: str, collector: FootballDataCollector):
    print(f"\nAnalisi partite del {date}")

    # 1. Recupera le partite del giorno (già filtrate per leghe monitorate)
    matches = collector.get_matches(date)
    if not matches or len(matches['response']) == 0:
        print("Nessuna partita trovata")
        return

    # 2. Inizializza il calcolatore
    calculator = XGoalsCalculator(collector)

    # 3. Analizza le partite
    results = []
    total_matches = len(matches['response'])
    print(f"\nAnalisi di {total_matches} partite in corso...")

    for i, match in enumerate(matches['response'], 1):
        print(
            f"\nAnalisi partita {i}/{total_matches}: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
        result = calculator.calculate_xgoals(match)
        if result:
            results.append(result)
            print(f"xGoals calcolati: {result['xgoals']}")

    if not results:
        print("\nNessun risultato valido")
        return

    # 4. Crea il DataFrame e salva
    df = pd.DataFrame(results)
    df = df.sort_values('xgoals', ascending=False)

    # Configura display pandas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.expand_frame_repr', False)

    # Filtra le colonne per il CSV
    csv_df = df[['datetime', 'home_team', 'away_team', 'league', 'country', 'xgoals', 'details']]

    # Crea il percorso completo per il file
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"xgoals_{date}.csv")
    csv_df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')

    print(f"\nAnalisi completata!")
    print(f"Analizzate {len(results)}/{total_matches} partite")
    print(f"Chiamate API effettuate: {collector.daily_calls}/{collector.MAX_DAILY_CALLS}")

    print("\nTutte le partite ordinate per xGoals attesi:")
    display_df = df[['datetime', 'home_team', 'away_team', 'league', 'country', 'xgoals', 'details']]

    # Formatta le colonne
    display_df = display_df.copy()

    # Definisci le colonne di testo e numeriche
    text_columns = ['datetime', 'home_team', 'away_team', 'league', 'country', 'xgoals', 'details']
    numeric_columns = ['xgoals']

    # Formatta le colonne di testo
    for column in text_columns:
        display_df[column] = display_df[column].astype(str).str.ljust(25)

    # Formatta le colonne numeriche con 2 decimali
    for column in numeric_columns:
        display_df[column] = display_df[column].round(2)

    print(display_df.to_string())


if __name__ == "__main__":
    # Setup
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        filename=f'xgoals_{datetime.now().strftime("%Y%m%d")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Inizializza il collector
        collector = FootballDataCollector()

        # Input data con nuovo sistema
        date = get_date_from_input()
        analyze_daily_matches(date, collector)

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        logging.error(f"Errore durante l'esecuzione: {e}")