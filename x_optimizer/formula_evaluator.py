class FormulaParameters:
    def __init__(self):
        self.home_weight = 0.6
        self.away_weight = 0.4
        self.off_weight = 0.55
        self.def_weight = 0.45
        self.league_factor = 1.0

    def adjust(self, error):
        """Aggiusta i parametri in base all'errore"""
        step = 0.05
        if error > 1.0:
            self.home_weight = min(0.8, self.home_weight + step)
            self.away_weight = 1 - self.home_weight
            self.off_weight = min(0.7, self.off_weight + step)
            self.def_weight = 1 - self.off_weight


class FormulaEvaluator:
    def __init__(self, historical_matches):
        self.historical_matches = historical_matches
        self.best_formula = None
        self.best_error = float('inf')
        self.parameters = FormulaParameters()

    @staticmethod
    def formula2(match, params):
        """Formula 2: basata sulla forza relativa"""
        home_stats = match['home_stats']
        away_stats = match['away_stats']

        # Estrai e converti le statistiche
        hs = float(str(home_stats['goals']['for']['average']['home']).replace(',', '.'))
        hc = float(str(home_stats['goals']['against']['average']['home']).replace(',', '.'))
        aws = float(str(away_stats['goals']['for']['average']['away']).replace(',', '.'))
        awc = float(str(away_stats['goals']['against']['average']['away']).replace(',', '.'))

        # Calcola la media del campionato
        league_avg = (
                             float(str(home_stats['goals']['for']['average']['total']).replace(',', '.')) +
                             float(str(away_stats['goals']['for']['average']['total']).replace(',', '.')
                                   )) / 2

        # Previeni divisione per zero
        league_avg = max(league_avg, 0.1)
        hc = max(hc, 0.1)
        awc = max(awc, 0.1)

        # Calcola la forza relativa delle squadre
        home_strength = (hs / league_avg) * (1 / (hc / league_avg))
        away_strength = (aws / league_avg) * (1 / (awc / league_avg))

        # Calcola xgoals basati sulla forza relativa
        home_xg = league_avg * home_strength * params.home_weight
        away_xg = league_avg * away_strength * params.away_weight

        return home_xg + away_xg

    def test_formula2_detailed(self, params):
        """Test dettagliato della Formula 2 con analisi degli errori"""
        analyses = []
        total_error = 0
        error_distribution = {'Buono': 0, 'Accettabile': 0, 'Alto': 0, 'Molto Alto': 0}

        for match in self.historical_matches:
            try:
                predicted = self.formula2(match, params)
                actual = match['goals']['home'] + match['goals']['away']
                error = abs(predicted - actual)

                # Categorizza l'errore
                if error <= 0.5:
                    category = 'Buono'
                elif error <= 1.0:
                    category = 'Accettabile'
                elif error <= 2.0:
                    category = 'Alto'
                else:
                    category = 'Molto Alto'

                error_distribution[category] += 1
                total_error += error

                analyses.append({
                    'match': f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                    'predicted': round(predicted, 2),
                    'actual': actual,
                    'error': round(error, 2),
                    'category': category
                })

            except Exception as e:
                print(f"Errore nell'analisi della partita: {e}")
                continue

        avg_error = total_error / len(analyses) if analyses else float('inf')

        return {
            'analyses': analyses,
            'avg_error': avg_error,
            'error_distribution': error_distribution
        }

    def test_formula(self, formula_func, formula_name):
        """
        Testa una formula specifica sui dati storici
        formula_func: funzione che prende i dati di una partita e restituisce xgoals
        """
        total_error = 0
        valid_matches = 0
        accurates = 0  # partite con errore <= 0.5

        for match in self.historical_matches:
            try:
                predicted = formula_func(match, self.parameters)
                actual = match['goals']['home'] + match['goals']['away']
                error = abs(predicted - actual)

                total_error += error
                valid_matches += 1
                if error <= 0.5:
                    accurates += 1

            except Exception as e:
                print(f"Errore nell'analisi della partita: {e}")
                continue

        avg_error = total_error / valid_matches if valid_matches > 0 else float('inf')
        accuracy = (accurates / valid_matches * 100) if valid_matches > 0 else 0

        print(f"\nRisultati formula '{formula_name}':")
        print(f"Errore medio: {avg_error:.2f} gol")
        print(f"Accuratezza (errore <= 0.5): {accuracy:.2f}%")
        print(f"Partite accurate: {accurates}/{valid_matches}")
        print(
            f"Parametri usati: home_weight={self.parameters.home_weight:.2f}, off_weight={self.parameters.off_weight:.2f}")

        if avg_error < self.best_error:
            self.best_formula = formula_name
            self.best_error = avg_error

        # Aggiusta i parametri per la prossima iterazione
        self.parameters.adjust(avg_error)

        return avg_error, accuracy


def test_formulas(historical_matches):
    evaluator = FormulaEvaluator(historical_matches)

    # Formula 1: originale modificata con pesi
    def formula1(match, params):
        home_stats = match['home_stats']
        away_stats = match['away_stats']

        # Estrai e converti le statistiche
        hs = float(str(home_stats['goals']['for']['average']['home']).replace(',', '.'))
        hc = float(str(home_stats['goals']['against']['average']['home']).replace(',', '.'))
        aws = float(str(away_stats['goals']['for']['average']['away']).replace(',', '.'))
        awc = float(str(away_stats['goals']['against']['average']['away']).replace(',', '.'))

        # Calcola la media del campionato
        league_avg = (
                             float(str(home_stats['goals']['for']['average']['total']).replace(',', '.')) +
                             float(str(away_stats['goals']['for']['average']['total']).replace(',', '.')
                                   )) / 2

        # Prospettiva offensiva pesata
        off_perspective = (hs * params.home_weight + aws * params.away_weight)

        # Prospettiva difensiva pesata
        def_perspective = (hc * params.away_weight + awc * params.home_weight)

        # Media pesata finale
        xgoals = (off_perspective * params.off_weight + def_perspective * params.def_weight) * (league_avg / 2.5)

        return xgoals

    # Formula 3: media ponderata con fattore difensivo
    def formula3(match, params):
        home_stats = match['home_stats']
        away_stats = match['away_stats']

        # Estrai e converti le statistiche
        hs = float(str(home_stats['goals']['for']['average']['home']).replace(',', '.'))
        hc = float(str(home_stats['goals']['against']['average']['home']).replace(',', '.'))
        aws = float(str(away_stats['goals']['for']['average']['away']).replace(',', '.'))
        awc = float(str(away_stats['goals']['against']['average']['away']).replace(',', '.'))

        # Fattore difensivo
        home_def_factor = 1 / (hc + 0.5)
        away_def_factor = 1 / (awc + 0.5)

        # xgoals pesati con fattore difensivo
        xgoals = ((hs * home_def_factor * params.home_weight) +
                  (aws * away_def_factor * params.away_weight)) * params.league_factor

        return xgoals

    # Test delle formule
    print("\nTesting Formula 1 - Pesi differenziati")
    evaluator.test_formula(formula1, "Formula 1 - Pesi differenziati")

    print("\nTesting Formula 2 - Forza relativa")
    evaluator.test_formula(evaluator.formula2, "Formula 2 - Forza relativa")

    print("\nTesting Formula 3 - Fattore difensivo")
    evaluator.test_formula(formula3, "Formula 3 - Fattore difensivo")

    return evaluator.best_formula, evaluator.best_error