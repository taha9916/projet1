#!/usr/bin/env python3
"""
Dialogues pour la gestion des projets d'analyse environnementale.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List, Optional

class ProjectDialog:
    """Dialogue pour créer ou modifier un projet."""
    
    def __init__(self, parent, title="Nouveau Projet", project_data=None):
        """Initialise le dialogue de projet.
        
        Args:
            parent: Fenêtre parente
            title: Titre du dialogue
            project_data: Données du projet existant (pour modification)
        """
        self.result = None
        
        # Créer la fenêtre modale
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self._create_widgets(project_data)
        
        # Attendre que la fenêtre soit fermée
        self.dialog.wait_window()
    
    def _create_widgets(self, project_data):
        """Crée les widgets du dialogue."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Informations du projet", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Nom du projet
        ttk.Label(main_frame, text="Nom du projet *:").pack(anchor=tk.W, pady=(0, 5))
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Description
        ttk.Label(main_frame, text="Description:").pack(anchor=tk.W, pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=5, width=50)
        self.description_text.pack(fill=tk.X, pady=(0, 15))
        
        # Localisation
        ttk.Label(main_frame, text="Localisation:").pack(anchor=tk.W, pady=(0, 5))
        self.location_entry = ttk.Entry(main_frame, width=50)
        self.location_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Remplir avec les données existantes si disponibles
        if project_data:
            self.name_entry.insert(0, project_data.get('name', ''))
            self.description_text.insert(1.0, project_data.get('description', ''))
            self.location_entry.insert(0, project_data.get('location', ''))
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Créer" if not project_data else "Modifier", 
                  command=self._ok).pack(side=tk.RIGHT)
        
        # Focus sur le champ nom
        self.name_entry.focus()
        
        # Bind Enter pour valider
        self.dialog.bind('<Return>', lambda e: self._ok())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _ok(self):
        """Valide et ferme le dialogue."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom du projet est obligatoire.")
            self.name_entry.focus()
            return
        
        self.result = {
            'name': name,
            'description': self.description_text.get(1.0, tk.END).strip(),
            'location': self.location_entry.get().strip()
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Annule et ferme le dialogue."""
        self.dialog.destroy()

