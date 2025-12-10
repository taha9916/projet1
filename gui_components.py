import tkinter as tk
from tkinter import ttk, filedialog
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
from config import UI_CONFIG, SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)

class FileSelectionFrame(ttk.Frame):
    """Cadre pour la sélection de fichiers."""
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.file_path = ""
        self._create_widgets()
    
    def _create_widgets(self):
        # Label
        self.label = ttk.Label(self, text="Sélectionnez un fichier à analyser:")
        self.label.pack(pady=UI_CONFIG["padding"])
        
        # Champ de texte pour afficher le chemin du fichier
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(self, textvariable=self.path_var, width=50)
        self.path_entry.pack(pady=5, fill=tk.X, expand=True)
        
        # Bouton de parcours
        self.browse_button = ttk.Button(self, text="Parcourir", command=self.browse_file)
        self.browse_button.pack(pady=5)
    
    def browse_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un ou plusieurs fichiers."""
        filetypes = [(k, v) for k, v in SUPPORTED_FILE_TYPES.items()]
        file_paths = filedialog.askopenfilenames(filetypes=filetypes)
        
        if file_paths:
            # Convertir le tuple en liste pour faciliter la manipulation
            file_paths = list(file_paths)
            self.file_path = file_paths  # Stocker tous les chemins de fichiers
            
            # Afficher le nombre de fichiers sélectionnés dans le champ de texte
            if len(file_paths) == 1:
                self.path_var.set(file_paths[0])
                logger.info(f"Fichier sélectionné: {file_paths[0]}")
            else:
                self.path_var.set(f"{len(file_paths)} fichiers sélectionnés")
                logger.info(f"{len(file_paths)} fichiers sélectionnés: {', '.join(file_paths)}")
            
            if self.callback:
                self.callback(file_paths)
    
    def get_file_path(self):
        """Retourne le chemin du fichier sélectionné."""
        return self.file_path

class StatusBar(ttk.Frame):
    """Barre de statut pour afficher les messages."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._create_widgets()
    
    def _create_widgets(self):
        # Label de statut
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill=tk.X, expand=True, pady=5)
        
        # Barre de progression
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, expand=True, pady=5)
    
    def set_status(self, message, progress=None):
        """Met à jour le message de statut et la barre de progression."""
        self.status_var.set(message)
        
        if progress is not None:
            self.progress['value'] = progress
        
        # Mettre à jour l'interface
        self.update_idletasks()

class DataPreviewFrame(ttk.Frame):
    """Cadre pour prévisualiser les données."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._create_widgets()
    
    def _create_widgets(self):
        # Label
        self.label = ttk.Label(self, text="Aperçu des données:")
        self.label.pack(pady=UI_CONFIG["padding"])
        
        # Treeview pour afficher les données
        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
    
    def display_dataframe(self, df):
        """Affiche un DataFrame dans le Treeview."""
        # Effacer les données existantes
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Configurer les colonnes
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"
        
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Ajouter les données
        for i, row in df.iterrows():
            values = [row[col] for col in df.columns]
            self.tree.insert("", "end", values=values)
    
    def update_data(self, df):
        """Met à jour les données affichées."""
        self.display_dataframe(df)

class DataVisualizationFrame(ttk.Frame):
    """Cadre pour visualiser les données."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.canvas = None
        self._create_widgets()
    
    def _create_widgets(self):
        # Label
        self.label = ttk.Label(self, text="Visualisation des données:")
        self.label.pack(pady=UI_CONFIG["padding"])
        
        # Canvas pour le graphique
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_data(self, df, x_col=None, y_col=None, plot_type="bar"):
        """Crée un graphique à partir des données."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            if plot_type == "bar":
                df.plot(kind="bar", x=x_col, y=y_col, ax=ax, legend=True)
            elif plot_type == "line":
                df.plot(kind="line", x=x_col, y=y_col, ax=ax, legend=True)
            elif plot_type == "scatter":
                df.plot(kind="scatter", x=x_col, y=y_col, ax=ax)
        else:
            # Graphique par défaut si les colonnes ne sont pas spécifiées
            if len(df) > 0:
                df.iloc[:10].plot(kind="bar", ax=ax, legend=True)
        
        ax.set_title("Visualisation des données")
        ax.set_xlabel(x_col if x_col else "")
        ax.set_ylabel(y_col if y_col else "")
        
        self.canvas.draw()
    
    def update_data(self, df):
        """Met à jour les données visualisées."""
        # Déterminer les colonnes à visualiser
        if 'Milieu' in df.columns and 'Paramètre' in df.columns:
            # Créer un graphique de répartition par milieu
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Compter les paramètres par milieu
            milieu_counts = df['Milieu'].value_counts()
            milieu_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
            
            ax.set_title("Répartition des paramètres par milieu")
            ax.set_ylabel('')
            
            self.canvas.draw()
        else:
            # Utiliser le plot_data par défaut
            self.plot_data(df)

class ToolbarFrame(ttk.Frame):
    """Barre d'outils avec boutons d'action."""
    def __init__(self, parent, commands=None):
        super().__init__(parent)
        self.parent = parent
        self.commands = commands or {}
        self._create_widgets()
    
    def _create_widgets(self):
        # Conteneur pour les boutons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, expand=True)
        
        # Boutons standard
        standard_buttons = {
            "Analyser": "analyze",
            "Analyser texte": "analyze_text",
            "Enregistrer": "save",
            "Visualiser": "visualize",
            "Aide": "help"
        }
        
        # Créer les boutons
        for text, command_key in standard_buttons.items():
            command = self.commands.get(command_key, lambda: None)
            button = ttk.Button(button_frame, text=text, command=command)
            button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def add_button(self, text, command):
        """Ajoute un bouton à la barre d'outils."""
        button = ttk.Button(self, text=text, command=command)
        button.pack(side=tk.LEFT, padx=5, pady=5)
        return button
    
    def enable_button(self, button_key):
        """Active un bouton spécifique."""
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for button in widget.winfo_children():
                    if isinstance(button, ttk.Button):
                        button_text = button.cget("text")
                        if (button_key == "save" and button_text == "Enregistrer") or \
                           (button_key == "analyze" and button_text == "Analyser") or \
                           (button_key == "analyze_text" and button_text == "Analyser texte") or \
                           (button_key == "visualize" and button_text == "Visualiser") or \
                           (button_key == "help" and button_text == "Aide"):
                            button.config(state=tk.NORMAL)
                            return True
        return False
    
    def disable_button(self, button_key):
        """Désactive un bouton spécifique."""
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for button in widget.winfo_children():
                    if isinstance(button, ttk.Button):
                        button_text = button.cget("text")
                        if (button_key == "save" and button_text == "Enregistrer") or \
                           (button_key == "analyze" and button_text == "Analyser") or \
                           (button_key == "analyze_text" and button_text == "Analyser texte") or \
                           (button_key == "visualize" and button_text == "Visualiser") or \
                           (button_key == "help" and button_text == "Aide"):
                            button.config(state=tk.DISABLED)
                            return True
        return False

