import tkinter as tk
from tkinter import ttk
import pandas as pd

def create_default_phase_content(parent_frame, phase_key, phase_config):
    """Crée un contenu par défaut pour une phase SLRI"""
    
    # En-tête de la phase
    header = ttk.Frame(parent_frame)
    header.pack(fill="x", pady=(0, 15))
    
    icon = phase_config.get('icon', '📊')
    title = phase_config.get('title', phase_key.title())
    description = phase_config.get('description', '')
    
    ttk.Label(header, text=f"{icon} {title}", 
             font=("Arial", 14, "bold")).pack(anchor="w")
    
    if description:
        ttk.Label(header, text=description, 
                 font=("Arial", 10), foreground="gray").pack(anchor="w")
    
    # Créer un notebook pour organiser les données de la phase
    phase_notebook = ttk.Notebook(parent_frame)
    phase_notebook.pack(fill="both", expand=True)
    
    # Onglet Vue d'ensemble
    overview_frame = ttk.Frame(phase_notebook)
    phase_notebook.add(overview_frame, text="Vue d'ensemble")
    
    # Message d'information
    info_frame = ttk.LabelFrame(overview_frame, text="Information", padding=15)
    info_frame.pack(fill="x", pady=10)
    
    info_text = f"""Phase sélectionnée : {title}
    
Pour voir les données d'analyse SLRI, vous devez d'abord :
1. Sélectionner un fichier à analyser (bouton "Parcourir")
2. Lancer l'analyse SLRI depuis le menu "Analyse"
3. Les résultats s'afficheront automatiquement ici

Cette phase analysera les paramètres suivants :"""
    
    ttk.Label(info_frame, text=info_text, justify="left").pack(anchor="w")
    
    # Paramètres configurés pour cette phase
    parameters = phase_config.get('parameters', [])
    if parameters:
        param_frame = ttk.LabelFrame(overview_frame, text="Paramètres à analyser", padding=10)
        param_frame.pack(fill="x", pady=10)
        
        # Afficher les paramètres
        for i, param in enumerate(parameters):
            if param == "Système de Surveillance Continue Implémenté":
                icon = "🔄"
                color = "#27ae60"
            else:
                icon = "📋"
                color = "#3498db"
            
            param_label = tk.Label(param_frame, 
                                 text=f"{icon} {param}",
                                 font=("Arial", 9),
                                 fg=color,
                                 anchor="w")
            param_label.pack(anchor="w", pady=2)
    
    # Onglet spécial pour la phase d'exploitation : Surveillance Continue
    if phase_key == "exploitation":
        monitoring_frame = ttk.Frame(phase_notebook)
        phase_notebook.add(monitoring_frame, text="Surveillance Continue")
        
        # Contenu de surveillance
        monitoring_info = ttk.LabelFrame(monitoring_frame, text="Système de Surveillance Continue", padding=15)
        monitoring_info.pack(fill="x", pady=10)
        
        monitoring_text = """Le système de surveillance continue sera activé lors de la phase d'exploitation.

Fonctionnalités disponibles :
• Traitement par lots des rapports environnementaux
• Système d'alertes automatiques
• Tableau de bord interactif
• Analyse des tendances
• Comparaison des plans d'action
• Historique des alertes

Pour activer la surveillance, utilisez le menu "Surveillance" de l'application."""
        
        ttk.Label(monitoring_info, text=monitoring_text, justify="left").pack(anchor="w")
