import os
import sys
import logging
import time
import pandas as pd
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importer les fonctions nécessaires
try:
    from cloud_api import CloudVisionAPI
    logger.info("Module CloudVisionAPI importé avec succès.")
except ImportError as e:
    logger.error(f"Impossible d'importer CloudVisionAPI: {e}")
    logger.error("Assurez-vous que le fichier cloud_api.py est présent dans le répertoire.")
    sys.exit(1)

def extraire_donnees_rapport(fichier_path, type_rapport="environnement", format_sortie="dataframe"):
    """
    Extrait les données d'un rapport en utilisant dots.ocr.
    
    Args:
        fichier_path (str): Chemin vers le fichier rapport (image ou PDF)
        type_rapport (str): Type de rapport ('environnement', 'pollution', 'biodiversite', etc.)
        format_sortie (str): Format de sortie ('dataframe', 'json', 'dict', 'markdown')
        
    Returns:
        Union[pd.DataFrame, dict, str]: Données extraites dans le format spécifié
    """
    if not os.path.exists(fichier_path):
        logger.error(f"Le fichier {fichier_path} n'existe pas.")
        return None
    
    # Vérifier l'extension du fichier
    _, extension = os.path.splitext(fichier_path)
    extension = extension.lower()
    
    # Traiter différemment selon le type de fichier
    if extension in [".jpg", ".jpeg", ".png"]:
        return _extraire_donnees_image(fichier_path, type_rapport, format_sortie)
    elif extension == ".pdf":
        return _extraire_donnees_pdf(fichier_path, type_rapport, format_sortie)
    else:
        logger.error(f"Format de fichier non supporté: {extension}")
        return None

def _extraire_donnees_image(image_path, type_rapport, format_sortie):
    """
    Extrait les données d'une image de rapport en utilisant dots.ocr.
    """
    try:
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(api_provider="dots_ocr")
        
        # Construire le prompt selon le type de rapport
        prompt = _generer_prompt(type_rapport)
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Analyser l'image
        logger.info(f"Analyse de l'image {image_path} avec dots.ocr...")
        df, response = api.analyze_image(image_path, prompt)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        logger.info(f"Analyse terminée en {execution_time:.2f} secondes.")
        
        # Formater la sortie selon le format demandé
        resultat = _formater_sortie(df, response, format_sortie)
        
        # Libérer la mémoire
        if hasattr(api, 'cleanup'):
            api.cleanup()
        
        return resultat
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des données de l'image: {e}")
        return None

def _extraire_donnees_pdf(pdf_path, type_rapport, format_sortie):
    """
    Extrait les données d'un PDF en utilisant dots.ocr page par page.
    """
    try:
        import fitz  # PyMuPDF
        
        logger.info(f"Extraction des données du PDF {pdf_path}...")
        
        # Ouvrir le PDF
        pdf_document = fitz.open(pdf_path)
        nombre_pages = pdf_document.page_count
        logger.info(f"Le PDF contient {nombre_pages} pages.")
        
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(api_provider="dots_ocr")
        
        # Construire le prompt selon le type de rapport
        prompt = _generer_prompt(type_rapport)
        
        # Initialiser les résultats
        resultats_combines = []
        reponses_combinees = ""
        
        # Traiter chaque page
        for i in range(nombre_pages):
            logger.info(f"Traitement de la page {i+1}/{nombre_pages}...")
            
            # Extraire l'image de la page
            page = pdf_document.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # Résolution 300 DPI
            
            # Sauvegarder l'image temporairement
            temp_image_path = f"temp_page_{i+1}.png"
            pix.save(temp_image_path)
            
            # Analyser l'image
            try:
                df, response = api.analyze_image(temp_image_path, prompt)
                if df is not None and not df.empty:
                    resultats_combines.append(df)
                if response:
                    reponses_combinees += f"\n\n--- PAGE {i+1} ---\n\n{response}"
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de la page {i+1}: {e}")
            
            # Supprimer l'image temporaire
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        
        # Fermer le PDF
        pdf_document.close()
        
        # Combiner les résultats
        if resultats_combines:
            df_combinee = pd.concat(resultats_combines, ignore_index=True)
        else:
            df_combinee = pd.DataFrame()
        
        # Formater la sortie selon le format demandé
        resultat = _formater_sortie(df_combinee, reponses_combinees, format_sortie)
        
        # Libérer la mémoire
        if hasattr(api, 'cleanup'):
            api.cleanup()
        
        return resultat
    except ImportError:
        logger.error("PyMuPDF (fitz) est requis pour traiter les PDF. Installez-le avec 'pip install pymupdf'.")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des données du PDF: {e}")
        return None

