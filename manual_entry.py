import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import logging
from config import UI_CONFIG

logger = logging.getLogger(__name__)

class ManualEntryWindow(tk.Toplevel):
    """Fenêtre pour la saisie manuelle des paramètres environnementaux."""
    def __init__(self, parent, callback=None, initial_data=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.initial_data = initial_data if initial_data is not None else pd.DataFrame(columns=["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée"])
        
        # Configuration de la fenêtre
        self.title("Saisie manuelle des paramètres")
        self.geometry("800x600")
        self.transient(parent)  # Fenêtre modale
        self.grab_set()  # Capture les événements
        
        # Initialiser les widgets
        self._create_widgets()
        
        # Remplir avec les données initiales si disponibles
        if not self.initial_data.empty:
            self._populate_data()
    
    def _create_widgets(self):
        # Cadre principal
        main_frame = ttk.Frame(self, padding=UI_CONFIG["padding"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section pour télécharger un fichier PDF/image
        upload_frame = ttk.LabelFrame(main_frame, text="Télécharger un rapport")
        upload_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(upload_frame, text="Télécharger un rapport PDF ou une image:").pack(pady=5)
        
        upload_button_frame = ttk.Frame(upload_frame)
        upload_button_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(upload_button_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(upload_button_frame, text="Parcourir", command=self._browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(upload_button_frame, text="Analyser", command=self._analyze_file).pack(side=tk.LEFT, padx=5)
        
        # Séparateur
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Section pour la saisie manuelle
        manual_frame = ttk.LabelFrame(main_frame, text="Saisie manuelle des paramètres")
        manual_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tableau pour afficher et modifier les paramètres
        table_frame = ttk.Frame(manual_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Créer le tableau avec Treeview
        columns = ("Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Définir les en-têtes de colonnes
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Ajouter une barre de défilement
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Placer le tableau et la barre de défilement
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Lier le double-clic pour éditer une ligne
        self.tree.bind("<Double-1>", self._edit_item)
        
        # Boutons pour ajouter/supprimer des lignes
        button_frame = ttk.Frame(manual_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Ajouter un paramètre", command=self._add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Supprimer le paramètre sélectionné", command=self._remove_item).pack(side=tk.LEFT, padx=5)
        
        # Boutons de validation
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Annuler", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Valider", command=self._validate).pack(side=tk.RIGHT, padx=5)
    
    def _browse_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier PDF ou image."""
        filetypes = [
            ("Documents PDF", "*.pdf"),
            ("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")
        ]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            self.file_path_var.set(file_path)
    
    def _analyze_file(self):
        """Analyse le fichier sélectionné et extrait les paramètres."""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("Aucun fichier sélectionné", "Veuillez sélectionner un fichier à analyser.")
            return
        
        # Appeler la fonction d'analyse du parent (app.py)
        if self.callback:
            # Fermer cette fenêtre
            self.destroy()
            # Appeler le callback avec le chemin du fichier
            self.callback(file_path, mode="analyze")
    
    def _add_item(self):
        """Ajoute un nouvel élément au tableau."""
        # Ouvrir une fenêtre de dialogue pour saisir les informations
        self._edit_dialog()
    
    def _remove_item(self):
        """Supprime l'élément sélectionné du tableau."""
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
    
    def _edit_item(self, event):
        """Édite l'élément sélectionné."""
        selected_item = self.tree.selection()
        if selected_item:
            item = selected_item[0]
            values = self.tree.item(item, "values")
            self._edit_dialog(item, values)
    
    def _edit_dialog(self, item=None, values=None):
        """Ouvre une boîte de dialogue pour éditer ou ajouter un élément."""
        dialog = tk.Toplevel(self)
        dialog.title("Éditer le paramètre" if item else "Ajouter un paramètre")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Créer les champs de saisie
        ttk.Label(dialog, text="Milieu:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        milieu_var = tk.StringVar(value=values[0] if values else "")
        milieu_combo = ttk.Combobox(dialog, textvariable=milieu_var, values=["Eau", "Air", "Sol", "Bruit"])
        milieu_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(dialog, text="Paramètre:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        parametre_var = tk.StringVar(value=values[1] if values else "")
        ttk.Entry(dialog, textvariable=parametre_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(dialog, text="Unité:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        unite_var = tk.StringVar(value=values[2] if values else "")
        ttk.Entry(dialog, textvariable=unite_var).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(dialog, text="Intervalle acceptable:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        intervalle_var = tk.StringVar(value=values[3] if values else "")
        ttk.Entry(dialog, textvariable=intervalle_var).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(dialog, text="Valeur mesurée:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        valeur_var = tk.StringVar(value=values[4] if values else "")
        ttk.Entry(dialog, textvariable=valeur_var).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Boutons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        def save_item():
            new_values = (milieu_var.get(), parametre_var.get(), unite_var.get(), 
                          intervalle_var.get(), valeur_var.get())
            
            # Vérifier que les champs obligatoires sont remplis
            if not new_values[1]:  # Paramètre obligatoire
                messagebox.showwarning("Champ obligatoire", "Le champ 'Paramètre' est obligatoire.")
                return
            
            if item:  # Mise à jour d'un élément existant
                self.tree.item(item, values=new_values)
            else:  # Ajout d'un nouvel élément
                self.tree.insert("", tk.END, values=new_values)
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Enregistrer", command=save_item).pack(side=tk.LEFT, padx=5)
    
    def _populate_data(self):
        """Remplit le tableau avec les données initiales."""
        for _, row in self.initial_data.iterrows():
            values = (row["Milieu"], row["Paramètre"], row["Unité"], 
                      row["Intervalle acceptable"], row["Valeur mesurée"])
            self.tree.insert("", tk.END, values=values)
    
    def _validate(self):
        """Valide les données saisies et les renvoie au callback."""
        # Récupérer toutes les données du tableau
        data = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            data.append({
                "Milieu": values[0],
                "Paramètre": values[1],
                "Unité": values[2],
                "Intervalle acceptable": values[3],
                "Valeur mesurée": values[4]
            })
        
        # Créer un DataFrame
        df = pd.DataFrame(data)
        
        # Vérifier si des données ont été saisies
        if df.empty:
            messagebox.showwarning("Aucune donnée", "Veuillez saisir au moins un paramètre.")
            return
        
        # Appeler le callback avec les données
        if self.callback:
            self.callback(df, mode="manual")
        
        # Fermer la fenêtre
        self.destroy()