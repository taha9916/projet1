#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface graphique de démonstration pour le modèle dots.ocr.

Cette interface permet de sélectionner une image, de l'analyser avec le modèle dots.ocr
et d'afficher le résultat. Elle montre comment intégrer la classe DotsOCRModel
dans une application avec interface graphique.
"""

import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import torch

# Import de la classe DotsOCRModel
from dots_ocr_model import DotsOCRModel

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DotsOCRApp:
    """
    Interface graphique pour le modèle dots.ocr.
    """
    
    def __init__(self, root):
        """
        Initialise l'interface graphique.
        
        Args:
            root (tk.Tk): Fenêtre principale de l'application.
        """
        self.root = root
        self.root.title("Analyse d'images avec dots.ocr")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.image_path = tk.StringVar()
        self.prompt = tk.StringVar()
        self.force_cpu = tk.BooleanVar(value=False)
        self.model = None
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
        
        # Prompt
        ttk.Label(control_frame, text="Prompt:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(control_frame, textvariable=self.prompt, width=50).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Force CPU
        ttk.Checkbutton(control_frame, text="Forcer l'utilisation du CPU", variable=self.force_cpu).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Boutons d'action
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)
        
        ttk.Button(button_frame, text="Analyser", command=self.analyze_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Effacer", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Quitter", command=self.quit_app).pack(side=tk.RIGHT, padx=5)
        
        # Configuration du grid pour le redimensionnement
        control_frame.columnconfigure(1, weight=1)
        
        # Frame pour l'affichage
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Paned window pour séparer l'image et le résultat
        paned_window = ttk.PanedWindow(display_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour l'image
        self.image_frame = ttk.LabelFrame(paned_window, text="Image", padding=10)
        paned_window.add(self.image_frame, weight=1)
        
        # Canvas pour l'image
        self.image_canvas = tk.Canvas(self.image_frame, bg="white")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour le résultat
        result_frame = ttk.LabelFrame(paned_window, text="Résultat", padding=10)
        paned_window.add(result_frame, weight=1)
        
        # Zone de texte pour le résultat
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=40, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Barre de progression
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def initialize_model(self):
        """
        Initialise le modèle dots.ocr.
        """
        try:
            self.model = DotsOCRModel()
            self.status_var.set("Modèle initialisé")
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
        
        image_path = filedialog.askopenfilename(filetypes=filetypes, title="Sélectionner une image")
        
        if image_path:
            self.image_path.set(image_path)
            self.display_image(image_path)
    
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
            
            # Mettre à jour le statut
            self.status_var.set(f"Image chargée: {os.path.basename(image_path)}")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'image: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage de l'image: {str(e)}")
            self.status_var.set("Erreur lors de l'affichage de l'image")
    
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
            self.model.device_map = "cpu"
            self.model.torch_dtype = torch.float32
            self.model.load_in_4bit = False
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
            result = self.model.load_model()
            if not result:
                self.root.after(0, lambda: self.status_var.set("Erreur lors du chargement du modèle"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Impossible de charger le modèle dots.ocr"))
                return
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(50))
            
            # Analyser l'image
            self.root.after(0, lambda: self.status_var.set("Analyse de l'image..."))
            prompt = self.prompt.get()
            result = self.model.analyze_image(image_path, prompt)
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(90))
            
            # Afficher le résultat
            if result:
                self.root.after(0, lambda: self.result_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.result_text.insert(tk.END, result))
                self.root.after(0, lambda: self.status_var.set("Analyse terminée"))
            else:
                self.root.after(0, lambda: self.status_var.set("Erreur lors de l'analyse"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Échec de l'analyse de l'image"))
            
            # Libérer la mémoire
            self.model.unload_model()
            
            # Mettre à jour la progression
            self.root.after(0, lambda: self.progress_var.set(100))
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
            self.root.after(0, lambda: self.status_var.set(f"Erreur: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Erreur", f"Erreur lors de l'analyse de l'image: {str(e)}"))
            
            # Libérer la mémoire en cas d'erreur
            try:
                self.model.unload_model()
            except:
                pass
    
    def clear_results(self):
        """
        Efface les résultats et réinitialise l'interface.
        """
        # Effacer le chemin de l'image
        self.image_path.set("")
        
        # Effacer le prompt
        self.prompt.set("")
        
        # Effacer l'image
        self.image_canvas.delete("all")
        self.pil_image = None
        self.tk_image = None
        
        # Effacer le résultat
        self.result_text.delete(1.0, tk.END)
        
        # Réinitialiser la progression
        self.progress_var.set(0)
        
        # Mettre à jour le statut
        self.status_var.set("Prêt")
    
    def quit_app(self):
        """
        Quitte l'application en libérant la mémoire.
        """
        try:
            # Libérer la mémoire
            if self.model is not None:
                self.model.unload_model()
            
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
    app = DotsOCRApp(root)
    
    # Configurer le redimensionnement de l'image lors du redimensionnement de la fenêtre
    def on_resize(event):
        app.resize_image()
    
    root.bind("<Configure>", on_resize)
    
    # Configurer la fermeture de l'application
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    
    # Lancer la boucle principale
    root.mainloop()

if __name__ == "__main__":
    main()