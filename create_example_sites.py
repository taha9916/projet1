import pandas as pd

# Créer un DataFrame avec des exemples de sites à analyser
sites = [
    {"id": 1, "nom_site": "Rabat Centre", "latitude": 34.0209, "longitude": -6.8416, "type": "Urbain", "risque_initial": "Moyen"},
    {"id": 2, "nom_site": "Casablanca Port", "latitude": 33.6032, "longitude": -7.6226, "type": "Industriel", "risque_initial": "Élevé"},
    {"id": 3, "nom_site": "Marrakech Médina", "latitude": 31.6295, "longitude": -7.9811, "type": "Touristique", "risque_initial": "Faible"},
    {"id": 4, "nom_site": "Tanger Med", "latitude": 35.8984, "longitude": -5.5059, "type": "Portuaire", "risque_initial": "Élevé"},
    {"id": 5, "nom_site": "Agadir Plage", "latitude": 30.4202, "longitude": -9.6026, "type": "Côtier", "risque_initial": "Moyen"}
]

# Créer le DataFrame
df = pd.DataFrame(sites)

# Enregistrer dans un fichier Excel
df.to_excel("exemple_sites.xlsx", index=False)

print("Fichier exemple_sites.xlsx créé avec succès.")
print("Contenu:")
print(df)