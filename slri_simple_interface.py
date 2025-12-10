import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configuration du logger
logger = logging.getLogger(__name__)

class SLRISimpleInterface:
    """Interface simplifiée pour l'analyse SLRI"""
    
    def __init__(self, parent):
        self.parent = parent
        self.coordinates = {"lat": None, "lon": None}
        self.selected_file = None
        self.analysis_mode = tk.StringVar(value="coordinates")
        
    def create_interface(self, container):
        """Crée l'interface simplifiée SLRI"""
        # Canvas et scrollbar pour permettre le défilement
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
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
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Bind mousewheel pour le défilement
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Titre
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(title_frame, text="🌍 Analyse SLRI Environnementale", 
                 font=("Arial", 18, "bold")).pack(side="left")
        
        # Description
        desc_text = ("Analyse rapide des risques environnementaux selon la méthodologie SLRI.\n"
                    "Choisissez votre méthode d'analyse ci-dessous.")
        ttk.Label(main_frame, text=desc_text, font=("Arial", 10), 
                 foreground="gray").pack(anchor="w", pady=(0, 20))
        
        # Mode d'analyse
        mode_frame = ttk.LabelFrame(main_frame, text="Méthode d'Analyse", padding=15)
        mode_frame.pack(fill="x", pady=(0, 20))
        
        # Option 1: Coordonnées géographiques
        coord_frame = ttk.Frame(mode_frame)
        coord_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Radiobutton(coord_frame, text="📍 Analyse par coordonnées géographiques", 
                       variable=self.analysis_mode, value="coordinates",
                       command=self._toggle_mode).pack(anchor="w")
        
        # Sous-frame pour les coordonnées
        self.coord_input_frame = ttk.Frame(coord_frame)
        self.coord_input_frame.pack(fill="x", padx=20, pady=10)
        
        # Latitude
        lat_frame = ttk.Frame(self.coord_input_frame)
        lat_frame.pack(fill="x", pady=2)
        ttk.Label(lat_frame, text="Latitude:", width=12).pack(side="left")
        self.lat_entry = ttk.Entry(lat_frame, width=15)
        self.lat_entry.pack(side="left", padx=(5, 10))
        ttk.Label(lat_frame, text="(ex: 33.5731)", font=("Arial", 8), 
                 foreground="gray").pack(side="left")
        
        # Longitude
        lon_frame = ttk.Frame(self.coord_input_frame)
        lon_frame.pack(fill="x", pady=2)
        ttk.Label(lon_frame, text="Longitude:", width=12).pack(side="left")
        self.lon_entry = ttk.Entry(lon_frame, width=15)
        self.lon_entry.pack(side="left", padx=(5, 10))
        ttk.Label(lon_frame, text="(ex: -7.5898)", font=("Arial", 8), 
                 foreground="gray").pack(side="left")
        
        # Option 2: Fichier d'entrée
        file_frame = ttk.Frame(mode_frame)
        file_frame.pack(fill="x")
        
        ttk.Radiobutton(file_frame, text="📄 Analyse à partir d'un fichier", 
                       variable=self.analysis_mode, value="file",
                       command=self._toggle_mode).pack(anchor="w")
        
        # Sous-frame pour le fichier
        self.file_input_frame = ttk.Frame(file_frame)
        self.file_input_frame.pack(fill="x", padx=20, pady=10)
        
        file_select_frame = ttk.Frame(self.file_input_frame)
        file_select_frame.pack(fill="x")
        
        self.file_label = ttk.Label(file_select_frame, text="Aucun fichier sélectionné", 
                                   foreground="gray")
        self.file_label.pack(side="left", fill="x", expand=True)
        
        ttk.Button(file_select_frame, text="Parcourir...", 
                  command=self._select_file).pack(side="right")
        
        # Sélection des phases
        phases_frame = ttk.LabelFrame(main_frame, text="Phases d'Analyse", padding=15)
        phases_frame.pack(fill="x", pady=(0, 20))
        
        # Statut du projet
        status_frame = ttk.Frame(phases_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(status_frame, text="Statut actuel du projet:", 
                 font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.project_status = tk.StringVar(value="pre_construction")
        status_options = [
            ("🔍 Pré-construction (études)", "pre_construction"),
            ("🏗️ Construction en cours", "construction"),
            ("⚡ Exploitation active", "exploitation"),
            ("🔄 Démantèlement", "demantelement")
        ]
        
        for text, value in status_options:
            ttk.Radiobutton(status_frame, text=text, variable=self.project_status, 
                           value=value, command=self._update_phase_selection).pack(anchor="w", pady=1)
        
        # Phases sélectionnées automatiquement
        self.phases_info_frame = ttk.Frame(phases_frame)
        self.phases_info_frame.pack(fill="x", pady=10)
        
        self.phases_label = ttk.Label(self.phases_info_frame, text="", 
                                     font=("Arial", 9), foreground="blue")
        self.phases_label.pack(anchor="w")
        
        # Bouton d'analyse
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        self.analyze_button = ttk.Button(button_frame, text="🚀 Lancer l'Analyse SLRI", 
                                        command=self._start_analysis,
                                        style="Accent.TButton")
        self.analyze_button.pack(side="right", padx=(10, 0))
        
        ttk.Button(button_frame, text="📋 Aide", 
                  command=self._show_help).pack(side="left")
        
        # Initialiser l'interface
        self._toggle_mode()
        self._update_phase_selection()
        
    def _toggle_mode(self):
        """Active/désactive les champs selon le mode sélectionné"""
        mode = self.analysis_mode.get()
        
        if mode == "coordinates":
            # Activer les coordonnées
            for widget in self.coord_input_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Entry):
                        child.config(state="normal")
            
            # Désactiver le fichier
            for widget in self.file_input_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(state="disabled")
        else:
            # Désactiver les coordonnées
            for widget in self.coord_input_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Entry):
                        child.config(state="disabled")
            
            # Activer le fichier
            for widget in self.file_input_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(state="normal")
    
    def _select_file(self):
        """Sélectionne un fichier pour l'analyse"""
        filetypes = [
            ("Tous les fichiers supportés", "*.pdf *.xlsx *.xls *.csv *.txt"),
            ("Fichiers PDF", "*.pdf"),
            ("Fichiers Excel", "*.xlsx *.xls"),
            ("Fichiers CSV", "*.csv"),
            ("Fichiers texte", "*.txt"),
            ("Tous les fichiers", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier à analyser",
            filetypes=filetypes
        )
        
        if filename:
            self.selected_file = filename
            # Afficher seulement le nom du fichier
            file_name = os.path.basename(filename)
            self.file_label.config(text=f"📄 {file_name}", foreground="black")
        else:
            self.selected_file = None
            self.file_label.config(text="Aucun fichier sélectionné", foreground="gray")
    
    def _update_phase_selection(self):
        """Met à jour la sélection des phases selon le statut du projet"""
        status = self.project_status.get()
        
        phase_recommendations = {
            "pre_construction": {
                "phases": ["Pré-construction"],
                "description": "💡 Analyse de la phase de pré-construction pour évaluer les risques initiaux"
            },
            "construction": {
                "phases": ["Pré-construction", "Construction"],
                "description": "💡 Comparaison pré-construction vs construction pour suivi des impacts"
            },
            "exploitation": {
                "phases": ["Pré-construction", "Construction", "Exploitation"],
                "description": "💡 Analyse complète du cycle de vie jusqu'à l'exploitation"
            },
            "demantelement": {
                "phases": ["Pré-construction", "Construction", "Exploitation", "Démantèlement"],
                "description": "💡 Bilan environnemental complet de toutes les phases"
            }
        }
        
        rec = phase_recommendations.get(status, {"phases": [], "description": ""})
        phases_text = f"Phases analysées : {', '.join(rec['phases'])}\n{rec['description']}"
        self.phases_label.config(text=phases_text)
    
    def _start_analysis(self):
        """Lance l'analyse SLRI"""
        mode = self.analysis_mode.get()
        
        # Validation des entrées
        if mode == "coordinates":
            try:
                lat = float(self.lat_entry.get())
                lon = float(self.lon_entry.get())
                
                if not (-90 <= lat <= 90):
                    messagebox.showerror("Erreur", "La latitude doit être entre -90 et 90")
                    return
                
                if not (-180 <= lon <= 180):
                    messagebox.showerror("Erreur", "La longitude doit être entre -180 et 180")
                    return
                
                self.coordinates = {"lat": lat, "lon": lon}
                
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer des coordonnées valides")
                return
        
        elif mode == "file":
            if not self.selected_file or not os.path.exists(self.selected_file):
                messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide")
                return
        
        # Lancer l'analyse
        self._perform_slri_analysis()
    
    def _perform_slri_analysis(self):
        """Effectue l'analyse SLRI avec extraction IA"""
        try:
            # Importer les modules nécessaires
            from slri_phases_analyzer import SLRIPhasesAnalyzer
            from slri_ai_extractor import SLRIAIExtractor, extract_environmental_parameters
            from external_apis import ExternalAPIs
            
            # Créer l'analyseur et l'extracteur IA
            analyzer = SLRIPhasesAnalyzer()
            ai_extractor = SLRIAIExtractor()
            
            # Déterminer les phases à analyser
            status = self.project_status.get()
            phase_mapping = {
                "pre_construction": ["pre_construction"],
                "construction": ["pre_construction", "construction"],
                "exploitation": ["pre_construction", "construction", "exploitation"],
                "demantelement": ["pre_construction", "construction", "exploitation", "demantelement"]
            }
            
            selected_phases = phase_mapping.get(status, ["pre_construction"])
            
            # Obtenir les données environnementales avec IA
            if self.analysis_mode.get() == "coordinates":
                # Analyse par coordonnées avec collecte API + IA
                api_client = ExternalAPIs()
                lat, lon = self.coordinates["lat"], self.coordinates["lon"]
                
                messagebox.showinfo("Analyse IA en cours", 
                                  f"🤖 Collecte intelligente des données pour:\n"
                                  f"Latitude: {lat}\nLongitude: {lon}\n\n"
                                  f"L'IA va extraire et classifier automatiquement\n"
                                  f"tous les paramètres selon les références SLRI...")
                
                # Collecter les données réelles via APIs
                try:
                    # Utiliser les vraies APIs comme dans l'analyse normale
                    from external_apis import ExternalAPIs
                    from water_parameters_collector import WaterParametersCollector
                    
                    api_client = ExternalAPIs()
                    water_collector = WaterParametersCollector()
                    
                    # Collecter données météo
                    weather_data = api_client.get_weather_data(lat, lon)
                    
                    # Collecter données qualité de l'air
                    air_data = api_client.get_air_quality_data(lat, lon)
                    
                    # Collecter données eau (FAO)
                    water_data = api_client.get_water_data(lat, lon)
                    water_params = water_collector.collect_water_parameters(lat, lon)
                    
                    # Collecter données sol (SoilGrids)
                    soil_data = api_client.get_soil_data(lat, lon)
                    
                    # Formatter les données pour l'extraction IA
                    raw_data = self._format_api_data_for_ai(lat, lon, weather_data, air_data, water_data, water_params, soil_data)
                    
                    # Extraction IA des paramètres avec données réelles
                    extracted_params = ai_extractor.extract_parameters_from_text(raw_data, "coordinates")
                    
                except Exception as e:
                    logger.error(f"Erreur collecte coordonnées: {e}")
                    extracted_params = {"error": str(e)}
                
            else:
                # Analyse par fichier avec IA
                messagebox.showinfo("Analyse IA en cours", 
                                  f"🤖 Analyse intelligente du fichier:\n"
                                  f"{os.path.basename(self.selected_file)}\n\n"
                                  f"L'IA va extraire automatiquement tous les\n"
                                  f"paramètres environnementaux et les classifier\n"
                                  f"selon les références SLRI...")
                
                # Extraction IA du fichier
                extracted_params = extract_environmental_parameters(self.selected_file, "file")
            
            # Vérifier si l'extraction a réussi
            if "error" in extracted_params:
                messagebox.showerror("Erreur d'extraction", 
                                   f"Erreur lors de l'extraction IA:\n{extracted_params['error']}")
                return
            
            # Convertir les paramètres extraits au format attendu par l'analyseur
            environmental_data = self._convert_ai_params_to_analyzer_format(extracted_params)
            
            # Effectuer l'analyse SLRI
            results = analyzer.analyze_project_phases(
                environmental_data=environmental_data,
                project_type="general"
            )
            
            # Enrichir les résultats avec les données IA
            results['ai_extraction'] = extracted_params
            results['extraction_method'] = 'AI_Enhanced'
            
            # Afficher les résultats
            self._display_results(results, selected_phases)
            
        except Exception as e:
            messagebox.showerror("Erreur d'analyse", f"Erreur lors de l'analyse SLRI IA:\n{str(e)}")
    
    def _convert_ai_params_to_analyzer_format(self, ai_params: Dict) -> Dict:
        """Convertit les paramètres extraits par IA au format de l'analyseur SLRI"""
        try:
            converted = {
                'water_data': {},
                'soil_data': {},
                'air_data': {},
                'biological_data': {},
                'human_data': {}
            }
            
            # Mapping des milieux
            milieu_mapping = {
                'eau': 'water_data',
                'sol': 'soil_data', 
                'air': 'air_data',
                'biologique': 'biological_data',
                'humain': 'human_data'
            }
            
            # Convertir chaque milieu
            for ai_milieu, analyzer_milieu in milieu_mapping.items():
                if ai_milieu in ai_params:
                    for param_name, param_data in ai_params[ai_milieu].items():
                        if isinstance(param_data, dict) and 'valeur' in param_data:
                            # Extraire la valeur numérique
                            value = param_data['valeur']
                            if isinstance(value, str):
                                # Essayer d'extraire le nombre de la chaîne
                                import re
                                numbers = re.findall(r'[-+]?\d*\.?\d+', value)
                                if numbers:
                                    value = float(numbers[0])
                                else:
                                    value = 0
                            
                            # Mapper le nom du paramètre
                            mapped_name = self._map_parameter_name(param_name)
                            converted[analyzer_milieu][mapped_name] = value
            
            return converted
            
        except Exception as e:
            logger.error(f"Erreur conversion paramètres IA: {e}")
            # Retourner des données par défaut en cas d'erreur
            return {
                'water_data': {'ph': 7.0, 'conductivity': 500, 'turbidity': 2.0},
                'soil_data': {'ph': 6.5, 'organic_matter': 3.0},
                'air_data': {'pm25': 15, 'pm10': 30}
            }
    
    def _map_parameter_name(self, ai_param_name: str) -> str:
        """Mappe les noms de paramètres IA vers les noms attendus par l'analyseur"""
        mapping = {
            'pH': 'ph',
            'Température': 'temperature',
            'Turbidité': 'turbidity',
            'Conductivité': 'conductivity',
            'DBO5': 'dbo5',
            'DCO': 'dco',
            'Oxygène dissous': 'dissolved_oxygen',
            'Nitrates': 'nitrates',
            'Phosphore total': 'total_phosphorus',
            'Plomb': 'lead',
            'Cadmium': 'cadmium',
            'Matière organique': 'organic_matter',
            'PM10': 'pm10',
            'PM2.5': 'pm25',
            'SO2': 'so2',
            'NOx': 'nox',
            'CO': 'co'
        }
        
        return mapping.get(ai_param_name, ai_param_name.lower().replace(' ', '_'))
    
    def _format_api_data_for_ai(self, lat, lon, weather_data, air_data, water_data, water_params, soil_data):
        """Formate les données des APIs pour l'analyse IA selon les références SLRI"""
        try:
            formatted_data = f"""
DONNÉES ENVIRONNEMENTALES RÉELLES - Coordonnées: {lat}, {lon}

=== MILIEU PHYSIQUE - EAU ===
"""
            
            # Données météorologiques (température, précipitations)
            if weather_data and isinstance(weather_data, dict):
                if 'temperature' in weather_data:
                    formatted_data += f"Température: {weather_data['temperature']}°C\n"
                if 'humidity' in weather_data:
                    formatted_data += f"Humidité: {weather_data['humidity']}%\n"
            
            # Paramètres d'eau collectés
            if water_params and isinstance(water_params, dict):
                for param, value in water_params.items():
                    if isinstance(value, (int, float)):
                        unit = self._get_water_parameter_unit(param)
                        formatted_data += f"{param}: {value} {unit}\n"
            
            # Données FAO eau
            if water_data and isinstance(water_data, dict):
                for param, value in water_data.items():
                    if isinstance(value, (int, float)):
                        unit = self._get_water_parameter_unit(param)
                        formatted_data += f"{param}: {value} {unit}\n"
            
            formatted_data += "\n=== MILIEU PHYSIQUE - SOL ===\n"
            
            # Données SoilGrids
            if soil_data and isinstance(soil_data, dict):
                for param, value in soil_data.items():
                    if isinstance(value, (int, float)):
                        unit = self._get_soil_parameter_unit(param)
                        formatted_data += f"{param}: {value} {unit}\n"
            
            formatted_data += "\n=== MILIEU PHYSIQUE - AIR ===\n"
            
            # Données qualité de l'air
            if air_data and isinstance(air_data, dict):
                for param, value in air_data.items():
                    if isinstance(value, (int, float)):
                        unit = self._get_air_parameter_unit(param)
                        formatted_data += f"{param}: {value} {unit}\n"
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Erreur formatage données API: {e}")
            return f"Erreur formatage données pour coordonnées: {lat}, {lon}"
    
    def _get_water_parameter_unit(self, param_name):
        """Retourne l'unité appropriée pour un paramètre d'eau selon SLRI"""
        units = {
            'ph': '',
            'temperature': '°C',
            'turbidity': 'NTU',
            'conductivity': 'µS/cm',
            'dbo5': 'mg/L',
            'dco': 'mg/L',
            'dissolved_oxygen': 'mg/L',
            'nitrates': 'mg/L',
            'nitrites': 'mg/L',
            'ammoniac': 'mg/L',
            'total_phosphorus': 'mg/L',
            'total_nitrogen': 'mg/L',
            'lead': 'mg/L',
            'cadmium': 'mg/L',
            'chrome': 'mg/L',
            'copper': 'mg/L',
            'zinc': 'mg/L',
            'nickel': 'mg/L',
            'mercury': 'mg/L',
            'arsenic': 'mg/L'
        }
        return units.get(param_name.lower(), 'mg/L')
    
    def _get_soil_parameter_unit(self, param_name):
        """Retourne l'unité appropriée pour un paramètre de sol selon SLRI"""
        units = {
            'ph': '',
            'organic_matter': '%',
            'carbon': '%',
            'permeability': 'm/s',
            'lead': 'mg/kg',
            'cadmium': 'mg/kg',
            'chrome': 'mg/kg',
            'copper': 'mg/kg',
            'zinc': 'mg/kg',
            'nickel': 'mg/kg',
            'mercury': 'mg/kg',
            'arsenic': 'mg/kg',
            'total_nitrogen': '%',
            'total_phosphorus': 'mg/kg'
        }
        return units.get(param_name.lower(), 'mg/kg')
    
    def _get_air_parameter_unit(self, param_name):
        """Retourne l'unité appropriée pour un paramètre d'air selon SLRI"""
        units = {
            'pm10': 'µg/m³',
            'pm25': 'µg/m³',
            'pm2.5': 'µg/m³',
            'so2': 'µg/m³',
            'nox': 'µg/m³',
            'no2': 'µg/m³',
            'co': 'mg/m³',
            'o3': 'µg/m³',
            'dust': 'µg/m³'
        }
        return units.get(param_name.lower(), 'µg/m³')
    
    def _display_results(self, results, selected_phases):
        """Affiche les résultats de l'analyse SLRI"""
        # Créer une nouvelle fenêtre pour les résultats
        results_window = tk.Toplevel(self.parent)
        results_window.title("Résultats de l'Analyse SLRI")
        results_window.geometry("900x700")
        results_window.transient(self.parent)
        
        # Créer l'interface des résultats avec Canvas pour défilement
        canvas = tk.Canvas(results_window)
        scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Titre principal
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(title_frame, text="🤖 Résultats de l'Analyse SLRI avec IA", 
                 font=("Arial", 16, "bold")).pack()
        
        if results.get('extraction_method') == 'AI_Enhanced':
            ttk.Label(title_frame, text="✨ Extraction automatique des paramètres par Intelligence Artificielle", 
                     font=("Arial", 10), foreground="blue").pack()
        
        # Afficher les résultats d'extraction IA
        if 'ai_extraction' in results:
            ai_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Paramètres Extraits par IA", padding=10)
            ai_frame.pack(fill="x", padx=10, pady=5)
            
            ai_data = results['ai_extraction']
            
            # Résumé de l'extraction
            if 'metadata' in ai_data:
                metadata = ai_data['metadata']
                summary_text = f"""
📊 Méthode d'extraction: {metadata.get('extraction_method', 'IA')}
🔢 Paramètres trouvés: {metadata.get('total_parameters', 'N/A')}
✅ Conformes: {metadata.get('conformes', 'N/A')}
⚠️ Dépassements: {metadata.get('depassements', 'N/A')}
                """
                ttk.Label(ai_frame, text=summary_text, justify="left").pack(anchor="w")
            
            # Afficher les paramètres par milieu
            for milieu in ['eau', 'sol', 'air', 'biologique', 'humain']:
                if milieu in ai_data and ai_data[milieu]:
                    milieu_frame = ttk.LabelFrame(ai_frame, text=f"🌊 {milieu.title()}", padding=5)
                    milieu_frame.pack(fill="x", pady=2)
                    
                    # Créer un tableau des paramètres
                    tree = ttk.Treeview(milieu_frame, columns=("Valeur", "Unité", "Score", "Statut"), 
                                       show="tree headings", height=min(6, len(ai_data[milieu])))
                    
                    tree.heading("#0", text="Paramètre")
                    tree.heading("Valeur", text="Valeur")
                    tree.heading("Unité", text="Unité")
                    tree.heading("Score", text="Score SLRI")
                    tree.heading("Statut", text="Statut")
                    
                    tree.column("#0", width=150)
                    tree.column("Valeur", width=80)
                    tree.column("Unité", width=80)
                    tree.column("Score", width=80)
                    tree.column("Statut", width=100)
                    
                    for param_name, param_data in ai_data[milieu].items():
                        if isinstance(param_data, dict):
                            valeur = param_data.get('valeur', 'N/A')
                            unite = param_data.get('unité', '')
                            score = param_data.get('score', 'N/A')
                            statut = param_data.get('statut', 'N/A')
                            
                            # Couleur selon le statut
                            tag = "conforme" if statut == "conforme" else "depassement"
                            tree.insert("", "end", text=param_name, 
                                      values=(valeur, unite, score, statut), tags=(tag,))
                    
                    tree.tag_configure("conforme", foreground="green")
                    tree.tag_configure("depassement", foreground="red")
                    
                    tree.pack(fill="x", padx=5, pady=2)
        
        # Afficher les résultats SLRI par phases
        phases_frame = ttk.LabelFrame(scrollable_frame, text="📋 Analyse SLRI par Phases", padding=10)
        phases_frame.pack(fill="x", padx=10, pady=5)
        
        if 'phases' in results:
            for phase_key in selected_phases:
                if phase_key in results['phases']:
                    phase_data = results['phases'][phase_key]
                    
                    phase_subframe = ttk.LabelFrame(phases_frame, text=f"🔄 Phase: {phase_key.title()}", padding=5)
                    phase_subframe.pack(fill="x", pady=2)
                    
                    # Afficher le score et les recommandations
                    if isinstance(phase_data, dict):
                        score = phase_data.get('score_total', 'N/A')
                        niveau = phase_data.get('niveau_risque', 'N/A')
                        
                        info_text = f"Score total: {score} | Niveau de risque: {niveau}"
                        ttk.Label(phase_subframe, text=info_text, font=("Arial", 10, "bold")).pack(anchor="w")
                        
                        if 'recommandations' in phase_data:
                            rec_text = "Recommandations: " + "; ".join(phase_data['recommandations'][:3])
                            ttk.Label(phase_subframe, text=rec_text, wraplength=800).pack(anchor="w", pady=2)
        
        # Boutons d'action
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="💾 Exporter Rapport", 
                  command=lambda: self._export_ai_results(results)).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="🔄 Nouvelle Analyse", 
                  command=results_window.destroy).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="❌ Fermer", 
                  command=results_window.destroy).pack(side="right", padx=5)
    
    def _export_ai_results(self, results):
        """Exporte les résultats de l'analyse IA"""
        try:
            from tkinter import filedialog
            import json
            from datetime import datetime
            
            # Demander le fichier de destination
            filename = filedialog.asksaveasfilename(
                title="Exporter les résultats SLRI IA",
                defaultextension=".json",
                filetypes=[
                    ("Fichier JSON", "*.json"),
                    ("Fichier Excel", "*.xlsx"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if filename:
                if filename.endswith('.json'):
                    # Export JSON
                    export_data = {
                        'timestamp': datetime.now().isoformat(),
                        'analysis_type': 'SLRI_AI_Enhanced',
                        'results': results
                    }
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                        
                elif filename.endswith('.xlsx'):
                    # Export Excel
                    import pandas as pd
                    
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        # Feuille résumé
                        summary_data = {
                            'Méthode': ['Extraction IA'],
                            'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                            'Phases analysées': [', '.join(results.get('phases', {}).keys())]
                        }
                        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Résumé', index=False)
                        
                        # Feuille paramètres IA
                        if 'ai_extraction' in results:
                            ai_data = results['ai_extraction']
                            for milieu in ['eau', 'sol', 'air']:
                                if milieu in ai_data and ai_data[milieu]:
                                    df_data = []
                                    for param, data in ai_data[milieu].items():
                                        if isinstance(data, dict):
                                            df_data.append({
                                                'Paramètre': param,
                                                'Valeur': data.get('valeur', ''),
                                                'Unité': data.get('unité', ''),
                                                'Score SLRI': data.get('score', ''),
                                                'Statut': data.get('statut', '')
                                            })
                                    
                                    if df_data:
                                        pd.DataFrame(df_data).to_excel(writer, sheet_name=f'{milieu.title()}', index=False)
                
                messagebox.showinfo("Export réussi", f"Résultats exportés vers:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Erreur lors de l'export:\n{str(e)}")
    
    def _create_simple_phase_content(self, parent, phase_key, phase_data, phase_config):
        """Crée un contenu simplifié pour une phase"""
        # Titre de la phase
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        icon = phase_config.get('icon', '📊')
        title = phase_config.get('title', phase_key.title())
        
        ttk.Label(title_frame, text=f"{icon} {title}", 
                 font=("Arial", 14, "bold")).pack()
        
        # Contenu de la phase
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        if isinstance(phase_data, dict):
            # Afficher les informations principales
            info_text = f"Score: {phase_data.get('score_total', 'N/A')}\n"
            info_text += f"Niveau de risque: {phase_data.get('niveau_risque', 'N/A')}"
            
            ttk.Label(content_frame, text=info_text, justify="left").pack(anchor="w")
            
            # Recommandations
            if 'recommandations' in phase_data:
                rec_frame = ttk.LabelFrame(content_frame, text="Recommandations", padding=5)
                rec_frame.pack(fill="x", pady=5)
                
                for i, rec in enumerate(phase_data['recommandations'][:5]):
                    ttk.Label(rec_frame, text=f"• {rec}", wraplength=600).pack(anchor="w")
        else:
            ttk.Label(content_frame, text="Données de phase non disponibles").pack()
    
    def _get_risk_level(self, score):
        """Détermine le niveau de risque selon le score"""
        if score <= 4:
            return "FAIBLE"
        elif score <= 8:
            return "MOYEN"
        elif score <= 12:
            return "FORT"
        else:
            return "TRÈS GRAVE"
    
    def _get_risk_color(self, risk_level):
        """Retourne la couleur associée au niveau de risque"""
        colors = {
            "FAIBLE": "green",
            "MOYEN": "orange", 
            "FORT": "red",
            "TRÈS GRAVE": "darkred"
        }
        return colors.get(risk_level, "black")
    
    def _show_help(self):
        """Affiche l'aide pour l'utilisation"""
        help_text = """🌍 Guide d'Utilisation - Analyse SLRI

📍 ANALYSE PAR COORDONNÉES :
• Entrez la latitude et longitude du site
• Exemple : Casablanca (33.5731, -7.5898)
• Les données environnementales seront collectées automatiquement

📄 ANALYSE PAR FICHIER :
• Sélectionnez un fichier contenant des données environnementales
• Formats supportés : PDF, Excel, CSV, TXT
• Le système extraira automatiquement les paramètres pertinents

🔄 PHASES D'ANALYSE :
• Pré-construction : Évaluation initiale des risques
• Construction : Impact des travaux
• Exploitation : Fonctionnement normal
• Démantèlement : Fin de vie du projet

📊 RÉSULTATS :
• Scores par milieu (eau, sol, air)
• Classification des risques (FAIBLE à TRÈS GRAVE)
• Recommandations spécifiques par phase
• Identification des risques majeurs

Pour plus d'informations, consultez la documentation complète."""
        
        messagebox.showinfo("Aide - Analyse SLRI", help_text)

# Fonction d'intégration
def integrate_simple_slri_interface(app_instance):
    """Intègre l'interface SLRI simplifiée dans l'application principale"""
    # Créer un nouvel onglet pour l'interface SLRI
    slri_frame = ttk.Frame(app_instance.notebook)
    app_instance.notebook.add(slri_frame, text="🌍 Analyse SLRI")
    
    # Créer l'interface
    slri_interface = SLRISimpleInterface(app_instance.root)
    slri_interface.create_interface(slri_frame)
    
    return slri_interface
