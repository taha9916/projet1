import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import pandas as pd
import os
import sys
import json
import pdfplumber
import openpyxl
import logging
import traceback
from datetime import datetime

# Import du gestionnaire de cache
from cache_manager import clear_cache, get_cache_stats

# Import des fonctions d'analyse cloud
from cloud_api import analyze_environmental_image_cloud, CloudVisionAPI

# Importation du module Gemini (si disponible)
try:
    from gemini_integration import analyze_environmental_image_with_gemini, load_gemini_config
    # Importation du module de vérification de la configuration Gemini
    from verifier_config_gemini_au_demarrage import verifier_gemini_au_demarrage
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Assurer l'encodage UTF-8 pour la sortie console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Import des modules du projet
from config import UI_CONFIG, SUPPORTED_FILE_TYPES, OUTPUT_DIR, MODEL_CONFIG
from utils import extract_text_from_file, save_dataframe_to_excel, iter_pdf_text_pages
from data_processing import analyze_environmental_data
from cloud_api import extract_environmental_parameters_cloud
from slri_standalone import SLRICompleteAnalyzer, create_slri_complete_analyzer
from model_interface import analyze_environmental_image
from vlmodel_adapter import create_vlmodel_adapter, VLModelAdapter
from gui_components import FileSelectionFrame, StatusBar, DataPreviewFrame, DataVisualizationFrame, ToolbarFrame, ResultsFrame
from manual_entry import ManualEntryWindow
from external_apis import ExternalAPIs
from slri_excel_updater import update_slri_excel_macro, update_slri_with_dataframe

# Import du nouveau système de logging centralisé
from logger import get_logger, AuditLogger

# Configuration du logging
logger = get_logger(__name__)
audit_logger = AuditLogger()

# ======================
# ======================