class ResultsFrame(ttk.Frame):
    """Cadre pour afficher les résultats de l'analyse."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._create_widgets()
    
    def _create_widgets(self):
        # Créer un widget Text avec scrollbar pour afficher les résultats
        self.text_frame = ttk.Frame(self)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.scrollbar = ttk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text = tk.Text(self.text_frame, wrap=tk.WORD, yscrollcommand=self.scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text.config(state=tk.DISABLED)  # Lecture seule par défaut
        
        self.scrollbar.config(command=self.text.yview)
    
    def update_results(self, project_info=None, data=None):
        """Met à jour les résultats affichés."""
        self.text.config(state=tk.NORMAL)  # Permettre l'édition
        self.text.delete(1.0, "end")  # Effacer le contenu existant
        
        # Afficher les informations du projet si disponibles
        if project_info:
            self.text.insert("end", "INFORMATIONS DU PROJET\n", "heading")
            self.text.insert("end", "======================\n\n")
            
            for key, value in project_info.items():
                self.text.insert("end", f"{key}: {value}\n")
            
            self.text.insert("end", "\n")
        
        # Afficher les statistiques des données si disponibles
        if data is not None and not data.empty:
            self.text.insert("end", "RÉSUMÉ DES DONNÉES\n", "heading")
            self.text.insert("end", "=================\n\n")
            
            # Nombre total de paramètres
            total_params = len(data)
            self.text.insert("end", f"Nombre total de paramètres: {total_params}\n\n")
            
            # Répartition par milieu
            if 'Milieu' in data.columns:
                self.text.insert("end", "Répartition par milieu:\n")
                milieu_counts = data['Milieu'].value_counts()
                for milieu, count in milieu_counts.items():
                    percentage = (count / total_params) * 100
                    self.text.insert("end", f"  - {milieu}: {count} ({percentage:.1f}%)\n")
                self.text.insert("end", "\n")
            
            # Résultats de conformité
            if 'Résultat conformité' in data.columns:
                self.text.insert("end", "Résultats de conformité:\n")
                conformity_counts = data['Résultat conformité'].value_counts()
                for result, count in conformity_counts.items():
                    percentage = (count / total_params) * 100
                    self.text.insert("end", f"  - {result}: {count} ({percentage:.1f}%)\n")
                self.text.insert("end", "\n")
            
            # Score global
            if 'Score' in data.columns:
                # Convertir la colonne Score en numérique, en remplaçant les valeurs non numériques par 0
                data['Score'] = pd.to_numeric(data['Score'], errors='coerce').fillna(0)
                total_score = data['Score'].sum()
                max_score = len(data)
                score_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
                self.text.insert("end", f"Score global: {total_score}/{max_score} ({score_percentage:.1f}%)\n\n")
        
        # Configurer les tags pour le formatage
        self.text.tag_configure("heading", font=("Helvetica", 12, "bold"))
        
        self.text.config(state=tk.DISABLED)  # Remettre en lecture seule