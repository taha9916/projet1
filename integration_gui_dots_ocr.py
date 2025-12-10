#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Intégration de l'adaptateur VLModel dans l'interface graphique existante.

Ce script montre comment intégrer l'adaptateur VLModel dans une interface graphique
existante pour résoudre l'erreur "VLModel object has no attribute load_model".
"""

import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import torch

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import de l'adaptateur VLModel
from integration_dots_ocr import initialize_dots_ocr_model

class AnalyseRisqueApp:
    """
    Interface graphique pour l'analyse de risque environnemental.
    
    Cette classe montre comment intégrer l'adaptateur VLModel dans une interface
    graphique existante pour résoudre l'erreur "VLModel object has no attribute load_model".
    """
    
    def __init__(self, root):
        """
        Initialise l'interface graphique.
        
        Args:
            root (tk.Tk): Fenêtre principale de l'application.
        """
        self.root = root
        self.root.title("Analyse de Risque Environnemental - Masec")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.image_path = tk.StringVar()
        self.model_path = tk.StringVar(value="./weights/DotsOCR")
        self.force_cpu = tk.BooleanVar(value=False)
        self.vlmodel = None
        self.pil_image = None
        self.tk_image = None
        
        # Création de l'interface
        self.create_widgets()
        
        # Initialisation du modèle
        self.initialize_model()
    
    def create_widgets(self):
        """
        Crée les widgets de l'interface graphique.
        """
        # Création du menu
        self.create_menu()
        
        # Frame principale
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour les contrôles
        control_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Sélection de l'image
        ttk.Label(control_frame, text="Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(control_frame, textvariable=self.image_path, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        ttk.Button(control_frame, text="Parcourir", command=self.browse_image).grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Force CPU
        ttk.Checkbutton(control_frame, text="Forcer l'utilisation du CPU", variable=self.force_cpu).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Boutons d'action
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)
        
        ttk.Button(button_frame, text="Analyser", command=self.analyze_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Visualiser", command=self.visualize_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Enregistrer", command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Aide", command=self.show_help).pack(side=tk.RIGHT, padx=5)
        
        # Configuration du grid pour le redimensionnement
        control_frame.columnconfigure(1, weight=1)
        
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Onglet Aperçu des données
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="Aperçu des données")
        
        # Paned window pour séparer l'image et les métadonnées
        data_paned = ttk.PanedWindow(self.data_frame, orient=tk.HORIZONTAL)
        data_paned.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour l'image
        self.image_frame = ttk.LabelFrame(data_paned, text="Image", padding=10)
        data_paned.add(self.image_frame, weight=2)
        
        # Canvas pour l'image
        self.image_canvas = tk.Canvas(self.image_frame, bg="white")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour les métadonnées
        metadata_frame = ttk.LabelFrame(data_paned, text="Métadonnées", padding=10)
        data_paned.add(metadata_frame, weight=1)
        
        # Zone de texte pour les métadonnées
        self.metadata_text = scrolledtext.ScrolledText(metadata_frame, wrap=tk.WORD, width=30, height=20)
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Visualisation
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="Visualisation")
        
        # Onglet Résultats
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Résultats")
        
        # Zone de texte pour les résultats
        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD, width=80, height=30)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Barre de progression
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_menu(self):
        """
        Crée le menu de l'application.
        """
        menubar = tk.Menu(self.root)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Ouvrir", command=self.browse_image)
        file_menu.add_command(label="Enregistrer", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Analyse
        analyze_menu = tk.Menu(menubar, tearoff=0)
        analyze_menu.add_command(label="Analyser", command=self.analyze_image)
        analyze_menu.add_command(label="Analyser texte", command=self.analyze_text)
        menubar.add_cascade(label="Analyse", menu=analyze_menu)
        
        # Menu Configuration
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Paramètres", command=self.show_settings)
        config_menu.add_checkbutton(label="Forcer CPU", variable=self.force_cpu)
        menubar.add_cascade(label="Configuration", menu=config_menu)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Aide", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def initialize_model(self):
        """
        Initialise le modèle dots.ocr avec l'adaptateur VLModel.
        """
        try:
            # Créer l'adaptateur VLModel compatible
            self.vlmodel = initialize_dots_ocr_model(self.model_path.get())
            self.status_var.set("Modèle initialisé")
            logger.info("Adaptateur VLModel initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du modèle: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'initialisation du modèle: {str(e)}")
            self.status_var.set("Erreur lors de l'initialisation du modèle")
    
    def browse_image(self):
        """
        Ouvre une boîte de dialogue pour sélectionner une image.
        """
        filetypes = [
            ("Images", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("Tous les fichiers", "*.*")
        ]
        
        image_path = filedialog.askopenfilename(filetypes=filetypes, title="Sélectionner une image à analyser")
        
        if image_path:
            self.image_path.set(image_path)
            self.display_image(image_path)
            self.extract_metadata(image_path)
            self.status_var.set(f"Image chargée: {os.path.basename(image_path)}")
    
    def display_image(self, image_path):
        """
        Affiche l'image sélectionnée dans le canvas.
        
        Args:
            image_path (str): Chemin vers l'image à afficher.
        """
        try:
            # Charger l'image avec PIL
            self.pil_image = Image.open(image_path)
            
            # Redimensionner l'image pour l'affichage
            self.resize_image()
            
            # Afficher l'image dans le canvas
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'image: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage de l'image: {str(e)}")
    
    def resize_image(self):
        """
        Redimensionne l'image pour l'affichage dans le canvas.
        """
        if self.pil_image is None:
            return
        
        # Obtenir les dimensions du canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # Si le canvas n'est pas encore affiché, utiliser des dimensions par défaut
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 400
            canvas_height = 400
        
        # Obtenir les dimensions de l'image
        img_width, img_height = self.pil_image.size
        
        # Calculer le ratio pour redimensionner l'image
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        ratio = min(width_ratio, height_ratio)
        
        # Redimensionner l'image
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        # Redimensionner l'image avec PIL
        resized_image = self.pil_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convertir l'image PIL en image Tkinter
        self.tk_image = ImageTk.PhotoImage(resized_image)
        
        # Configurer le canvas pour l'image
        self.image_canvas.config(width=new_width, height=new_height)
        self.image_canvas.config(scrollregion=(0, 0, new_width, new_height))
    
    def extract_metadata(self, image_path):
        """
        Extrait les métadonnées de l'image.
        
        Args:
            image_path (str): Chemin vers l'image.
        """
        try:
            # Effacer les métadonnées précédentes
            self.metadata_text.delete(1.0, tk.END)
            
            # Extraire les métadonnées de base
            image = Image.open(image_path)
            metadata = {
                "Nom du fichier": os.path.basename(image_path),
                "Chemin": image_path,
                "Format": image.format,
                "Mode": image.mode,
                "Taille": f"{image.width} x {image.height} pixels",
                "Taille du fichier": f"{os.path.getsize(image_path) / 1024:.2f} Ko"
            }
            
            # Extraire les métadonnées EXIF si disponibles
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[f"EXIF:{tag}"] = value
            
            # Afficher les métadonnées
            for key, value in metadata.items():
                self.metadata_text.insert(tk.END, f"{key}: {value}\n")
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
            self.metadata_text.insert(tk.END, f"Erreur lors de l'extraction des métadonnées: {str(e)}")
    
    def analyze_image(self):
        """
        Analyse l'image sélectionnée avec le modèle dots.ocr.
        """
        # Vérifier que l'image est sélectionnée
        image_path = self.image_path.get()
        if not image_path or not os.path.exists(image_path):
            messagebox.showerror("Erreur", "Veuillez sélectionner une image valide")
            return
        
        # Configurer le modèle
        if self.force_cpu.get():
            # Configurer le modèle pour utiliser le CPU si l'option est activée
            if hasattr(self.vlmodel, 'dots_ocr_model'):
                # Pour l'adaptateur VLModelAdapter de integration_dots_ocr.py
                self.vlmodel.dots_ocr_model.device_map = "cpu"
                self.vlmodel.dots_ocr_model.torch_dtype = torch.float32
                self.vlmodel.dots_ocr_model.load_in_4bit = False
            else:
                # Fallback pour d'autres implémentations
                self.vlmodel.device_map = "cpu"
                self.vlmodel.torch_dtype = torch.float32
                self.vlmodel.load_in_4bit = False
            logger.info("Utilisation forcée du CPU pour l'analyse")
        
        # Mettre à jour le statut
        self.status_var.set("Analyse en cours...")
        self.progress_var.set(10)
        self.root.update_idletasks()
        
        # Lancer l'analyse dans un thread séparé
        threading.Thread(target=self._analyze_image_thread, args=(image_path,), daemon=True).start()
    
    def _analyze_image_thread(self, image_path):
        """
        Thread pour l'analyse de l'image.
        
        Args:
            image_path (str): Chemin vers l'image à analyser.
        """
        try:
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(20))
            
            # Charger le modèle
            self.root.after(0, lambda: self.status_var.set("Chargement du modèle..."))
            result = self.vlmodel.load_model()
            if not result:
                self.root.after(0, lambda: self.status_var.set("Erreur lors du chargement du modèle"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Impossible de charger le modèle dots.ocr"))
                return
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(50))
            
            # Analyser l'image
            self.root.after(0, lambda: self.status_var.set("Analyse de l'image..."))
            prompt = "Décris cette image en détail et identifie les risques environnementaux potentiels."
            result = self.vlmodel.analyze_image(image_path, prompt)
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(90))
            
            # Afficher le résultat
            if result:
                self.root.after(0, lambda: self.results_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.results_text.insert(tk.END, result))
                self.root.after(0, lambda: self.status_var.set("Analyse terminée"))
                self.root.after(0, lambda: self.notebook.select(self.results_frame))
            else:
                self.root.after(0, lambda: self.status_var.set("Erreur lors de l'analyse"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Échec de l'analyse de l'image"))
            
            # Libérer la mémoire
            self.vlmodel.unload_model()
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(100))
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
            self.root.after(0, lambda: self.status_var.set(f"Erreur: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Erreur", f"Erreur lors de l'analyse de l'image: {str(e)}"))
            
            # Libérer la mémoire en cas d'erreur
            try:
                self.vlmodel.unload_model()
            except:
                pass
    
    def analyze_text(self):
        """
        Analyse le texte extrait de l'image.
        """
        messagebox.showinfo("Information", "Fonctionnalité non implémentée")
    
    def visualize_image(self):
        """
        Visualise l'image avec des annotations.
        """
        messagebox.showinfo("Information", "Fonctionnalité non implémentée")
    
    def save_results(self):
        """
        Enregistre les résultats de l'analyse.
        """
        # Vérifier qu'il y a des résultats à enregistrer
        results = self.results_text.get(1.0, tk.END).strip()
        if not results:
            messagebox.showwarning("Avertissement", "Aucun résultat à enregistrer")
            return
        
        # Ouvrir une boîte de dialogue pour sélectionner le fichier de destination
        filetypes = [
            ("Fichiers texte", "*.txt"),
            ("Tous les fichiers", "*.*")
        ]
        
        file_path = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=".txt", title="Enregistrer les résultats")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(results)
                
                self.status_var.set(f"Résultats enregistrés dans {os.path.basename(file_path)}")
                messagebox.showinfo("Information", f"Résultats enregistrés dans {file_path}")
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement des résultats: {str(e)}")
                messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement des résultats: {str(e)}")
    
    def show_settings(self):
        """
        Affiche la boîte de dialogue des paramètres.
        """
        # Créer une fenêtre de dialogue
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("Paramètres")
        settings_dialog.geometry("500x300")
        settings_dialog.resizable(False, False)
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # Frame pour les paramètres
        settings_frame = ttk.Frame(settings_dialog, padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Paramètres du modèle
        ttk.Label(settings_frame, text="Chemin du modèle:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.model_path, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        ttk.Button(settings_frame, text="Parcourir", command=self.browse_model).grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Force CPU
        ttk.Checkbutton(settings_frame, text="Forcer l'utilisation du CPU", variable=self.force_cpu).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Boutons
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)
        
        ttk.Button(button_frame, text="OK", command=settings_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Appliquer", command=self.apply_settings).pack(side=tk.RIGHT, padx=5)
        
        # Configuration du grid pour le redimensionnement
        settings_frame.columnconfigure(1, weight=1)
    
    def browse_model(self):
        """
        Ouvre une boîte de dialogue pour sélectionner le répertoire du modèle.
        """
        model_path = filedialog.askdirectory(title="Sélectionner le répertoire du modèle")
        
        if model_path:
            self.model_path.set(model_path)
    
    def apply_settings(self):
        """
        Applique les paramètres.
        """
        # Réinitialiser le modèle avec les nouveaux paramètres
        try:
            # Décharger le modèle existant
            if self.vlmodel is not None:
                self.vlmodel.unload_model()
            
            # Créer un nouvel adaptateur VLModel
            self.vlmodel = create_vlmodel_adapter(self.model_path.get())
            
            # Configurer le modèle
            if self.force_cpu.get():
                self.vlmodel.device_map = "cpu"
                self.vlmodel.torch_dtype = torch.float32
                self.vlmodel.load_in_4bit = False
            
            self.status_var.set("Paramètres appliqués")
            messagebox.showinfo("Information", "Paramètres appliqués avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'application des paramètres: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'application des paramètres: {str(e)}")
    
    def show_help(self):
        """
        Affiche l'aide de l'application.
        """
        help_text = """