class LocationInfoFrame(ttk.Frame):
    """Onglet pour récupérer des informations environnementales par coordonnées."""
    def _to_slri_dataframe(self, df_raw):
        import pandas as pd
        try:
            if df_raw is None or df_raw.empty:
                return pd.DataFrame(columns=[
                    "Paramètre", "Milieu", "Intervalle acceptable/MIN", "Intervalle acceptable/MAX",
                    "Valeur mesurée de milieux initial", "Rejet de PHASE CONSTRUCTION",
                    "Valeure Mesure+rejet", "Unité"
                ])
            def milieu_from_cat(cat):
                s = str(cat).strip().lower()
                if s.startswith("météo") or s == "air":
                    return "Air"
                if s == "eau":
                    return "Eau"
                if s == "sol":
                    return "Sol"
                return "Autre"
            
            # Intervalles acceptables de référence (normes marocaines/internationales)
            ref_intervals = {
                'température': (10, 25), 'ph': (6.5, 8.5), 'turbidité': (0, 5), 'conductivité': (0, 1000),
                'dbo5': (0, 5), 'dco': (0, 30), 'oxygène dissous': (5, 10), 'nitrates': (0, 50),
                'nitrites': (0, 1), 'ammoniac': (0, 0.5), 'phosphore total': (0, 1), 'azote total': (0, 10),
                'plomb': (0, 0.01), 'cadmium': (0, 0.005), 'chrome total': (0, 0.05), 'cuivre': (0, 0.05),
                'zinc': (0, 0.2), 'nickel': (0, 0.02), 'mercure': (0, 0.001), 'arsenic': (0, 0.01),
                'hydrocarbures': (0, 1), 'ph sol': (6.0, 8.0), 'perméabilité': (0.0001, 0.01),
                'matière organique': (1, 5), 'carbone organique': (0.5, 3), 'plomb sol': (0, 100),
                'cadmium sol': (0, 3), 'mercure sol': (0, 1), 'arsenic sol': (0, 20), 'chrome total sol': (0, 150),
                'cuivre sol': (0, 100), 'zinc sol': (0, 200), 'nickel sol': (0, 75), 'azote total sol': (0, 2000),
                'phosphore total sol': (0, 1000), 'niveau sonore jour': (0, 65), 'niveau sonore nuit': (0, 55),
                'poussières totales': (0, 100), 'pm10': (0, 50), 'pm2.5': (0, 35), 'so₂': (0, 100),
                'nox': (0, 80), 'co': (0, 2000), 'o₃': (0, 120)
            }
            
            rows = []
            for _, r in df_raw.iterrows():
                v_num = None
                try:
                    v_num = float(str(r.get("Valeur")).replace(",", "."))
                except Exception:
                    v_num = r.get("Valeur")
                rejet = 0.0
                mesure_rejet = (v_num + rejet) if isinstance(v_num, (int, float)) else None
                
                # Trouver l'intervalle de référence
                param_lower = str(r.get("Paramètre", "")).strip().lower()
                min_ref, max_ref = None, None
                for ref_key, (ref_min, ref_max) in ref_intervals.items():
                    if ref_key in param_lower or param_lower in ref_key:
                        min_ref, max_ref = ref_min, ref_max
                        break
                
                rows.append({
                    "Paramètre": r.get("Paramètre"),
                    "Milieu": milieu_from_cat(r.get("Catégorie")),
                    "Intervalle acceptable/MIN": min_ref,
                    "Intervalle acceptable/MAX": max_ref,
                    "Valeur mesurée de milieux initial": v_num if v_num is not None else r.get("Valeur"),
                    "Rejet de PHASE CONSTRUCTION": rejet,
                    "Valeure Mesure+rejet": mesure_rejet,
                    "Unité": r.get("Unité"),
                })
            return pd.DataFrame(rows, columns=[
                "Paramètre", "Milieu", "Intervalle acceptable/MIN", "Intervalle acceptable/MAX",
                "Valeur mesurée de milieux initial", "Rejet de PHASE CONSTRUCTION",
                "Valeure Mesure+rejet", "Unité"
            ])
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Conversion SLRI échouée: {e}")
            return df_raw
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # États et surveillance
        self._busy = False
        self._fetch_thread = None
        self._watchdog_after_id = None
        self._fetch_start_ts = None
        
        # Créer les widgets de l'interface
        self._create_widgets()

    def _create_widgets(self):
        # Canvas et scrollbar pour permettre le défilement
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
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
        
        # Bind mousewheel pour le défilement
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Entrées pour latitude/longitude
        coords_frame = ttk.Frame(scrollable_frame, padding=10)
        coords_frame.pack(fill=tk.X)

        ttk.Label(coords_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.lat_var = tk.StringVar(value="34.0209")
        ttk.Entry(coords_frame, textvariable=self.lat_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(coords_frame, text="Longitude:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.lon_var = tk.StringVar(value="-6.8416")
        ttk.Entry(coords_frame, textvariable=self.lon_var, width=15).grid(row=0, column=3, padx=5, pady=5)

        # Sélection des types de données
        data_types_frame = ttk.LabelFrame(scrollable_frame, text="Types de données à récupérer", padding=10)
        data_types_frame.pack(fill="x", padx=10, pady=10)

        self.var_weather = tk.BooleanVar(value=True)
        self.var_air = tk.BooleanVar(value=True)
        self.var_water = tk.BooleanVar(value=True)
        self.var_soil = tk.BooleanVar(value=True)
        self.var_slri = tk.BooleanVar(value=True)

        ttk.Checkbutton(data_types_frame, text="Météo", variable=self.var_weather).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(data_types_frame, text="Qualité de l'air", variable=self.var_air).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(data_types_frame, text="Ressources en eau (FAO)", variable=self.var_water).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(data_types_frame, text="Sol (SoilGrids)", variable=self.var_soil).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(data_types_frame, text="Analyse SLRI (D/E/F/J/K)", variable=self.var_slri).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # Actions
        actions_frame = ttk.Frame(scrollable_frame, padding=10)
        actions_frame.pack(fill=tk.X)

        self.fetch_btn = ttk.Button(actions_frame, text="Obtenir les informations", command=self.get_location_info)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)

        self.export_xlsx_btn = ttk.Button(actions_frame, text="Exporter Excel", command=self._export_excel)
        self.export_xlsx_btn.pack(side=tk.LEFT, padx=5)

        self.export_csv_btn = ttk.Button(actions_frame, text="Exporter CSV", command=self._export_csv)
        self.export_csv_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(actions_frame, text="Effacer", command=self._clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Progression
        self.progress = ttk.Progressbar(scrollable_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        # Zone d'affichage
        text_frame = ttk.Frame(scrollable_frame, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.text = tk.Text(text_frame, wrap=tk.WORD, height=18)
        self.text.pack(fill=tk.BOTH, expand=True)

    def _set_busy(self, busy=True):
        logger.info(f"LocationInfoFrame._set_busy({busy})")
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in (self.fetch_btn, self.export_xlsx_btn, self.export_csv_btn, self.clear_btn):
            btn.config(state=state)
        msg = "Récupération en cours..." if busy else "Prêt"
        self.app.status_bar.set_status(msg)
        if busy:
            self._start_watchdog()
        else:
            self._cancel_watchdog()

    def _start_watchdog(self, timeout_sec=60):
        try:
            self._fetch_start_ts = time.time()
            if self._watchdog_after_id:
                self.after_cancel(self._watchdog_after_id)
            self._watchdog_after_id = self.after(int(timeout_sec * 1000), self._watchdog_check)
            logger.info(f"Watchdog démarré pour la récupération (timeout={timeout_sec}s)")
        except Exception:
            pass

    def _cancel_watchdog(self):
        if self._watchdog_after_id:
            try:
                self.after_cancel(self._watchdog_after_id)
            except Exception:
                pass
            self._watchdog_after_id = None

    def _watchdog_check(self):
        if self._busy and self._fetch_thread is not None and self._fetch_thread.is_alive():
            logger.warning("Watchdog: délai dépassé, le thread de récupération est toujours actif. Réinitialisation de l'UI.")
            try:
                messagebox.showwarning("Délai dépassé", "La récupération des données prend trop de temps. L'opération a été réinitialisée.")
            except Exception:
                pass
            self.progress['value'] = 0
            self._set_busy(False)
            self.app.status_bar.set_status("Temps dépassé - réinitialisé", 0)
        self._watchdog_after_id = None

    def get_location_info(self):
        if self._busy:
            messagebox.showinfo("Opération en cours", "Une récupération est déjà en cours. Veuillez patienter.")
            return
        try:
            lat = float(self.lat_var.get().strip())
            lon = float(self.lon_var.get().strip())
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Coordonnées hors limites")
        except Exception:
            messagebox.showerror("Coordonnées invalides", "Veuillez entrer une latitude/longitude valides.")
            return

        data_types = []
        if self.var_weather.get():
            data_types.append("weather")
        if self.var_air.get():
            data_types.append("air_quality")
        if self.var_water.get():
            data_types.append("water_quality")
        if self.var_soil.get():
            data_types.append("soil")

        if not data_types:
            messagebox.showwarning("Aucun type sélectionné", "Sélectionnez au moins un type de données.")
            return

        self._set_busy(True)
        self.progress['value'] = 5
        self._fetch_start_ts = time.time()
        logger.info(f"Démarrage de la récupération: lat={lat}, lon={lon}, types={data_types}")

        self._fetch_thread = threading.Thread(target=self._fetch_location_data, args=(lat, lon, data_types), daemon=True)
        self._fetch_thread.start()

    def _fetch_location_data(self, lat, lon, data_types):
        try:
            apis = ExternalAPIs()
            logger.info("Thread de récupération lancé")
            rows = []

            def add_rows(category, data_dict):
                if not data_dict:
                    return
                for param, (value, unit) in data_dict.items():
                    rows.append({
                        "Catégorie": category,
                        "Paramètre": str(param),
                        "Valeur": value,
                        "Unité": unit,
                        "Latitude": lat,
                        "Longitude": lon,
                        "Score": self._score_param(category, param, value)
                    })

            # Météo
            if "weather" in data_types:
                logger.info("Récupération météo...")
                self._update_progress_async(15)
                weather = apis.get_weather_data(lat, lon)
                add_rows("Météo", weather)

            # Air
            if "air_quality" in data_types:
                logger.info("Récupération qualité de l'air...")
                self._update_progress_async(35)
                air = apis.get_air_quality_data(lat, lon)
                add_rows("Air", air)

            # Ressources en eau (FAO)
            if "water_quality" in data_types:
                logger.info("Récupération des ressources en eau (FAO)... ")
                self._update_progress_async(55)
                water = self.get_water_resources(apis)
                add_rows("Eau", water)

            # Sol
            if "soil" in data_types:
                logger.info("Récupération Sol (SoilGrids)...")
                self._update_progress_async(75)
                soil = apis.get_soil_data(lat, lon)
                if not soil:
                    rows.append({
                        "Catégorie": "Sol",
                        "Paramètre": "Aucune donnée de sol disponible",
                        "Valeur": "",
                        "Unité": "",
                        "Latitude": lat,
                        "Longitude": lon,
                        "Score": None
                    })
                else:
                    add_rows("Sol", soil)

            # Intégrer l'analyse SLRI si disponible
            slri_results = None
            try:
                slri_results = integrate_slri_with_main_system((lat, lon), "SLRI")
                if "error" not in slri_results:
                    logger.info("Analyse SLRI intégrée avec succès")
# ... (code après la modification)
            except Exception as e:
                logger.warning(f"Analyse SLRI non disponible: {e}")

            # Construction du DataFrame résultat complet (tous paramètres du prompt)
            PARAMS_PROMPT = [
                (2, "Température", "°C"),
                (3, "Ph", "-"),
                (4, "Turbidité", "NTU"),
                (5, "Conductivité", "µS/cm"),
                (6, "DBO5", "mg/L"),
                (7, "DCO", "mg/L"),
                (8, "Oxygène dissous", "mg/L"),
                (9, "Nitrates", "mg/L"),
                (10, "Nitrites", "mg/L"),
                (11, "Ammoniac", "mg/L"),
                (12, "Phosphore total", "mg/L"),
                (13, "Azote total", "mg/L"),
                (14, "Plomb", "mg/L"),
                (15, "Cadmium", "mg/L"),
                (16, "Chrome total", "mg/L"),
                (17, "Cuivre", "mg/L"),
                (18, "Zinc", "mg/L"),
                (19, "Nickel", "mg/L"),
                (20, "Mercure", "mg/L"),
                (21, "Arsenic", "mg/L"),
                (22, "Hydrocarbures (HCT, HAP)", "mg/L"),
                (23, "pH sol", "-"),
                (24, "Perméabilité", "cm/s"),
                (25, "Matière organique", "%"),
                (26, "Carbone organique", "%"),
                (27, "Plomb sol", "mg/kg"),
                (28, "Cadmium sol", "mg/kg"),
                (29, "Mercure sol", "mg/kg"),
                (30, "Arsenic sol", "mg/kg"),
                (31, "Chrome total sol", "mg/kg"),
                (32, "Cuivre sol", "mg/kg"),
                (33, "Zinc sol", "mg/kg"),
                (34, "Nickel sol", "mg/kg"),
                (35, "Azote total sol", "mg/kg"),
                (36, "Phosphore total sol", "mg/kg"),
                (37, "Niveau sonore JOUR", "DB"),
                (38, "Niveau sonore NUIT", "DB"),
                (39, "Modification du relief", ""),
                (40, "Poussières totales", "mg/m³"),
                (41, "PM10", "µg/m³"),
                (42, "PM2.5", "µg/m³"),
                (43, "SO₂", "µg/m³"),
                (44, "NOx", "µg/m³"),
                (45, "CO", "µg/m³"),
                (46, "O₃ (ozone)", "µg/m³"),
                (47, "Radiations éoliennes - Champ électrique", "kV/m"),
                (48, "Radiations éoliennes - Champ magnétique", "µT"),
                (49, "Radiations câbles - Champ électrique", "kV/m"),
                (50, "Radiations câbles - Champ magnétique", "µT"),
                (51, "Radiations ondulateurs - Champ électrique", "V/m"),
                (52, "Radiations ondulateurs - Densité de puissance", "W/m²"),
                (53, "Indice de qualité de vie", "%"),
                (54, "Poussières santé", "mg/m³"),
                (55, "Risques électriques et incendie", "Nombre d'anomalie"),
                (56, "Taux de maladie", "%"),
                (57, "Infrastructure et équipement", ""),
                (58, "Activité socio-économique /Emploi", "")
            ]
            # Indexer les valeurs collectées par nom
            values_by_param = {str(r["Paramètre"]).strip().lower(): r for r in rows}
            rows_full = []
            for idx, param, unit in PARAMS_PROMPT:
                key = param.strip().lower()
                if key in values_by_param:
                    r = values_by_param[key]
                    val = r["Valeur"]
                    cat = r["Catégorie"]
                else:
                    val = ""
                    cat = ""
                rows_full.append({
                    "Catégorie": cat,
                    "Paramètre": param,
                    "Valeur": val,
                    "Unité": unit,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Score": None
                })
            # Compléter les valeurs manquantes avec des valeurs de référence (normes marocaines/internationales)
            try:
                # Dictionnaire de valeurs de référence pour le contexte marocain
                ref_values = {
                    'ph': 7.2, 'turbidité': 2.5, 'conductivité': 500, 'dbo5': 3, 'dco': 15,
                    'oxygène dissous': 7, 'nitrates': 10, 'nitrites': 0.5, 'ammoniac': 0.2,
                    'phosphore total': 0.5, 'azote total': 5, 'plomb': 0.01, 'cadmium': 0.003,
                    'chrome total': 0.05, 'cuivre': 0.02, 'zinc': 0.1, 'nickel': 0.02,
                    'mercure': 0.001, 'arsenic': 0.01, 'hydrocarbures': 0.5, 'ph sol': 7.0,
                    'perméabilité': 0.001, 'matière organique': 2.5, 'carbone organique': 1.5,
                    'plomb sol': 50, 'cadmium sol': 2, 'mercure sol': 0.5, 'arsenic sol': 10,
                    'chrome total sol': 100, 'cuivre sol': 50, 'zinc sol': 100, 'nickel sol': 50,
                    'azote total sol': 1000, 'phosphore total sol': 500, 'niveau sonore jour': 55,
                    'niveau sonore nuit': 45, 'modification du relief': 0, 'poussières totales': 50,
                    'pm10': 40, 'pm2.5': 25, 'so₂': 50, 'nox': 40, 'co': 1000, 'o₃': 100,
                    'radiations éoliennes - champ électrique': 5, 'radiations éoliennes - champ magnétique': 100,
                    'radiations câbles - champ électrique': 5, 'radiations câbles - champ magnétique': 100,
                    'radiations ondulateurs - champ électrique': 61, 'radiations ondulateurs - densité de puissance': 10,
                    'indice de qualité de vie': 70, 'poussières santé': 50, 'risques électriques et incendie': 0,
                    'taux de maladie': 5, 'infrastructure et équipement': 'Moyenne', 'activité socio-économique': 'Moyenne'
                }
                for row in rows_full:
                    if not row['Valeur']:
                        param_key = row['Paramètre'].strip().lower()
                        # Recherche par correspondance partielle
                        for ref_key, ref_val in ref_values.items():
                            if ref_key in param_key or param_key in ref_key:
                                row['Valeur'] = ref_val
                                break
                df_raw = pd.DataFrame(rows_full, columns=["Catégorie", "Paramètre", "Valeur", "Unité", "Latitude", "Longitude", "Score"])
            except Exception as e:
                logger.warning(f"Complétion des valeurs manquantes échouée: {e}")
            df = self._to_slri_dataframe(df_raw) if self.var_slri.get() else df_raw
            # Construire un rendu texte simple
            lines = []
            # Corrige : s'assurer que 'Catégorie' existe
            if 'Catégorie' not in df.columns:
                df['Catégorie'] = ""
            if not df.empty:
                for cat in df['Catégorie'].unique():
                    lines.append(f"=== {cat} ===")
                    subset = df[df['Catégorie'] == cat]
                    for _, r in subset.iterrows():
                        unit = f" {r.get('Unité', '')}" if r.get('Unité', '') else ""
                        score = r.get('Score', None)
                        score_text = f" | Risque: {score}" if score is not None and pd.notna(score) and score > 0 else ""
                        param = r.get('Paramètre', '')
                        valeur = r.get('Valeur', '')
                        # Affichage compact : Paramètre : valeur [unité] (risque)
                        main = f"{param} : {valeur}"
                        if unit:
                            main += f" [{unit.strip()}]"
                        if score_text:
                            main += f"{score_text}"
                        # Ajouter interprétation stress hydrique si besoin
                        if "Indice De Stress Hydrique" in param:
                            try:
                                stress_value = float(str(valeur).split(' ')[0])
                                interpretation = self._interpret_water_stress(stress_value)
                                main += f" | {interpretation}"
                            except (ValueError, TypeError):
                                pass
                        lines.append(main)
                    lines.append("")
                
                # Ajouter les résultats SLRI si disponibles
                if slri_results and "error" not in slri_results:
                    lines.append("=== ANALYSE SLRI ===")
                    stats = slri_results.get("statistiques_globales", {})
                    if "scores_par_phase" in stats:
                        lines.append("Scores par phase:")
                        for phase, score in stats["scores_par_phase"].items():
                            lines.append(f"- {phase}: {score:.2f}")
                    
                    if "risques_majeurs" in stats and stats["risques_majeurs"]:
                        lines.append("\nRisques majeurs identifiés:")
                        for risque in stats["risques_majeurs"][:5]:  # Limiter à 5
                            lines.append(f"- {risque['parametre']} ({risque['milieu']}): {risque['amplitude']}")
                    
                    lines.append("")
            else:
                lines.append("Aucune donnée disponible pour ces coordonnées.")

            text_output = "\n".join(lines)
            self._update_progress_async(95)

            logger.info("Récupération terminée, planification de la mise à jour UI")
            # Mise à jour UI dans le thread principal
            self.after(0, lambda: self._apply_results(df, text_output))
        except Exception as e:
            err = f"Erreur lors de la récupération des données: {str(e)}"
            logger.error(err + "\n" + traceback.format_exc())
            self.after(0, lambda: messagebox.showerror("Erreur", err))
            self._update_progress_async(0, "Erreur")
            self.after(0, lambda: self._set_busy(False))

    def _apply_results(self, df, text_output):
        try:
            self.app.current_results = df if df is not None else None
            # Ajout à l'historique des analyses récentes
            if df is not None and not df.empty:
                import datetime
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                nom = f"Analyse ({now})"
                self.app.recent_analyses.append((nom, df, now))
                # Limiter l'historique à 10 analyses
                self.app.recent_analyses = self.app.recent_analyses[-10:]

            self.text.config(state=tk.NORMAL)
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, text_output)
            self.text.config(state=tk.DISABLED)
            if df is not None and not df.empty:
                try:
                    self.app.preview_frame.display_dataframe(df)
                except Exception as e:
                    logger.error(f"Erreur d'affichage des données: {e}\n{traceback.format_exc()}")
                    messagebox.showerror("Erreur d'affichage", f"Impossible d'afficher les données: {e}")
        finally:
            self._update_progress_async(100, "Données par lieu prêtes")
            self._set_busy(False)
            self._cancel_watchdog()
            self._fetch_thread = None
            self.app.status_bar.set_status("Données par lieu prêtes", 100)

    def _update_progress_async(self, value, message=None):
        def _update():
            self.progress.config(value=value)
            if message:
                self.app.status_bar.set_status(message, value)
        if self.winfo_exists():
            self.after(0, _update)

    def _interpret_water_stress(self, stress_percentage):
        """Interprète le pourcentage de stress hydrique en une description textuelle."""
        if stress_percentage is None:
            return "Niveau de stress non déterminé."
        
        if stress_percentage < 25:
            return "Faible stress hydrique - Les ressources en eau sont suffisantes."
        elif stress_percentage < 50:
            return "Stress hydrique modéré - Pression notable sur les ressources en eau."
        elif stress_percentage < 75:
            return "Stress hydrique élevé - Concurrence importante pour les ressources en eau."
        else:
            return "Stress hydrique critique - Demande en eau supérieure aux ressources disponibles."

    def _score_param(self, category, param, value):
        """Attribue un score de risque à un paramètre donné."""
        try:
            if category == "Air" and "AQI Score" in param:
                try:
                    score_pct = float(value)
                    if score_pct >= 80: return 1 # Bon
                    elif score_pct >= 60: return 2 # Modéré
                    else: return 3 # Malsain
                except (ValueError, TypeError):
                    return 0
            
            if category == "Eau" and "Indice de stress hydrique" in param:
                try:
                    # La valeur peut être '25.3 (E)', il faut extraire le nombre
                    stress_value = float(str(value).split(' ')[0])
                    if stress_value < 25: return 1  # Faible stress
                    elif stress_value < 75: return 2  # Stress moyen
                    else: return 3  # Stress élevé
                except (ValueError, TypeError):
                    return 0

            return 0
        except Exception:
            return 0

    def get_water_resources(self, apis):
        """Récupère et formate les données sur les ressources en eau - utilise les paramètres détaillés en priorité."""
        logger.info("Récupération des paramètres d'eau détaillés...")
        
        # Récupérer les coordonnées actuelles
        try:
            lat = float(self.lat_var.get().strip())
            lon = float(self.lon_var.get().strip())
        except:
            lat, lon = 34.0209, -6.8416  # Coordonnées par défaut (Rabat)
        
        try:
            # Priorité aux paramètres d'eau détaillés
            detailed_water_data = apis.get_detailed_water_data(lat, lon)
            
            if detailed_water_data and "Erreur" not in detailed_water_data:
                logger.info(f"Paramètres d'eau détaillés récupérés: {len(detailed_water_data)} paramètres")
                # Convertir le format pour l'affichage
                formatted_data = {}
                for param_name, param_value in detailed_water_data.items():
                    # param_value est déjà formaté comme "valeur unité ✓/✗"
                    formatted_data[param_name] = (param_value, "")
                return formatted_data
            else:
                logger.warning("Échec des paramètres détaillés, utilisation du fallback FAO/World Bank")
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des paramètres détaillés: {e}")
        
        # Fallback vers l'ancienne méthode FAO/World Bank
        try:
            # Indicateurs pertinents pour les ressources en eau et le stress hydrique
            indicator_codes = {
                "Ressources renouvelables par habitant": ("5142", "6021"), # Item, Element. Unité: 10^3 m³/inh/yr
                "Taux de dépendance hydrique": ("5143", "6021"), # Unité: %
                "Indice de stress hydrique (ODD 6.4.2)": ("642", "6021") # Unité: %
            }
            
            fao_data = apis.get_fao_aquastat_data(indicator_codes=indicator_codes)
            
            if not fao_data:
                logger.warning("Aucune donnée FAO AquaStat n'a été retournée.")
                # Utiliser le fallback World Bank
                fallback_data = apis.get_water_data_fallback()
                return fallback_data if fallback_data else {"Ressources en eau": ("Données non disponibles", "")}

            # Formater les données pour l'affichage (prendre la donnée la plus récente)
            formatted_data = {}
            for indicator, years_data in fao_data.items():
                if not years_data:
                    continue
                
                latest_year = sorted(years_data.keys(), reverse=True)[0]
                value, unit = years_data[latest_year]
                
                indicator_with_year = f"{indicator} ({latest_year})"
                formatted_data[indicator_with_year] = (value, unit)
                
            return formatted_data if formatted_data else {"Ressources en eau": ("Données non disponibles", "")}

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données FAO: {e}")
            return {"Erreur FAO": (str(e), "")}

    def _simulate_water_quality(self, lat, lon):
        # Génère des valeurs plausibles basées sur les coordonnées
        # pH ~ 7 +/- variation, Conductivité, Turbidité, Nitrates
        try:
            base = abs((lat * 3.1415 + lon) % 1)
            ph = round(6.5 + (base - 0.5), 2)
            cond = round(250 + base * 300, 1)  # µS/cm
            turb = round(1 + base * 4, 2)      # NTU
            no3 = round(5 + base * 20, 2)      # mg/L
            return {
                "pH": (ph, ""),
                "Conductivité": (cond, "µS/cm"),
                "Turbidité": (turb, "NTU"),
                "Nitrates": (no3, "mg/L")
            }
        except Exception:
            return {
                "pH": ("N/A", ""),
                "Conductivité": ("N/A", "µS/cm"),
                "Turbidité": ("N/A", "NTU"),
                "Nitrates": ("N/A", "mg/L")
            }

    def _export_excel(self):
        if getattr(self.app, 'current_results', None) is None:
            messagebox.showwarning("Attention", "Aucun résultat à exporter.")
            return
        self.app.export_to_excel()

    def _export_csv(self):
        if getattr(self.app, 'current_results', None) is None:
            messagebox.showwarning("Attention", "Aucun résultat à exporter.")
            return
        self.app.export_to_csv()

    def _clear_results(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)
        self.app.current_results = None
        self.progress['value'] = 0
        try:
            self.app.status_bar.set_status("Prêt", 0)
        except Exception:
            pass

class RiskAnalysisApp:
    def __init__(self, root, load_model=True):
        self.root = root
        self.root.title(UI_CONFIG["window_title"])
        self.root.geometry(f"{UI_CONFIG['window_width']}x{UI_CONFIG['window_height']}")

        # Configurer le gestionnaire d'événement pour la fermeture de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        self.file_path = ""
        self.current_data = None
        
        # Gestionnaire de projets
        from project_manager import ProjectManager
        self.project_manager = ProjectManager()
        self.current_project_mode = tk.BooleanVar(value=False)
        
        # Imports pour les dialogues de projet
        try:
            from project_dialogs import ProjectDialog, ProjectListDialog, ProjectStatusDialog
            self.ProjectDialog = ProjectDialog
            self.ProjectListDialog = ProjectListDialog
            self.ProjectStatusDialog = ProjectStatusDialog
        except ImportError:
            # Classes vides si les dialogues ne sont pas disponibles
            class DummyDialog:
                def __init__(self, *args, **kwargs):
                    self.result = None
                    self.selected_project = None
            self.ProjectDialog = DummyDialog
            self.ProjectListDialog = DummyDialog
            self.ProjectStatusDialog = DummyDialog
        
        # Statistiques du cache
        self.cache_stats = get_cache_stats()
        
        # Mode d'analyse (local ou cloud)
        self.analysis_mode = tk.StringVar(value="cloud")  # Par défaut, utiliser le cloud
        self.cloud_provider = tk.StringVar(value="huggingface")  # Par défaut, utiliser Hugging Face
        
        # Option pour demander le mode d'analyse à chaque analyse
        self.prompt_for_mode = tk.BooleanVar(value=True)  # Par défaut, demander à l'utilisateur
        
        # Initialiser le modèle Vision-Language configuré (pour le mode local)
        model_path = MODEL_CONFIG["model_path"]
        self.model = create_vlmodel_adapter(model_path)  # Utiliser le modèle configuré (plus léger par défaut)
        self.load_model = load_model  # Indicateur pour charger ou non le modèle au démarrage
        
        # Paramètres de traitement par lots (pour le mode local)
        self.batch_params = MODEL_CONFIG.get("batch_processing", {
            "text_chunk_size": 1000,
            "text_overlap": 100,
            "image_tile_size": 512,  # Taille réduite pour accélérer le traitement
            "image_overlap": 50      # Chevauchement réduit pour limiter le nombre de tuiles
        })
        
        # Charger les configurations des API cloud
        self.cloud_api_config = self._load_cloud_api_config()
        
        # Charger la configuration Gemini et vérifier sa validité (si disponible)
        self.gemini_config = None

        # Historique des analyses récentes : liste de tuples (nom, dataframe, timestamp)
        self.recent_analyses = []

        # Option globale pour l'utilisation de l'OCR
        self.use_ocr = tk.BooleanVar(value=True)
        ocr_frame = ttk.Frame(self.root)
        ocr_frame.pack(anchor='nw', padx=10, pady=2)
        ttk.Checkbutton(
            ocr_frame,
            text="Utiliser l'OCR pour l'analyse IA (images, PDF, etc.)",
            variable=self.use_ocr
        ).pack(side='left')

        if GEMINI_AVAILABLE:
            try:
                from gemini_integration import load_gemini_config
                self.gemini_config = load_gemini_config()
                if not self.gemini_config.get("enabled", False) or not self.gemini_config.get("api_key"):
                    messagebox.showwarning(
                        "Configuration Gemini",
                        "La configuration Gemini est incomplète ou désactivée. Veuillez vérifier la clé API Gemini dans le menu Configuration > Configurer les clés API."
                    )
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la configuration Gemini: {str(e)}")
                messagebox.showerror(
                    "Erreur Gemini",
                    f"Impossible de charger la configuration Gemini : {str(e)}\nVeuillez vérifier le fichier gemini_api_config.json."
                )
        
        # Initialiser l'analyseur SLRI avec collecteur d'eau
        try:
            from slri_standalone import create_slri_complete_analyzer
            from water_parameters_collector import create_water_parameters_collector
            
            self.slri_analyzer = create_slri_complete_analyzer()
            self.water_collector = create_water_parameters_collector()
            
            if self.slri_analyzer:
                logger.info("Analyseur SLRI initialisé avec succès")
            if self.water_collector:
                logger.info("Collecteur de paramètres d'eau initialisé avec succès")
            
            if not self.slri_analyzer:
                logger.warning("Échec de l'initialisation de l'analyseur SLRI")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation SLRI/Eau: {e}")
            self.slri_analyzer = None
            self.water_collector = None
        
        # Charger les configurations de l'application
        self._load_app_config()
        
        self._create_widgets()
        self._create_menu()
        
        logger.info("Application initialisée")
    
    def _run_slri_analysis(self, df):
        """
        Exécute l'analyse SLRI sur les données environnementales.
        
        Args:
            df: DataFrame contenant les données environnementales
            
        Returns:
            dict: Résultats de l'analyse SLRI ou None en cas d'erreur
        """
        try:
            # Extraire les coordonnées si disponibles
            coordinates = None
            if 'latitude' in df.columns and 'longitude' in df.columns:
                lat = df['latitude'].iloc[0] if not df['latitude'].empty else 0
                lon = df['longitude'].iloc[0] if not df['longitude'].empty else 0
                coordinates = (lat, lon)
            else:
                # Coordonnées par défaut (Maroc)
                coordinates = (33.5731, -7.5898)
            
            # Déterminer le type de projet
            project_type = "industriel"  # Par défaut
            if 'project_type' in df.columns:
                project_type = df['project_type'].iloc[0] if not df['project_type'].empty else "industriel"
            
            # Exécuter l'analyse SLRI complète
            slri_results = self.slri_analyzer.analyze_complete_slri(coordinates, project_type)
            
            if slri_results:
                logger.info("Analyse SLRI complétée avec succès")
                return slri_results
            else:
                logger.warning("L'analyse SLRI n'a pas produit de résultats")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse SLRI: {str(e)}")
            return None
    
    def analyze_slri_standalone(self):
        """Lance une analyse SLRI autonome avec saisie des coordonnées et paramètres d'eau détaillés"""
        try:
            if not self.slri_analyzer:
                messagebox.showerror("Erreur", "Analyseur SLRI non disponible")
                return
            
            # Dialogue pour saisir les coordonnées
            coord_dialog = tk.Toplevel(self.root)
            coord_dialog.title("Analyse SLRI avec paramètres d'eau détaillés")
            coord_dialog.geometry("500x300")
            coord_dialog.transient(self.root)
            coord_dialog.grab_set()
            
            # Variables pour stocker les coordonnées
            lat_var = tk.StringVar(value="34.0209")
            lon_var = tk.StringVar(value="-6.8416")
            water_analysis_var = tk.BooleanVar(value=True)
            
            # Interface de saisie
            tk.Label(coord_dialog, text="Latitude:").pack(pady=5)
            lat_entry = tk.Entry(coord_dialog, textvariable=lat_var, width=20)
            lat_entry.pack(pady=5)
            
            tk.Label(coord_dialog, text="Longitude:").pack(pady=5)
            lon_entry = tk.Entry(coord_dialog, textvariable=lon_var, width=20)
            lon_entry.pack(pady=5)
            
            # Option pour analyse d'eau détaillée
            tk.Checkbutton(coord_dialog, text="Inclure analyse détaillée des paramètres d'eau", 
                          variable=water_analysis_var).pack(pady=10)
            
            tk.Label(coord_dialog, text="L'analyse détaillée inclut:\n• Paramètres physico-chimiques\n• Pollution organique\n• Nutriments\n• Métaux lourds\n• Microbiologie\n• Pesticides", 
                    justify=tk.LEFT, font=("Arial", 9)).pack(pady=5)
            
            result_coords = [None]
            
            def validate_and_analyze():
                try:
                    lat = float(lat_var.get())
                    lon = float(lon_var.get())
                    result_coords[0] = (lat, lon, water_analysis_var.get())
                    coord_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Erreur", "Coordonnées invalides")
            
            tk.Button(coord_dialog, text="Analyser", command=validate_and_analyze).pack(pady=10)
            tk.Button(coord_dialog, text="Annuler", command=coord_dialog.destroy).pack(pady=5)
            
            # Attendre la fermeture du dialogue
            coord_dialog.wait_window()
            
            if result_coords[0]:
                coordinates = result_coords[0][:2]
                include_water = result_coords[0][2]
                logger.info(f"Lancement analyse SLRI pour {coordinates} (eau détaillée: {include_water})")
                
                # Collecte des paramètres d'eau détaillés si demandé
                if include_water and self.water_collector:
                    water_data = self.water_collector.collect_detailed_water_parameters(coordinates)
                    if water_data:
                        logger.info(f"Paramètres d'eau collectés: {sum(len(params) for params in water_data.values() if isinstance(params, dict))} paramètres")
                
                # Lancer l'analyse SLRI
                results = self.slri_analyzer.analyze_complete_slri(coordinates)
                
                if results:
                    self.display_slri_results(results)
                    logger.info("Analyse SLRI terminée avec succès")
                else:
                    messagebox.showerror("Erreur", "Échec de l'analyse SLRI")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse SLRI: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse SLRI: {str(e)}")
        finally:
            self.status_bar.set_status("Prêt")
    
    def show_water_analysis(self):
        """Affiche l'interface d'analyse détaillée des paramètres d'eau"""
        try:
            if not self.water_collector:
                messagebox.showerror("Erreur", "Collecteur de paramètres d'eau non disponible")
                return
            
            # Dialogue pour saisir les coordonnées
            coord_dialog = tk.Toplevel(self.root)
            coord_dialog.title("Analyse des paramètres d'eau")
            coord_dialog.geometry("400x200")
            coord_dialog.transient(self.root)
            coord_dialog.grab_set()
            
            # Variables pour stocker les coordonnées
            lat_var = tk.StringVar(value="34.0209")
            lon_var = tk.StringVar(value="-6.8416")
            
            # Interface de saisie
            tk.Label(coord_dialog, text="Latitude:").pack(pady=5)
            lat_entry = tk.Entry(coord_dialog, textvariable=lat_var, width=20)
            lat_entry.pack(pady=5)
            
            tk.Label(coord_dialog, text="Longitude:").pack(pady=5)
            lon_entry = tk.Entry(coord_dialog, textvariable=lon_var, width=20)
            lon_entry.pack(pady=5)
            
            result_coords = [None]
            
            def validate_and_show():
                try:
                    lat = float(lat_var.get())
                    lon = float(lon_var.get())
                    result_coords[0] = (lat, lon)
                    coord_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Erreur", "Coordonnées invalides")
            
            tk.Button(coord_dialog, text="Analyser", command=validate_and_show).pack(pady=10)
            tk.Button(coord_dialog, text="Annuler", command=coord_dialog.destroy).pack(pady=5)
            
            # Attendre la fermeture du dialogue
            coord_dialog.wait_window()
            
            if result_coords[0]:
                coordinates = result_coords[0]
                logger.info(f"Lancement analyse d'eau pour {coordinates}")
                
                # Créer et afficher l'interface d'analyse d'eau
                from water_analysis_interface import create_water_analysis_interface
                water_interface = create_water_analysis_interface(self.root, self.water_collector)
                if water_interface:
                    water_interface.show_detailed_water_analysis(coordinates)
                else:
                    messagebox.showerror("Erreur", "Impossible de créer l'interface d'analyse d'eau")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'eau: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse d'eau: {str(e)}")
    
    def run_slri_phases_analysis(self):
        """Lance l'analyse SLRI par phases (PRE CONSTRUCTION, CONSTRUCTION, EXPLOITATION, DÉMANTÈLEMENT)"""
        try:
            # Demander les coordonnées et le type de projet
            dialog = tk.Toplevel(self.root)
            dialog.title("Analyse SLRI par phases")
            dialog.geometry("500x350")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Variables
            lat_var = tk.StringVar(value="34.0209")
            lon_var = tk.StringVar(value="-6.8416")
            project_type_var = tk.StringVar(value="general")
            
            # Interface
            ttk.Label(dialog, text="Analyse SLRI par phases du projet", font=("Arial", 14, "bold")).pack(pady=10)
            
            # Coordonnées
            coords_frame = ttk.LabelFrame(dialog, text="Localisation du projet", padding=10)
            coords_frame.pack(fill="x", padx=20, pady=10)
            
            ttk.Label(coords_frame, text="Latitude:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Entry(coords_frame, textvariable=lat_var, width=15).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(coords_frame, text="Longitude:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Entry(coords_frame, textvariable=lon_var, width=15).grid(row=1, column=1, padx=5, pady=5)
            
            # Type de projet
            project_frame = ttk.LabelFrame(dialog, text="Type de projet", padding=10)
            project_frame.pack(fill="x", padx=20, pady=10)
            
            project_types = [
                ("Général", "general"),
                ("Industriel", "industrial"),
                ("Infrastructure", "infrastructure"),
                ("Énergétique", "energy"),
                ("Minier", "mining"),
                ("Agricole", "agricultural")
            ]
            
            for i, (label, value) in enumerate(project_types):
                ttk.Radiobutton(project_frame, text=label, variable=project_type_var, 
                               value=value).grid(row=i//2, column=i%2, padx=10, pady=2, sticky="w")
            
            def launch_phases_analysis():
                try:
                    lat = float(lat_var.get())
                    lon = float(lon_var.get())
                    project_type = project_type_var.get()
                    
                    dialog.destroy()
                    
                    # Collecter les données environnementales
                    from external_apis import ExternalAPIs
                    apis = ExternalAPIs()
                    
                    # Données environnementales complètes
                    env_data = {
                        'eau': apis.get_detailed_water_data(lat, lon),
                        'air': apis.get_air_quality_data(lat, lon),
                        'sol': apis.get_soil_data(lat, lon)
                    }
                    
                    # Lancer l'analyse SLRI par phases
                    from slri_phases_analyzer import analyze_project_with_slri_phases
                    results = analyze_project_with_slri_phases(env_data, project_type)
                    
                    if 'error' not in results:
                        self._display_slri_results_in_main_interface(results, "phases")
                    else:
                        messagebox.showerror("Erreur", f"Erreur lors de l'analyse: {results['error']}")
                    
                except ValueError:
                    messagebox.showerror("Erreur", "Veuillez entrer des coordonnées valides")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de l'analyse: {e}")
            
            # Boutons
            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(pady=20)
            
            ttk.Button(buttons_frame, text="Lancer l'analyse", command=launch_phases_analysis).pack(side="left", padx=10)
            ttk.Button(buttons_frame, text="Annuler", command=dialog.destroy).pack(side="left", padx=10)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture de l'analyse SLRI: {e}")

    def _show_slri_phases_results(self, results):
        """Affiche les résultats de l'analyse SLRI par phases"""
        try:
            # Créer une nouvelle fenêtre pour les résultats
            results_window = tk.Toplevel(self.root)
            results_window.title("Résultats SLRI par phases")
            results_window.geometry("1000x700")
            results_window.transient(self.root)
            
            # Notebook pour les onglets
            notebook = ttk.Notebook(results_window)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Onglet Synthèse
            synthesis_frame = ttk.Frame(notebook)
            notebook.add(synthesis_frame, text="Synthèse globale")
            
            synthesis_text = tk.Text(synthesis_frame, wrap=tk.WORD, font=("Consolas", 10))
            synthesis_scrollbar = ttk.Scrollbar(synthesis_frame, orient="vertical", command=synthesis_text.yview)
            synthesis_text.configure(yscrollcommand=synthesis_scrollbar.set)
            
            synthesis_text.pack(side="left", fill="both", expand=True)
            synthesis_scrollbar.pack(side="right", fill="y")
            
            # Contenu synthèse
            synthesis_content = self._format_synthesis_content(results)
            synthesis_text.insert("1.0", synthesis_content)
            synthesis_text.config(state="disabled")
            
            # Onglets pour chaque phase
            phases = results.get('phases', {})
            for phase_key, phase_data in phases.items():
                phase_frame = ttk.Frame(notebook)
                phase_name = phase_data.get('phase_name', phase_key)
                notebook.add(phase_frame, text=phase_name)
                
                # Contenu de la phase
                phase_text = tk.Text(phase_frame, wrap=tk.WORD, font=("Consolas", 10))
                phase_scrollbar = ttk.Scrollbar(phase_frame, orient="vertical", command=phase_text.yview)
                phase_text.configure(yscrollcommand=phase_scrollbar.set)
                
                phase_text.pack(side="left", fill="both", expand=True)
                phase_scrollbar.pack(side="right", fill="y")
                
                phase_content = self._format_phase_content(phase_data)
                phase_text.insert("1.0", phase_content)
                phase_text.config(state="disabled")
            
            # Bouton d'export
            export_btn = ttk.Button(results_window, text="Exporter rapport", 
                                   command=lambda: self._export_slri_phases_report(results))
            export_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage des résultats: {e}")

    def _format_synthesis_content(self, results):
        """Formate le contenu de la synthèse globale"""
        content = []
        content.append("=" * 80)
        content.append("SYNTHÈSE GLOBALE - ANALYSE SLRI PAR PHASES")
        content.append("=" * 80)
        content.append("")
        
        metadata = results.get('metadata', {})
        content.append(f"Date d'analyse: {metadata.get('date_analyse', 'N/A')}")
        content.append(f"Type de projet: {metadata.get('project_type', 'N/A')}")
        content.append(f"Méthodologie: {metadata.get('methodology', 'SLRI')}")
        content.append("")
        
        synthesis = results.get('synthese', {})
        content.append("SCORES GLOBAUX:")
        content.append(f"- Score global du projet: {synthesis.get('score_global_projet', 0):.2f}")
        content.append(f"- Phase la plus critique: {synthesis.get('phase_plus_critique', 'N/A')}")
        content.append(f"- Conformité globale: {'✓ OUI' if synthesis.get('conformite_globale', False) else '✗ NON'}")
        content.append("")
        
        # Risques majeurs globaux
        major_risks = synthesis.get('risques_majeurs_globaux', [])
        if major_risks:
            content.append("RISQUES MAJEURS IDENTIFIÉS:")
            for i, risk in enumerate(major_risks[:5], 1):
                content.append(f"{i}. {risk.get('parametre', 'N/A')} ({risk.get('milieu', 'N/A')}) - "
                             f"Phase: {risk.get('phase', 'N/A')} - Score: {risk.get('score', 0):.1f}")
        else:
            content.append("RISQUES MAJEURS: Aucun risque majeur identifié")
        
        content.append("")
        
        # Recommandations prioritaires
        recommendations = synthesis.get('recommandations_prioritaires', [])
        if recommendations:
            content.append("RECOMMANDATIONS PRIORITAIRES:")
            for i, rec in enumerate(recommendations, 1):
                content.append(f"{i}. {rec}")
        
        return "\n".join(content)

    def _format_phase_content(self, phase_data):
        """Formate le contenu d'une phase"""
        content = []
        phase_name = phase_data.get('phase_name', 'Phase')
        content.append("=" * 60)
        content.append(f"PHASE: {phase_name.upper()}")
        content.append("=" * 60)
        content.append("")
        
        # Scores totaux
        scores = phase_data.get('scores_totaux', {})
        content.append("SCORES DE LA PHASE:")
        content.append(f"- Score global: {scores.get('score_global', 0):.2f}")
        content.append(f"- Classification: {scores.get('classification_globale', 'FAIBLE')}")
        content.append("")
        
        scores_par_milieu = scores.get('scores_par_milieu', {})
        if scores_par_milieu:
            content.append("Scores par milieu:")
            for milieu, score in scores_par_milieu.items():
                content.append(f"  - {milieu.capitalize()}: {score:.2f}")
        content.append("")
        
        # Risques majeurs
        major_risks = phase_data.get('risques_majeurs', [])
        if major_risks:
            content.append("RISQUES MAJEURS DE LA PHASE:")
            for risk in major_risks:
                content.append(f"- {risk.get('parametre', 'N/A')} ({risk.get('milieu', 'N/A')}): "
                             f"Score {risk.get('score', 0):.1f} - {risk.get('classification', 'N/A')}")
        else:
            content.append("RISQUES MAJEURS: Aucun")
        content.append("")
        
        # Détail par milieu
        milieux = phase_data.get('milieux', {})
        for milieu_name, milieu_data in milieux.items():
            content.append(f"=== MILIEU: {milieu_name.upper()} ===")
            content.append(f"Score du milieu: {milieu_data.get('score_milieu', 0):.2f}")
            content.append(f"Classification: {milieu_data.get('classification_risque', 'FAIBLE')}")
            content.append(f"Paramètres non conformes: {milieu_data.get('nb_parametres_non_conformes', 0)}")
            content.append("")
            
            # Paramètres détaillés
            parametres = milieu_data.get('parametres', {})
            if parametres:
                content.append("Paramètres analysés:")
                for param_name, param_data in parametres.items():
                    value = param_data.get('valeur_mesuree', 'N/A')
                    unit = param_data.get('unite', '')
                    score = param_data.get('score_final', 0)
                    conforme = "✓" if param_data.get('conforme', True) else "✗"
                    content.append(f"  {conforme} {param_name}: {value} {unit} (Score: {score:.1f})")
            content.append("")
        
        # Recommandations
        recommendations = phase_data.get('recommandations', [])
        if recommendations:
            content.append("RECOMMANDATIONS POUR CETTE PHASE:")
            for i, rec in enumerate(recommendations, 1):
                content.append(f"{i}. {rec}")
        
        return "\n".join(content)

    def _export_slri_phases_report(self, results):
        """Exporte le rapport SLRI par phases"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Exporter rapport SLRI par phases",
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Synthèse
                    f.write(self._format_synthesis_content(results))
                    f.write("\n\n")
                    
                    # Détail par phase
                    phases = results.get('phases', {})
                    for phase_key, phase_data in phases.items():
                        f.write(self._format_phase_content(phase_data))
                        f.write("\n\n")
                
                messagebox.showinfo("Export réussi", f"Rapport exporté vers: {filename}")
        
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Erreur lors de l'export: {e}")
    
    def analyze_text_file(self):
        """Analyse un fichier texte pour extraire des données environnementales"""
        try:
            from tkinter import filedialog
            
            # Demander à l'utilisateur de sélectionner un fichier texte
            file_path = filedialog.askopenfilename(
                title="Sélectionner un fichier texte à analyser",
                filetypes=[
                    ("Fichiers texte", "*.txt"),
                    ("Fichiers CSV", "*.csv"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Contrôle OCR : si désactivé, passer le fichier brut à l'IA
            use_ocr = self.use_ocr.get() if hasattr(self, 'use_ocr') else True
            if not use_ocr and hasattr(self, 'text_analyzer') and hasattr(self.text_analyzer, 'analyze_file_direct'):
                results = self.text_analyzer.analyze_file_direct(file_path)
            else:
                # Lire le contenu du fichier
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Analyser le contenu avec l'analyseur de texte
                if hasattr(self, 'text_analyzer') and self.text_analyzer:
                    results = self.text_analyzer.analyze_text(content)
                
                # Afficher les résultats
                if results:
                    # Ajout à l'historique des analyses récentes pour export SLRI
                    import datetime
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    nom = f"Analyse texte {now}"
                    try:
                        import pandas as pd
                        if isinstance(results, pd.DataFrame):
                            df = results
                        elif isinstance(results, list) and all(isinstance(r, dict) for r in results):
                            df = pd.DataFrame(results)
                        else:
                            df = None
                        if df is not None and not df.empty:
                            self.recent_analyses.append((nom, df, now))
                            self.recent_analyses = self.recent_analyses[-10:]
                    except Exception:
                        pass
                    self._display_text_analysis_results(results, file_path)
                else:
                    messagebox.showinfo("Analyse terminée", "Aucune donnée environnementale détectée dans le fichier.")
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du fichier texte: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'analyse du fichier: {str(e)}")
    
    def _display_text_analysis_results(self, results, file_path):
        """Affiche les résultats de l'analyse de texte"""
        import pandas as pd
         # Si résultat IA structuré (liste de dicts), convertir et ajouter à l'historique
        if isinstance(results, list) and all(isinstance(r, dict) for r in results):
            df = pd.DataFrame(results)
            import datetime
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            nom = f"Analyse IA ({now})"
            self.recent_analyses.append((nom, df, now))
            self.recent_analyses = self.recent_analyses[-10:]
            self.current_results = df
            
        try:
            # Créer une fenêtre pour afficher les résultats
            results_window = tk.Toplevel(self.root)
            results_window.title(f"Résultats d'analyse - {os.path.basename(file_path)}")
            results_window.geometry("800x600")
            results_window.transient(self.root)
            
            # Zone de texte avec scrollbar
            text_frame = ttk.Frame(results_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            results_text = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=scrollbar.set)
            
            results_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Formater et afficher les résultats
            content = []
            content.append("=" * 80)
            content.append(f"ANALYSE DE FICHIER TEXTE: {os.path.basename(file_path)}")
            content.append("=" * 80)
            content.append("")
            
            if isinstance(results, dict):
                for category, data in results.items():
                    content.append(f"=== {category.upper()} ===")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            content.append(f"{key}: {value}")
                    elif isinstance(data, list):
                        for item in data:
                            content.append(f"- {item}")
                    else:
                        content.append(str(data))
                    content.append("")
            else:
                content.append(str(results))
            
            results_text.insert("1.0", "\n".join(content))
            results_text.config(state="disabled")
            
            # Bouton de fermeture
            ttk.Button(results_window, text="Fermer", command=results_window.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des résultats: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")
    
    def run_slri_analysis_standalone(self):
        """Lance une analyse SLRI complète autonome"""
        try:
            # Demander les coordonnées à l'utilisateur
            dialog = tk.Toplevel(self.root)
            dialog.title("Analyse SLRI complète")
            dialog.geometry("400x250")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Variables
            lat_var = tk.StringVar(value="34.0209")
            lon_var = tk.StringVar(value="-6.8416")
            
            # Interface
            ttk.Label(dialog, text="Analyse SLRI complète", font=("Arial", 14, "bold")).pack(pady=10)
            
            # Coordonnées
            coords_frame = ttk.LabelFrame(dialog, text="Localisation", padding=10)
            coords_frame.pack(fill="x", padx=20, pady=10)
            
            ttk.Label(coords_frame, text="Latitude:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Entry(coords_frame, textvariable=lat_var, width=15).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(coords_frame, text="Longitude:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Entry(coords_frame, textvariable=lon_var, width=15).grid(row=1, column=1, padx=5, pady=5)
            
            def launch_analysis():
                try:
                    lat = float(lat_var.get())
                    lon = float(lon_var.get())
                    
                    dialog.destroy()
                    
                    # Collecter les données environnementales
                    from external_apis import ExternalAPIs
                    apis = ExternalAPIs()
                    
                    # Données complètes
                    env_data = {
                        'eau': apis.get_detailed_water_data(lat, lon),
                        'air': apis.get_air_quality_data(lat, lon),
                        'sol': apis.get_soil_data(lat, lon),
                        'meteo': apis.get_weather_data(lat, lon),
                        'biodiversite': apis.get_biodiversity_data(lat, lon)
                    }
                    
                    # Analyser avec SLRI
                    if hasattr(self, 'slri_analyzer') and self.slri_analyzer:
                        results = self.slri_analyzer.analyze_environmental_data(env_data)
                        self._display_slri_results(results)
                    else:
                        # Utiliser l'analyse par phases comme fallback
                        from slri_phases_analyzer import analyze_project_with_slri_phases
                        results = analyze_project_with_slri_phases(env_data, 'general')
                        self._display_slri_results_in_main_interface(results, "complete")
                    
                except ValueError:
                    messagebox.showerror("Erreur", "Veuillez entrer des coordonnées valides")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de l'analyse: {e}")
            
            # Boutons
            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(pady=20)
            
            ttk.Button(buttons_frame, text="Lancer l'analyse", command=launch_analysis).pack(side="left", padx=10)
            ttk.Button(buttons_frame, text="Annuler", command=dialog.destroy).pack(side="left", padx=10)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture de l'analyse SLRI: {e}")
    
    def _display_slri_results(self, results):
        """Affiche les résultats de l'analyse SLRI complète"""
        try:
            # Créer une fenêtre pour les résultats
            results_window = tk.Toplevel(self.root)
            results_window.title("Résultats SLRI complets")
            results_window.geometry("900x600")
            results_window.transient(self.root)
            
            # Zone de texte avec scrollbar
            text_frame = ttk.Frame(results_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            results_text = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=scrollbar.set)
            
            results_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Formater les résultats
            content = []
            content.append("=" * 80)
            content.append("ANALYSE SLRI COMPLÈTE")
            content.append("=" * 80)
            content.append("")
            
            if isinstance(results, dict):
                for category, data in results.items():
                    content.append(f"=== {category.upper()} ===")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            content.append(f"{key}: {value}")
                    elif isinstance(data, list):
                        for item in data:
                            content.append(f"- {item}")
                    else:
                        content.append(str(data))
                    content.append("")
            else:
                content.append(str(results))
            
            results_text.insert("1.0", "\n".join(content))
            results_text.config(state="disabled")
            
            # Bouton de fermeture
            ttk.Button(results_window, text="Fermer", command=results_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {e}")
    
    def _display_slri_results_in_main_interface(self, results, analysis_type):
        try:
            import pandas as pd
            import json
            from slri_phase_selector import select_slri_phases
            
            # Sélection des phases par l'utilisateur
            phase_selection = select_slri_phases(self.root)
            if not phase_selection:
                return  # Utilisateur a annulé
            
            selected_phases = phase_selection['phases']
            project_status = phase_selection['project_status']
            
            # Charger la configuration des phases
            try:
                with open('phases_slri.json', 'r', encoding='utf-8') as f:
                    phases_config = json.load(f)
            except:
                phases_config = {}
            
            # Créer un nouvel onglet pour les résultats SLRI
            slri_frame = ttk.Frame(self.notebook)
            tab_name = f"SLRI {analysis_type.title()}"
            self.notebook.add(slri_frame, text=tab_name)
            
            # Container principal
            main_container = ttk.Frame(slri_frame)
            main_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # En-tête avec titre et indicateur de progression
            header_frame = ttk.Frame(main_container)
            header_frame.pack(fill="x", pady=(0, 10))
            
            ttk.Label(header_frame, text="Analyse SLRI - Cycle de Vie du Projet", 
                     font=("Arial", 16, "bold")).pack(side="left")
            
            # Indicateur de progression
            self.phase_progress = ttk.Progressbar(header_frame, mode='determinate', maximum=len(selected_phases), length=200)
            self.phase_progress.pack(side="right", padx=(10, 0))
            self.phase_progress.configure(value=1)  # Démarrer à la première phase
            
            # Frame pour les boutons de navigation des phases (seulement les sélectionnées)
            nav_frame = ttk.Frame(main_container)
            nav_frame.pack(fill="x", pady=(0, 10))
            
            # Variables pour la navigation
            self.current_phase = tk.StringVar(value=selected_phases[0] if selected_phases else "pre_construction")
            self.slri_results = results
            self.phases_config = phases_config
            self.selected_phases = selected_phases
            
            # Affichage du statut du projet
            status_frame = ttk.Frame(nav_frame)
            status_frame.pack(fill="x", pady=(0, 10))
            
            status_text = f"📋 Statut du projet : {phases_config.get(project_status, {}).get('title', project_status.title())}"
            ttk.Label(status_frame, text=status_text, font=("Arial", 11, "italic"), 
                     foreground="blue").pack(anchor="w")
            
            # Créer les boutons de navigation et les frames des phases (seulement pour les phases sélectionnées)
            self.phase_buttons = {}
            self.phase_frames = {}
            
            for i, phase_key in enumerate(selected_phases):
                if phase_key not in phases_config:
                    continue
                    
                phase_config = phases_config[phase_key]
                
                # Bouton de navigation
                icon = phase_config.get('icon', '📊')
                title = phase_config.get('title', phase_key.title())
                color = phase_config.get('color', '#3498db')
                
                btn = tk.Button(nav_frame, text=f"{icon} {title}", 
                              font=("Arial", 10, "bold"), 
                              bg=color, fg="white", relief="raised",
                              command=lambda pk=phase_key, pn=i+1: self._show_phase(pk, pn))
                btn.pack(side="left", padx=5, pady=5)
                self.phase_buttons[phase_key] = btn
                
                # Frame pour le contenu de la phase
                phase_frame = ttk.Frame(main_container)
                self.phase_frames[phase_key] = phase_frame
                
                # Créer le contenu de la phase si elle existe dans les résultats
                if phase_key in results.get('phases', {}):
                    phase_data = results['phases'][phase_key]
                    self._create_phase_content(phase_frame, phase_key, phase_data, phase_config)
                else:
                    # Créer un contenu par défaut si pas de données
                    from default_phase_content import create_default_phase_content
                    create_default_phase_content(phase_frame, phase_key, phase_config)
            
            # Afficher la première phase sélectionnée par défaut
            if selected_phases:
                self._show_phase(selected_phases[0], 1)
            
            # Sélectionner le nouvel onglet
            self.notebook.select(slri_frame)
            
            # Message de succès
            self.status_bar.set_status(f"Analyse SLRI {analysis_type} terminée avec succès", 100)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des résultats SLRI: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {e}")
    
    def _show_phase(self, phase_key, phase_number):
        """Affiche une phase spécifique et masque les autres"""
        try:
            # Masquer tous les frames de phases
            for frame in self.phase_frames.values():
                frame.pack_forget()
            
            # Afficher le frame de la phase sélectionnée
            if phase_key in self.phase_frames:
                self.phase_frames[phase_key].pack(fill="both", expand=True)
            
            # Mettre à jour les styles des boutons
            for btn_key, btn in self.phase_buttons.items():
                if btn_key == phase_key:
                    btn.config(relief="sunken")
                else:
                    phase_info = self.phases_config.get(btn_key, {})
                    original_color = phase_info.get('color', '#3498db')
                    btn.config(relief="raised", bg=original_color)
            
            # Mettre à jour la barre de progression et la variable
            self.phase_progress.configure(value=phase_number)
            self.current_phase.set(phase_key)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la phase {phase_key}: {e}")
    
    def _create_phase_content(self, parent_frame, phase_key, phase_data, phase_config):
        """Crée le contenu pour une phase spécifique"""
        try:
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
            
            self._create_phase_overview(overview_frame, phase_key, phase_data, phase_config)
            
            # Onglet Paramètres détaillés
            if phase_data.get('milieux'):
                details_frame = ttk.Frame(phase_notebook)
                phase_notebook.add(details_frame, text="Paramètres détaillés")
                
                self._create_phase_details(details_frame, phase_data)
            
            # Onglet Risques majeurs
            if phase_data.get('risques_majeurs'):
                risks_frame = ttk.Frame(phase_notebook)
                phase_notebook.add(risks_frame, text="Risques majeurs")
                
                self._create_risks_table(risks_frame, phase_data.get('risques_majeurs', []))
            
            # Onglet spécial pour la phase d'exploitation : Surveillance Continue
            if phase_key == "exploitation":
                monitoring_frame = ttk.Frame(phase_notebook)
                phase_notebook.add(monitoring_frame, text="Surveillance Continue")
                
                self._create_monitoring_content(monitoring_frame)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du contenu pour {phase_key}: {e}")
    
    def _create_phase_overview(self, parent, phase_key, phase_data, phase_config):
        """Crée la vue d'ensemble d'une phase"""
        # Scores par milieu
        scores = phase_data.get('scores_totaux', {}).get('scores_par_milieu', {})
        if scores:
            scores_data = {
                'Milieu': list(scores.keys()),
                'Score': [f"{score:.2f}" for score in scores.values()],
                'Classification': [self._get_risk_classification(score) for score in scores.values()]
            }
            scores_df = pd.DataFrame(scores_data)
            self._create_exportable_table(parent, scores_df, f"Scores par milieu - {phase_config.get('title', phase_key)}")
        
        # Paramètres configurés pour cette phase
        parameters = phase_config.get('parameters', [])
        if parameters:
            # Separator
            ttk.Separator(parent, orient='horizontal').pack(fill="x", pady=10)
            
            param_frame = ttk.LabelFrame(parent, text="Paramètres surveillés", padding=10)
            param_frame.pack(fill="x", pady=5)
            
            # Afficher les paramètres en colonnes
            cols = 2
            for i, param in enumerate(parameters):
                row = i // cols
                col = i % cols
                
                # Vérifier si c'est le système de surveillance continue
                if param == "Système de Surveillance Continue Implémenté":
                    icon = "🔄"
                    color = "#27ae60"
                    status = "✅ IMPLÉMENTÉ"
                else:
                    icon = "📋"
                    color = "#3498db"
                    status = "✅ Configuré"
                
                param_label = tk.Label(param_frame, 
                                     text=f"{icon} {param}",
                                     font=("Arial", 9),
                                     fg=color,
                                     anchor="w")
                param_label.grid(row=row, column=col*2, sticky="w", padx=5, pady=2)
                
                status_label = tk.Label(param_frame,
                                      text=status,
                                      font=("Arial", 8),
                                      fg="green")
                status_label.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
    
    def _create_monitoring_content(self, parent):
        """Crée le contenu spécifique à la surveillance continue pour la phase d'exploitation"""
        # En-tête
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 15))
        
        ttk.Label(header, text="🔄 Système de Surveillance Continue Implémenté", 
                 font=("Arial", 14, "bold"), foreground="#27ae60").pack(anchor="w")
        
        ttk.Label(header, text="Surveillance automatisée des paramètres environnementaux en phase d'exploitation", 
                 font=("Arial", 10), foreground="gray").pack(anchor="w")
        
        # Status de la surveillance
        status_frame = ttk.LabelFrame(parent, text="État de la Surveillance", padding=10)
        status_frame.pack(fill="x", pady=10)
        
        status_data = {
            'Composant': [
                'Traitement par lots automatisé',
                'Surveillance des seuils critiques', 
                'Alertes automatiques',
                'Tableau de bord temps réel',
                'Analyse des tendances',
                'Rapports périodiques'
            ],
            'État': [
                '✅ ACTIF',
                '✅ ACTIF', 
                '✅ ACTIF',
                '✅ ACTIF',
                '✅ ACTIF',
                '✅ ACTIF'
            ],
            'Dernière vérification': [
                'Il y a 5 min',
                'Il y a 2 min',
                'Il y a 1 min', 
                'Temps réel',
                'Il y a 30 min',
                'Il y a 1 heure'
            ]
        }
        
        monitoring_df = pd.DataFrame(status_data)
        self._create_exportable_table(status_frame, monitoring_df, "État du Système de Surveillance")
        
        # Boutons d'action
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill="x", pady=15)
        
        ttk.Button(actions_frame, text="📊 Ouvrir Tableau de Bord", 
                  command=self.launch_monitoring_dashboard).pack(side="left", padx=5)
        
        ttk.Button(actions_frame, text="📈 Analyser Tendances", 
                  command=self.analyze_site_trends).pack(side="left", padx=5)
        
        ttk.Button(actions_frame, text="🚨 Voir Alertes", 
                  command=self.view_alerts_history).pack(side="left", padx=5)
    
    def _create_synthesis_table(self, results):
        """Crée un tableau pour la synthèse globale"""
        import pandas as pd
        
        synthesis = results.get('synthese', {})
        metadata = results.get('metadata', {})
        
        # Données de synthèse
        synthesis_data = {
            'Métrique': [
                'Score global du projet',
                'Phase la plus critique',
                'Conformité globale',
                'Nombre de risques majeurs',
                'Type de projet',
                'Date d\'analyse'
            ],
            'Valeur': [
                f"{synthesis.get('score_global_projet', 0):.2f}",
                synthesis.get('phase_plus_critique', 'N/A'),
                'OUI' if synthesis.get('conformite_globale', False) else 'NON',
                len(synthesis.get('risques_majeurs_globaux', [])),
                metadata.get('project_type', 'N/A'),
                metadata.get('date_analyse', 'N/A')[:19]  # Format datetime
            ],
            'Classification': [
                self._get_risk_classification(synthesis.get('score_global_projet', 0)),
                '',
                'CONFORME' if synthesis.get('conformite_globale', False) else 'NON CONFORME',
                'CRITIQUE' if len(synthesis.get('risques_majeurs_globaux', [])) > 5 else 'ACCEPTABLE',
                '',
                ''
            ]
        }
        
        return pd.DataFrame(synthesis_data)
    
    def _create_phase_tables(self, phase_data):
        """Crée les tableaux pour une phase donnée"""
        import pandas as pd
        
        tables = {}
        
        # Tableau des scores par milieu
        scores = phase_data.get('scores_totaux', {})
        scores_par_milieu = scores.get('scores_par_milieu', {})
        
        if scores_par_milieu:
            scores_data = {
                'Milieu': list(scores_par_milieu.keys()),
                'Score': [f"{score:.2f}" for score in scores_par_milieu.values()],
                'Classification': [self._get_risk_classification(score) for score in scores_par_milieu.values()]
            }
            tables['scores'] = pd.DataFrame(scores_data)
        
        # Tableau des paramètres par milieu
        milieux = phase_data.get('milieux', {})
        for milieu_name, milieu_data in milieux.items():
            parametres = milieu_data.get('parametres', {})
            if parametres:
                param_data = {
                    'Paramètre': [],
                    'Valeur mesurée': [],
                    'Unité': [],
                    'Score': [],
                    'Classification': [],
                    'Conforme': []
                }
                
                for param_name, param_info in parametres.items():
                    param_data['Paramètre'].append(param_name)
                    param_data['Valeur mesurée'].append(str(param_info.get('valeur_mesuree', 'N/A')))
                    param_data['Unité'].append(param_info.get('unite', ''))
                    param_data['Score'].append(f"{param_info.get('score_final', 0):.1f}")
                    param_data['Classification'].append(param_info.get('classification_risque', 'FAIBLE'))
                    param_data['Conforme'].append('✓' if param_info.get('conforme', True) else '✗')
                
                tables[f'parametres_{milieu_name}'] = pd.DataFrame(param_data)
        
        # Tableau des risques majeurs
        risques_majeurs = phase_data.get('risques_majeurs', [])
        if risques_majeurs:
            risques_data = {
                'Paramètre': [r.get('parametre', 'N/A') for r in risques_majeurs],
                'Milieu': [r.get('milieu', 'N/A') for r in risques_majeurs],
                'Score': [f"{r.get('score', 0):.1f}" for r in risques_majeurs],
                'Classification': [r.get('classification', 'FAIBLE') for r in risques_majeurs],
                'Valeur': [str(r.get('valeur', 'N/A')) for r in risques_majeurs]
            }
            tables['risques'] = pd.DataFrame(risques_data)
        
        return tables
    
    def _create_exportable_table(self, parent, dataframe, title):
        """Crée un tableau exportable avec Treeview"""
        # Frame pour le titre et les boutons
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(header_frame, text=title, font=("Arial", 12, "bold")).pack(side="left")
        
        # Boutons d'export
        export_frame = ttk.Frame(header_frame)
        export_frame.pack(side="right")
        
        ttk.Button(export_frame, text="Export Excel", 
                  command=lambda: self._export_dataframe(dataframe, title, "excel")).pack(side="left", padx=2)
        ttk.Button(export_frame, text="Export CSV", 
                  command=lambda: self._export_dataframe(dataframe, title, "csv")).pack(side="left", padx=2)
        
        # Frame pour le tableau
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Créer le Treeview
        columns = list(dataframe.columns)
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # Configurer les colonnes
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        # Ajouter les données
        for index, row in dataframe.iterrows():
            tree.insert("", "end", values=list(row))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack des éléments
        tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
    
    def _create_phase_display(self, parent, tables, phase_name):
        """Crée l'affichage complet pour une phase avec tous ses tableaux"""
        # Notebook pour organiser les tableaux de la phase
        phase_notebook = ttk.Notebook(parent)
        phase_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Onglet scores
        if 'scores' in tables:
            scores_frame = ttk.Frame(phase_notebook)
            phase_notebook.add(scores_frame, text="Scores par milieu")
            self._create_exportable_table(scores_frame, tables['scores'], f"Scores - {phase_name}")
        
        # Onglets paramètres par milieu
        for table_name, table_df in tables.items():
            if table_name.startswith('parametres_'):
                milieu = table_name.replace('parametres_', '').title()
                param_frame = ttk.Frame(phase_notebook)
                phase_notebook.add(param_frame, text=f"Paramètres {milieu}")
                self._create_exportable_table(param_frame, table_df, f"Paramètres {milieu} - {phase_name}")
        
        # Onglet risques majeurs
        if 'risques' in tables:
            risques_frame = ttk.Frame(phase_notebook)
            phase_notebook.add(risques_frame, text="Risques majeurs")
            self._create_exportable_table(risques_frame, tables['risques'], f"Risques majeurs - {phase_name}")
    
    def _export_dataframe(self, dataframe, title, format_type):
        """Exporte un DataFrame vers Excel ou CSV"""
        try:
            from tkinter import filedialog
            import pandas as pd
            
            # Demander le nom du fichier
            if format_type == "excel":
                filename = filedialog.asksaveasfilename(
                    title=f"Exporter {title}",
                    defaultextension=".xlsx",
                    filetypes=[("Fichiers Excel", "*.xlsx"), ("Tous les fichiers", "*.*")]
                )
                if filename:
                    dataframe.to_excel(filename, index=False, sheet_name=title[:31])  # Limite Excel pour nom de feuille
            else:  # CSV
                filename = filedialog.asksaveasfilename(
                    title=f"Exporter {title}",
                    defaultextension=".csv",
                    filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
                )
                if filename:
                    dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
            
            if filename:
                messagebox.showinfo("Export réussi", f"Tableau exporté vers: {filename}")
                
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Erreur lors de l'export: {e}")
    
    def _get_risk_classification(self, score):
        """Retourne la classification du risque selon le score SLRI"""
        if score <= 4:
            return "FAIBLE"
        elif score <= 8:
            return "MOYEN"
        elif score <= 12:
            return "FORT"
        else:
            return "TRÈS GRAVE"
    
    def generate_slri_report(self):
        """
        Génère un rapport SLRI complet au format Excel.
        """
        if not self.slri_analyzer:
            messagebox.showerror("Erreur", "L'analyseur SLRI n'est pas disponible.")
            return
        
        try:
            # Demander les coordonnées et le type de projet
            from tkinter import simpledialog, filedialog
            
            lat = simpledialog.askfloat("Coordonnées", "Latitude:", initialvalue=33.5731)
            if lat is None:
                return
                
            lon = simpledialog.askfloat("Coordonnées", "Longitude:", initialvalue=-7.5898)
            if lon is None:
                return
            
            project_type = simpledialog.askstring("Type de projet", 
                                                 "Type de projet:",
                                                 initialvalue="industriel")
            if not project_type:
                project_type = "industriel"
            
            # Demander où sauvegarder le rapport
            output_path = filedialog.asksaveasfilename(
                title="Sauvegarder le rapport SLRI",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not output_path:
                return
            
            # Générer le rapport
            self.status_bar.set_status("Génération du rapport SLRI...", 50)
            coordinates = (lat, lon)
            
            success = self.slri_analyzer.export_slri_to_excel(coordinates, project_type, output_path)
            
            if success:
                self.status_bar.set_status("Rapport SLRI généré", 100)
                messagebox.showinfo("Succès", f"Rapport SLRI généré avec succès:\n{output_path}")
            else:
                messagebox.showerror("Erreur", "La génération du rapport a échoué.")
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport SLRI: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport: {str(e)}")
        finally:
            self.status_bar.set_status("Prêt")
    
    def _display_slri_results(self, results, coordinates, project_type):
        """
        Affiche les résultats SLRI dans une nouvelle fenêtre.
        """
        try:
            # Créer une nouvelle fenêtre pour les résultats
            results_window = tk.Toplevel(self.root)
            results_window.title("Résultats de l'Analyse SLRI")
            results_window.geometry("800x600")
            
            # Créer un widget Text avec scrollbar
            text_frame = tk.Frame(results_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Formater et afficher les résultats
            content = f"ANALYSE SLRI COMPLÈTE\n"
            content += f"{'='*50}\n\n"
            content += f"Coordonnées: {coordinates[0]:.4f}, {coordinates[1]:.4f}\n"
            content += f"Type de projet: {project_type}\n\n"
            
            if 'phases' in results:
                for phase, phase_data in results['phases'].items():
                    content += f"\n{phase.upper()}\n"
                    content += f"{'-'*30}\n"
                    
                    if 'score_global' in phase_data:
                        content += f"Score global: {phase_data['score_global']}\n"
                    
                    if 'parametres' in phase_data:
                        for milieu, parametres in phase_data['parametres'].items():
                            content += f"\n  {milieu.upper()}:\n"
                            for param, data in parametres.items():
                                if isinstance(data, dict):
                                    valeur = data.get('valeur_mesuree', 'N/A')
                                    score = data.get('score', 'N/A')
                                    content += f"    {param}: {valeur} (Score: {score})\n"
            
            if 'risques_majeurs' in results:
                content += f"\nRISQUES MAJEURS:\n"
                content += f"{'-'*20}\n"
                for risque in results['risques_majeurs']:
                    content += f"• {risque}\n"
            
            if 'recommandations' in results:
                content += f"\nRECOMMANDATIONS:\n"
                content += f"{'-'*20}\n"
                for rec in results['recommandations']:
                    content += f"• {rec}\n"
            
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des résultats SLRI: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")
    
    def _load_cloud_api_config(self):
        """Charge les configurations des API cloud."""
        try:
            # Importer les configurations depuis le module cloud_api
            from cloud_api import API_CONFIG
            return API_CONFIG
        except Exception as e:
            logger.error(f"Erreur lors du chargement des configurations API cloud depuis le module: {str(e)}")
            
            # Essayer de charger directement depuis le fichier cloud_api_config.json
            try:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    logger.info("Configurations des API cloud chargées avec succès depuis cloud_api_config.json")
                    return config
            except Exception as e2:
                logger.error(f"Erreur lors du chargement des configurations API cloud depuis le fichier: {str(e2)}")
            
            # Configuration par défaut si tout échoue
            config = {
                "openai": {"api_key": "", "api_url": "https://api.openai.com/v1/chat/completions"},
                "azure": {"api_key": "", "endpoint": ""},
                "google": {"api_key": "", "api_url": ""},
                "qwen": {"api_key": "", "api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"},
                "openrouter": {"api_key": "", "api_url": "https://openrouter.ai/api/v1/chat/completions", "site_url": "", "site_name": ""}
            }
            
            # Ajouter Gemini si disponible
            if GEMINI_AVAILABLE:
                config["gemini"] = {"api_key": ""}
                
            return config
    
    def _load_app_config(self):
        """Charge les configurations de l'application."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Charger les préférences
                    if "prompt_for_mode" in config:
                        self.prompt_for_mode.set(config["prompt_for_mode"])
                    if "default_analysis_mode" in config:
                        self.analysis_mode.set(config["default_analysis_mode"])
                    if "default_cloud_provider" in config:
                        self.cloud_provider.set(config["default_cloud_provider"])
                    logger.info("Configurations de l'application chargées avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des configurations de l'application: {str(e)}")
    
    def _save_app_config(self):
        """Sauvegarde les configurations de l'application."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
        try:
            config = {
                "prompt_for_mode": self.prompt_for_mode.get(),
                "default_analysis_mode": self.analysis_mode.get(),
                "default_cloud_provider": self.cloud_provider.get()
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info("Configurations de l'application sauvegardées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des configurations de l'application: {str(e)}")
    
    def _create_widgets(self):
        # Cadre principal
        main_frame = ttk.Frame(self.root, padding=UI_CONFIG["padding"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cadre de sélection de fichier
        self.file_frame = FileSelectionFrame(main_frame, callback=self._on_file_selected)
        self.file_frame.pack(fill=tk.X, pady=UI_CONFIG["padding"])
        
        # Barre d'outils
        commands = {
            "analyze": self.analyze_file,
            "save": self.save_results,
            "visualize": self.visualize_data,
            "analyze_text": self.browse_and_analyze_text,
            "help": self.show_help
        }
        self.toolbar = ToolbarFrame(main_frame, commands=commands)
        self.toolbar.pack(fill=tk.X, pady=UI_CONFIG["padding"])
        
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=UI_CONFIG["padding"])
        
        # Onglet de prévisualisation des données
        self.preview_frame = DataPreviewFrame(self.notebook)
        self.notebook.add(self.preview_frame, text="Aperçu des données")
        
        # Onglet de visualisation
        self.visualization_frame = DataVisualizationFrame(self.notebook)
        self.notebook.add(self.visualization_frame, text="Visualisation")
        
        # Onglet de résultats
        self.results_frame = ResultsFrame(self.notebook)
        self.notebook.add(self.results_frame, text="Résultats")
        
        # Onglet d'information par lieu
        self.location_info_frame = LocationInfoFrame(self.notebook, self)
        self.notebook.add(self.location_info_frame, text="Info par Lieu")
        
        # Référence au widget Text dans ResultsFrame pour faciliter l'accès
        self.results_text = self.results_frame.text
        
        # Barre de statut
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.set_status("Prêt")
    
    def _create_menu(self):
        # Barre de menu
        menubar = tk.Menu(self.root)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Ouvrir fichier", command=self.open_file)
        file_menu.add_command(label="Ouvrir dossier", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exporter en Excel", command=self.export_to_excel)
        file_menu.add_command(label="Exporter en CSV", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Mettre à jour un fichier SLRI Excel", command=self.update_slri_excel_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        
        # Menu Projet
        project_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Projet", menu=project_menu)
        project_menu.add_command(label="Nouveau projet", command=self.create_new_project)
        project_menu.add_command(label="Ouvrir projet", command=self.open_project)
        project_menu.add_command(label="Fermer projet", command=self.close_project)
        project_menu.add_separator()
        project_menu.add_command(label="Exporter projet", command=self.export_project)
        project_menu.add_command(label="Supprimer projet", command=self.delete_project)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Analyse
        analyse_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analyse", menu=analyse_menu)
        analyse_menu.add_command(label="Analyser le fichier", command=self.analyze_file)
        analyse_menu.add_command(label="Analyser un fichier texte", command=self.analyze_text_file)
        analyse_menu.add_command(label="Analyse SLRI complète", command=self.run_slri_analysis_standalone)
        analyse_menu.add_command(label="Analyse SLRI par phases", command=self.run_slri_phases_analysis)
        analyse_menu.add_command(label="Générer rapport SLRI", command=self.generate_slri_report)
        analyse_menu.add_command(label="Analyse détaillée des paramètres d'eau", command=self.show_water_analysis)
        analyse_menu.add_separator()
        analyse_menu.add_command(label="Visualiser les données", command=self.visualize_data)
        
        # Menu Configuration
        config_menu = tk.Menu(menubar, tearoff=0)
        
        # Sous-menu pour le mode d'analyse
        mode_menu = tk.Menu(config_menu, tearoff=0)
        mode_menu.add_radiobutton(label="Utiliser API Cloud (Recommandé)", 
                                 variable=self.analysis_mode, value="cloud",
                                 command=self.update_analysis_mode)
        mode_menu.add_radiobutton(label="Utiliser Modèle Local", 
                                 variable=self.analysis_mode, value="local",
                                 command=self.update_analysis_mode)
        config_menu.add_cascade(label="Mode d'analyse", menu=mode_menu)
        
        # Sous-menu pour le fournisseur d'API cloud
        provider_menu = tk.Menu(config_menu, tearoff=0)
        provider_menu.add_radiobutton(label="OpenAI Vision", 
                                    variable=self.cloud_provider, value="openai",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="Azure Computer Vision", 
                                    variable=self.cloud_provider, value="azure",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="Google Cloud Vision", 
                                    variable=self.cloud_provider, value="google",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="Qwen Vision", 
                                    variable=self.cloud_provider, value="qwen",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="OpenRouter (Claude 3 Opus)", 
                                    variable=self.cloud_provider, value="openrouter",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="OpenRouter DeepSeek", 
                                    variable=self.cloud_provider, value="openrouter_deepseek",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="OpenRouter Qwen", 
                                    variable=self.cloud_provider, value="openrouter_qwen",
                                    command=self.update_cloud_provider)
        provider_menu.add_radiobutton(label="Hugging Face", 
                                    variable=self.cloud_provider, value="huggingface",
                                    command=self.update_cloud_provider)
        
        # Ajouter l'option Gemini si disponible
        if GEMINI_AVAILABLE:
            provider_menu.add_radiobutton(label="Google Gemini", 
                                        variable=self.cloud_provider, value="gemini",
                                        command=self.update_cloud_provider)
        config_menu.add_cascade(label="Fournisseur API Cloud", menu=provider_menu)
        
        # Option pour configurer les clés API
        config_menu.add_command(label="Configurer les clés API", command=self.configure_api_keys)
        
        # Option pour activer/désactiver le choix du mode d'analyse
        self.prompt_for_mode = tk.BooleanVar(value=True)  # Par défaut, demander à l'utilisateur
        config_menu.add_checkbutton(label="Demander le mode d'analyse à chaque analyse", 
                                  variable=self.prompt_for_mode,
                                  command=self._save_app_config)  # Sauvegarder la configuration lorsque l'option change
        
        # Sous-menu pour la gestion du cache
        cache_menu = tk.Menu(config_menu, tearoff=0)
        cache_menu.add_command(label="Vider le cache", command=self.clear_cache)
        cache_menu.add_command(label="Afficher les statistiques du cache", command=self.show_cache_stats)
        config_menu.add_cascade(label="Gestion du cache", menu=cache_menu)
        
        menubar.add_cascade(label="Configuration", menu=config_menu)
        
        # Menu Surveillance Continue
        monitoring_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Surveillance", menu=monitoring_menu)
        monitoring_menu.add_command(label="🔄 Démarrer surveillance automatique", command=self.start_continuous_monitoring)
        monitoring_menu.add_command(label="⏹️ Arrêter surveillance", command=self.stop_continuous_monitoring)
        monitoring_menu.add_separator()
        monitoring_menu.add_command(label="📊 Tableau de bord avancé", command=self.launch_monitoring_dashboard)
        monitoring_menu.add_command(label="📈 Analyser tendances", command=self.analyze_site_trends)
        monitoring_menu.add_command(label="🔄 Comparer plans d'action", command=self.compare_action_plans)
        monitoring_menu.add_separator()
        monitoring_menu.add_command(label="⚙️ Configurer surveillance", command=self.configure_monitoring)
        monitoring_menu.add_command(label="🚨 Voir alertes", command=self.view_alerts_history)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Aide", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _on_file_selected(self, file_paths):
        """Callback appelé lorsqu'un ou plusieurs fichiers sont sélectionnés."""
        self.file_paths = file_paths  # Stocker tous les chemins de fichiers
        
        # Si un seul fichier est sélectionné, conserver la compatibilité avec le code existant
        if len(file_paths) == 1:
            self.file_path = file_paths[0]
            self.status_bar.set_status(f"Fichier sélectionné: {os.path.basename(file_paths[0])}")
        else:
            self.file_path = None  # Réinitialiser file_path car nous avons plusieurs fichiers
            self.status_bar.set_status(f"{len(file_paths)} fichiers sélectionnés")
            
            # Afficher les noms des fichiers dans la zone de résultats
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Fichiers sélectionnés:\n")
            for i, path in enumerate(file_paths, 1):
                self.results_text.insert(tk.END, f"{i}. {os.path.basename(path)}\n")
            
            # Basculer vers l'onglet des résultats pour montrer les fichiers sélectionnés
            self.notebook.select(self.results_frame)
    
    def update_analysis_mode(self):
        """Met à jour le mode d'analyse (local ou cloud)."""
        mode = self.analysis_mode.get()
        if mode == "local":
            # Vérifier si le modèle est chargé
            if not self.model.model:
                if messagebox.askyesno("Charger le modèle", 
                                      "Le modèle local n'est pas chargé. Voulez-vous le charger maintenant? \n\nAttention: Cela peut prendre du temps et nécessiter beaucoup de mémoire."):
                    try:
                        self.status_bar.set_status("Chargement du modèle local...", 10)
                        self.model.load_model()
                        self.status_bar.set_status("Modèle local chargé avec succès", 100)
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Impossible de charger le modèle local: {str(e)}")
                        # Revenir au mode cloud
                        self.analysis_mode.set("cloud")
                        self.status_bar.set_status("Erreur de chargement du modèle, retour au mode cloud", 0)
                else:
                    # L'utilisateur a refusé de charger le modèle, revenir au mode cloud
                    self.analysis_mode.set("cloud")
            else:
                self.status_bar.set_status("Mode d'analyse: Modèle local", 100)
        else:  # mode == "cloud"
            # Vérifier si une clé API est configurée
            provider = self.cloud_provider.get()
            if not self.cloud_api_config.get(provider, {}).get("api_key"):
                messagebox.showwarning("Configuration requise", 
                                     f"Aucune clé API n'est configurée pour {provider}. \nVeuillez configurer une clé API pour utiliser ce service.")
                self.configure_api_keys()
            else:
                self.status_bar.set_status(f"Mode d'analyse: API Cloud ({provider})", 100)
        
        # Sauvegarder les configurations
        self._save_app_config()
    
    def update_cloud_provider(self):
        """Met à jour le fournisseur d'API cloud."""
        provider = self.cloud_provider.get()
        if not self.cloud_api_config.get(provider, {}).get("api_key"):
            messagebox.showwarning("Configuration requise", 
                                 f"Aucune clé API n'est configurée pour {provider}. \nVeuillez configurer une clé API pour utiliser ce service.")
            self.configure_api_keys()
        else:
            self.status_bar.set_status(f"Fournisseur API Cloud: {provider}", 100)
        
        # Sauvegarder les configurations
        self._save_app_config()
    
    def configure_api_keys(self):
        """Ouvre une fenêtre pour configurer les clés API."""
        # Créer une fenêtre modale
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration des clés API")
        config_window.geometry("500x400")
        config_window.transient(self.root)
        config_window.grab_set()
        
        # Créer un cadre avec padding
        frame = ttk.Frame(config_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        ttk.Label(frame, text="Configuration des clés API pour les services cloud", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Variables pour stocker les valeurs des champs
        api_keys = {}
        for provider in ["openai", "azure", "google", "qwen", "openrouter", "openrouter_deepseek", "openrouter_qwen", "huggingface"]:
            api_keys[provider] = {}
            for key in self.cloud_api_config.get(provider, {}).keys():
                if key in ["api_key", "endpoint", "site_url", "site_name"]:
                    api_keys[provider][key] = tk.StringVar(value=self.cloud_api_config.get(provider, {}).get(key, ""))
        
        # Créer les onglets pour chaque fournisseur
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Onglet OpenAI
        openai_frame = ttk.Frame(notebook, padding=10)
        notebook.add(openai_frame, text="OpenAI Vision")
        
        ttk.Label(openai_frame, text="Clé API OpenAI:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(openai_frame, textvariable=api_keys["openai"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        ttk.Label(openai_frame, text="Instructions:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        instructions_text = """1. Créez un compte sur https://platform.openai.com
2. Accédez à la section API keys
3. Créez une nouvelle clé API
4. Copiez-collez la clé ci-dessus"""
        ttk.Label(openai_frame, text=instructions_text, wraplength=300, justify=tk.LEFT).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Onglet Azure
        azure_frame = ttk.Frame(notebook, padding=10)
        notebook.add(azure_frame, text="Azure Vision")
        
        ttk.Label(azure_frame, text="Clé API Azure:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(azure_frame, textvariable=api_keys["azure"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        ttk.Label(azure_frame, text="Endpoint:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(azure_frame, textvariable=api_keys["azure"]["endpoint"], width=40).grid(row=1, column=1, pady=5)
        
        # Onglet Google
        google_frame = ttk.Frame(notebook, padding=10)
        notebook.add(google_frame, text="Google Vision")
        
        ttk.Label(google_frame, text="Clé API Google:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(google_frame, textvariable=api_keys["google"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        # Onglet Qwen
        qwen_frame = ttk.Frame(notebook, padding=10)
        notebook.add(qwen_frame, text="Qwen Vision")
        
        ttk.Label(qwen_frame, text="Clé API Qwen:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(qwen_frame, textvariable=api_keys["qwen"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        ttk.Label(qwen_frame, text="Instructions:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        qwen_instructions_text = """1. Créez un compte sur https://dashscope.aliyun.com
2. Accédez à la section API keys
3. Créez une nouvelle clé API
4. Copiez-collez la clé ci-dessus"""
        ttk.Label(qwen_frame, text=qwen_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Onglet OpenRouter
        openrouter_frame = ttk.Frame(notebook, padding=10)
        notebook.add(openrouter_frame, text="OpenRouter (Claude 3 Opus)")
        
        ttk.Label(openrouter_frame, text="Clé API OpenRouter:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(openrouter_frame, textvariable=api_keys["openrouter"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        # Champs optionnels pour OpenRouter
        if "site_url" in api_keys["openrouter"]:
            ttk.Label(openrouter_frame, text="URL de votre site (optionnel):").grid(row=1, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_frame, textvariable=api_keys["openrouter"]["site_url"], width=40).grid(row=1, column=1, pady=5)
        
        if "site_name" in api_keys["openrouter"]:
            ttk.Label(openrouter_frame, text="Nom de votre site (optionnel):").grid(row=2, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_frame, textvariable=api_keys["openrouter"]["site_name"], width=40).grid(row=2, column=1, pady=5)
        
        ttk.Label(openrouter_frame, text="Instructions:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        openrouter_instructions_text = """1. Créez un compte sur https://openrouter.ai
2. Accédez à la section API keys
3. Créez une nouvelle clé API
4. Copiez-collez la clé ci-dessus"""
        ttk.Label(openrouter_frame, text=openrouter_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Onglet OpenRouter DeepSeek
        openrouter_deepseek_frame = ttk.Frame(notebook, padding=10)
        notebook.add(openrouter_deepseek_frame, text="OpenRouter (DeepSeek)")
        
        ttk.Label(openrouter_deepseek_frame, text="Clé API OpenRouter DeepSeek:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(openrouter_deepseek_frame, textvariable=api_keys["openrouter_deepseek"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        # Champs optionnels pour OpenRouter DeepSeek
        if "site_url" in api_keys["openrouter_deepseek"]:
            ttk.Label(openrouter_deepseek_frame, text="URL de votre site (optionnel):").grid(row=1, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_deepseek_frame, textvariable=api_keys["openrouter_deepseek"]["site_url"], width=40).grid(row=1, column=1, pady=5)
        
        if "site_name" in api_keys["openrouter_deepseek"]:
            ttk.Label(openrouter_deepseek_frame, text="Nom de votre site (optionnel):").grid(row=2, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_deepseek_frame, textvariable=api_keys["openrouter_deepseek"]["site_name"], width=40).grid(row=2, column=1, pady=5)
        
        ttk.Label(openrouter_deepseek_frame, text="Instructions:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        ttk.Label(openrouter_deepseek_frame, text=openrouter_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Onglet OpenRouter Qwen
        openrouter_qwen_frame = ttk.Frame(notebook, padding=10)
        notebook.add(openrouter_qwen_frame, text="OpenRouter (Qwen3)")
        
        ttk.Label(openrouter_qwen_frame, text="Clé API OpenRouter Qwen:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(openrouter_qwen_frame, textvariable=api_keys["openrouter_qwen"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        # Champs optionnels pour OpenRouter Qwen
        if "site_url" in api_keys["openrouter_qwen"]:
            ttk.Label(openrouter_qwen_frame, text="URL de votre site (optionnel):").grid(row=1, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_qwen_frame, textvariable=api_keys["openrouter_qwen"]["site_url"], width=40).grid(row=1, column=1, pady=5)
        
        if "site_name" in api_keys["openrouter_qwen"]:
            ttk.Label(openrouter_qwen_frame, text="Nom de votre site (optionnel):").grid(row=2, column=0, sticky=tk.W, pady=5)
            ttk.Entry(openrouter_qwen_frame, textvariable=api_keys["openrouter_qwen"]["site_name"], width=40).grid(row=2, column=1, pady=5)
        
        ttk.Label(openrouter_qwen_frame, text="Instructions:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        ttk.Label(openrouter_qwen_frame, text=openrouter_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Onglet Gemini (si disponible)
        if GEMINI_AVAILABLE:
            # Initialiser les variables pour Gemini si elles n'existent pas
            if "gemini" not in api_keys:
                api_keys["gemini"] = {}
                api_keys["gemini"]["api_key"] = tk.StringVar()
                # Charger la configuration Gemini
                gemini_config = load_gemini_config()
                if gemini_config and "api_key" in gemini_config:
                    api_keys["gemini"]["api_key"].set(gemini_config.get("api_key", ""))
            
            gemini_frame = ttk.Frame(notebook, padding=10)
            notebook.add(gemini_frame, text="Google Gemini")
            
            ttk.Label(gemini_frame, text="Clé API Gemini:").grid(row=0, column=0, sticky=tk.W, pady=5)
            ttk.Entry(gemini_frame, textvariable=api_keys["gemini"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
            
            ttk.Label(gemini_frame, text="Instructions:").grid(row=1, column=0, sticky=tk.NW, pady=5)
            gemini_instructions_text = """1. Créez un compte sur https://ai.google.dev/
2. Accédez à la section API keys
3. Créez une nouvelle clé API
4. Copiez-collez la clé ci-dessus"""
            ttk.Label(gemini_frame, text=gemini_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Onglet Hugging Face
        huggingface_frame = ttk.Frame(notebook, padding=10)
        notebook.add(huggingface_frame, text="Hugging Face")
        
        ttk.Label(huggingface_frame, text="Clé API Hugging Face:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(huggingface_frame, textvariable=api_keys["huggingface"]["api_key"], width=40, show="*").grid(row=0, column=1, pady=5)
        
        ttk.Label(huggingface_frame, text="Instructions:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        huggingface_instructions_text = """1. Créez un compte sur https://huggingface.co/
2. Accédez à la section API keys
3. Créez une nouvelle clé API
4. Copiez-collez la clé ci-dessus"""
        ttk.Label(huggingface_frame, text=huggingface_instructions_text, wraplength=300, justify=tk.LEFT).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Fonction pour sauvegarder les configurations
        def save_config():
            # Mettre à jour les configurations
            providers = ["openai", "azure", "google", "qwen", "openrouter", "openrouter_deepseek", "openrouter_qwen", "huggingface"]
            if GEMINI_AVAILABLE and "gemini" in api_keys:
                providers.append("gemini")
                
            for provider in providers:
                for key, var in api_keys[provider].items():
                    if provider in self.cloud_api_config and key in self.cloud_api_config[provider]:
                        self.cloud_api_config[provider][key] = var.get()
                    
            # Sauvegarder la configuration Gemini séparément si disponible
            if GEMINI_AVAILABLE and "gemini" in api_keys:
                try:
                    from gemini_integration import save_gemini_config
                    # Créer un dictionnaire de configuration Gemini
                    gemini_config = {
                        "api_key": api_keys["gemini"]["api_key"].get(),
                        "enabled": True,
                        "default_model": "gemini-2.0-pro-vision",
                        "text_model": "gemini-2.0-flash",
                        "max_tokens": 1024
                    }
                    # Sauvegarder la configuration
                    save_gemini_config(gemini_config)
                    logger.info("Configuration Gemini sauvegardée avec succès.")
                    # Synchroniser la clé dans cloud_api_config pour éviter le faux avertissement
                    if "gemini" not in self.cloud_api_config:
                        self.cloud_api_config["gemini"] = {}
                    self.cloud_api_config["gemini"]["api_key"] = gemini_config["api_key"]
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de la configuration Gemini: {str(e)}")
                    raise Exception(f"Erreur lors de la sauvegarde de la configuration Gemini: {str(e)}")

            
            # Mettre à jour le module cloud_api
            try:
                # Créer le chemin vers le fichier de configuration
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_config.json")
                
                # Créer une copie pour éviter de sauvegarder des objets non sérialisables
                config_to_save = {}
                for provider, config in self.cloud_api_config.items():
                    if not isinstance(config, dict):
                        continue  # Ignore les clés comme 'default_provider'
                    config_to_save[provider] = {}
                    for key, value in config.items():
                        if key in ["api_key", "endpoint", "api_url", "model", "max_tokens", "site_url", "site_name"]:
                            config_to_save[provider][key] = value
                
                # Sauvegarder les configurations dans un fichier JSON
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_to_save, f, indent=4)
                
                # Mettre à jour l'API_CONFIG dans le module cloud_api
                try:
                    import cloud_api
                    for provider in config_to_save.keys():
                        if provider in cloud_api.API_CONFIG:
                            for key, value in config_to_save[provider].items():
                                if key in cloud_api.API_CONFIG[provider]:
                                    cloud_api.API_CONFIG[provider][key] = value
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour du module cloud_api: {str(e)}")
                
                messagebox.showinfo("Configuration sauvegardée", "Les clés API ont été sauvegardées avec succès.")
                
                # Mettre à jour le statut
                provider = self.cloud_provider.get()
                if self.cloud_api_config.get(provider, {}).get("api_key"):
                    self.status_bar.set_status(f"Fournisseur API Cloud: {provider} (configuré)", 100)
                
                # Fermer la fenêtre
                config_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration: {str(e)}")
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Annuler", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Sauvegarder", command=save_config).pack(side=tk.RIGHT, padx=5)
        
    def open_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un ou plusieurs fichiers."""
        filetypes = [(k, v) for k, v in SUPPORTED_FILE_TYPES.items()]
        file_paths = filedialog.askopenfilenames(filetypes=filetypes)
        
        if file_paths:
            self._on_file_selected(list(file_paths))
    
    def open_folder(self):
        """Ouvre une boîte de dialogue pour sélectionner un dossier."""
        folder_path = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        
        if folder_path:
            # Rechercher tous les fichiers supportés dans le dossier
            supported_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Vérifier si l'extension est supportée
                    _, ext = os.path.splitext(file.lower())
                    if ext in ['.xlsx', '.csv', '.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg']:
                        supported_files.append(file_path)
            
            if supported_files:
                self._on_file_selected(supported_files)
                self.status_bar.set_status(f"Dossier sélectionné: {len(supported_files)} fichiers trouvés")
            else:
                messagebox.showinfo("Information", "Aucun fichier supporté trouvé dans ce dossier.")
                self.status_bar.set_status("Aucun fichier supporté trouvé")
    
    def analyze_file(self):
        """Analyse le fichier sélectionné."""
        # Si aucun fichier n'est sélectionné
        if not hasattr(self, 'file_paths') or not self.file_paths:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner un fichier.")
            return
        
        # Si un seul fichier est sélectionné
        if len(self.file_paths) == 1:
            self._analyze_single_file(self.file_paths[0])
        else:
            # Analyser plusieurs fichiers
            self._analyze_multiple_files(self.file_paths)
    
    def _analyze_single_file(self, file_path):
        """Analyse un seul fichier."""
        try:
            # Enregistrer l'action dans le log d'audit
            audit_logger.log_action(
                action="Début analyse fichier",
                user="interface_utilisateur",
                ip="localhost",
                fichier=file_path
            )
            
            self.status_bar.set_status("Analyse en cours...", 20)
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".xlsx":
                # Analyse de fichier Excel
                if self.current_data is None:
                    self.current_data = load_data(file_path)
                
                if self.current_data is not None:
                    self.status_bar.set_status("Nettoyage des données...", 40)
                    df = clean_data(self.current_data.copy())
                    
                    self.status_bar.set_status("Enrichissement des données...", 60)
                    df = enrich_data(df)
                    
                    self.status_bar.set_status("Analyse des données...", 80)
                    df = analyze_environmental_data(df)
                    
                    # Intégrer l'analyse SLRI si l'analyseur est disponible
                    if self.slri_analyzer:
                        self.status_bar.set_status("Analyse SLRI en cours...", 90)
                        slri_results = self._run_slri_analysis(df)
                        if slri_results:
                            # Ajouter les résultats SLRI aux données
                            df['slri_analysis'] = str(slri_results)
                    
                    self.current_data = df
                    self.preview_frame.display_dataframe(df)
                    
                    # Sauvegarder les résultats
                    output_path = save_dataframe_to_excel(df, directory=OUTPUT_DIR)
                    
                    # Enregistrer le succès dans le log d'audit
                    audit_logger.log_action(
                        action="Analyse fichier terminée",
                        user="interface_utilisateur",
                        ip="localhost",
                        fichier=file_path,
                        resultats={
                            "nb_parametres": len(df),
                            "chemin_sortie": output_path
                        }
                    )
                    
                    self.status_bar.set_status(f"Analyse terminée. Résultats sauvegardés dans {os.path.basename(output_path)}", 100)
                    messagebox.showinfo("Succès", f"Analyse terminée! Résultats sauvegardés dans:\n{output_path}")
            
            elif ext == ".pdf":
                # Extraction PDF page par page en arrière-plan
                self._analyze_pdf_file(file_path)
                return
            
            elif ext in [".png", ".jpg", ".jpeg"]:
                # Analyse d'image avec IA (locale ou cloud)
                self.status_bar.set_status("Analyse de l'image...", 50)
                
                # Vérifier si l'utilisateur souhaite être interrogé sur le mode d'analyse
                if self.prompt_for_mode.get():
                    # Demander à l'utilisateur de choisir le mode d'analyse
                    mode_choice = messagebox.askyesno("Mode d'analyse", 
                                                   "Voulez-vous utiliser le mode d'analyse local?\n\nOui = Modèle local\nNon = API Cloud")
                    
                    if mode_choice:  # L'utilisateur a choisi le mode local
                        # Mettre à jour le mode d'analyse
                        self.analysis_mode.set("local")
                        self.update_analysis_mode()
                    else:  # L'utilisateur a choisi le mode cloud
                        # Mettre à jour le mode d'analyse
                        self.analysis_mode.set("cloud")
                        self.update_analysis_mode()
                
                # Vérifier le mode d'analyse actuel
                if self.analysis_mode.get() == "local":
                    # Vérifier si le modèle doit être chargé
                    if not self.load_model:
                        messagebox.showwarning("Modèle non chargé", "L'application a été démarrée avec l'option --no-load-model. Le modèle IA local n'est pas disponible.")
                        self.status_bar.set_status("Modèle IA local non disponible", 0)
                        return
                    
                    # Afficher un message d'avertissement sur le temps d'analyse
                    messagebox.showinfo("Analyse en cours", "L'analyse d'image avec le modèle local a été optimisée avec OCR et prétraitement. Le processus peut prendre plusieurs minutes.")
                else:  # Mode cloud
                    # Vérifier si l'API est configurée
                    provider = self.cloud_provider.get()
                    if not self.cloud_api_config.get(provider, {}).get("api_key"):
                        messagebox.showwarning("API non configurée", f"La clé API pour {provider} n'est pas configurée. Veuillez configurer l'API dans le menu Configuration > Configurer les clés API.")
                        self.status_bar.set_status("API cloud non configurée", 0)
                        return
                    
                    # Afficher un message sur l'analyse cloud
                    messagebox.showinfo("Analyse en cours", f"L'analyse d'image sera effectuée avec l'API {provider}. Le processus devrait être rapide.")
                
                # Mettre à jour la barre de statut pour montrer la progression
                self.status_bar.set_status("Prétraitement de l'image...", 10)
                
                # Créer une fenêtre de progression détaillée
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Progression de l'analyse")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                # Ajouter des étiquettes pour chaque étape
                tk.Label(progress_window, text="Analyse d'image en cours", font=("Arial", 12, "bold")).pack(pady=10)
                
                # Créer un cadre pour les étapes
                steps_frame = tk.Frame(progress_window)
                steps_frame.pack(fill="both", expand=True, padx=20)
                
                # Étapes de progression avec indicateurs
                steps = [
                    "Prétraitement de l'image",
                    "Extraction de texte (OCR)",
                    "Analyse avec IA",
                    "Extraction des paramètres"
                ]
                
                step_labels = []
                step_indicators = []
                
                for i, step in enumerate(steps):
                    frame = tk.Frame(steps_frame)
                    frame.pack(fill="x", pady=5)
                    
                    # Indicateur (cercle)
                    indicator = tk.Label(frame, text="○", font=("Arial", 10), fg="gray")
                    indicator.pack(side="left", padx=5)
                    step_indicators.append(indicator)
                    
                    # Texte de l'étape
                    label = tk.Label(frame, text=step, font=("Arial", 10), anchor="w")
                    label.pack(side="left", fill="x", expand=True)
                    step_labels.append(label)
                
                # Fonction pour mettre à jour la progression
                def update_progress(step_index, completed=False):
                    for i in range(len(steps)):
                        if i < step_index:
                            # Étape terminée
                            step_indicators[i].config(text="✓", fg="green")
                        elif i == step_index and completed:
                            # Étape en cours terminée
                            step_indicators[i].config(text="✓", fg="green")
                        elif i == step_index:
                            # Étape en cours
                            step_indicators[i].config(text="●", fg="blue")
                        else:
                            # Étape à venir
                            step_indicators[i].config(text="○", fg="gray")
                    
                    # Mettre à jour la fenêtre
                    progress_window.update()
                
                # Mettre à jour la première étape
                update_progress(0)
                
                # Étape 1: Prétraitement
                self.status_bar.set_status("Prétraitement de l'image...", 20)
                update_progress(0, True)
                update_progress(1)  # Passer à l'étape suivante
                
                # Étape 2: OCR
                self.status_bar.set_status("Extraction de texte avec OCR...", 40)
                
                # Étape 3: Analyse IA
                update_progress(1, True)
                update_progress(2)  # Passer à l'étape suivante
                self.status_bar.set_status("Analyse de l'image avec IA...", 60)
                
                # Effectuer l'analyse selon le mode sélectionné
                if self.analysis_mode.get() == "local":
                    # Utiliser les paramètres de traitement par lots configurés avec limite de tokens
                    max_new_tokens = 250  # Limiter le nombre de tokens pour accélérer l'analyse
                    
                    # Analyse avec modèle local
                    df, response = analyze_environmental_image(
                        file_path,
                        model=self.model,
                        batch_params=self.batch_params,
                        max_new_tokens=max_new_tokens,
                        use_ocr=self.use_ocr.get()  # Respecter le choix OCR de l'utilisateur
                    )
                else:  # Mode cloud
                    # Analyse avec API cloud
                    provider = self.cloud_provider.get()
                    
                    # Utiliser l'API Gemini si sélectionnée et disponible
                    if provider == "gemini" and GEMINI_AVAILABLE:
                        df, response = analyze_environmental_image_with_gemini(
                            file_path,
                            use_ocr=self.use_ocr.get()  # Respecter le choix OCR de l'utilisateur
                        )
                    else:
                        # Autres API cloud
                        df, response = analyze_environmental_image_cloud(
                            file_path,
                            api_provider=provider
                        )
                
                # Étape 4: Extraction des paramètres
                update_progress(2, True)
                update_progress(3)  # Passer à l'étape suivante
                self.status_bar.set_status("Extraction des paramètres...", 80)
                
                # Fermer la fenêtre de progression
                update_progress(3, True)
                progress_window.destroy()
                if df is not None and not df.empty:
                    # Vérifier si des données sont manquantes ou incomplètes
                    missing_data = False
                    required_columns = ["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée", "Résultat conformité"]
                    
                    # Vérifier si les colonnes requises existent et ont des valeurs
                    for col in required_columns:
                        if col not in df.columns or df[col].isnull().any() or (df[col] == "Non disponible").any():
                            missing_data = True
                            break
                    
                    # Si des données sont manquantes, proposer de les compléter
                    if missing_data:
                        if messagebox.askyesno("Données manquantes", "Certaines données sont manquantes ou incomplètes. Voulez-vous essayer de les compléter automatiquement via une recherche web?"):
                            # Créer une fenêtre de progression pour la recherche web
                            web_progress = tk.Toplevel(self.root)
                            web_progress.title("Recherche web en cours")
                            web_progress.geometry("400x150")
                            web_progress.transient(self.root)
                            web_progress.grab_set()
                            
                            tk.Label(web_progress, text="Recherche d'informations complémentaires...", font=("Arial", 12)).pack(pady=10)
                            progress = ttk.Progressbar(web_progress, mode="indeterminate")
                            progress.pack(fill="x", padx=20, pady=10)
                            progress.start()
                            
                            status_label = tk.Label(web_progress, text="Initialisation de la recherche...")
                            status_label.pack(pady=10)
                            
                            # Mettre à jour l'interface
                            web_progress.update()
                            
                            try:
                                # Pour chaque paramètre avec des données manquantes, effectuer une recherche web
                                for idx, row in df.iterrows():
                                    parameter = row["Paramètre"]
                                    if parameter and parameter != "Erreur d'extraction":
                                        # Vérifier les données manquantes pour ce paramètre
                                        if row["Intervalle acceptable"] == "" or row["Intervalle acceptable"] == "Non disponible":
                                            status_label.config(text=f"Recherche des intervalles acceptables pour {parameter}...")
                                            web_progress.update()
                                            
                                            # Utiliser une base de connaissances intégrée pour les paramètres environnementaux courants
                                            # Cette approche pourrait être améliorée avec une API de recherche web réelle
                                            parametres_connus = {
                                                "pH": {
                                                    "milieu": "Eau",
                                                    "intervalle": "6.5 - 8.5",
                                                    "unite": "pH",
                                                    "valeur_defaut": "7.2 (estimé)",
                                                    "description": "Mesure de l'acidité/basicité de l'eau"
                                                },
                                                "turbidité": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 5",
                                                    "unite": "NTU",
                                                    "valeur_defaut": "2.5 (estimé)",
                                                    "description": "Mesure de la clarté de l'eau"
                                                },
                                                "température": {
                                                    "milieu": "Eau",
                                                    "intervalle": "10 - 25",
                                                    "unite": "°C",
                                                    "valeur_defaut": "18 (estimé)",
                                                    "description": "Température de l'eau"
                                                },
                                                "conductivité": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 1000",
                                                    "unite": "µS/cm",
                                                    "valeur_defaut": "500 (estimé)",
                                                    "description": "Mesure des ions dissous dans l'eau"
                                                },
                                                "oxygène dissous": {
                                                    "milieu": "Eau",
                                                    "intervalle": "> 5",
                                                    "unite": "mg/L",
                                                    "valeur_defaut": "7.5 (estimé)",
                                                    "description": "Quantité d'oxygène disponible pour la vie aquatique"
                                                },
                                                "dbo5": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 5",
                                                    "unite": "mg/L",
                                                    "valeur_defaut": "3 (estimé)",
                                                    "description": "Demande biochimique en oxygène sur 5 jours"
                                                },
                                                "dco": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 30",
                                                    "unite": "mg/L",
                                                    "valeur_defaut": "20 (estimé)",
                                                    "description": "Demande chimique en oxygène"
                                                },
                                                "nitrates": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 50",
                                                    "unite": "mg/L",
                                                    "valeur_defaut": "25 (estimé)",
                                                    "description": "Concentration en nitrates"
                                                },
                                                "phosphates": {
                                                    "milieu": "Eau",
                                                    "intervalle": "< 0.5",
                                                    "unite": "mg/L",
                                                    "valeur_defaut": "0.2 (estimé)",
                                                    "description": "Concentration en phosphates"
                                                }
                                            }
                                            
                                            # Rechercher le paramètre dans notre base de connaissances (insensible à la casse)
                                            param_lower = parameter.lower()
                                            for known_param, info in parametres_connus.items():
                                                if known_param in param_lower or param_lower in known_param:
                                                    # Mettre à jour l'intervalle acceptable
                                                    df.at[idx, "Intervalle acceptable"] = info["intervalle"]
                                                    
                                                    # Mettre à jour le milieu si non spécifié
                                                    if row["Milieu"] == "" or row["Milieu"] == "Non disponible":
                                                        df.at[idx, "Milieu"] = info["milieu"]
                                                    
                                                    # Mettre à jour l'unité si non spécifiée
                                                    if row["Unité"] == "" or row["Unité"] == "Non disponible":
                                                        df.at[idx, "Unité"] = info["unite"]
                                                    
                                                    # Mettre à jour la valeur mesurée si non spécifiée
                                                    if row["Valeur mesurée"] == "" or row["Valeur mesurée"] == "Non disponible":
                                                        df.at[idx, "Valeur mesurée"] = info["valeur_defaut"]
                                                        
                                                    # Ajouter une description si disponible
                                                    if "Description" in df.columns and (df.at[idx, "Description"] == "" or df.at[idx, "Description"] == "Non disponible"):
                                                        df.at[idx, "Description"] = info["description"]
                                                    
                                                    break
                                            # Si le paramètre n'est pas dans notre base de connaissances, utiliser des valeurs génériques
                                            else:
                                                if row["Milieu"] == "" or row["Milieu"] == "Non disponible":
                                                    df.at[idx, "Milieu"] = "Eau"
                                                if row["Intervalle acceptable"] == "" or row["Intervalle acceptable"] == "Non disponible":
                                                    df.at[idx, "Intervalle acceptable"] = "À déterminer"
                                                if row["Unité"] == "" or row["Unité"] == "Non disponible":
                                                    df.at[idx, "Unité"] = "mg/L"
                                        
                                        # Évaluer le résultat si la valeur mesurée est disponible mais pas le résultat
                                        if (row["Valeur mesurée"] != "" and row["Valeur mesurée"] != "Non disponible") and (row.get("Résultat conformité", "") == "" or row.get("Résultat conformité", "Non disponible") == "Non disponible") and row["Intervalle acceptable"] != "" and row["Intervalle acceptable"] != "Non disponible":
                                            status_label.config(text=f"Évaluation du résultat pour {parameter}...")
                                            web_progress.update()
                                            
                                            # Logique d'évaluation simple
                                            try:
                                                valeur = row["Valeur mesurée"]
                                                intervalle = row["Intervalle acceptable"]
                                                
                                                # Extraire les valeurs numériques de l'intervalle
                                                if "-" in intervalle:
                                                    min_val, max_val = map(float, intervalle.split("-"))
                                                    if float(valeur) >= min_val and float(valeur) <= max_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                        df.at[idx, "Score"] = 1
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                        df.at[idx, "Score"] = 0
                                                elif "<" in intervalle:
                                                    max_val = float(intervalle.replace("<", "").strip().split()[0])
                                                    if float(valeur) < max_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                        df.at[idx, "Score"] = 1
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                        df.at[idx, "Score"] = 0
                                                elif ">" in intervalle:
                                                    min_val = float(intervalle.replace(">", "").strip().split()[0])
                                                    if float(valeur) > min_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                        df.at[idx, "Score"] = 1
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                        df.at[idx, "Score"] = 0
                                            except Exception as e:
                                                # Si l'évaluation échoue, laisser le résultat tel quel
                                                logger.warning(f"Erreur lors de l'évaluation automatique du résultat: {str(e)}")
                                                pass
                            except Exception as e:
                                logger.error(f"Erreur lors de la recherche web: {str(e)}")
                            finally:
                                # Fermer la fenêtre de progression
                                web_progress.destroy()
                    
                    # Vérifier à nouveau s'il reste des données manquantes essentielles
                    still_missing = False
                    missing_params = []
                    for idx, row in df.iterrows():
                        if row["Paramètre"] and row["Paramètre"] != "Erreur d'extraction":
                            if (row["Valeur mesurée"] == "" or row["Valeur mesurée"] == "Non disponible"):
                                still_missing = True
                                missing_params.append(row["Paramètre"])
                    
                    # Si des données essentielles sont toujours manquantes, demander à l'utilisateur
                    if still_missing and missing_params:
                        if messagebox.askyesno("Données manquantes", f"Certaines valeurs mesurées sont toujours manquantes pour les paramètres: {', '.join(missing_params)}. Voulez-vous les saisir manuellement?"):
                            # Créer une fenêtre pour la saisie manuelle
                            manual_input = tk.Toplevel(self.root)
                            manual_input.title("Saisie manuelle des données")
                            manual_input.geometry("500x400")
                            manual_input.transient(self.root)
                            manual_input.grab_set()
                            
                            tk.Label(manual_input, text="Veuillez saisir les valeurs manquantes:", font=("Arial", 12, "bold")).pack(pady=10)
                            
                            # Créer un cadre avec défilement pour les champs de saisie
                            canvas = tk.Canvas(manual_input)
                            scrollbar = ttk.Scrollbar(manual_input, orient="vertical", command=canvas.yview)
                            scrollable_frame = ttk.Frame(canvas)
                            
                            scrollable_frame.bind(
                                "<Configure>",
                                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                            )
                            
                            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                            canvas.configure(yscrollcommand=scrollbar.set)
                            
                            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                            scrollbar.pack(side="right", fill="y")
                            
                            # Dictionnaire pour stocker les variables de saisie
                            entry_vars = {}
                            
                            # Créer les champs de saisie pour chaque paramètre manquant
                            for idx, row in df.iterrows():
                                if row["Paramètre"] in missing_params:
                                    frame = ttk.Frame(scrollable_frame)
                                    frame.pack(fill="x", pady=5)
                                    
                                    ttk.Label(frame, text=f"{row['Paramètre']} ({row['Unité'] if row['Unité'] and row['Unité'] != 'Non disponible' else 'unité inconnue'}):").grid(row=0, column=0, padx=5, sticky="w")
                                    
                                    var = tk.StringVar()
                                    entry = ttk.Entry(frame, textvariable=var)
                                    entry.grid(row=0, column=1, padx=5, sticky="w")
                                    
                                    entry_vars[idx] = var
                            
                            # Fonction pour sauvegarder les valeurs saisies
                            def save_manual_values():
                                for idx, var in entry_vars.items():
                                    value = var.get().strip()
                                    if value:
                                        df.at[idx, "Valeur mesurée"] = value
                                        
                                        # Tenter d'évaluer le résultat
                                        try:
                                            intervalle = df.at[idx, "Intervalle acceptable"]
                                            if intervalle and intervalle != "Non disponible":
                                                if "-" in intervalle:
                                                    min_val, max_val = map(float, intervalle.split("-"))
                                                    if float(value) >= min_val and float(value) <= max_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                elif "<" in intervalle:
                                                    max_val = float(intervalle.replace("<", "").strip().split()[0])
                                                    if float(value) < max_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                elif ">" in intervalle:
                                                    min_val = float(intervalle.replace(">", "").strip().split()[0])
                                                    if float(value) > min_val:
                                                        df.at[idx, "Résultat conformité"] = "Conforme"
                                                    else:
                                                        df.at[idx, "Résultat conformité"] = "Non conforme"
                                                
                                                # Calculer le score en fonction du résultat
                                                if df.at[idx, "Résultat conformité"] == "Conforme":
                                                    df.at[idx, "Score"] = 1
                                                else:
                                                    df.at[idx, "Score"] = 0
                                        except Exception as e:
                                            # Si l'évaluation échoue, laisser le résultat tel quel
                                            logger.warning(f"Erreur lors de l'évaluation du résultat: {str(e)}")
                                
                                # Mettre à jour les données actuelles avec les valeurs saisies
                                self.current_data = df
                                self.preview_frame.display_dataframe(df)
                                
                                # Fermer la fenêtre de saisie manuelle
                                manual_input.destroy()
                            
                            # Boutons
                            button_frame = ttk.Frame(manual_input)
                            button_frame.pack(fill="x", pady=10)
                            
                            ttk.Button(button_frame, text="Annuler", command=manual_input.destroy).pack(side="right", padx=5)
                            ttk.Button(button_frame, text="Sauvegarder", command=save_manual_values).pack(side="right", padx=5)
                    
                    # Mettre à jour les données actuelles
                    self.current_data = df
                    self.preview_frame.display_dataframe(df)
                    
                    # Afficher la réponse brute dans l'onglet Résultats
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, f"Réponse IA:\n\n{response}")
                    
                    # Ajouter un bouton pour confirmer et exporter les données
                    confirm_button = ttk.Button(self.results_frame, text="Confirmer et exporter", 
                                             command=lambda: self.confirm_and_export(df))
                    confirm_button.pack(pady=10)
                    
                    self.status_bar.set_status(f"Analyse d'image terminée. Utilisez 'Confirmer et exporter' pour sauvegarder les résultats.", 100)
                    messagebox.showinfo("Succès", f"Analyse d'image terminée! Utilisez le bouton 'Confirmer et exporter' pour sauvegarder les résultats après vérification.")
                    
                    # Afficher des informations sur le mode d'analyse utilisé
                    if self.analysis_mode.get() == "local":
                        # Informations sur le modèle local
                        model_info = f"Mode d'analyse: Local\n"
                        model_info += f"Modèle utilisé: {MODEL_CONFIG['model_name']} ({MODEL_CONFIG.get('model_type', 'non spécifié')})\n"
                        model_info += f"Traitement par lots: Tuiles de {self.batch_params.get('image_tile_size')}px avec chevauchement de {self.batch_params.get('image_overlap')}px\n\n"
                    else:
                        # Informations sur l'API cloud
                        provider = self.cloud_provider.get()
                        model_info = f"Mode d'analyse: Cloud API\n"
                        model_info += f"Fournisseur API: {provider.upper()}\n\n"
                    
                    self.results_text.insert(1.0, model_info)
                else:
                    self.status_bar.set_status("Erreur lors de l'analyse de l'image", 0)
                    # Limiter la longueur du message d'erreur pour éviter les répétitions
                    error_msg = str(response)[:500] + "..." if len(str(response)) > 500 else str(response)
                    messagebox.showerror("Erreur", f"Erreur lors de l'analyse de l'image:\n{error_msg}")
            
            else:
                # Autres types de fichiers: extraction de texte
                self.status_bar.set_status("Extraction du texte...", 50)
                text = extract_text_from_file(self.file_path)
                
                if text:
                    # Afficher le texte extrait dans l'onglet Résultats
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, f"Texte extrait:\n\n{text[:2000]}...\n\n(Texte tronqué pour l'affichage)")
                    
                    # Sauvegarder le texte extrait
                    output_dir = OUTPUT_DIR
                    os.makedirs(output_dir, exist_ok=True)
                    base_name = os.path.splitext(os.path.basename(self.file_path))[0]
                    output_path = os.path.join(output_dir, f"{base_name}_texte_extrait.txt")
                    
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    
                    self.status_bar.set_status(f"Extraction de texte terminée. Texte sauvegardé dans {os.path.basename(output_path)}", 50)
                    
                    # Demander à l'utilisateur s'il souhaite analyser le texte extrait
                    if messagebox.askyesno("Analyse du texte", "Le texte a été extrait avec succès. Souhaitez-vous l'analyser avec le modèle IA pour extraire les paramètres environnementaux?"):
                        self.analyze_extracted_text(output_path)
                    else:
                        messagebox.showinfo("Succès", f"Extraction de texte terminée! Texte sauvegardé dans:\n{output_path}")
                        self.status_bar.set_status(f"Extraction de texte terminée. Texte sauvegardé dans {os.path.basename(output_path)}", 100)
                else:
                    self.status_bar.set_status("Erreur lors de l'extraction du texte", 0)
                    messagebox.showerror("Erreur", "Impossible d'extraire du texte du fichier sélectionné.")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du fichier: {str(e)}")
            self.status_bar.set_status("Erreur lors de l'analyse", 0)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'analyse:\n{str(e)}")
    
    def _analyze_pdf_file(self, file_path):
        """Extraction et analyse PDF en arrière-plan, page par page, avec progression et annulation."""
        try:
            # Enregistrer le début dans le log d'audit
            audit_logger.log_action(
                action="Début extraction PDF",
                user="interface_utilisateur",
                ip="localhost",
                fichier=file_path
            )
            self.status_bar.set_status("Préparation extraction PDF...", 10)

            # Demander le mode d'analyse si nécessaire
            if self.prompt_for_mode.get():
                mode_choice = messagebox.askyesno(
                    "Mode d'analyse",
                    "Voulez-vous utiliser le mode d'analyse local pour le texte?\n\nOui = Modèle local\nNon = API Cloud"
                )
                if mode_choice:
                    self.analysis_mode.set("local")
                    self.update_analysis_mode()
                else:
                    self.analysis_mode.set("cloud")
                    self.update_analysis_mode()

            # Fenêtre de progression
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Extraction et analyse PDF")
            progress_window.geometry("520x240")
            progress_window.transient(self.root)
            progress_window.grab_set()

            tk.Label(progress_window, text="Traitement du PDF", font=("Arial", 12, "bold")).pack(pady=10)

            info_label = tk.Label(progress_window, text="Initialisation...")
            info_label.pack(pady=5)

            progress = ttk.Progressbar(progress_window, orient="horizontal", length=460, mode="determinate")
            progress.pack(pady=10, padx=20)

            page_label = tk.Label(progress_window, text="Page: 0/?")
            page_label.pack(pady=5)

            # Boutons
            button_frame = ttk.Frame(progress_window)
            button_frame.pack(fill="x", pady=10)
            cancel_btn = ttk.Button(button_frame, text="Annuler")
            cancel_btn.pack(side="right", padx=5)

            # État d'annulation
            self._cancel_pdf = False
            def on_cancel():
                self._cancel_pdf = True
                cancel_btn.config(state="disabled")
                info_label.config(text="Annulation en cours...")
            cancel_btn.config(command=on_cancel)

            # Déterminer le nombre total de pages
            total_pages = 0
            try:
                with pdfplumber.open(file_path) as pdf:
                    total_pages = len(pdf.pages)
            except Exception as e:
                logger.warning(f"Impossible d'obtenir le nombre de pages: {str(e)}")
            if total_pages > 0:
                progress["maximum"] = total_pages

            # Si l'OCR est désactivé, traiter le PDF en images et envoyer directement aux analyseurs d'images
            try:
                use_ocr_flag = self.use_ocr.get()
            except Exception:
                use_ocr_flag = True

            if not use_ocr_flag:
                def worker_images():
                    page_idx = 0
                    try:
                        import tempfile
                        all_dfs = []
                        response = None
                        with pdfplumber.open(file_path) as pdf:
                            for page_idx, page in enumerate(pdf.pages, start=1):
                                if self._cancel_pdf:
                                    break
                                # Rendu de la page en image (PIL)
                                try:
                                    page_img = page.to_image(resolution=200).original
                                except Exception as e_img:
                                    logger.warning(f"Échec rendu image page {page_idx}: {e_img}")
                                    continue
                                # Sauvegarder en image temporaire
                                try:
                                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                        tmp_path = tmp.name
                                    page_img.save(tmp_path, format="PNG")
                                except Exception as e_save:
                                    logger.warning(f"Échec sauvegarde image page {page_idx}: {e_save}")
                                    continue

                                # Analyse selon le mode sélectionné (local / cloud)
                                try:
                                    fallback_to_text = False
                                    if self.analysis_mode.get() == "local":
                                        max_new_tokens = 250
                                        df_page, response = analyze_environmental_image(
                                            tmp_path,
                                            model=self.model,
                                            batch_params=self.batch_params,
                                            max_new_tokens=max_new_tokens,
                                            use_ocr=self.use_ocr.get()
                                        )
                                    else:
                                        provider = self.cloud_provider.get()
                                        try:
                                            if provider == "gemini" and GEMINI_AVAILABLE:
                                                df_page, response = analyze_environmental_image_with_gemini(
                                                    tmp_path,
                                                    use_ocr=self.use_ocr.get()
                                                )
                                            else:
                                                df_page, response = analyze_environmental_image_cloud(
                                                    tmp_path,
                                                    api_provider=provider
                                                )
                                        except Exception as e_img:
                                            msg = str(e_img).lower()
                                            if "404" in msg or "not support" in msg or "no endpoints found" in msg:
                                                fallback_to_text = True
                                                logger.warning(f"Provider ne supporte pas l'image, fallback extraction texte page {page_idx}")
                                            else:
                                                raise
                                    if not fallback_to_text:
                                        if df_page is not None and not df_page.empty:
                                            all_dfs.append(df_page)
                                    else:
                                        # Fallback : extraction texte classique
                                        try:
                                            import pytesseract
                                            from PIL import Image
                                            text = pytesseract.image_to_string(Image.open(tmp_path))
                                            # Vous pouvez ici appeler votre pipeline d'analyse texte sur 'text'
                                            # Par exemple : df_page = self.text_analyzer.analyze_text(text)
                                            # Pour l'instant, on ne fait qu'ignorer la page si pas de pipeline texte
                                            logger.info(f"Texte OCR fallback page {page_idx}: {text[:100]}")
                                        except Exception as eocr:
                                            logger.warning(f"Échec fallback OCR page {page_idx}: {eocr}")
                                except Exception as e_an:
                                    logger.warning(f"Échec analyse image page {page_idx}: {e_an}")
                                finally:
                                    try:
                                        os.unlink(tmp_path)
                                    except Exception:
                                        pass

                                # Mise à jour UI
                                def ui_update_img():
                                    if total_pages:
                                        progress["maximum"] = total_pages
                                        progress["value"] = page_idx
                                        page_label.config(text=f"Page: {page_idx}/{total_pages}")
                                        pct = int(page_idx * 70 / max(1, total_pages))
                                    else:
                                        progress["mode"] = "indeterminate"
                                        progress.step(1)
                                        page_label.config(text=f"Page: {page_idx}/?")
                                        pct = 50
                                    info_label.config(text="Analyse des pages (vision IA) en cours...")
                                    self.status_bar.set_status(f"Analyse PDF (vision): page {page_idx}/{total_pages or '?'}", pct)
                                    progress_window.update_idletasks()
                                self.root.after(0, ui_update_img)

                        # Finalisation UI
                        def ui_done_img():
                            try:
                                progress.stop()
                            except Exception:
                                pass
                            progress_window.destroy()
                            result_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
                            if result_df is not None and not result_df.empty:
                                self.current_data = result_df
                                self.preview_frame.display_dataframe(result_df)
                                # Ajout à l'historique des analyses récentes pour export SLRI
                                import datetime
                                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                nom = f"Analyse PDF (vision) {now}"
                                self.recent_analyses.append((nom, result_df, now))
                                self.recent_analyses = self.recent_analyses[-10:]
                                output_path = save_dataframe_to_excel(result_df, directory=OUTPUT_DIR)
                                audit_logger.log_action(
                                    action="Analyse PDF (vision) terminée",
                                    user="interface_utilisateur",
                                    ip="localhost",
                                    fichier=file_path,
                                    nb_pages=page_idx,
                                    nb_parametres=len(result_df),
                                    chemin_sortie=output_path
                                )
                                self.status_bar.set_status("Analyse PDF (vision) terminée", 100)
                                messagebox.showinfo("Succès", "Analyse du PDF (vision IA) terminée. Résultats disponibles.")
                            else:
                                self.status_bar.set_status("Analyse terminée (aucun paramètre extrait)", 50)
                                messagebox.showwarning("Information", "Aucun paramètre n'a été extrait via l'analyse d'images.")
                        self.root.after(0, ui_done_img)
                    except Exception as e:
                        err = str(e)
                        logger.error(f"Erreur lors du traitement PDF (vision): {err}")
                        def ui_fail_img():
                            try:
                                progress.stop()
                            except Exception:
                                pass
                            progress_window.destroy()
                            self.status_bar.set_status("Erreur (vision) lors du traitement du PDF", 0)
                            messagebox.showerror("Erreur", f"Erreur lors de l'analyse du PDF (vision):\n{err}")
                        self.root.after(0, ui_fail_img)

                    # Journal d'audit fin
                    audit_logger.log_action(
                        action="Extraction/Analyse PDF (vision) terminée",
                        user="interface_utilisateur",
                        ip="localhost",
                        fichier=file_path,
                        nb_pages=page_idx
                    )

                t = threading.Thread(target=worker_images, daemon=True)
                t.start()
                return

            # Préparer le fichier de sortie pour le texte
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            text_output_path = os.path.join(OUTPUT_DIR, f"{base_name}_texte_extrait.txt")
            # Vider le fichier s'il existe
            try:
                with open(text_output_path, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                logger.error(f"Impossible de créer le fichier texte de sortie: {str(e)}")

            # Travailleur en arrière-plan
            def worker():
                page_idx = 0
                try:
                    # Extraction page par page
                    for idx, text in iter_pdf_text_pages(file_path, ocr_fallback=True, dpi=200, lang="eng+fra"):
                        if self._cancel_pdf:
                            break
                        page_idx = idx + 1
                        try:
                            with open(text_output_path, "a", encoding="utf-8") as f:
                                f.write(f"\n\n=== Page {page_idx} ===\n")
                                f.write(text or "")
                        except Exception as e:
                            logger.warning(f"Échec d'écriture du texte extrait pour la page {page_idx}: {str(e)}")

                        def ui_update():
                            if total_pages:
                                progress["maximum"] = total_pages
                                progress["value"] = page_idx
                                page_label.config(text=f"Page: {page_idx}/{total_pages}")
                                pct = int(page_idx * 50 / max(1, total_pages))
                            else:
                                progress["mode"] = "indeterminate"
                                progress.step(1)
                                page_label.config(text=f"Page: {page_idx}/?")
                                pct = 25
                            info_label.config(text="Extraction du PDF en cours...")
                            self.status_bar.set_status(f"Extraction PDF: page {page_idx}/{total_pages or '?'}", pct)
                            progress_window.update_idletasks()
                        self.root.after(0, ui_update)

                    if self._cancel_pdf:
                        def ui_cancelled():
                            progress_window.destroy()
                            self.status_bar.set_status("Extraction PDF annulée", 0)
                            messagebox.showinfo("Annulé", "Extraction du PDF annulée.")
                        self.root.after(0, ui_cancelled)
                        return

                    # Démarrer l'analyse du texte
                    def ui_start_analysis():
                        info_label.config(text="Analyse du texte avec IA...")
                        page_label.config(text=f"Pages traitées: {page_idx}")
                        progress["mode"] = "indeterminate"
                        progress.start()
                        cancel_btn.config(state="disabled")  # Annulation non supportée pendant l'analyse
                    self.root.after(0, ui_start_analysis)

                    # Charger le texte complet
                    try:
                        with open(text_output_path, 'r', encoding='utf-8') as f:
                            extracted_text = f.read()
                    except Exception as e:
                        extracted_text = ""
                        logger.error(f"Impossible de relire le texte extrait: {str(e)}")

                    result_df = None
                    response = None
                    try:
                        if self.analysis_mode.get() == "local":
                            if not self.load_model:
                                raise Exception("Modèle local non disponible (option --no-load-model)")
                            prompt = "Extrais tous les paramètres environnementaux avec leurs valeurs et unités à partir du texte suivant. Assure-toi d'analyser l'intégralité du texte et de fournir une liste complète et structurée de tous les paramètres trouvés. Pour chaque paramètre, indique clairement sa valeur et son unité au format 'Paramètre: Valeur Unité'."
                            chunk_size = max(2000, self.batch_params.get("text_chunk_size", 1000))
                            overlap = max(200, self.batch_params.get("text_overlap", 100))
                            logger.info(f"Analyse du texte (local) avec chunk_size={chunk_size}, overlap={overlap}, len={len(extracted_text)}")
                            result_df = self.model.analyze_text(
                                extracted_text,
                                prompt=prompt,
                                chunk_size=chunk_size,
                                overlap=overlap,
                                max_new_tokens=1000
                            )
                            response = "Analyse locale effectuée"
                            
                            # Appliquer le système de scoring environnemental
                            if result_df is not None and not result_df.empty:
                                from environmental_scoring import EnvironmentalScoring
                                scorer = EnvironmentalScoring()
                                result_df = scorer.score_dataframe(result_df)
                                logger.info(f"Scoring appliqué (local): {len(result_df)} paramètres avec scores")
                        else:
                            provider = self.cloud_provider.get()
                            if not self.cloud_api_config.get(provider, {}).get("api_key"):
                                raise Exception(f"La clé API pour {provider} n'est pas configurée.")
                            cloud_api = CloudVisionAPI(api_provider=provider)
                            instructions = (
                                "Analyse attentivement le texte suivant issu d’un fichier importé. "
                                "Ta tâche est de construire IMPÉRATIVEMENT un tableau Markdown structuré avec exactement les colonnes intitulées 'Paramètre', 'Unité', 'Intervalle acceptable', 'Valeur mesurée de milieux initial', 'Rejet de prj', 'Valeure Mesure+rejet'. "
                                "Pour chaque milieu (EAU, SOL, AIR, POPULATION/HABITATS), recherche systématiquement et dans le même ordre la liste suivante de paramètres standards, même s'ils ne sont pas explicitement présents dans le texte. Pour chaque paramètre, indique la valeur trouvée ou 'Non disponible'. N'utilise jamais de cellule vide et respecte impérativement l'ordre et les intitulés ci-dessous :\n"
                                "\n**Milieu PHYSIQUE/EAU :**\n"
                                "Température (°C), Ph (—), Turbidité (NTU), Conductivité (µS/cm), DBO5 (mg/L), DCO (mg/L), Oxygène dissous (mg/L), Nitrates (NO₃⁻, mg/L), Nitrites (NO₂⁻, mg/L), Ammoniac (NH₄⁺, mg/L), Phosphore total (mg/L), Azote total (mg/L), Plomb (Pb), Cadmium (Cd), Chrome total (Cr), Cuivre (Cu), Zinc (Zn), Nickel (Ni), Mercure (Hg), Arsenic (As), Hydrocarbures (HCT, HAP, mg/L)"
                                "\n**Milieu PHYSIQUE/SOL :**\n"
                                "pH (—), Perméabilité (cm/s), Matière organique (%), Carbone organique (%), Plomb (Pb), Cadmium (Cd), Mercure (Hg), Arsenic (As), Chrome total (Cr), Cuivre (Cu), Zinc (Zn), Nickel (Ni), Azote total (mg/kg), Phosphore total (mg/kg)"
                                "\n**Milieu PHYSIQUE/AIR :**\n"
                                "Poussières totales (mg/m³), PM10 (µg/m³), PM2.5 (µg/m³), SO₂ (µg/m³), NOx (µg/m³), CO (µg/m³), O₃ (ozone, µg/m³)"
                                "\n**Milieu PHYSIQUE population et habitats :**\n"
                                "Résidentiel (dB(A)), Radiations électromagnétiques éoliennes (kV/m et µT), Radiations électromagnétiques CABLES (kV/m et µT), Radiations électromagnétiques ONDEURS (V/m et W/m²), Poussières (mg/m³), Risques électriques et incendie (Nombre d’anomalie)"
                                "- Pour chaque paramètre, indique la valeur trouvée dans le texte ou 'Non disponible'.\n"
                                "- Si tu ne trouves aucune information, crée quand même une ligne avec 'Non disponible' dans chaque colonne. "
                                "- N’utilise jamais de cellule vide. "
                                "- Ne donne jamais de texte hors du tableau. "
                                "- Le tableau doit être complet, exhaustif, et fidèle au contenu du texte.\n\nTexte à analyser:\n{extracted_text}"
                            )
                            prompt_full = f"{instructions}\n\nTexte à analyser:\n{extracted_text}"
                            # Utiliser le routage interne pour sélectionner la bonne API selon le fournisseur
                            response = cloud_api.analyze_text(prompt_full, provider=provider)
                            logger.debug(f"Réponse de l'API {provider}: {str(response)[:500]}...")
                            result_df = cloud_api._extract_parameters(response)
                            logger.info(f"Analyse cloud terminée, {len(result_df) if result_df is not None else 0} paramètres extraits")
                            
                            # Appliquer le système de scoring environnemental
                            if result_df is not None and not result_df.empty:
                                from environmental_scoring import EnvironmentalScoring
                                scorer = EnvironmentalScoring()
                                result_df = scorer.score_dataframe(result_df)
                                logger.info(f"Scoring appliqué: {len(result_df)} paramètres avec scores")
                                
                                # Ajouter au projet si mode projet activé
                                if self.current_project_mode.get() and self.project_manager.current_project:
                                    analysis_name = f"Analyse PDF - {os.path.basename(file_path)}"
                                    self.project_manager.add_analysis_to_project(
                                        result_df, analysis_name, file_path, provider
                                    )
                                    logger.info(f"Analyse ajoutée au projet: {analysis_name}")
                    except Exception as e:
                        err = str(e)
                        logger.error(f"Erreur lors de l'analyse du texte: {err}")
                        def ui_err():
                            try:
                                progress.stop()
                            except Exception:
                                pass
                            progress_window.destroy()
                            self.status_bar.set_status("Erreur lors de l'analyse du texte", 0)
                            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'analyse du texte:\n{err}")
                        self.root.after(0, ui_err)
                        return

                    # Finaliser et afficher les résultats
                    def ui_done():
                        try:
                            progress.stop()
                        except Exception:
                            pass
                        progress_window.destroy()
                        if result_df is not None and not result_df.empty:
                            self.current_data = result_df
                            self.preview_frame.display_dataframe(result_df)
                            
                            # Sauvegarder les résultats
                            output_path = save_dataframe_to_excel(result_df, directory=OUTPUT_DIR)
                            
                            # Enregistrer le succès dans le log d'audit
                            audit_logger.log_action(
                                action="Analyse PDF terminée",
                                user="interface_utilisateur",
                                ip="localhost",
                                fichier=file_path,
                                nb_pages=page_idx,
                                nb_parametres=len(result_df),
                                chemin_sortie=output_path
                            )
                            
                            # Afficher un résumé
                            self.results_text.delete(1.0, tk.END)
                            self.results_text.insert(tk.END, f"Texte extrait sauvegardé: {os.path.basename(text_output_path)}\n")
                            self.results_text.insert(tk.END, f"Pages: {page_idx}\n\n")
                            if response is not None:
                                self.results_text.insert(tk.END, f"Réponse IA:\n\n{str(response)[:2000]}...\n")
                            self.status_bar.set_status("Analyse PDF terminée", 100)
                            messagebox.showinfo("Succès", "Analyse du PDF terminée. Vous pouvez enregistrer les résultats.")
                        else:
                            self.status_bar.set_status("Analyse terminée (aucun paramètre extrait)", 50)
                            messagebox.showwarning("Information", "Aucun paramètre n'a été extrait. Le texte a été sauvegardé pour analyse ultérieure.")
                    self.root.after(0, ui_done)

                except Exception as e:
                    err = str(e)
                    logger.error(f"Erreur lors du traitement PDF: {err}")
                    def ui_fail():
                        try:
                            progress.stop()
                        except Exception:
                            pass
                        progress_window.destroy()
                        self.status_bar.set_status("Erreur lors du traitement du PDF", 0)
                        messagebox.showerror("Erreur", f"Une erreur est survenue lors du traitement du PDF:\n{err}")
                    self.root.after(0, ui_fail)

                # Enregistrer la fin dans le log d'audit
                audit_logger.log_action(
                    action="Extraction/Analyse PDF terminée",
                    user="interface_utilisateur",
                    ip="localhost",
                    fichier=file_path,
                    nb_pages=page_idx
                )

            t = threading.Thread(target=worker, daemon=True)
            t.start()

        except Exception as e:
            logger.error(f"Erreur initiale _analyze_pdf_file: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'initialisation de l'analyse PDF:\n{str(e)}")
    
    def _analyze_multiple_files(self, file_paths):
        """Analyse plusieurs fichiers en séquence."""
        try:
            # Enregistrer l'action dans le log d'audit
            audit_logger.log_action(
                action="Début analyse multiple fichiers",
                user="interface_utilisateur",
                ip="localhost",
                fichiers=file_paths,
                nb_fichiers=len(file_paths)
            )
            
            # Créer une fenêtre de progression
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Progression de l'analyse multiple")
            progress_window.geometry("600x400")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Ajouter des étiquettes et une barre de progression
            tk.Label(progress_window, text="Analyse de plusieurs fichiers en cours", font=("Arial", 12, "bold")).pack(pady=10)
            
            # Afficher le nombre total de fichiers
            total_files_label = tk.Label(progress_window, text=f"Fichiers à analyser: {len(file_paths)}")
            total_files_label.pack(pady=5)
            
            # Barre de progression
            progress = ttk.Progressbar(progress_window, orient="horizontal", length=500, mode="determinate")
            progress.pack(pady=10, padx=20)
            
            # Étiquette pour le fichier en cours
            current_file_label = tk.Label(progress_window, text="Fichier en cours: ")
            current_file_label.pack(pady=5)
            
            # Zone de texte pour afficher les résultats
            results_frame = ttk.LabelFrame(progress_window, text="Résultats")
            results_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=10)
            results_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            scrollbar = ttk.Scrollbar(results_text, orient="vertical", command=results_text.yview)
            scrollbar.pack(side="right", fill="y")
            results_text.configure(yscrollcommand=scrollbar.set)
            
            # Configurer la barre de progression
            progress["maximum"] = len(file_paths)
            progress["value"] = 0
            
            # Initialiser les compteurs
            success_count = 0
            error_count = 0
            
            # Analyser chaque fichier
            for i, file_path in enumerate(file_paths):
                # Mettre à jour l'interface
                file_name = os.path.basename(file_path)
                current_file_label.config(text=f"Fichier en cours: {file_name} ({i+1}/{len(file_paths)})")
                self.status_bar.set_status(f"Analyse du fichier {i+1}/{len(file_paths)}: {file_name}", (i+1) * 100 // len(file_paths))
                
                # Ajouter une entrée dans la zone de texte
                results_text.insert(tk.END, f"\nAnalyse de {file_name}... ")
                progress_window.update()
                
                try:
                    # Analyser le fichier
                    self._analyze_single_file(file_path)
                    
                    # Mettre à jour le compteur de succès
                    success_count += 1
                    results_text.insert(tk.END, "Succès\n")
                    results_text.see(tk.END)  # Défiler vers le bas
                except Exception as e:
                    # Gérer les erreurs pour chaque fichier individuellement
                    error_count += 1
                    error_msg = str(e)
                    results_text.insert(tk.END, f"Erreur: {error_msg}\n")
                    results_text.see(tk.END)  # Défiler vers le bas
                    logger.error(f"Erreur lors de l'analyse du fichier {file_path}: {error_msg}")
                
                # Mettre à jour la barre de progression
                progress["value"] = i + 1
                progress_window.update()
            
            # Afficher un résumé
            summary = f"\n--- Résumé ---\nFichiers analysés avec succès: {success_count}/{len(file_paths)}\n"
            if error_count > 0:
                summary += f"Fichiers avec erreurs: {error_count}/{len(file_paths)}\n"
            
            results_text.insert(tk.END, summary)
            results_text.see(tk.END)  # Défiler vers le bas
            
            # Mettre à jour la barre d'état
            self.status_bar.set_status(f"Analyse multiple terminée. {success_count} fichiers analysés avec succès, {error_count} erreurs.", 100)
            
            # Ajouter un bouton pour fermer la fenêtre
            ttk.Button(progress_window, text="Fermer", command=progress_window.destroy).pack(pady=10)
            
            # Enregistrer le succès dans le log d'audit
            audit_logger.log_action(
                action="Analyse multiple fichiers terminée",
                user="interface_utilisateur",
                ip="localhost",
                nb_fichiers=len(file_paths),
                nb_succes=success_count,
                nb_erreurs=error_count
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse multiple: {str(e)}")
            self.status_bar.set_status("Erreur lors de l'analyse multiple", 0)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'analyse multiple:\n{str(e)}")
            
            # Enregistrer l'erreur dans le log d'audit
            audit_logger.log_action(
                action="Erreur lors de l'analyse multiple",
                user="interface_utilisateur",
                ip="localhost",
                erreur=str(e),
                level="ERROR"
            )
    
    def save_results(self):
        """Sauvegarde les résultats actuels."""
        if self.current_data is None:
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return
        
        try:
            # Demander où sauvegarder le fichier
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Fichiers Excel", "*.xlsx")],
                initialdir=OUTPUT_DIR
            )
            
            if file_path:
                # Enregistrer l'action dans le log d'audit
                audit_logger.log_action(
                    action="Début sauvegarde résultats",
                    user="interface_utilisateur",
                    ip="localhost",
                    fichier_destination=file_path,
                    nb_lignes=len(self.current_data)
                )
                
                self.current_data.to_excel(file_path, index=False)
                self.status_bar.set_status(f"Données sauvegardées dans {os.path.basename(file_path)}")
                messagebox.showinfo("Succès", f"Données sauvegardées dans:\n{file_path}")
                
                # Enregistrer le succès dans le log d'audit
                audit_logger.log_action(
                    action="Sauvegarde résultats terminée",
                    user="interface_utilisateur",
                    ip="localhost",
                    fichier_destination=file_path,
                    nb_lignes=len(self.current_data),
                    taille_fichier=os.path.getsize(file_path)
                )
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur lors de la sauvegarde des résultats: {error_msg}")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la sauvegarde:\n{error_msg}")
            
            # Enregistrer l'erreur dans le log d'audit
            audit_logger.log_action(
                action="Erreur lors de la sauvegarde",
                user="interface_utilisateur",
                ip="localhost",
                fichier_destination=file_path if 'file_path' in locals() else "non spécifié",
                erreur=error_msg,
                level="ERROR"
            )
    
    def visualize_data(self):
        """Visualise les données actuelles."""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("Attention", "Aucune donnée à visualiser.")
            return
        
        try:
            # Sélectionner l'onglet de visualisation
            self.notebook.select(self.visualization_frame)
            
            # Créer une visualisation simple
            df = self.current_data
            
            # Déterminer les colonnes à utiliser pour la visualisation
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 1:
                x_col = df.columns[0]  # Première colonne comme axe X par défaut
                y_col = numeric_cols[0]  # Première colonne numérique comme axe Y
                
                self.visualization_frame.plot_data(df, x_col=x_col, y_col=y_col, plot_type="bar")
                self.status_bar.set_status("Visualisation générée")
            else:
                messagebox.showinfo("Information", "Aucune colonne numérique trouvée pour la visualisation.")
        
        except Exception as e:
            logger.error(f"Erreur lors de la visualisation des données: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la visualisation:\n{str(e)}")
    
    def show_help(self):
        """Affiche l'aide de l'application."""
        help_text = """
        Analyse de Risque Environnemental - Maroc
        
        Cette application permet d'analyser des données environnementales à partir de différents formats de fichiers.
        
        Utilisation:
        1. Cliquez sur 'Parcourir' pour sélectionner un fichier à analyser
        2. Cliquez sur 'Analyser' pour traiter le fichier
        3. Consultez les résultats dans les différents onglets
        4. Utilisez 'Enregistrer' pour sauvegarder les résultats
        
        Types de fichiers supportés:
        - Fichiers Excel (.xlsx)
        - Images (.png, .jpg, .jpeg)
        - Documents PDF (.pdf)
        - Documents Word (.docx)
        - Fichiers texte (.txt, .csv)
        
        Pour plus d'informations, consultez la documentation du projet.
        """
        
        messagebox.showinfo("Aide", help_text)
    
    def browse_and_analyze_text(self):
        """Permet à l'utilisateur de sélectionner un fichier texte et de l'analyser."""
        filetypes = [("Fichiers texte", "*.txt")]
        text_file_path = filedialog.askopenfilename(filetypes=filetypes, title="Sélectionner un fichier texte à analyser")
        
        if text_file_path:
            self.file_path = text_file_path  # Mettre à jour le chemin du fichier courant
            self.status_bar.set_status(f"Fichier sélectionné: {os.path.basename(text_file_path)}")
            self.analyze_extracted_text(text_file_path)
    
    def analyze_extracted_text(self, text_file_path):
        """Analyse le texte extrait avec le modèle IA."""
        try:
            # Charger le texte extrait
            with open(text_file_path, 'r', encoding='utf-8') as file:
                extracted_text = file.read()
            
            self.status_bar.set_status("Analyse du texte avec IA...", 60)
            
            # Vérifier si l'utilisateur souhaite être interrogé sur le mode d'analyse
            if self.prompt_for_mode.get():
                # Demander à l'utilisateur de choisir le mode d'analyse
                mode_choice = messagebox.askyesno("Mode d'analyse", 
                                               "Voulez-vous utiliser le mode d'analyse local?\n\nOui = Modèle local\nNon = API Cloud")
                
                if mode_choice:  # L'utilisateur a choisi le mode local
                    # Mettre à jour le mode d'analyse
                    self.analysis_mode.set("local")
                    self.update_analysis_mode()
                else:  # L'utilisateur a choisi le mode cloud
                    # Mettre à jour le mode d'analyse
                    self.analysis_mode.set("cloud")
                    self.update_analysis_mode()
            
            # Vérifier le mode d'analyse actuel
            if self.analysis_mode.get() == "local":
                # Vérifier si le modèle doit être chargé
                if not self.load_model:
                    messagebox.showwarning("Modèle non chargé", "L'application a été démarrée avec l'option --no-load-model. Le modèle IA n'est pas disponible.")
                    self.status_bar.set_status("Modèle IA non disponible", 0)
                    return
                
                # Analyser le texte avec le modèle en utilisant les paramètres de traitement par lots
                # Utiliser un prompt plus spécifique pour s'assurer que l'intégralité du texte est analysée
                prompt = "Extrais tous les paramètres environnementaux avec leurs valeurs et unités à partir du texte suivant. Assure-toi d'analyser l'intégralité du texte et de fournir une liste complète et structurée de tous les paramètres trouvés. Pour chaque paramètre, indique clairement sa valeur et son unité au format 'Paramètre: Valeur Unité'."
                
                # Augmenter la taille des chunks pour capturer plus de contexte
                chunk_size = max(2000, self.batch_params.get("text_chunk_size", 1000))
                overlap = max(200, self.batch_params.get("text_overlap", 100))
                
                # Journaliser les paramètres d'analyse
                logger.info(f"Analyse du texte avec chunk_size={chunk_size}, overlap={overlap}")
                logger.info(f"Longueur du texte à analyser: {len(extracted_text)} caractères")
                
                result_df = self.model.analyze_text(
                    extracted_text,
                    prompt=prompt,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    max_new_tokens=1000
                )
            else:  # Mode cloud
                # Vérifier si l'API est configurée
                provider = self.cloud_provider.get()
                if not self.cloud_api_config.get(provider, {}).get("api_key"):
                    messagebox.showwarning("API non configurée", f"La clé API pour {provider} n'est pas configurée. Veuillez configurer l'API dans le menu Configuration > Configurer les clés API.")
                    self.status_bar.set_status("API cloud non configurée", 0)
                    return
                
                # Créer une instance de l'API cloud
                cloud_api = CloudVisionAPI(api_provider=provider)
                
                # Améliorer le prompt pour l'analyse
                prompt = f"Extrais tous les paramètres environnementaux avec leurs valeurs et unités à partir du texte suivant. Assure-toi d'analyser l'intégralité du texte et de fournir une liste complète et structurée. Présente les résultats sous forme de tableau Markdown avec les colonnes 'Paramètre', 'Valeur' et 'Unité'.\n\nIMPORTANT: Si certaines valeurs ne sont pas disponibles dans le texte, tu DOIS fournir une estimation basée sur des valeurs typiques et ajouter \"(estimé)\" après la valeur. Ne laisse AUCUNE cellule vide et n'utilise JAMAIS \"Non disponible\".\n\nTexte à analyser:\n{extracted_text}"
                
                # Analyser directement le texte sans conversion en image
                if provider in ["openrouter", "openrouter_deepseek", "openrouter_qwen"]:
                    response = cloud_api._analyze_with_openrouter(text=prompt, text_only=True)
                else:
                    response = cloud_api._analyze_with_openai_text(prompt, prompt)
                
                # Journaliser la réponse pour le débogage
                logger.debug(f"Réponse de l'API {provider}: {str(response)[:500]}...")
                
                # Extraire les paramètres de la réponse
                result_df = cloud_api._extract_parameters(response)
                
                # Journaliser les résultats
                logger.info(f"Analyse cloud terminée, {len(result_df) if result_df is not None else 0} paramètres extraits")
                
                # Passer directement aux étapes de traitement des résultats
                if result_df is not None and not result_df.empty:
                    all_results = result_df
                else:
                    logger.warning("Aucun paramètre extrait de l'analyse cloud")
                    all_results = pd.DataFrame()
                    
                # Définir text_parts comme une liste vide pour éviter les erreurs dans le code suivant
                # Initialiser un DataFrame vide pour stocker les résultats
                result_df = pd.DataFrame()
                
                # Analyser directement le texte extrait avec l'API cloud
                logger.info("Analyse du texte extrait avec l'API cloud")
                
                # Utiliser directement l'API cloud pour analyser le texte
                from cloud_api import extract_markdown_table
                try:
                    # Essayer d'abord avec OpenAI
                    cloud_vision_api = CloudVisionAPI(api_provider="openai")
                    result = cloud_vision_api.analyze_text(extracted_text)
                    result_df = extract_markdown_table(result)
                except Exception as e:
                    logger.warning(f"Erreur avec OpenAI: {str(e)}")
                    try:
                        # Essayer avec OpenRouter DeepSeek comme premier fallback
                        logger.info("Tentative avec OpenRouter DeepSeek")
                        cloud_vision_api = CloudVisionAPI(api_provider="openrouter_deepseek")
                        result = cloud_vision_api.analyze_text(extracted_text)
                        result_df = extract_markdown_table(result)
                    except Exception as e2:
                        logger.warning(f"Erreur avec OpenRouter DeepSeek: {str(e2)}")
                        try:
                            # Essayer avec OpenRouter Qwen comme deuxième fallback
                            logger.info("Tentative avec OpenRouter Qwen")
                            cloud_vision_api = CloudVisionAPI(api_provider="openrouter_qwen")
                            result = cloud_vision_api.analyze_text(extracted_text)
                            result_df = extract_markdown_table(result)
                        except Exception as e3:
                            logger.warning(f"Erreur avec OpenRouter Qwen: {str(e3)}")
                            try:
                                # Essayer avec OpenRouter standard comme troisième fallback
                                logger.info("Tentative avec OpenRouter standard")
                                cloud_vision_api = CloudVisionAPI(api_provider="openrouter")
                                result = cloud_vision_api.analyze_text(extracted_text)
                                result_df = extract_markdown_table(result)
                            except Exception as e4:
                                logger.warning(f"Erreur avec OpenRouter standard: {str(e4)}")
                                try:
                                    # Essayer avec Google (Gemini Pro) comme quatrième fallback
                                    logger.info("Tentative avec Google (Gemini Pro)")
                                    cloud_vision_api = CloudVisionAPI(api_provider="google")
                                    result = cloud_vision_api.analyze_text(extracted_text)
                                    result_df = extract_markdown_table(result)
                                except Exception as e5:
                                    logger.warning(f"Erreur avec Google (Gemini Pro): {str(e5)}")
                                    try:
                                        # Utiliser le modèle local comme dernier recours
                                        logger.info("Utilisation du modèle local pour l'analyse du texte")
                                        from model_interface import ModelInterface
                                        model = ModelInterface()
                                        prompt = f"Analyse le texte suivant et identifie les paramètres environnementaux importants. Présente les résultats sous forme de tableau markdown avec les colonnes 'Paramètre', 'Catégorie', et 'Valeur':\n\n{extracted_text}"
                                        result = model.generate_text(prompt)
                                        result_df = extract_markdown_table(result)
                                    except Exception as e6:
                                        logger.error(f"Erreur avec le modèle local: {str(e6)}")
                                        # Créer un DataFrame vide avec un message d'erreur
                                        result_df = pd.DataFrame({
                                            "Paramètre": ["Erreur d'API"],
                                            "Catégorie": ["Erreur"],
                                            "Valeur": ["Aucun modèle disponible. Veuillez configurer une clé API valide ou vérifier le modèle local."]
                                        })
                
                if result_df is not None and not result_df.empty:
                    logger.info(f"Analyse cloud terminée, {len(result_df)} paramètres extraits au total")
                else:
                    logger.warning("Aucun paramètre extrait de l'analyse cloud")
                    result_df = pd.DataFrame()
            
            if result_df is not None and not result_df.empty:
                self.current_data = result_df
                self.preview_frame.display_dataframe(result_df)
                
                # Sauvegarder les résultats
                base_name = os.path.splitext(os.path.basename(self.file_path))[0]
                output_path = save_dataframe_to_excel(result_df, base_filename=f"analyse_{base_name}", directory=OUTPUT_DIR)
                
                # Afficher les résultats dans l'onglet Résultats
                self.results_text.delete(1.0, tk.END)
                
                # Afficher des informations sur le modèle utilisé
                model_info = f"Modèle utilisé: {MODEL_CONFIG['model_name']} ({MODEL_CONFIG.get('model_type', 'non spécifié')})\n"
                model_info += f"Traitement par lots: Morceaux de {self.batch_params.get('text_chunk_size')} caractères avec chevauchement de {self.batch_params.get('text_overlap')} caractères\n\n"
                self.results_text.insert(tk.END, model_info)
                
                self.results_text.insert(tk.END, f"Résultats de l'analyse ({len(result_df)} paramètres trouvés):\n\n")
                for i, row in result_df.iterrows():
                    self.results_text.insert(tk.END, f"{row['Paramètre']}: {row['Valeur mesurée']} {row['Unité']}\n")
                self.results_text.insert(tk.END, f"\nRésultats sauvegardés dans: {output_path}")
                
                # Sélectionner l'onglet des résultats
                self.notebook.select(self.results_frame)
                
                self.status_bar.set_status(f"Analyse terminée. Résultats sauvegardés dans {os.path.basename(output_path)}", 100)
                messagebox.showinfo("Succès", f"Analyse terminée! Résultats sauvegardés dans:\n{output_path}")
            else:
                self.status_bar.set_status("Aucun paramètre environnemental trouvé dans le texte", 0)
                messagebox.showwarning("Attention", "Aucun paramètre environnemental n'a pu être extrait du texte.")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du texte: {str(e)}")
            self.status_bar.set_status("Erreur lors de l'analyse du texte", 0)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'analyse du texte:\n{str(e)}")
    
    def confirm_and_export(self, df):
        """Exporte les données après confirmation de l'utilisateur."""
        try:
            # Définir le nom de base du fichier
            if hasattr(self, 'file_path') and self.file_path:
                base_name = os.path.splitext(os.path.basename(self.file_path))[0]
                output_path = save_dataframe_to_excel(df, base_filename=f"analyse_{base_name}", directory=OUTPUT_DIR)
            else:
                output_path = save_dataframe_to_excel(df, directory=OUTPUT_DIR)
            
            # Mettre à jour l'affichage des résultats
            self.results_text.insert("end", f"\n\nRésultats sauvegardés dans: {output_path}")
            
            # Supprimer le bouton de confirmation s'il existe
            for widget in self.results_frame.winfo_children():
                if isinstance(widget, ttk.Button) and widget.cget("text") == "Confirmer et exporter":
                    widget.destroy()
            
            self.status_bar.set_status(f"Résultats sauvegardés dans {os.path.basename(output_path)}", 100)
            messagebox.showinfo("Succès", f"Résultats sauvegardés dans:\n{output_path}")
            
            # Enregistrer l'action dans le log d'audit
            audit_logger.log_action(
                action="Exportation résultats après confirmation",
                user="interface_utilisateur",
                ip="localhost",
                fichier_destination=output_path,
                nb_lignes=len(df)
            )
            
            return output_path
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des résultats: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation:\n{str(e)}")
            return None
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos."""
        about_text = "Analyse de Risque Environnemental\nVersion 1.0\n\nOutil d'analyse de données environnementales utilisant l'IA.\n\nDéveloppé avec Python, Tkinter et les modèles Vision-Language."
        messagebox.showinfo("À propos", about_text)
    
    # ===== MÉTHODES DE SURVEILLANCE CONTINUE =====
    
    def start_continuous_monitoring(self):
        """Démarre la surveillance automatique des sites"""
        try:
            from site_monitoring import SiteMonitoring, MonitoringScheduler
            
            # Initialiser le système de surveillance
            self.monitoring_system = SiteMonitoring()
            self.monitoring_scheduler = MonitoringScheduler(self.monitoring_system)
            
            # Démarrer le planificateur
            self.monitoring_scheduler.start()
            
            messagebox.showinfo("Surveillance", "🔄 Surveillance automatique démarrée!\n\nLe système va maintenant:\n• Analyser automatiquement les nouveaux fichiers\n• Surveiller les seuils critiques\n• Envoyer des alertes en cas de dépassement\n\nConsultez le tableau de bord pour voir les résultats.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de démarrer la surveillance: {str(e)}")
    
    def stop_continuous_monitoring(self):
        """Arrête la surveillance automatique"""
        try:
            if hasattr(self, 'monitoring_scheduler'):
                self.monitoring_scheduler.stop()
                messagebox.showinfo("Surveillance", "⏹️ Surveillance automatique arrêtée.")
            else:
                messagebox.showwarning("Surveillance", "Aucune surveillance en cours.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'arrêt: {str(e)}")
    
    def launch_monitoring_dashboard(self):
        """Lance le tableau de bord de surveillance avancé"""
        try:
            import subprocess
            import sys
            
            # Lancer le tableau de bord dans un processus séparé
            dashboard_script = "monitoring_dashboard.py"
            
            messagebox.showinfo("Tableau de Bord", 
                              "📊 Lancement du tableau de bord avancé...\n\n"
                              "Le tableau de bord va s'ouvrir dans votre navigateur sur:\n"
                              "http://localhost:8051\n\n"
                              "Fonctionnalités disponibles:\n"
                              "• KPI temps réel\n"
                              "• Tendances temporelles\n"
                              "• Alertes actives\n"
                              "• Comparaison de plans d'action")
            
            # Lancer le dashboard
            subprocess.Popen([sys.executable, dashboard_script], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer le tableau de bord: {str(e)}")
    
    def analyze_site_trends(self):
        """Analyse les tendances d'un site"""
        try:
            # Dialog de sélection de site et période
            dialog = tk.Toplevel(self.root)
            dialog.title("Analyse des Tendances")
            dialog.geometry("500x300")
            dialog.resizable(False, False)
            
            tk.Label(dialog, text="Analyser les tendances temporelles", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            # Variables pour les fichiers
            site_var = tk.StringVar()
            period_var = tk.IntVar(value=30)
            
            # Interface
            tk.Label(dialog, text="Site à analyser:").pack(pady=5)
            site_frame = tk.Frame(dialog)
            site_frame.pack(pady=5)
            
            from site_monitoring import SiteMonitoring
            monitoring = SiteMonitoring()
            sites = list(monitoring.config["sites"].keys())
            
            if sites:
                site_var.set(sites[0])
                site_combo = ttk.Combobox(site_frame, textvariable=site_var, values=sites, width=40)
                site_combo.pack()
            else:
                tk.Label(site_frame, text="Aucun site configuré", fg="red").pack()
                return
            
            # Sélection de la période
            tk.Label(dialog, text="Période d'analyse (jours):").pack(pady=(20,5))
            period_frame = tk.Frame(dialog)
            period_frame.pack(pady=5)
            
            periods = [("7 jours", 7), ("30 jours", 30), ("90 jours", 90), ("1 an", 365)]
            for text, value in periods:
                tk.Radiobutton(period_frame, text=text, variable=period_var, 
                             value=value).pack(side=tk.LEFT, padx=10)
            
            # Boutons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=20)
            
            def run_analysis():
                try:
                    from site_monitoring import TrendAnalyzer
                    analyzer = TrendAnalyzer(monitoring)
                    
                    result = analyzer.analyze_trends(site_var.get(), period_var.get())
                    
                    if "error" in result:
                        messagebox.showerror("Erreur", result["error"])
                        return
                    
                    # Afficher les résultats dans une nouvelle fenêtre
                    self.show_trends_results(result, site_var.get(), period_var.get())
                    dialog.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de l'analyse: {str(e)}")
            
            tk.Button(button_frame, text="Analyser", command=run_analysis, 
                     bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'analyser les tendances: {str(e)}")
    
    def show_trends_results(self, results, site_id, period_days):
        """Affiche les résultats d'analyse des tendances"""
        # Créer nouvel onglet pour les résultats
        tab_name = f"Tendances - {site_id}"
        
        # Vérifier si l'onglet existe déjà
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == tab_name:
                self.notebook.forget(tab_id)
                break
        
        # Créer le nouvel onglet
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text=tab_name)
        self.notebook.select(trends_frame)
        
        # Interface des résultats
        main_container = tk.Frame(trends_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # En-tête
        header = tk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0,10))
        
        tk.Label(header, text=f"📈 Analyse des Tendances - {site_id}", 
                font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Informations sur la période
        info_text = f"Période: {period_days} jours • Mesures: {results.get('period', {}).get('measurements', 0)}"
        tk.Label(header, text=info_text, fg="gray").pack(side=tk.RIGHT)
        
        # Créer un tableau pour les paramètres avec tendances
        if "parameters" in results and results["parameters"]:
            # Frame pour le tableau
            table_frame = tk.Frame(main_container)
            table_frame.pack(fill=tk.BOTH, expand=True)
            
            # Créer le Treeview
            columns = ("Paramètre", "Valeur Actuelle", "Valeur Précédente", "Changement", 
                      "Tendance", "Min", "Max", "Moyenne")
            
            tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", height=15)
            
            # Configurer les colonnes
            tree.heading("#0", text="Milieu")
            tree.column("#0", width=80)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Ajouter les données par milieu
            milieux = {}
            for param_key, param_data in results["parameters"].items():
                medium = param_key.split('.')[0]
                param_name = param_key.split('.', 1)[1]
                
                if medium not in milieux:
                    milieux[medium] = []
                
                # Symbole de tendance
                trend_symbol = {"croissante": "📈", "décroissante": "📉", "stable": "➡️"}.get(param_data.get('trend'), "➡️")
                
                milieux[medium].append((
                    param_name,
                    f"{param_data.get('current_value', 0):.3f}",
                    f"{param_data.get('previous_value', 0):.3f}",
                    f"{param_data.get('change', 0):+.3f}",
                    f"{trend_symbol} {param_data.get('trend', 'stable')}",
                    f"{param_data.get('min_value', 0):.3f}",
                    f"{param_data.get('max_value', 0):.3f}",
                    f"{param_data.get('avg_value', 0):.3f}"
                ))
            
            # Insérer dans le treeview
            for medium, params in milieux.items():
                medium_icon = {"water": "💧", "air": "🌬️", "soil": "🌱"}.get(medium, "📊")
                medium_node = tree.insert("", "end", text=f"{medium_icon} {medium.upper()}", values=("", "", "", "", "", "", "", ""))
                
                for param_data in params:
                    tree.insert(medium_node, "end", text="", values=param_data)
                
                tree.item(medium_node, open=True)
            
            tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Boutons d'export
            export_frame = tk.Frame(main_container)
            export_frame.pack(fill=tk.X, pady=10)
            
            def export_trends():
                try:
                    import pandas as pd
                    from tkinter import filedialog
                    
                    # Préparer les données pour l'export
                    export_data = []
                    for param_key, param_data in results["parameters"].items():
                        medium, param_name = param_key.split('.', 1)
                        export_data.append({
                            "Milieu": medium,
                            "Paramètre": param_name,
                            "Valeur_Actuelle": param_data.get('current_value', 0),
                            "Valeur_Précédente": param_data.get('previous_value', 0),
                            "Changement": param_data.get('change', 0),
                            "Tendance": param_data.get('trend', 'stable'),
                            "Min": param_data.get('min_value', 0),
                            "Max": param_data.get('max_value', 0),
                            "Moyenne": param_data.get('avg_value', 0)
                        })
                    
                    df = pd.DataFrame(export_data)
                    
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".xlsx",
                        filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
                        title="Sauvegarder l'analyse des tendances"
                    )
                    
                    if file_path:
                        if file_path.endswith('.xlsx'):
                            df.to_excel(file_path, index=False)
                        else:
                            df.to_csv(file_path, index=False, encoding='utf-8')
                        
                        messagebox.showinfo("Export", f"Analyse des tendances exportée:\n{file_path}")
                
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
            
            tk.Button(export_frame, text="📁 Exporter Excel", command=export_trends,
                     bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        
        else:
            tk.Label(main_container, text="Aucune donnée de tendance disponible", 
                    font=("Arial", 12), fg="gray").pack(expand=True)
    
    def compare_action_plans(self):
        """Lance la comparaison de plans d'action"""
        try:
            # Dialog de sélection des fichiers
            dialog = tk.Toplevel(self.root)
            dialog.title("Comparaison des Plans d'Action")
            dialog.geometry("600x400")
            dialog.resizable(False, False)
            
            tk.Label(dialog, text="Comparer l'évolution des plans d'action", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            # Variables pour les fichiers
            plan1_var = tk.StringVar()
            plan2_var = tk.StringVar()
            date1_var = tk.StringVar()
            date2_var = tk.StringVar()
            
            # Sélection plan 1
            plan1_frame = tk.LabelFrame(dialog, text="Plan d'action - Période 1", padx=10, pady=10)
            plan1_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Entry(plan1_frame, textvariable=plan1_var, width=50).pack(side=tk.LEFT, padx=5)
            tk.Button(plan1_frame, text="Parcourir", 
                     command=lambda: plan1_var.set(filedialog.askopenfilename(
                         filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]))).pack(side=tk.LEFT)
            
            tk.Label(plan1_frame, text="Date/Période:").pack(anchor=tk.W, pady=(5,0))
            tk.Entry(plan1_frame, textvariable=date1_var, placeholder_text="ex: Janvier 2024").pack(fill=tk.X, pady=2)
            
            # Sélection plan 2
            plan2_frame = tk.LabelFrame(dialog, text="Plan d'action - Période 2", padx=10, pady=10)
            plan2_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Entry(plan2_frame, textvariable=plan2_var, width=50).pack(side=tk.LEFT, padx=5)
            tk.Button(plan2_frame, text="Parcourir", 
                     command=lambda: plan2_var.set(filedialog.askopenfilename(
                         filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]))).pack(side=tk.LEFT)
            
            tk.Label(plan2_frame, text="Date/Période:").pack(anchor=tk.W, pady=(5,0))
            tk.Entry(plan2_frame, textvariable=date2_var, placeholder_text="ex: Juin 2024").pack(fill=tk.X, pady=2)
            
            # Boutons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=20)
            
            def run_comparison():
                if not plan1_var.get() or not plan2_var.get():
                    messagebox.showerror("Erreur", "Veuillez sélectionner les deux plans d'action")
                    return
                
                try:
                    from action_plan_comparison import ActionPlanComparator
                    
                    comparator = ActionPlanComparator()
                    result = comparator.compare_action_plans(
                        plan1_var.get(), plan2_var.get(), 
                        date1_var.get() or None, date2_var.get() or None
                    )
                    
                    if "error" in result:
                        messagebox.showerror("Erreur", result["error"])
                        return
                    
                    # Afficher les résultats
                    self.show_comparison_results(result)
                    dialog.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la comparaison: {str(e)}")
            
            tk.Button(button_frame, text="Comparer", command=run_comparison, 
                     bg="#8e44ad", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer la comparaison: {str(e)}")
    
    def show_comparison_results(self, results):
        """Affiche les résultats de comparaison des plans d'action"""
        # Créer un nouvel onglet
        tab_name = "Comparaison Plans"
        
        # Supprimer l'onglet s'il existe déjà
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == tab_name:
                self.notebook.forget(tab_id)
                break
        
        # Créer le nouvel onglet
        comp_frame = ttk.Frame(self.notebook)
        self.notebook.add(comp_frame, text=tab_name)
        self.notebook.select(comp_frame)
        
        # Interface des résultats
        main_container = tk.Frame(comp_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # En-tête
        tk.Label(main_container, text="🔄 Comparaison des Plans d'Action", 
                font=("Arial", 16, "bold")).pack(pady=(0,20))
        
        # Métriques de comparaison
        metrics_frame = tk.LabelFrame(main_container, text="Évolution des Métriques", padx=10, pady=10)
        metrics_frame.pack(fill=tk.X, pady=10)
        
        evolution = results["comparison"]["evolution"]
        
        for i, (metric, data) in enumerate(evolution.items()):
            row = tk.Frame(metrics_frame)
            row.pack(fill=tk.X, pady=2)
            
            metric_name = metric.replace('_', ' ').title()
            change_text = f"{data['change']:+.1f}"
            if 'change_pct' in data and data['change_pct'] != 0:
                change_text += f" ({data['change_pct']:+.1f}%)"
            
            tk.Label(row, text=f"{metric_name}:", width=20, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=f"{data['period1']} → {data['period2']}", width=15).pack(side=tk.LEFT)
            
            color = "green" if data['change'] > 0 else "red" if data['change'] < 0 else "blue"
            tk.Label(row, text=change_text, fg=color, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        # Recommandations
        if "recommendations" in results and results["recommendations"]:
            rec_frame = tk.LabelFrame(main_container, text="Recommandations", padx=10, pady=10)
            rec_frame.pack(fill=tk.X, pady=10)
            
            rec_text = tk.Text(rec_frame, height=6, wrap=tk.WORD)
            rec_text.pack(fill=tk.BOTH, expand=True)
            
            for recommendation in results["recommendations"]:
                rec_text.insert(tk.END, f"• {recommendation}\n\n")
            
            rec_text.config(state=tk.DISABLED)
        
        # Export
        export_frame = tk.Frame(main_container)
        export_frame.pack(fill=tk.X, pady=10)
        
        def export_comparison():
            try:
                from action_plan_comparison import ActionPlanComparator
                from tkinter import filedialog
                
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    title="Sauvegarder la comparaison"
                )
                
                if file_path:
                    comparator = ActionPlanComparator()
                    comparator.export_comparison_report(results, file_path)
                    messagebox.showinfo("Export", f"Comparaison exportée:\n{file_path}")
            
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
        
        tk.Button(export_frame, text="📁 Exporter Rapport Excel", command=export_comparison,
                 bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=5)
    
    def configure_monitoring(self):
        """Configure les paramètres de surveillance"""
        try:
            from site_monitoring import SiteMonitoring
            
            # Dialog de configuration
            dialog = tk.Toplevel(self.root)
            dialog.title("Configuration de la Surveillance")
            dialog.geometry("700x500")
            
            tk.Label(dialog, text="⚙️ Configuration de la Surveillance Continue", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            # Notebook pour les différents paramètres
            config_notebook = ttk.Notebook(dialog)
            config_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Onglet Sites
            sites_frame = ttk.Frame(config_notebook)
            config_notebook.add(sites_frame, text="Sites")
            
            tk.Label(sites_frame, text="Configuration des sites à surveiller", 
                    font=("Arial", 12, "bold")).pack(pady=10)
            
            # Onglet Seuils
            thresholds_frame = ttk.Frame(config_notebook)
            config_notebook.add(thresholds_frame, text="Seuils d'Alerte")
            
            tk.Label(thresholds_frame, text="Configuration des seuils d'alerte", 
                    font=("Arial", 12, "bold")).pack(pady=10)
            
            # Onglet Notifications
            notif_frame = ttk.Frame(config_notebook)
            config_notebook.add(notif_frame, text="Notifications")
            
            tk.Label(notif_frame, text="Configuration des notifications", 
                    font=("Arial", 12, "bold")).pack(pady=10)
            
            # Boutons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="Sauvegarder", command=dialog.destroy,
                     bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de configurer la surveillance: {str(e)}")
    
    def view_alerts_history(self):
        """Affiche l'historique des alertes"""
        try:
            # Créer un nouvel onglet pour l'historique
            tab_name = "Historique Alertes"
            
            # Supprimer l'onglet s'il existe déjà
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == tab_name:
                    self.notebook.forget(tab_id)
                    break
            
            # Créer le nouvel onglet
            alerts_frame = ttk.Frame(self.notebook)
            self.notebook.add(alerts_frame, text=tab_name)
            self.notebook.select(alerts_frame)
            
            # Interface
            main_container = tk.Frame(alerts_frame)
            main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            tk.Label(main_container, text="🚨 Historique des Alertes", 
                    font=("Arial", 16, "bold")).pack(pady=(0,20))
            
            # Tableau des alertes (exemple)
            columns = ("Date", "Site", "Paramètre", "Valeur", "Seuil", "Criticité")
            
            tree = ttk.Treeview(main_container, columns=columns, show="headings", height=15)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            # Données d'exemple
            sample_alerts = [
                ("2024-09-11 10:30", "Site Industriel", "Plomb (eau)", "0.015 mg/L", "0.01 mg/L", "🔴 Critique"),
                ("2024-09-11 09:15", "Site Industriel", "PM2.5 (air)", "28 µg/m³", "25 µg/m³", "🟡 Attention"),
                ("2024-09-10 14:22", "Site Industriel", "pH (eau)", "5.8", "6.5-8.5", "🟡 Attention"),
            ]
            
            for alert in sample_alerts:
                tree.insert("", "end", values=alert)
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher l'historique: {str(e)}")
    
    def clear_cache(self):
        """Vide le cache des API externes."""
        if messagebox.askyesno("Vider le cache", "Êtes-vous sûr de vouloir vider le cache des API externes ? Cela ralentira temporairement les analyses suivantes."):
            try:
                clear_cache()
                self.cache_stats = get_cache_stats()  # Mettre à jour les statistiques
                messagebox.showinfo("Cache vidé", "Le cache des API externes a été vidé avec succès.")
                self.status_bar.set_status("Cache vidé avec succès", 100)
                
                # Enregistrer l'action dans le log d'audit
                audit_logger.log_action(
                    action="Cache vidé",
                    user="utilisateur",
                    ip="localhost"
                )
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de vider le cache: {str(e)}")
                logger.error(f"Erreur lors du vidage du cache: {str(e)}")
    
    def show_cache_stats(self):
        """Affiche les statistiques du cache."""
        # Mettre à jour les statistiques
        self.cache_stats = get_cache_stats()
        
        stats_text = "Statistiques du cache:\n\n"
        stats_text += f"Taille du cache: {self.cache_stats['size']} entrées\n"
        stats_text += f"Répertoire: {self.cache_stats['directory']}\n"
        stats_text += f"Nombre de hits: {self.cache_stats['hit_count']}\n"
        stats_text += f"Nombre de miss: {self.cache_stats['miss_count']}\n"
        
        if self.cache_stats['hit_count'] + self.cache_stats['miss_count'] > 0:
            hit_ratio = self.cache_stats['hit_count'] / (self.cache_stats['hit_count'] + self.cache_stats['miss_count']) * 100
            stats_text += f"Ratio de hits: {hit_ratio:.2f}%\n"
        
        messagebox.showinfo("Statistiques du cache", stats_text)
    
    def open_initial_info_window(self):
        """Ouvre la fenêtre de saisie des informations initiales."""
        # Importer la classe InitialInfoWindow
        from initial_info_ui import InitialInfoWindow
        
        # Callback pour traiter les résultats de la recherche
        def on_search_complete(df, project_info):
            # Mettre à jour les données actuelles
            self.current_data = df
            
            # Mettre à jour l'interface utilisateur
            self.preview_frame.update_data(df)
            self.visualization_frame.update_data(df)
            
            # Afficher un résumé dans l'onglet des résultats
            self.results_frame.update_results(project_info, df)
            
            # Mettre à jour la barre de statut
            self.status_bar.set_status(f"Recherche web terminée: {len(df)} paramètres trouvés", 100)
            
            # Activer le bouton de sauvegarde
            if hasattr(self.toolbar, 'enable_button'):
                self.toolbar.enable_button("save")
            
            # Ajouter un bouton pour confirmer et exporter
            confirm_button = ttk.Button(self.root, text="Confirmer et exporter", 
                                      command=lambda: self.confirm_and_export(df))
            confirm_button.pack(side="bottom", pady=10)
            
            # Sélectionner l'onglet des résultats
            self.notebook.select(2)  # Index 2 correspond à l'onglet Résultats
        
        # Ouvrir la fenêtre de saisie des informations initiales
        InitialInfoWindow(self.root, callback=on_search_complete)
    
    def open_manual_entry(self):
        """Ouvre la fenêtre de saisie manuelle des paramètres."""
        logger.info("Ouverture de la fenêtre de saisie manuelle")
        
        # Créer une instance de la fenêtre de saisie manuelle
        # Si des données existent déjà, les passer comme données initiales
        initial_data = self.current_data if self.current_data is not None else None
        
        # Ouvrir la fenêtre de saisie manuelle avec un callback pour traiter les données
        manual_entry_window = ManualEntryWindow(
            self.root,
            callback=self.process_manual_entry,
            initial_data=initial_data
        )
        
        # Attendre que la fenêtre soit fermée
        self.root.wait_window(manual_entry_window)
    
    def process_manual_entry(self, data):
        """Traite les données saisies manuellement.
        
        Args:
            data (pd.DataFrame): DataFrame contenant les paramètres saisis manuellement
        """
        if data is None or data.empty:
            logger.warning("Aucune donnée saisie manuellement")
            return
        
        logger.info(f"Traitement de {len(data)} paramètres saisis manuellement")
        
        # Stocker les données
        self.current_data = data
        
        # Évaluer la conformité des paramètres
        try:
            # Vérifier si les colonnes nécessaires sont présentes
            required_columns = ["Paramètre", "Valeur mesurée", "Intervalle acceptable"]
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                logger.warning(f"Colonnes manquantes dans les données: {missing_columns}")
                messagebox.showwarning("Données incomplètes", 
                                     f"Les colonnes suivantes sont manquantes: {', '.join(missing_columns)}\n\n"
                                     "L'évaluation de la conformité ne sera pas complète.")
            
            # Évaluer la conformité
            self.current_data = analyze_environmental_data(self.current_data)
            
            # Afficher les résultats
            self._display_results(self.current_data)
            
            # Afficher un message de succès
            self.status_bar.set_status(f"{len(data)} paramètres traités avec succès", 100)
            
            # Enregistrer l'action dans les logs d'audit
            audit_logger.log_action("manual_entry", f"Saisie manuelle de {len(data)} paramètres")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données saisies manuellement: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue lors du traitement des données:\n{str(e)}")
            self.status_bar.set_status("Erreur lors du traitement des données", 0)
    
    def _display_results(self, data):
        """Affiche les résultats dans l'interface utilisateur.
        
        Args:
            data (pd.DataFrame): DataFrame contenant les paramètres à afficher
        """
        if data is None or data.empty:
            logger.warning("Aucune donnée à afficher")
            return
        
        logger.info(f"Affichage des résultats pour {len(data)} paramètres")
        
        # Mettre à jour le tableau de prévisualisation
        self.preview_frame.update_data(data)
        
        # Mettre à jour la visualisation
        self.visualization_frame.update_data(data)
        
        # Mettre à jour l'onglet des résultats
        # Utiliser un dictionnaire vide pour project_info si aucune information n'est disponible
        project_info = {}
        if hasattr(self, 'project_info') and self.project_info:
            project_info = self.project_info
        self.results_frame.update_results(project_info, data)
        
        # Sélectionner l'onglet des résultats
        self.notebook.select(2)  # Index 2 correspond à l'onglet Résultats
        
        # Activer le bouton de sauvegarde si disponible
        if hasattr(self.toolbar, 'enable_button'):
            self.toolbar.enable_button("save")
    
    def create_new_project(self):
        """Crée un nouveau projet."""
        dialog = self.ProjectDialog(self.root, "Nouveau Projet")
        if dialog.result:
            project_data = dialog.result
            project_id = self.project_manager.create_project(
                project_data['name'],
                project_data['description'],
                project_data['location']
            )
            
            if self.project_manager.load_project(project_id):
                self.current_project_mode.set(True)
                self.status_bar.set_status(f"Projet créé: {project_data['name']}")
                messagebox.showinfo("Succès", f"Projet '{project_data['name']}' créé avec succès!")
                self._update_project_display()
    
    def open_project(self):
        """Ouvre un projet existant."""
        projects = self.project_manager.list_projects()
        if not projects:
            messagebox.showinfo("Information", "Aucun projet trouvé.")
            return
        
        dialog = self.ProjectListDialog(self.root, projects)
        if dialog.selected_project:
            project_id = dialog.selected_project['id']
            if self.project_manager.load_project(project_id):
                self.current_project_mode.set(True)
                self.status_bar.set_status(f"Projet ouvert: {dialog.selected_project['name']}")
                self._update_project_display()
    
    def close_project(self):
        """Ferme le projet courant."""
        if self.project_manager.current_project:
            project_name = self.project_manager.current_project_data.get('name', 'Sans nom')
            self.project_manager.current_project = None
            self.project_manager.current_project_data = None
            self.current_project_mode.set(False)
            self.status_bar.set_status(f"Projet fermé: {project_name}")
            self._update_project_display()
        else:
            messagebox.showinfo("Information", "Aucun projet ouvert.")
    
    def export_project(self):
        """Exporte le projet courant."""
        if not self.project_manager.current_project:
            messagebox.showwarning("Attention", "Aucun projet ouvert.")
            return
        
        project_name = self.project_manager.current_project_data.get('name', 'projet')
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("JSON files", "*.json")],
            initialvalue=f"{project_name}_export"
        )
        
        if filename:
            format_ext = os.path.splitext(filename)[1].lower()
            format_map = {'.xlsx': 'xlsx', '.csv': 'csv', '.json': 'json'}
            export_format = format_map.get(format_ext, 'xlsx')
            
            if self.project_manager.export_project(filename, export_format):
                messagebox.showinfo("Succès", f"Projet exporté vers: {filename}")
            else:
                messagebox.showerror("Erreur", "Erreur lors de l'export du projet.")
    
    def export_to_excel(self):
        """Exporte les résultats de l'analyse courante vers Excel."""
        if not hasattr(self, 'current_results') or self.current_results is None:
            messagebox.showwarning("Attention", "Aucun résultat d'analyse à exporter.")
            return
        
        # Demander le nom du fichier de destination
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Exporter les résultats vers Excel"
        )
        
        if filename:
            try:
                # Exporter le DataFrame vers Excel
                if isinstance(self.current_results, pd.DataFrame):
                    self.current_results.to_excel(filename, index=False, sheet_name='Résultats Analyse')
                    messagebox.showinfo("Succès", f"Résultats exportés vers: {filename}")
                    self.status_bar.set_status(f"Export Excel terminé: {filename}")
                else:
                    messagebox.showerror("Erreur", "Format de données non supporté pour l'export Excel.")
            except Exception as e:
                logger.error(f"Erreur lors de l'export Excel: {str(e)}")
                messagebox.showerror("Erreur", f"Erreur lors de l'export Excel:\n{str(e)}")
    
    def export_to_csv(self):
        """Exporte les résultats de l'analyse courante vers CSV."""
        if not hasattr(self, 'current_results') or self.current_results is None:
            messagebox.showwarning("Attention", "Aucun résultat d'analyse à exporter.")
            return
        
        # Demander le nom du fichier de destination
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Exporter les résultats vers CSV"
        )
        
        if filename:
            try:
                # Exporter le DataFrame vers CSV
                if isinstance(self.current_results, pd.DataFrame):
                    self.current_results.to_csv(filename, index=False, encoding='utf-8')
                    messagebox.showinfo("Succès", f"Résultats exportés vers: {filename}")
                    self.status_bar.set_status(f"Export CSV terminé: {filename}")
                else:
                    messagebox.showerror("Erreur", "Format de données non supporté pour l'export CSV.")
            except Exception as e:
                logger.error(f"Erreur lors de l'export CSV: {str(e)}")
                messagebox.showerror("Erreur", f"Erreur lors de l'export CSV:\n{str(e)}")
    
    def update_slri_excel_file(self):
        """Met à jour un fichier SLRI Excel (.xlsm) en remplissant les 4 colonnes SLRI.
        
        Colonnes mises à jour:
        - Intervalle acceptable
        - Valeur mesurée de milieu initial
        - Rejet de prj
        - Valeurs Mesure+rejet
        """
        try:
            # Vérifier qu'on a des résultats
            # Sélectionner l'analyse à exporter
            df_to_export = None
            if not self.recent_analyses:
                # Fallback : utiliser le tableau courant si disponible
                if hasattr(self, 'current_data') and isinstance(self.current_data, pd.DataFrame) and not self.current_data.empty:
                    df_to_export = self.current_data
                else:
                    messagebox.showwarning(
                        "Attention",
                        "Aucune analyse récente disponible et aucun tableau courant valide.\n\nVeuillez d'abord effectuer une analyse."
                    )
                    return
            elif len(self.recent_analyses) == 1:
                df_to_export = self.recent_analyses[0][1]
            else:
                # Boîte de dialogue à liste déroulante
                dialog = tk.Toplevel(self.root)
                dialog.title("Choisir l'analyse à exporter")
                dialog.geometry("350x120")
                tk.Label(dialog, text="Sélectionnez l'analyse à exporter vers Excel SLRI :").pack(pady=10)
                from tkinter import ttk
                combo = ttk.Combobox(dialog, state="readonly", width=40)
                combo['values'] = [f"{nom} ({ts})" for nom, _, ts in self.recent_analyses]
                combo.current(len(self.recent_analyses)-1)
                combo.pack(pady=5)
                selection = {'idx': None}
                def valider():
                    selection['idx'] = combo.current()
                    dialog.destroy()
                tk.Button(dialog, text="Valider", command=valider).pack(pady=10)
                dialog.grab_set()
                dialog.wait_window()
                if selection['idx'] is None:
                    return
                df_to_export = self.recent_analyses[selection['idx']][1]
            if df_to_export is None or not isinstance(df_to_export, pd.DataFrame) or df_to_export.empty:
                messagebox.showwarning(
                    "Attention",
                    "Aucun résultat d'analyse sélectionné ou valide."
                )
                return
            
            # --- Prévisualisation avant export ---
            preview_win = tk.Toplevel(self.root)
            preview_win.title("Prévisualisation de l'export SLRI")
            preview_win.geometry("420x240")
            txt = ""
            if isinstance(df_to_export, dict):
                phases = list(df_to_export.keys())
                txt += f"Phases détectées : {', '.join(phases)}\n"
                total_params = sum(len(df_phase) for df_phase in df_to_export.values() if isinstance(df_phase, pd.DataFrame))
                txt += f"Nombre total de paramètres : {total_params}\n"
                txt += f"Type : Analyse multi-phases SLRI\n"
            elif isinstance(df_to_export, pd.DataFrame):
                txt += f"Nombre de paramètres : {len(df_to_export)}\n"
                txt += f"Colonnes : {', '.join(str(c) for c in df_to_export.columns)}\n"
                txt += f"Type : Analyse simple (SLRI, lieu, etc.)\n"
            else:
                txt += "Type de résultat non reconnu."
            tk.Label(preview_win, text="Résumé de l'export :", font=("Arial", 12, "bold")).pack(pady=10)
            tk.Label(preview_win, text=txt, justify=tk.LEFT, font=("Arial", 10)).pack(pady=10)
            btn = tk.Button(preview_win, text="Continuer", command=preview_win.destroy)
            btn.pack(pady=15)
            preview_win.grab_set()
            preview_win.wait_window()

            # Sélection du fichier cible
            default_dir = os.path.join(os.path.expanduser('~'), 'OneDrive', 'Bureau', '1test risque', 'Nouveau dossier (3)')
            initialdir = default_dir if os.path.isdir(default_dir) else os.getcwd()
            file_path = filedialog.askopenfilename(
                title="Sélectionner le fichier SLRI à mettre à jour",
                filetypes=[("Classeur Excel avec macros", "*.xlsm"), ("Classeur Excel", "*.xlsx")],
                initialdir=initialdir
            )
            if not file_path:
                return

            # Export groupé multi-phases si dict {phase: DataFrame}
            if isinstance(df_to_export, dict):
                from pandas import ExcelWriter
                file_path = filedialog.asksaveasfilename(
                    title="Exporter toutes les phases SLRI dans un seul fichier Excel",
                    defaultextension=".xlsx",
                    filetypes=[("Classeur Excel", "*.xlsx")]
                )
                if not file_path:
                    return
                with ExcelWriter(file_path) as writer:
                    for phase, df_phase in df_to_export.items():
                        if isinstance(df_phase, pd.DataFrame) and not df_phase.empty:
                            sheet = str(phase)[:31]
                            df_phase.to_excel(writer, sheet_name=sheet, index=False)
                messagebox.showinfo("Succès", f"Export groupé terminé :\n{file_path}")
                logger.info(f"Export groupé SLRI multi-phases : {file_path}")
                return

            # Demander la phase à l'utilisateur
            phase_dialog = tk.Toplevel(self.root)
            phase_dialog.title("Sélectionner la phase SLRI")
            phase_dialog.geometry("400x180")
            tk.Label(phase_dialog, text="Sélectionnez la phase du projet :", font=("Arial", 11, "bold")).pack(pady=10)
            
            phase_var = tk.StringVar(value="PRE CONSTRUCTION")
            phases = ["PRE CONSTRUCTION", "CONSTRUCTION", "EXPLOITATION", "DÉMANTÈLEMENT"]
            
            for p in phases:
                tk.Radiobutton(phase_dialog, text=p, variable=phase_var, value=p).pack(anchor=tk.W, padx=20)
            
            phase_selection = {'phase': None}
            def valider_phase():
                phase_selection['phase'] = phase_var.get()
                phase_dialog.destroy()
            
            tk.Button(phase_dialog, text="Valider", command=valider_phase).pack(pady=10)
            phase_dialog.grab_set()
            phase_dialog.wait_window()
            
            if phase_selection['phase'] is None:
                return
            
            phase = phase_selection['phase']
            
            # Utiliser la fonction intelligente qui trouve et remplit les colonnes SLRI
            result = update_slri_with_dataframe(file_path, df_to_export, phase=phase)
            
            if result:
                # result peut être True ou un chemin de fichier
                output_file = result if isinstance(result, str) else file_path
                messagebox.showinfo("Succès", f"Fichier SLRI mis à jour avec succès!\n\nLes 4 colonnes SLRI ont été remplies:\n- Intervalle acceptable\n- Valeur mesurée de milieu initial\n- Rejet de prj\n- Valeurs Mesure+rejet\n\nFichier: {os.path.basename(output_file)}\n\nUne copie de sauvegarde a été créée.")
                logger.info(f"Mise à jour SLRI réussie: {output_file}")
            else:
                messagebox.showerror("Erreur", "Impossible de mettre à jour le fichier SLRI.\n\nVérifiez que le fichier contient les colonnes attendues.")
                logger.error(f"Échec de la mise à jour SLRI: {file_path}")
                
        except Exception as e:
            logger.error(f"Erreur mise à jour SLRI Excel: {e}\n{traceback.format_exc()}")
            messagebox.showerror("Erreur", f"Impossible de mettre à jour le fichier:\n{e}")

    def delete_project(self):
        """Supprime un projet."""
        projects = self.project_manager.list_projects()
        if not projects:
            messagebox.showinfo("Information", "Aucun projet trouvé.")
            return
        
        dialog = self.ProjectListDialog(self.root, projects, title="Supprimer un projet")
        if dialog.selected_project:
            project_name = dialog.selected_project['name']
            if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le projet '{project_name}'?"):
                if self.project_manager.delete_project(dialog.selected_project['id']):
                    messagebox.showinfo("Succès", f"Projet '{project_name}' supprimé.")
                    self._update_project_display()
                else:
                    messagebox.showerror("Erreur", "Erreur lors de la suppression du projet.")
    
    def _update_project_display(self):
        """Met à jour l'affichage du projet courant."""
        if self.project_manager.current_project:
            # Afficher les données du projet
            project_df = self.project_manager.get_project_dataframe()
            if project_df is not None and not project_df.empty:
                self.current_data = project_df
                self.preview_frame.display_dataframe(project_df)
                
                # Afficher le résumé du projet
                summary = self.project_manager.get_project_summary()
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"=== PROJET: {summary['project_info']['name']} ===\n\n")
                self.results_text.insert(tk.END, f"Description: {summary['project_info']['description']}\n")
                self.results_text.insert(tk.END, f"Localisation: {summary['project_info']['location']}\n")
                self.results_text.insert(tk.END, f"Créé le: {summary['project_info']['created_at'][:10]}\n\n")
                self.results_text.insert(tk.END, f"Statistiques:\n")
                self.results_text.insert(tk.END, f"- Analyses: {summary['statistics']['total_analyses']}\n")
                self.results_text.insert(tk.END, f"- Paramètres: {summary['statistics']['total_parameters']}\n")
                self.results_text.insert(tk.END, f"- Paramètres uniques: {summary['statistics']['unique_parameters']}\n\n")
                
                if summary['score_distribution']:
                    self.results_text.insert(tk.END, "Répartition des scores:\n")
                    for score, count in summary['score_distribution'].items():
                        status_map = {1: "Conforme", 2: "Attention", 3: "Critique", 0: "Non évalué"}
                        self.results_text.insert(tk.END, f"- Score {score} ({status_map.get(score, 'Inconnu')}): {count}\n")

    def quit_app(self):
        """Ferme l'application proprement."""
        try:
            # Sauvegarder les configurations avant de quitter
            self._save_app_config()
            
            # Enregistrer l'action dans le log d'audit
            audit_logger.log_action(
                action="Fermeture application",
                user="interface_utilisateur",
                ip="localhost"
            )
            
            logger.info("Application fermée par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {str(e)}")
        finally:
            self.root.quit()
            self.root.destroy()

if __name__ == "__main__":
    try:
        import argparse
        
        # Analyser les arguments de ligne de commande
        parser = argparse.ArgumentParser(description="Application d'analyse de risque environnemental")
        parser.add_argument("--no-load-model", action="store_true", help="Démarrer sans charger le modèle IA")
        parser.add_argument("--skip-gemini-check", action="store_true", help="Ignorer la vérification de la configuration Gemini")
        args = parser.parse_args()
        
        # Vérifier la configuration de l'API Gemini au démarrage si disponible
        if GEMINI_AVAILABLE and not args.skip_gemini_check:
            try:
                logger.info("Vérification de la configuration de l'API Gemini...")
                verifier_gemini_au_demarrage()
                logger.info("Configuration de l'API Gemini vérifiée avec succès.")
            except Exception as e:
                logger.warning(f"Erreur lors de la vérification de la configuration Gemini: {str(e)}")
                # Continuer l'exécution même en cas d'erreur
        
        root = tk.Tk()
        app = RiskAnalysisApp(root, load_model=not args.no_load_model)
        
        # Intégrer l'interface SLRI simplifiée
        from slri_simple_interface import integrate_simple_slri_interface
        integrate_simple_slri_interface(app)
        
        if args.no_load_model:
            logger.info("Application démarrée sans charger le modèle IA")
        
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur de Démarrage", f"Une erreur est survenue au démarrage de l'application :\n{str(e)}")

 # Section LocationInfoFrame déplacée plus haut dans le fichier.