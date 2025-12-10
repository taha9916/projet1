"""
Interface graphique pour l'analyse détaillée des paramètres d'eau
Module complémentaire pour afficher les résultats d'analyse d'eau
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WaterAnalysisInterface:
    """Interface pour afficher et gérer les analyses d'eau détaillées"""
    
    def __init__(self, parent, water_collector):
        self.parent = parent
        self.water_collector = water_collector
        self.current_data = None
    
    def show_detailed_water_analysis(self, coordinates):
        """Affiche une fenêtre d'analyse détaillée des paramètres d'eau"""
        try:
            # Créer la fenêtre principale
            water_window = tk.Toplevel(self.parent)
            water_window.title(f"Analyse détaillée des paramètres d'eau - {coordinates}")
            water_window.geometry("1200x800")
            water_window.transient(self.parent)
            
            # Collecter les données
            water_data = self.water_collector.collect_detailed_water_parameters(coordinates)
            if not water_data:
                messagebox.showerror("Erreur", "Impossible de collecter les paramètres d'eau")
                water_window.destroy()
                return
            
            self.current_data = water_data
            
            # Créer le notebook pour les onglets
            notebook = ttk.Notebook(water_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Onglet synthèse
            self._create_synthesis_tab(notebook, water_data)
            
            # Onglets par catégorie
            for category, parameters in water_data.items():
                if category != 'contexte' and isinstance(parameters, dict):
                    self._create_category_tab(notebook, category, parameters)
            
            # Onglet statistiques
            self._create_statistics_tab(notebook, water_data)
            
            # Boutons d'action
            button_frame = tk.Frame(water_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Button(button_frame, text="Exporter Excel", 
                     command=lambda: self._export_to_excel(water_data)).pack(side=tk.LEFT, padx=5)
            
            tk.Button(button_frame, text="Générer rapport", 
                     command=lambda: self._generate_report(water_data)).pack(side=tk.LEFT, padx=5)
            
            tk.Button(button_frame, text="Fermer", 
                     command=water_window.destroy).pack(side=tk.RIGHT, padx=5)
            
            logger.info(f"Interface d'analyse d'eau ouverte pour {coordinates}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'analyse d'eau: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")
    
    def _create_synthesis_tab(self, notebook, water_data):
        """Crée l'onglet de synthèse"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Synthèse")
        
        # Créer le treeview pour la synthèse
        columns = ('Catégorie', 'Paramètre', 'Valeur', 'Unité', 'Référence', 'Conforme')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)
        
        # Configurer les colonnes
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Remplir les données
        for category, parameters in water_data.items():
            if category == 'contexte':
                continue
            
            category_name = category.replace('_', ' ').title()
            for param, data in parameters.items():
                conforme_text = "✓ Oui" if data['conforme'] else "✗ Non" if data['conforme'] is not None else "? N/A"
                
                # Colorer selon la conformité
                item = tree.insert('', tk.END, values=(
                    category_name, param, data['valeur_mesuree'], 
                    data['unite'], data['valeur_reference'], conforme_text
                ))
                
                if data['conforme'] is False:
                    tree.set(item, 'Conforme', '✗ Non')
                elif data['conforme'] is True:
                    tree.set(item, 'Conforme', '✓ Oui')
        
        # Pack les widgets
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
    
    def _create_category_tab(self, notebook, category, parameters):
        """Crée un onglet pour une catégorie spécifique"""
        frame = ttk.Frame(notebook)
        tab_name = category.replace('_', ' ').title()
        notebook.add(frame, text=tab_name)
        
        # Titre de la catégorie
        title_label = tk.Label(frame, text=f"Paramètres - {tab_name}", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Créer le treeview pour cette catégorie
        columns = ('Paramètre', 'Valeur mesurée', 'Unité', 'Référence', 'Conforme', 'Source')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        # Configurer les colonnes
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Scrollbars
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Remplir les données
        for param, data in parameters.items():
            conforme_text = "✓ Oui" if data['conforme'] else "✗ Non" if data['conforme'] is not None else "? N/A"
            
            tree.insert('', tk.END, values=(
                param, data['valeur_mesuree'], data['unite'], 
                data['valeur_reference'], conforme_text, data['source']
            ))
        
        # Pack les widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Statistiques de la catégorie
        stats_frame = tk.Frame(frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        total_params = len(parameters)
        non_compliant = sum(1 for data in parameters.values() if data['conforme'] is False)
        compliant = sum(1 for data in parameters.values() if data['conforme'] is True)
        
        stats_text = f"Total: {total_params} | Conformes: {compliant} | Non conformes: {non_compliant}"
        tk.Label(stats_frame, text=stats_text, font=("Arial", 10)).pack()
    
    def _create_statistics_tab(self, notebook, water_data):
        """Crée l'onglet des statistiques"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Statistiques")
        
        # Calculer les statistiques
        total_params = 0
        compliant_params = 0
        non_compliant_params = 0
        category_stats = {}
        
        for category, parameters in water_data.items():
            if category == 'contexte':
                continue
            
            cat_total = len(parameters)
            cat_compliant = sum(1 for data in parameters.values() if data['conforme'] is True)
            cat_non_compliant = sum(1 for data in parameters.values() if data['conforme'] is False)
            
            category_stats[category] = {
                'total': cat_total,
                'compliant': cat_compliant,
                'non_compliant': cat_non_compliant,
                'compliance_rate': (cat_compliant / cat_total * 100) if cat_total > 0 else 0
            }
            
            total_params += cat_total
            compliant_params += cat_compliant
            non_compliant_params += cat_non_compliant
        
        # Affichage des statistiques globales
        global_frame = tk.LabelFrame(frame, text="Statistiques globales", font=("Arial", 12, "bold"))
        global_frame.pack(fill=tk.X, padx=10, pady=10)
        
        global_stats = [
            f"Nombre total de paramètres: {total_params}",
            f"Paramètres conformes: {compliant_params}",
            f"Paramètres non conformes: {non_compliant_params}",
            f"Taux de conformité global: {(compliant_params/total_params*100):.1f}%" if total_params > 0 else "0%",
            f"Date d'analyse: {water_data.get('contexte', {}).get('date_collecte', 'N/A')}"
        ]
        
        for stat in global_stats:
            tk.Label(global_frame, text=stat, font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=2)
        
        # Statistiques par catégorie
        cat_frame = tk.LabelFrame(frame, text="Statistiques par catégorie", font=("Arial", 12, "bold"))
        cat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview pour les statistiques par catégorie
        cat_columns = ('Catégorie', 'Total', 'Conformes', 'Non conformes', 'Taux (%)')
        cat_tree = ttk.Treeview(cat_frame, columns=cat_columns, show='headings', height=10)
        
        for col in cat_columns:
            cat_tree.heading(col, text=col)
            cat_tree.column(col, width=120)
        
        for category, stats in category_stats.items():
            cat_name = category.replace('_', ' ').title()
            cat_tree.insert('', tk.END, values=(
                cat_name, stats['total'], stats['compliant'], 
                stats['non_compliant'], f"{stats['compliance_rate']:.1f}"
            ))
        
        cat_tree.pack(fill=tk.BOTH, expand=True)
    
    def _export_to_excel(self, water_data):
        """Exporte les données vers Excel"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Sauvegarder l'analyse d'eau"
            )
            
            if filename:
                success = self.water_collector.export_water_data_to_excel(water_data, filename)
                if success:
                    messagebox.showinfo("Succès", f"Données exportées vers:\n{filename}")
                else:
                    messagebox.showerror("Erreur", "Échec de l'export Excel")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def _generate_report(self, water_data):
        """Génère un rapport textuel"""
        try:
            summary = self.water_collector.get_water_quality_summary(water_data)
            if not summary:
                messagebox.showerror("Erreur", "Impossible de générer le résumé")
                return
            
            # Créer une fenêtre pour le rapport
            report_window = tk.Toplevel(self.parent)
            report_window.title("Rapport de qualité de l'eau")
            report_window.geometry("600x500")
            
            # Zone de texte avec scrollbar
            text_frame = tk.Frame(report_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # Contenu du rapport
            report_content = f"""RAPPORT DE QUALITÉ DE L'EAU
{'='*50}

Date d'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Coordonnées: {water_data.get('contexte', {}).get('coordinates', 'N/A')}

ÉVALUATION GLOBALE
{'='*20}
Qualité globale: {summary['qualite_globale']}
Score de qualité: {summary['score_qualite']}%

PARAMÈTRES CRITIQUES
{'='*20}
"""
            
            if summary['parametres_critiques']:
                report_content += "\n".join(f"• {param}" for param in summary['parametres_critiques'])
            else:
                report_content += "Aucun paramètre critique détecté"
            
            report_content += f"""

RECOMMANDATIONS
{'='*15}
"""
            report_content += "\n".join(f"• {rec}" for rec in summary['recommandations'])
            
            report_content += f"""

DÉTAIL PAR CATÉGORIE
{'='*20}
"""
            
            for category, parameters in water_data.items():
                if category == 'contexte':
                    continue
                
                cat_name = category.replace('_', ' ').title()
                total = len(parameters)
                non_compliant = sum(1 for data in parameters.values() if data['conforme'] is False)
                
                report_content += f"""
{cat_name}:
  - Nombre de paramètres: {total}
  - Paramètres non conformes: {non_compliant}
  - Taux de conformité: {((total-non_compliant)/total*100):.1f}%
"""
            
            text_widget.insert(tk.END, report_content)
            text_widget.config(state=tk.DISABLED)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bouton pour sauvegarder le rapport
            tk.Button(report_window, text="Sauvegarder rapport", 
                     command=lambda: self._save_report(report_content)).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def _save_report(self, content):
        """Sauvegarde le rapport dans un fichier"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Sauvegarder le rapport"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Succès", f"Rapport sauvegardé:\n{filename}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

def create_water_analysis_interface(parent, water_collector):
    """Fonction utilitaire pour créer l'interface d'analyse d'eau"""
    try:
        interface = WaterAnalysisInterface(parent, water_collector)
        logger.info("Interface d'analyse d'eau créée avec succès")
        return interface
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'interface: {e}")
        return None