# Aide - Analyse de Risque Environnemental

## Utilisation

1. Sélectionnez une image à analyser en cliquant sur le bouton "Parcourir".
2. Cliquez sur le bouton "Analyser" pour lancer l'analyse de l'image.
3. Les résultats de l'analyse seront affichés dans l'onglet "Résultats".
4. Vous pouvez enregistrer les résultats en cliquant sur le bouton "Enregistrer".

## Paramètres

- **Forcer l'utilisation du CPU**: Cochez cette case pour forcer l'utilisation du CPU au lieu du GPU.
- **Chemin du modèle**: Spécifiez le chemin vers le modèle dots.ocr.

## Résolution des problèmes

Si vous rencontrez l'erreur "VLModel object has no attribute load_model", cela signifie que l'interface VLModel n'est pas correctement implémentée. Cette application utilise un adaptateur VLModel qui résout ce problème.

## Contact

Pour toute question ou problème, veuillez contacter le support technique.
"""
        
        # Créer une fenêtre de dialogue
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Aide")
        help_dialog.geometry("600x400")
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        
        # Zone de texte pour l'aide
        help_text_widget = scrolledtext.ScrolledText(help_dialog, wrap=tk.WORD, width=80, height=30)
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
    
    def show_about(self):
        """
        Affiche les informations sur l'application.
        """
        about_text = """