def _generer_prompt(type_rapport):
    """
    Génère un prompt adapté au type de rapport.
    """
    prompts = {
        "environnement": """Analyse ce rapport environnemental et extrait toutes les données pertinentes.

Identifie les paramètres environnementaux, leurs valeurs, unités, et seuils réglementaires.
Présente les résultats sous forme de tableau Markdown avec les colonnes suivantes:
| Paramètre | Valeur | Unité | Seuil réglementaire | Conformité | Observations |

Si des tableaux sont présents dans l'image, reproduis-les fidèlement.
Pour les valeurs numériques, assure-toi de préserver la précision exacte.
Si certaines informations ne sont pas visibles, indique-le clairement.""",
        
        "pollution": """Analyse ce rapport de pollution et extrait toutes les données pertinentes.

Identifie les polluants, leurs concentrations, unités, et seuils réglementaires.
Présente les résultats sous forme de tableau Markdown avec les colonnes suivantes:
| Polluant | Concentration | Unité | Seuil réglementaire | Dépassement | Impact potentiel |

Si des tableaux sont présents dans l'image, reproduis-les fidèlement.
Pour les valeurs numériques, assure-toi de préserver la précision exacte.
Si certaines informations ne sont pas visibles, indique-le clairement.""",
        
        "biodiversite": """Analyse ce rapport de biodiversité et extrait toutes les données pertinentes.

Identifie les espèces, leur abondance, statut de conservation, et tendances.
Présente les résultats sous forme de tableau Markdown avec les colonnes suivantes:
| Espèce | Abondance | Statut de conservation | Tendance | Habitat | Menaces |

Si des tableaux sont présents dans l'image, reproduis-les fidèlement.
Pour les valeurs numériques, assure-toi de préserver la précision exacte.
Si certaines informations ne sont pas visibles, indique-le clairement.""",
    }
    
    # Retourner le prompt correspondant au type de rapport ou un prompt par défaut
    return prompts.get(type_rapport.lower(), prompts["environnement"])

def _formater_sortie(df, response, format_sortie):
    """
    Formate la sortie selon le format demandé.
    """
    if format_sortie.lower() == "dataframe":
        return df
    elif format_sortie.lower() == "json":
        try:
            return df.to_json(orient="records")
        except:
            return {"raw_response": response}
    elif format_sortie.lower() == "dict":
        try:
            return df.to_dict(orient="records")
        except:
            return {"raw_response": response}
    elif format_sortie.lower() == "markdown":
        try:
            return df.to_markdown(index=False)
        except:
            return response
    else:
        return response

def extraire_tableaux_markdown(texte):
    """
    Extrait les tableaux au format Markdown d'un texte.
    
    Args:
        texte (str): Texte contenant des tableaux Markdown
        
    Returns:
        list: Liste des tableaux extraits
    """
    if not texte:
        return []
    
    tableaux = []
    lignes = texte.split('\n')
    tableau_en_cours = []
    dans_tableau = False
    
    for ligne in lignes:
        if ligne.startswith('|') and '-|-' in ligne.replace(' ', ''):
            # Début d'un tableau ou ligne de séparation
            dans_tableau = True
            tableau_en_cours.append(ligne)
        elif dans_tableau and ligne.startswith('|'):
            # Ligne de tableau
            tableau_en_cours.append(ligne)
        elif dans_tableau:
            # Fin du tableau
            dans_tableau = False
            if tableau_en_cours:
                tableaux.append('\n'.join(tableau_en_cours))
                tableau_en_cours = []
    
    # Ajouter le dernier tableau s'il existe
    if dans_tableau and tableau_en_cours:
        tableaux.append('\n'.join(tableau_en_cours))
    
    return tableaux

def convertir_tableaux_en_dataframes(tableaux):
    """
    Convertit une liste de tableaux Markdown en DataFrames pandas.
    
    Args:
        tableaux (list): Liste de tableaux au format Markdown
        
    Returns:
        list: Liste de DataFrames pandas
    """
    import io
    import pandas as pd
    
    dataframes = []
    
    for tableau in tableaux:
        try:
            # Utiliser pandas pour lire le tableau Markdown
            df = pd.read_csv(io.StringIO(tableau), sep='|', skipinitialspace=True)
            
            # Nettoyer les noms de colonnes
            df.columns = [col.strip() for col in df.columns]
            
            # Supprimer les colonnes vides (dues aux | aux extrémités)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            dataframes.append(df)
        except Exception as e:
            logger.warning(f"Erreur lors de la conversion du tableau en DataFrame: {e}")
    
    return dataframes

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python extraire_donnees_rapports.py <chemin_fichier> [type_rapport] [format_sortie]")
        print("  type_rapport: environnement (par défaut), pollution, biodiversite")
        print("  format_sortie: dataframe (par défaut), json, dict, markdown")
        return
    
    # Récupérer les arguments
    fichier_path = sys.argv[1]
    type_rapport = sys.argv[2] if len(sys.argv) > 2 else "environnement"
    format_sortie = sys.argv[3] if len(sys.argv) > 3 else "dataframe"
    
    # Extraire les données du rapport
    resultat = extraire_donnees_rapport(fichier_path, type_rapport, format_sortie)
    
    # Afficher le résultat
    if resultat is not None:
        if isinstance(resultat, pd.DataFrame):
            print("\nDonnées extraites (DataFrame):")
            print(resultat.to_string(index=False))
        elif isinstance(resultat, dict):
            print("\nDonnées extraites (Dict):")
            for cle, valeur in resultat.items():
                print(f"{cle}: {valeur}")
        elif isinstance(resultat, str):
            print("\nDonnées extraites:")
            print(resultat)
        
        # Sauvegarder les résultats
        nom_fichier = os.path.splitext(os.path.basename(fichier_path))[0]
        if isinstance(resultat, pd.DataFrame):
            fichier_sortie = f"{nom_fichier}_resultats.xlsx"
            resultat.to_excel(fichier_sortie, index=False)
            print(f"\nRésultats sauvegardés dans {fichier_sortie}")
    else:
        logger.error("Échec de l'extraction des données du rapport.")

if __name__ == "__main__":
    main()