class ProjectListDialog:
    """Dialogue pour sélectionner un projet dans une liste."""
    
    def __init__(self, parent, projects: List[Dict], title="Sélectionner un projet"):
        """Initialise le dialogue de sélection de projet.
        
        Args:
            parent: Fenêtre parente
            projects: Liste des projets disponibles
            title: Titre du dialogue
        """
        self.selected_project = None
        self.projects = projects
        
        # Créer la fenêtre modale
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"700x500+{x}+{y}")
        
        self._create_widgets()
        
        # Attendre que la fenêtre soit fermée
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Crée les widgets du dialogue."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Projets disponibles", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame pour la liste avec scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Treeview pour afficher les projets
        columns = ('name', 'location', 'analyses', 'parameters', 'created')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configuration des colonnes
        self.tree.heading('name', text='Nom')
        self.tree.heading('location', text='Localisation')
        self.tree.heading('analyses', text='Analyses')
        self.tree.heading('parameters', text='Paramètres')
        self.tree.heading('created', text='Créé le')
        
        self.tree.column('name', width=200)
        self.tree.column('location', width=150)
        self.tree.column('analyses', width=80)
        self.tree.column('parameters', width=100)
        self.tree.column('created', width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack des widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Remplir la liste
        for project in self.projects:
            created_date = project.get('created_at', '')[:10] if project.get('created_at') else ''
            self.tree.insert('', tk.END, values=(
                project.get('name', 'Sans nom'),
                project.get('location', ''),
                project.get('total_analyses', 0),
                project.get('total_parameters', 0),
                created_date
            ), tags=(project['id'],))
        
        # Frame pour les détails
        details_frame = ttk.LabelFrame(main_frame, text="Détails du projet", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.details_text = tk.Text(details_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.details_text.pack(fill=tk.X)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=(10, 0))
        self.select_button = ttk.Button(button_frame, text="Sélectionner", 
                                       command=self._select, state=tk.DISABLED)
        self.select_button.pack(side=tk.RIGHT)
        
        # Bind des événements
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._select())
        self.dialog.bind('<Return>', lambda e: self._select() if self.selected_project else None)
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _on_select(self, event):
        """Appelé quand un projet est sélectionné."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            project_id = item['tags'][0]
            
            # Trouver le projet correspondant
            for project in self.projects:
                if project['id'] == project_id:
                    self.selected_project = project
                    break
            
            # Afficher les détails
            if self.selected_project:
                details = f"Description: {self.selected_project.get('description', 'Aucune description')}\n"
                details += f"Localisation: {self.selected_project.get('location', 'Non spécifiée')}\n"
                details += f"Analyses: {self.selected_project.get('total_analyses', 0)}\n"
                details += f"Paramètres: {self.selected_project.get('total_parameters', 0)}"
                
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(1.0, details)
                self.details_text.config(state=tk.DISABLED)
                
                self.select_button.config(state=tk.NORMAL)
        else:
            self.selected_project = None
            self.select_button.config(state=tk.DISABLED)
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.DISABLED)
    
    def _select(self):
        """Sélectionne le projet et ferme le dialogue."""
        if self.selected_project:
            self.dialog.destroy()
    
    def _cancel(self):
        """Annule et ferme le dialogue."""
        self.selected_project = None
        self.dialog.destroy()

class ProjectStatusDialog:
    """Dialogue pour afficher le statut du projet courant."""
    
    def __init__(self, parent, project_manager):
        """Initialise le dialogue de statut de projet.
        
        Args:
            parent: Fenêtre parente
            project_manager: Instance du gestionnaire de projets
        """
        self.project_manager = project_manager
        
        # Créer la fenêtre modale
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Statut du projet")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self._create_widgets()
        
        # Attendre que la fenêtre soit fermée
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Crée les widgets du dialogue."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        if not self.project_manager.current_project:
            ttk.Label(main_frame, text="Aucun projet ouvert", 
                     font=("Arial", 12)).pack(pady=50)
            ttk.Button(main_frame, text="Fermer", 
                      command=self.dialog.destroy).pack()
            return
        
        # Obtenir le résumé du projet
        summary = self.project_manager.get_project_summary()
        
        # Titre avec nom du projet
        title_label = ttk.Label(main_frame, 
                               text=f"Projet: {summary['project_info']['name']}", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Notebook pour organiser les informations
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Onglet Informations générales
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Informations")
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, state=tk.DISABLED)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_content = f"""Description: {summary['project_info']['description']}

Localisation: {summary['project_info']['location']}

Créé le: {summary['project_info']['created_at'][:19].replace('T', ' ')}

Dernière modification: {summary['project_info']['last_modified'][:19].replace('T', ' ')}

Statistiques:
• Nombre d'analyses: {summary['statistics']['total_analyses']}
• Nombre total de paramètres: {summary['statistics']['total_parameters']}
• Paramètres uniques: {summary['statistics']['unique_parameters']}"""
        
        info_text.config(state=tk.NORMAL)
        info_text.insert(1.0, info_content)
        info_text.config(state=tk.DISABLED)
        
        # Onglet Analyses
        analyses_frame = ttk.Frame(notebook)
        notebook.add(analyses_frame, text="Analyses")
        
        if summary['analyses']:
            # Treeview pour les analyses
            analyses_tree = ttk.Treeview(analyses_frame, columns=('name', 'date', 'method', 'params'), 
                                        show='headings', height=10)
            
            analyses_tree.heading('name', text='Nom')
            analyses_tree.heading('date', text='Date')
            analyses_tree.heading('method', text='Méthode')
            analyses_tree.heading('params', text='Paramètres')
            
            analyses_tree.column('name', width=200)
            analyses_tree.column('date', width=120)
            analyses_tree.column('method', width=100)
            analyses_tree.column('params', width=80)
            
            for analysis in summary['analyses']:
                date_str = analysis.get('timestamp', '')[:19].replace('T', ' ')
                analyses_tree.insert('', tk.END, values=(
                    analysis.get('name', ''),
                    date_str,
                    analysis.get('method', ''),
                    analysis.get('parameter_count', 0)
                ))
            
            analyses_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        else:
            ttk.Label(analyses_frame, text="Aucune analyse dans ce projet").pack(pady=50)
        
        # Onglet Scores
        scores_frame = ttk.Frame(notebook)
        notebook.add(scores_frame, text="Scores")
        
        if summary['score_distribution']:
            scores_text = tk.Text(scores_frame, wrap=tk.WORD, state=tk.DISABLED)
            scores_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scores_content = "Répartition des scores de conformité:\n\n"
            status_map = {1: "Conforme", 2: "Attention", 3: "Critique", 0: "Non évalué"}
            
            for score, count in sorted(summary['score_distribution'].items()):
                percentage = (count / summary['statistics']['total_parameters']) * 100
                scores_content += f"Score {score} ({status_map.get(score, 'Inconnu')}): {count} paramètres ({percentage:.1f}%)\n"
            
            if summary['category_distribution']:
                scores_content += "\n\nRépartition par catégorie:\n\n"
                for category, count in summary['category_distribution'].items():
                    percentage = (count / summary['statistics']['total_parameters']) * 100
                    scores_content += f"{category.title()}: {count} paramètres ({percentage:.1f}%)\n"
            
            scores_text.config(state=tk.NORMAL)
            scores_text.insert(1.0, scores_content)
            scores_text.config(state=tk.DISABLED)
        else:
            ttk.Label(scores_frame, text="Aucun score disponible").pack(pady=50)
        
        # Bouton Fermer
        ttk.Button(main_frame, text="Fermer", command=self.dialog.destroy).pack()

# Ajouter les imports nécessaires à app.py
def add_project_imports():
    """Ajoute les imports nécessaires pour les dialogues de projet."""
    return """
# Imports pour les dialogues de projet
try:
    from project_dialogs import ProjectDialog, ProjectListDialog, ProjectStatusDialog
except ImportError:
    # Définir des classes vides si les dialogues ne sont pas disponibles
    class ProjectDialog:
        def __init__(self, *args, **kwargs):
            self.result = None
    
    class ProjectListDialog:
        def __init__(self, *args, **kwargs):
            self.selected_project = None
    
    class ProjectStatusDialog:
        def __init__(self, *args, **kwargs):
            pass
"""