# Analyse de Risque Environnemental - Masec

## Version
1.0.0

## Description
Cette application permet d'analyser des images pour identifier les risques environnementaux potentiels.

## Modèle
Cette application utilise le modèle dots.ocr pour l'analyse d'images.

## Licence
Tous droits réservés.
"""
        
        # Créer une fenêtre de dialogue
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("À propos")
        about_dialog.geometry("400x300")
        about_dialog.resizable(False, False)
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Zone de texte pour les informations
        about_text_widget = scrolledtext.ScrolledText(about_dialog, wrap=tk.WORD, width=50, height=20)
        about_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        about_text_widget.insert(tk.END, about_text)
        about_text_widget.config(state=tk.DISABLED)
        
        # Bouton OK
        ttk.Button(about_dialog, text="OK", command=about_dialog.destroy).pack(pady=10)
    
    def quit_app(self):
        """
        Quitte l'application en libérant la mémoire.
        """
        try:
            # Libérer la mémoire
            if self.vlmodel is not None:
                self.vlmodel.unload_model()
            
            # Quitter l'application
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de l'application: {str(e)}")
            sys.exit(1)

def main():
    # Créer la fenêtre principale
    root = tk.Tk()
    
    # Appliquer un thème
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    # Créer l'application
    app = AnalyseRisqueApp(root)
    
    # Configurer le redimensionnement de l'image lors du redimensionnement de la fenêtre
    def on_resize(event):
        app.resize_image()
    
    root.bind("<Configure>", on_resize)
    
    # Configurer la fermeture de l'application
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    
    # Lancer la boucle principale
    root.mainloop()

if __name__ == "__main__":
    # Importer les modules nécessaires pour les métadonnées EXIF
    try:
        from PIL.ExifTags import TAGS
    except ImportError:
        TAGS = {}
        logger.warning("Module PIL.ExifTags non disponible, les métadonnées EXIF ne seront pas affichées")
    
    main()