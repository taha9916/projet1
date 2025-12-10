import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import logging
import traceback
from web_search import WebSearchEngine, parameters_to_dataframe
from config import WEB_CONFIG, UI_CONFIG
from cloud_api import extract_environmental_parameters_cloud
from external_apis import collect_environmental_data_from_apis

logger = logging.getLogger(__name__)

class InitialInfoWindow:
    """Fenêtre pour saisir les informations initiales et lancer la recherche web."""
    
    def __init__(self, parent, callback=None):
        """Initialise la fenêtre de saisie des informations initiales.
        
        Args:
            parent: La fenêtre parente
            callback: Fonction à appeler après la recherche web
        """
        self.parent = parent
        self.callback = callback
        
        # Créer une nouvelle fenêtre
        self.window = tk.Toplevel(parent)
        self.window.title("Informations initiales du projet")
        self.window.geometry("600x600")
        self.window.resizable(True, True)
        self.window.minsize(600, 600)  # Taille minimale pour assurer la visibilité des éléments
        self.window.transient(parent)  # Rendre la fenêtre modale
        self.window.grab_set()
        
        # Centrer la fenêtre
        self.center_window()
        
        # Créer les widgets
        self._create_widgets()
    
    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Crée les widgets de la fenêtre."""
        # Créer un canvas avec barre de défilement
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Créer un canvas qui contiendra tous les widgets
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Frame principal qui sera placé dans le canvas
        main_frame = ttk.Frame(canvas, padding="20")
        
        # Configurer le canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Ajouter le frame principal au canvas
        canvas_frame = canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        
        # Configurer le canvas pour qu'il s'adapte à la taille du frame
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=event.width)
            canvas.itemconfig(canvas_frame, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas)
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Permettre le défilement avec la molette de la souris
        def _on_mousewheel(event):
            try:
                # Vérifier si le canvas existe encore et est visible
                if canvas.winfo_exists() and canvas.winfo_ismapped():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception as e:
                # Ignorer l'erreur si le canvas n'existe plus
                logger.debug(f"Erreur de défilement: {str(e)}")
                pass
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Débinder l'événement quand la fenêtre est fermée
        def _on_window_close():
            try:
                canvas.unbind_all("<MouseWheel>")
                self.window.destroy()
            except Exception as e:
                logger.debug(f"Erreur lors de la fermeture: {str(e)}")
                self.window.destroy()
                pass
        
        self.window.protocol("WM_DELETE_WINDOW", _on_window_close)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Informations initiales du projet", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, text="Veuillez saisir les informations de base pour lancer la recherche automatique des paramètres environnementaux.", wraplength=550)
        desc_label.pack(pady=(0, 20))
        
        # Frame pour les champs de saisie
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nom du projet
        ttk.Label(input_frame, text="Nom du projet:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.project_name_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Localisation
        ttk.Label(input_frame, text="Localisation (ville, région):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.location_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Type de projet
        ttk.Label(input_frame, text="Type de projet:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.project_type_var = tk.StringVar()
        project_types = ["Industriel", "Agricole", "Urbain", "Infrastructure", "Touristique", "Minier", "Énergétique", "Autre"]
        ttk.Combobox(input_frame, textvariable=self.project_type_var, values=project_types, width=37).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Description du projet
        ttk.Label(input_frame, text="Description du projet:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(input_frame, textvariable=self.description_var, width=40)
        description_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Fournisseur d'API cloud
        ttk.Label(input_frame, text="Fournisseur d'API cloud:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.api_provider_var = tk.StringVar(value="openrouter")
        api_providers = ["openrouter", "openai"]
        api_provider_combo = ttk.Combobox(input_frame, textvariable=self.api_provider_var, values=api_providers, width=37)
        api_provider_combo.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Ajouter une infobulle
        ttk.Label(input_frame, text="ℹ️", cursor="hand2", foreground="blue").grid(row=5, column=2, sticky=tk.W)
        
        # Option pour utiliser les API externes
        ttk.Label(input_frame, text="Utiliser les API externes:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.use_external_apis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, variable=self.use_external_apis_var, command=self._toggle_api_options).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Ajouter une infobulle pour les API externes
        api_info_label = ttk.Label(input_frame, text="ℹ️", cursor="hand2", foreground="blue")
        api_info_label.grid(row=6, column=2, sticky=tk.W)
        
        # Frame pour les options d'API externes
        self.api_options_frame = ttk.LabelFrame(input_frame, text="Options des API externes")
        self.api_options_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Variables pour chaque API externe
        self.use_weather_api_var = tk.BooleanVar(value=True)
        self.use_air_quality_api_var = tk.BooleanVar(value=True)
        self.use_soil_api_var = tk.BooleanVar(value=True)
        self.use_worldbank_api_var = tk.BooleanVar(value=True)
        self.use_osm_api_var = tk.BooleanVar(value=True)
        self.use_copernicus_api_var = tk.BooleanVar(value=True)
        self.use_gbif_api_var = tk.BooleanVar(value=True)
        self.use_nasa_api_var = tk.BooleanVar(value=True)
        
        # Checkboxes pour chaque API - Première colonne
        ttk.Checkbutton(self.api_options_frame, text="OpenWeatherMap (météo)", variable=self.use_weather_api_var).grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="OpenWeatherMap Air Pollution (qualité de l'air)", variable=self.use_air_quality_api_var).grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="SoilGrids (données sur le sol)", variable=self.use_soil_api_var).grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="OpenStreetMap (géographique)", variable=self.use_osm_api_var).grid(row=3, column=0, sticky=tk.W, pady=2, padx=5)
        
        # Checkboxes pour chaque API - Deuxième colonne
        ttk.Checkbutton(self.api_options_frame, text="Banque Mondiale (indicateurs)", variable=self.use_worldbank_api_var).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="Copernicus (climat)", variable=self.use_copernicus_api_var).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="GBIF (biodiversité)", variable=self.use_gbif_api_var).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        ttk.Checkbutton(self.api_options_frame, text="NASA (satellite)", variable=self.use_nasa_api_var).grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Créer des infobulles pour expliquer les options
        api_tooltip_text = "OpenRouter (Llama 3 8B): Recommandé pour des résultats fiables\nOpenAI: Alternative utilisant GPT-4 Vision"
        
        external_apis_tooltip_text = "Activer pour collecter des données supplémentaires via:\n- OpenWeatherMap (météo)\n- OpenWeatherMap Air Pollution (qualité de l'air)\n- SoilGrids (données sur le sol)\n- Banque Mondiale (indicateurs environnementaux)\n- OpenStreetMap (données géographiques)\n- Copernicus (données climatiques)\n- GBIF (données sur la biodiversité)\n- NASA (données satellitaires)"
        
        def show_tooltip(event, text):
            tooltip = tk.Toplevel(self.window)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            ttk.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1).pack()
            self.window.after(5000, tooltip.destroy)  # Fermer après 5 secondes
        
        # Lier les événements de clic aux affichages des infobulles
        self.window.bind("<Button-1>", lambda e: show_tooltip(e, api_tooltip_text) if e.widget == api_provider_combo else None)
        api_info_label.bind("<Button-1>", lambda e: show_tooltip(e, external_apis_tooltip_text))
        
        # Paramètres spécifiques à rechercher
        ttk.Label(input_frame, text="Paramètres spécifiques\nà rechercher (optionnel):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.specific_params_text = tk.Text(input_frame, width=30, height=5)
        self.specific_params_text.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Ajouter une barre de défilement pour le champ de texte
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.specific_params_text.yview)
        scrollbar.grid(row=4, column=2, sticky=(tk.N, tk.S))
        self.specific_params_text.configure(yscrollcommand=scrollbar.set)
        
        # Ajuster les colonnes
        input_frame.columnconfigure(1, weight=1)
        
        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Bouton Annuler
        ttk.Button(button_frame, text="Annuler", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Bouton Rechercher
        ttk.Button(button_frame, text="Lancer la recherche", command=self._start_search).pack(side=tk.RIGHT, padx=5)
        
        # Bouton pour tester les API externes
        def test_external_apis():
            from external_apis import test_apis
            try:
                location = self.location_var.get()
                if not location:
                    messagebox.showwarning("Attention", "Veuillez saisir une localisation pour tester les API.")
                    return
                    
                # Afficher une fenêtre de progression
                test_window = tk.Toplevel(self.window)
                test_window.title("Test des API externes")
                test_window.geometry("400x200")
                test_window.transient(self.window)
                test_window.grab_set()
                
                # Centrer la fenêtre
                test_window.update_idletasks()
                width = test_window.winfo_width()
                height = test_window.winfo_height()
                x = (test_window.winfo_screenwidth() // 2) - (width // 2)
                y = (test_window.winfo_screenheight() // 2) - (height // 2)
                test_window.geometry(f"{width}x{height}+{x}+{y}")
                
                ttk.Label(test_window, text="Test des API externes en cours...", font=("Arial", 10)).pack(pady=(10, 5))
                progress = ttk.Progressbar(test_window, orient="horizontal", length=350, mode="indeterminate")
                progress.pack(pady=10)
                progress.start(10)
                
                # Fonction pour effectuer le test en arrière-plan
                def run_test():
                    try:
                        results = test_apis(location)
                        test_window.destroy()
                        
                        # Afficher les résultats
                        result_window = tk.Toplevel(self.window)
                        result_window.title("Résultats des tests API")
                        result_window.geometry("500x400")
                        result_window.transient(self.window)
                        
                        # Créer un widget Text avec scrollbar
                        text_frame = ttk.Frame(result_window)
                        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                        
                        scrollbar = ttk.Scrollbar(text_frame)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                        
                        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
                        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        scrollbar.config(command=text_widget.yview)
                        
                        # Insérer les résultats
                        text_widget.insert(tk.END, results)
                        text_widget.config(state=tk.DISABLED)  # Rendre le texte en lecture seule
                        
                        ttk.Button(result_window, text="Fermer", command=result_window.destroy).pack(pady=10)
                        
                    except Exception as e:
                        test_window.destroy()
                        messagebox.showerror("Erreur", f"Erreur lors du test des API: {str(e)}")
                
                # Lancer le test après un court délai
                self.window.after(100, run_test)
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du test des API: {str(e)}")
        
        ttk.Button(button_frame, text="Tester les API", command=test_external_apis).pack(side=tk.LEFT, padx=5)
    
    def _toggle_api_options(self):
        """Active ou désactive les options d'API externes en fonction de l'état de la case à cocher."""
        if self.use_external_apis_var.get():
            # Activer les options d'API
            for child in self.api_options_frame.winfo_children():
                child.configure(state="normal")
            self.api_options_frame.configure(state="normal")
        else:
            # Désactiver les options d'API
            for child in self.api_options_frame.winfo_children():
                child.configure(state="disabled")
            self.api_options_frame.configure(state="disabled")
    
    def _start_search(self):
        """Lance la recherche web basée sur les informations saisies."""
        # Vérifier les champs obligatoires
        if not self.location_var.get() or not self.project_type_var.get():
            messagebox.showerror("Erreur", "Veuillez remplir les champs obligatoires (Localisation et Type de projet).")
            return
        
        # Récupérer les paramètres spécifiques
        specific_params = self.specific_params_text.get("1.0", "end").strip().split('\n')
        specific_params = [param.strip() for param in specific_params if param.strip()]
        
        # Afficher une fenêtre de progression
        progress_window = tk.Toplevel(self.window)
        progress_window.title("Recherche en cours")
        progress_window.geometry("400x200")
        progress_window.transient(self.window)
        progress_window.grab_set()
        
        # Centrer la fenêtre de progression
        progress_window.update_idletasks()
        width = progress_window.winfo_width()
        height = progress_window.winfo_height()
        x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_window.winfo_screenheight() // 2) - (height // 2)
        progress_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Ajouter un label et une barre de progression
        ttk.Label(progress_window, text="Recherche des paramètres environnementaux en cours...", 
                 font=("Arial", 10)).pack(pady=(10, 5))
        
        # Ajouter un message indiquant que la recherche est effectuée par l'IA cloud
        ttk.Label(progress_window, text=f"Utilisation de l'IA cloud ({self.api_provider_var.get()}) pour des résultats fiables", 
                 font=("Arial", 8), foreground="blue").pack(pady=(0, 5))
        
        # Ajouter un message indiquant que les API externes sont utilisées si l'option est activée
        if self.use_external_apis_var.get():
            ttk.Label(progress_window, text="Collecte de données via API externes (météo, qualité de l'air, sol, biodiversité, climat...)", 
                     font=("Arial", 8), foreground="green").pack(pady=(0, 10))
        
        progress = ttk.Progressbar(progress_window, orient="horizontal", length=350, mode="indeterminate")
        progress.pack(pady=10)
        progress.start(10)
        
        # Fonction pour effectuer la recherche en arrière-plan
        def perform_search():
            try:
                # Importer les fonctions d'extraction des paramètres environnementaux
                from cloud_api import extract_environmental_parameters_cloud
                from external_apis import collect_environmental_data_from_apis
                
                # Effectuer la recherche avec l'API cloud
                df_cloud = extract_environmental_parameters_cloud(
                    self.location_var.get(),
                    self.project_type_var.get(),
                    specific_params=specific_params,
                    api_provider=self.api_provider_var.get()  # Utiliser le fournisseur d'API sélectionné
                )
                
                # Initialiser le DataFrame final avec les résultats de l'API cloud
                df = df_cloud
                
                # Effectuer la recherche avec les API externes si l'option est activée
                # Effectuer la recherche avec les API externes si l'option est activée
                if self.use_external_apis_var.get():
                    # Créer un dictionnaire des API à utiliser
                    api_options = {
                        "weather": self.use_weather_api_var.get(),
                        "air_quality": self.use_air_quality_api_var.get(),
                        "soil": self.use_soil_api_var.get(),
                        "worldbank": self.use_worldbank_api_var.get(),
                        "osm": self.use_osm_api_var.get(),
                        "copernicus": self.use_copernicus_api_var.get(),
                        "gbif": self.use_gbif_api_var.get(),
                        "nasa": self.use_nasa_api_var.get()
                    }
                    
                    # Créer une instance de ExternalAPIs pour utiliser ses méthodes
                    from external_apis import ExternalAPIs
                    external_apis = ExternalAPIs()
                
                    df_apis = collect_environmental_data_from_apis(
                    location=self.location_var.get(),
                    project_type=self.project_type_var.get(),
                    api_options=api_options
                )
                    # Fusionner les DataFrames s'ils ne sont pas vides
                    if df_cloud is not None and not df_cloud.empty and df_apis is not None and not df_apis.empty:
                        df = pd.concat([df_cloud, df_apis], ignore_index=True)
                    elif df_cloud is not None and not df_cloud.empty:
                        df = df_cloud
                    elif df_apis is not None and not df_apis.empty:
                        df = df_apis
                    else:
                        df = pd.DataFrame()  # Retourner un DataFrame vide si les deux sont vides
                
                # Supprimer les doublons éventuels
                if "Paramètre" in df.columns:
                    df = df.drop_duplicates(subset=["Paramètre"])
                
                # Ajouter des colonnes supplémentaires pour la conformité si elles n'existent pas
                for col in ["Valeur mesurée", "Résultat conformité"]:
                    if col not in df.columns:
                        df[col] = ""
                
                # Initialiser la colonne Score avec des valeurs numériques
                if "Score" not in df.columns:
                    df["Score"] = 0
                
                # Ajouter des informations sur le projet
                project_info = {
                    "Nom du projet": self.project_name_var.get(),
                    "Localisation": self.location_var.get(),
                    "Type de projet": self.project_type_var.get(),
                    "Description": self.description_var.get()
                }
                
                # Fermer les fenêtres
                progress_window.destroy()
                self.window.destroy()
                
                # Appeler le callback avec les résultats
                if self.callback:
                    self.callback(df, project_info)
                
            except Exception as e:
                error_message = f"{e}"
                detailed_error = traceback.format_exc()
                logger.error(f"Erreur détaillée lors de la recherche web:\n{detailed_error}")
                progress_window.destroy()
                messagebox.showerror("Erreur", f"Une erreur est survenue lors de la recherche: {error_message}\n\nConsultez app.log pour plus de détails.")
        
        # Lancer la recherche après un court délai
        self.window.after(100, perform_search)

# Fonction pour tester la fenêtre
def test_window():
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    def on_search_complete(df, project_info):
        print("Recherche terminée!")
        print(f"Informations du projet: {project_info}")
        print(f"DataFrame:\n{df}")
        
        # Sauvegarder les résultats dans un fichier Excel
        os.makedirs("output", exist_ok=True)
        output_file = os.path.join("output", f"resultats_recherche_{project_info['Nom du projet'].replace(' ', '_')}.xlsx")
        df.to_excel(output_file, index=False)
        print(f"Résultats sauvegardés dans {output_file}")
        
        root.destroy()
    
    window = InitialInfoWindow(root, callback=on_search_complete)
    root.mainloop()

# Exécuter le test si le script est exécuté directement
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_window()

# Fonction pour tester la fenêtre
def test_window():
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    def on_search_complete(df, project_info):
        print("Recherche terminée!")
        print(f"Informations du projet: {project_info}")
        print(f"DataFrame:\n{df}")
        
        # Sauvegarder les résultats dans un fichier Excel
        os.makedirs("output", exist_ok=True)
        output_file = os.path.join("output", f"resultats_recherche_{project_info['Nom du projet'].replace(' ', '_')}.xlsx")
        df.to_excel(output_file, index=False)
        print(f"Résultats sauvegardés dans {output_file}")
        
        root.destroy()
    
    window = InitialInfoWindow(root, callback=on_search_complete)
    root.mainloop()