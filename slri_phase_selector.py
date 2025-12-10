import tkinter as tk
from tkinter import ttk, messagebox
import json

class SLRIPhaseSelector:
    """Dialogue pour sélectionner les phases SLRI selon l'avancement du projet"""
    
    def __init__(self, parent):
        self.parent = parent
        self.selected_phases = []
        self.project_status = None
        self.dialog = None
        self.result = None
        
    def show_dialog(self):
        """Affiche le dialogue de sélection des phases"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Sélection des Phases SLRI")
        self.dialog.geometry("600x650")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.transient(self.parent)
        
        self._create_widgets()
        
        # Attendre la fermeture du dialogue
        self.parent.wait_window(self.dialog)
        return self.result
    
    def _create_widgets(self):
        """Crée les widgets du dialogue"""
        # Canvas et scrollbar pour permettre le défilement
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas et scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame principal avec padding
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Sélection des Phases d'Analyse SLRI", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = ("Sélectionnez les phases d'analyse SLRI selon l'avancement actuel de votre projet.\n"
                    "Vous pouvez analyser une phase spécifique ou comparer plusieurs phases.")
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=520, justify="left")
        desc_label.pack(pady=(0, 20))
        
        # Bind mousewheel pour le défilement
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Statut du projet
        status_frame = ttk.LabelFrame(main_frame, text="Statut Actuel du Projet", padding="15")
        status_frame.pack(fill="x", pady=(0, 20))
        
        self.status_var = tk.StringVar(value="pre_construction")
        status_options = [
            ("🔍 Études préliminaires / Pré-construction", "pre_construction"),
            ("🏗️ En cours de construction", "construction"),
            ("⚡ En exploitation / fonctionnement", "exploitation"),
            ("🔄 En phase de démantèlement", "demantelement")
        ]
        
        for i, (text, value) in enumerate(status_options):
            rb = ttk.Radiobutton(status_frame, text=text, variable=self.status_var, 
                               value=value, command=self._update_phase_recommendations)
            rb.pack(anchor="w", pady=2)
        
        # Phases disponibles
        phases_frame = ttk.LabelFrame(main_frame, text="Phases à Analyser", padding="15")
        phases_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Chargement de la configuration des phases
        try:
            with open('phases_slri.json', 'r', encoding='utf-8') as f:
                self.phases_config = json.load(f)
        except:
            self.phases_config = {}
        
        # Variables pour les checkboxes des phases
        self.phase_vars = {}
        self.phase_checkboxes = {}
        
        for phase_key, phase_config in self.phases_config.items():
            var = tk.BooleanVar()
            self.phase_vars[phase_key] = var
            
            icon = phase_config.get('icon', '📊')
            title = phase_config.get('title', phase_key.title())
            
            cb = ttk.Checkbutton(phases_frame, text=f"{icon} {title}", 
                               variable=var, command=self._validate_selection)
            cb.pack(anchor="w", pady=3)
            self.phase_checkboxes[phase_key] = cb
        
        # Recommandations
        self.recommendations_frame = ttk.Frame(phases_frame)
        self.recommendations_frame.pack(fill="x", pady=(10, 0))
        
        self.recommendations_label = ttk.Label(self.recommendations_frame, 
                                             text="", foreground="blue", 
                                             font=("Arial", 9, "italic"))
        self.recommendations_label.pack(anchor="w")
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        ttk.Button(buttons_frame, text="Annuler", 
                  command=self._cancel).pack(side="right", padx=(10, 0))
        
        self.ok_button = ttk.Button(buttons_frame, text="Analyser", 
                                   command=self._ok, state="disabled")
        self.ok_button.pack(side="right")
        
        ttk.Button(buttons_frame, text="Sélectionner Tout", 
                  command=self._select_all).pack(side="left")
        
        ttk.Button(buttons_frame, text="Désélectionner Tout", 
                  command=self._deselect_all).pack(side="left", padx=(10, 0))
        
        # Initialiser les recommandations
        self._update_phase_recommendations()
    
    def _update_phase_recommendations(self):
        """Met à jour les recommandations selon le statut du projet"""
        status = self.status_var.get()
        
        recommendations = {
            "pre_construction": {
                "recommended": ["pre_construction"],
                "text": "💡 Recommandé : Analyse de pré-construction pour évaluer les risques avant le début des travaux."
            },
            "construction": {
                "recommended": ["pre_construction", "construction"],
                "text": "💡 Recommandé : Pré-construction (historique) + Construction (actuelle) pour comparaison."
            },
            "exploitation": {
                "recommended": ["pre_construction", "construction", "exploitation"],
                "text": "💡 Recommandé : Analyse complète du cycle de vie jusqu'à l'exploitation actuelle."
            },
            "demantelement": {
                "recommended": ["pre_construction", "construction", "exploitation", "demantelement"],
                "text": "💡 Recommandé : Analyse complète de toutes les phases pour bilan environnemental final."
            }
        }
        
        rec = recommendations.get(status, {"recommended": [], "text": ""})
        self.recommendations_label.config(text=rec["text"])
        
        # Auto-sélection des phases recommandées
        for phase_key, var in self.phase_vars.items():
            if phase_key in rec["recommended"]:
                var.set(True)
            else:
                var.set(False)
        
        self._validate_selection()
    
    def _validate_selection(self):
        """Valide la sélection et active/désactive le bouton OK"""
        selected_count = sum(1 for var in self.phase_vars.values() if var.get())
        self.ok_button.config(state="normal" if selected_count > 0 else "disabled")
    
    def _select_all(self):
        """Sélectionne toutes les phases"""
        for var in self.phase_vars.values():
            var.set(True)
        self._validate_selection()
    
    def _deselect_all(self):
        """Désélectionne toutes les phases"""
        for var in self.phase_vars.values():
            var.set(False)
        self._validate_selection()
    
    def _ok(self):
        """Confirme la sélection"""
        self.selected_phases = [phase for phase, var in self.phase_vars.items() if var.get()]
        self.project_status = self.status_var.get()
        
        if not self.selected_phases:
            messagebox.showwarning("Sélection requise", 
                                 "Veuillez sélectionner au moins une phase à analyser.")
            return
        
        self.result = {
            'phases': self.selected_phases,
            'project_status': self.project_status,
            'phase_count': len(self.selected_phases)
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Annule la sélection"""
        self.result = None
        self.dialog.destroy()

# Fonction utilitaire
def select_slri_phases(parent):
    """Fonction helper pour ouvrir le dialogue de sélection"""
    selector = SLRIPhaseSelector(parent)
    return selector.show_dialog()
