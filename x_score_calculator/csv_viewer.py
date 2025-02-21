import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
from datetime import datetime
import tempfile
import webbrowser
from pathlib import Path
from dateutil import parser
import csv

class CSVViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xGoals Viewer")
        self.root.geometry("1200x600")

        # Frame per i pulsanti
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.load_button = tk.Button(button_frame, text="Carica CSV", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.print_button = tk.Button(button_frame, text="Esporta per Stampa", command=self.prepare_print)
        self.print_button.pack(side=tk.LEFT, padx=5)

        # Treeview per visualizzare i dati
        self.tree = ttk.Treeview(root)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        vsb = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)

    def detect_separator(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            sample = csvfile.read(2048)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter

    def format_date(self, date_str):
        try:
            date_str = str(date_str).strip()
            date_obj = parser.parse(date_str)
            return date_obj.strftime('%d/%m/%y - %H:%M')
        except Exception as e:
            print(f"Errore nel formato data: {e}")
            return date_str

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.display_csv(file_path)

    def display_csv(self, file_path):
        try:
            delimiter = self.detect_separator(file_path)
            print(f"Separatore rilevato: '{delimiter}'")
            df = pd.read_csv(file_path, encoding="utf-8", sep=delimiter)
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore: {e}")
            return

        # Formatta la data
        if 'datetime' in df.columns:
            df['datetime'] = df['datetime'].apply(self.format_date)

        # Rimuove la colonna details e aggiunge risultato_reale
        if 'details' in df.columns:
            df = df.drop('details', axis=1)
        df['risultato_reale'] = ''  # Aggiunge colonna vuota per i risultati

        self.df = df  # Salva il DataFrame per la stampa

        for widget in self.tree.get_children():
            self.tree.delete(widget)

        self.tree['columns'] = list(df.columns)
        self.tree['show'] = 'headings'

        # Definizione larghezze colonne
        column_widths = {
            "datetime": 150,
            "home_team": 150,
            "away_team": 150,
            "league": 200,
            "country": 100,
            "xgoals": 80,
            "risultato_reale": 100
        }

        for col in df.columns:
            self.tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.tree.column(col, width=width)

        for row in df.itertuples(index=False):
            self.tree.insert('', tk.END, values=row)

    def prepare_print(self):
        if not hasattr(self, 'df'):
            messagebox.showwarning("Attenzione", "Carica prima un file CSV")
            return

        try:
            # Crea un file HTML formattato per la stampa
            temp_dir = tempfile.gettempdir()
            html_file = Path(temp_dir) / 'xgoals_print.html'

            # Stile CSS per la tabella
            html_content = '''
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
                @media print {
                    table { page-break-inside: auto }
                    tr { page-break-inside: avoid; page-break-after: auto }
                    thead { display: table-header-group }
                    @page {
                        size: landscape;
                        margin: 1cm;
                    }
                }
            </style>
            </head>
            <body>
            '''

            # Converti il DataFrame in HTML con stili
            html_content += self.df.to_html(index=False)
            html_content += '</body></html>'

            # Salva il file HTML
            html_file.write_text(html_content, encoding='utf-8')

            # Apri il file nel browser predefinito
            webbrowser.open(html_file.as_uri())

            messagebox.showinfo("File Pronto",
                                "Il file è stato preparato per la stampa e aperto nel tuo browser.\\n"
                                "Usa la funzione di stampa del browser (CTRL+P o CMD+P) per stampare il documento.")

        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore durante la preparazione del file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVViewerApp(root)
    root.mainloop()
