#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module amélioré pour l'extraction des paramètres environnementaux à partir des réponses de l'API Cloud.

Ce module contient des versions améliorées des fonctions d'extraction de données tabulaires
du fichier cloud_api.py, avec une meilleure gestion de l'encodage et une validation plus souple
des en-têtes de tableau.
"""

import re
import unicodedata
import pandas as pd
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalise le texte en supprimant les accents et en convertissant en minuscules.
    
    Args:
        text (str): Texte à normaliser
        
    Returns:
        str: Texte normalisé
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Normaliser les caractères Unicode (NFD décompose les caractères accentués)
    normalized = unicodedata.normalize('NFD', text)
    # Supprimer les caractères diacritiques (accents)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Convertir en minuscules
    return normalized.lower()

def _extract_parameters_improved(response_text):
    """
    Version améliorée de la fonction _extract_parameters pour extraire les paramètres environnementaux
    d'une réponse textuelle, avec une meilleure gestion de l'encodage et une validation plus souple
    des en-têtes de tableau.
    
    Args:
        response_text (str): Texte de la réponse contenant potentiellement des données tabulaires
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres extraits
    """
    try:
        # Initialiser la liste pour stocker les données extraites
        data = []
        
        # Diviser le texte en lignes
        lines = response_text.split('\n')
        
        # Journaliser pour le débogage
        logger.info(f"Analyse de la réponse avec {len(lines)} lignes")
        
        # Rechercher des tableaux Markdown dans le texte
        table_lines = []
        in_table = False
        table_start_index = -1
        
        # Première passe: rechercher des tableaux bien formatés
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Journaliser la ligne pour le débogage
            logger.debug(f"Ligne {i}: '{line}'")
            
            # Vérifier si la ligne commence et se termine par des pipes (|)
            if line.startswith('|') and line.endswith('|'):
                if not in_table:
                    in_table = True
                    table_start_index = i
                table_lines.append(line)
            elif in_table and (not line or not line.strip()):
                # Ignorer les lignes vides à l'intérieur d'un tableau
                continue
            elif in_table:
                # Si nous étions dans un tableau mais cette ligne n'en fait pas partie,
                # nous sommes sortis du tableau
                in_table = False
                
                # Si nous avons trouvé un tableau complet (au moins 3 lignes: en-tête, séparateur, données)
                if len(table_lines) >= 3:
                    logger.info(f"Tableau complet trouvé avec {len(table_lines)} lignes")
                    break
                else:
                    # Réinitialiser et continuer à chercher un tableau plus complet
                    logger.info(f"Tableau incomplet trouvé avec {len(table_lines)} lignes, continuons à chercher")
                    table_lines = []
        
        # Si nous sommes toujours dans un tableau à la fin du texte
        if in_table and len(table_lines) < 3:
            logger.info(f"Tableau incomplet à la fin du texte: {len(table_lines)} lignes")
            # Réinitialiser si le tableau est trop petit
            if len(table_lines) < 2:
                table_lines = []
        
        # Deuxième passe: si aucun tableau bien formaté n'est trouvé, rechercher des lignes avec des pipes
        if not table_lines:
            logger.info("Recherche de tableaux mal formatés...")
            # Rechercher des lignes qui contiennent plusieurs pipes
            potential_table_lines = []
            for i, line in enumerate(lines):
                line = line.strip()
                # Compter le nombre de pipes dans la ligne
                pipe_count = line.count('|')
                if pipe_count >= 2:  # Au moins 3 colonnes (2 séparateurs)
                    potential_table_lines.append((i, line))
            
            # Vérifier si nous avons des lignes consécutives avec des pipes
            if len(potential_table_lines) >= 3:  # Au moins en-tête, séparateur, données
                consecutive_lines = []
                current_group = []
                
                for i in range(len(potential_table_lines) - 1):
                    current_idx, current_line = potential_table_lines[i]
                    next_idx, next_line = potential_table_lines[i + 1]
                    
                    if not current_group:
                        current_group.append((current_idx, current_line))
                    
                    # Vérifier si les lignes sont consécutives ou presque (max 2 lignes d'écart)
                    if next_idx - current_idx <= 3:
                        current_group.append((next_idx, next_line))
                    else:
                        # Fin d'un groupe
                        if len(current_group) >= 3:
                            consecutive_lines = current_group
                            break
                        current_group = [(next_idx, next_line)]
                
                # Vérifier le dernier groupe
                if len(current_group) >= 3 and not consecutive_lines:
                    consecutive_lines = current_group
                
                # Si nous avons trouvé des lignes consécutives, les considérer comme un tableau
                if consecutive_lines:
                    logger.info(f"Tableau potentiel trouvé avec {len(consecutive_lines)} lignes consécutives")
                    table_lines = [line for _, line in consecutive_lines]
                    # Ajouter des pipes au début et à la fin si nécessaire
                    table_lines = [f"|{line}|" if not line.startswith('|') else line for line in table_lines]
                    table_lines = [f"{line}|" if not line.endswith('|') else line for line in table_lines]
        
        # Journaliser les lignes de tableau trouvées
        if table_lines:
            logger.info(f"Lignes de tableau trouvées: {len(table_lines)}")
            for i, line in enumerate(table_lines):
                logger.info(f"Ligne {i}: {line}")
        else:
            logger.info("Aucune ligne de tableau trouvée dans la réponse")
            # Afficher les 10 premières lignes de la réponse pour le débogage
            for i, line in enumerate(lines[:10]):
                logger.info(f"Ligne de réponse {i}: {line}")
            if len(lines) > 10:
                logger.info(f"... et {len(lines) - 10} lignes supplémentaires")
        
        # Traiter le tableau Markdown s'il existe
        if table_lines:
            # Extraire les en-têtes du tableau
            headers = []
            header_found = False
            separator_found = False
            separator_index = -1
            
            # Première passe: identifier les en-têtes et les séparateurs
            for i, line in enumerate(table_lines):
                # Identifier la ligne de séparation (ex: |---|---|---|)
                if re.search(r'\|\s*[-:]+\s*\|', line):
                    logger.info(f"Ligne de séparation trouvée: {line}")
                    separator_found = True
                    separator_index = i
                    continue
                
                # Si nous n'avons pas encore trouvé d'en-têtes et que ce n'est pas une ligne de séparation
                if not header_found and (not separator_found or i < separator_index):
                    # Extraire les en-têtes potentiels
                    parts = [p.strip() for p in line.split('|')]
                    parts = [p for p in parts if p]  # Supprimer les éléments vides
                    
                    if parts and len(parts) >= 2:
                        headers = parts
                        header_found = True
                        logger.info(f"En-têtes potentiels trouvés: {headers}")
            
            # Si nous n'avons pas trouvé de ligne de séparation mais que nous avons des en-têtes,
            # considérer la deuxième ligne comme séparateur implicite
            if headers and not separator_found and len(table_lines) >= 2:
                logger.info("Pas de ligne de séparation trouvée, utilisation de la deuxième ligne comme séparateur implicite")
                separator_found = True
                separator_index = 1  # Considérer la deuxième ligne comme séparateur
            
            # Si nous n'avons pas trouvé d'en-têtes mais que nous avons une ligne de séparation,
            # considérer la première ligne comme en-têtes
            if not header_found and separator_found and separator_index > 0:
                # Extraire les en-têtes de la première ligne
                first_line = table_lines[0]
                parts = [p.strip() for p in first_line.split('|')]
                parts = [p for p in parts if p]  # Supprimer les éléments vides
                
                if parts and len(parts) >= 2:
                    headers = parts
                    header_found = True
                    logger.info(f"En-têtes extraits de la première ligne: {headers}")
            
            # Si nous avons trouvé des en-têtes et une ligne de séparation, traiter les données
            if headers and (separator_found or len(table_lines) >= 2):
                # Deuxième passe: extraire les données (ignorer les en-têtes et les séparateurs)
                data_started = False
                header_line_index = -1
                
                # Identifier l'index de la ligne d'en-tête
                for i, line in enumerate(table_lines):
                    if header_found and i == 0 and not re.search(r'\|\s*[-:]+\s*\|', line):
                        header_line_index = i
                        break
                
                # Parcourir les lignes pour extraire les données
                for i, line in enumerate(table_lines):
                    # Ignorer les lignes de séparation
                    if re.search(r'\|\s*[-:]+\s*\|', line):
                        data_started = True  # Les données commencent après la ligne de séparation
                        continue
                    
                    # Ignorer la ligne d'en-tête
                    if i == header_line_index or (not data_started and separator_found):
                        continue
                    
                    # Si nous avons un séparateur implicite, commencer après la première ligne
                    if not separator_found and i <= 1:
                        continue
                    
                    # Extraire les parties de la ligne
                    parts = [p.strip() for p in line.split('|')]
                    parts = [p for p in parts if p]  # Supprimer les éléments vides
                    
                    # Vérifier que nous avons au moins quelques colonnes
                    if parts and len(parts) >= 2:  # Au moins 2 colonnes (paramètre et valeur)
                        # Créer un dictionnaire pour cette ligne
                        row_data = {}
                        
                        # Associer chaque partie à un en-tête
                        for j, header in enumerate(headers):
                            if j < len(parts):
                                # Nettoyer les valeurs
                                value = parts[j].replace('\n', ' ').strip()
                                row_data[header] = value
                            else:
                                # Colonne manquante
                                row_data[header] = ""
                        
                        # Mapper les colonnes aux noms attendus dans le DataFrame
                        # Utiliser une correspondance flexible pour les noms de colonnes
                        column_mapping = {
                            "milieu": "Milieu",
                            "medium": "Milieu",
                            "parametre": "Paramètre",
                            "paramètre": "Paramètre",
                            "parameter": "Paramètre",
                            "param": "Paramètre",
                            "unite": "Unité",
                            "unité": "Unité",
                            "unit": "Unité",
                            "intervalle": "Intervalle acceptable",
                            "intervalle acceptable": "Intervalle acceptable",
                            "acceptable range": "Intervalle acceptable",
                            "range": "Intervalle acceptable",
                            "valeur": "Valeur mesurée",
                            "valeur mesuree": "Valeur mesurée",
                            "valeur mesurée": "Valeur mesurée",
                            "measured value": "Valeur mesurée",
                            "value": "Valeur mesurée",
                            "resultat": "Résultat conformité",
                            "résultat": "Résultat conformité",
                            "resultat conformite": "Résultat conformité",
                            "résultat conformité": "Résultat conformité",
                            "compliance": "Résultat conformité",
                            "conformite": "Résultat conformité",
                            "conformité": "Résultat conformité",
                            "score": "Score",
                            "observations": "Observations",
                            "notes": "Observations",
                            "description": "Description",
                            "evaluation": "Évaluation",
                            "évaluation": "Évaluation"
                        }
                        
                        # Créer une entrée avec les colonnes attendues
                        entry = {
                            "Milieu": "Eau",  # Valeur par défaut
                            "Paramètre": "",
                            "Unité": "",
                            "Intervalle acceptable": "",
                            "Valeur mesurée": "",
                            "Résultat conformité": "",
                            "Score": 0,  # Initialiser avec une valeur numérique
                            "Observations": "",
                            "Description": "",
                            "Évaluation": ""
                        }
                        
                        # Remplir l'entrée avec les données mappées en utilisant la normalisation
                        for header, value in row_data.items():
                            # Normaliser l'en-tête pour la comparaison
                            header_normalized = normalize_text(header)
                            
                            # Chercher une correspondance dans le mapping
                            for key, mapped_name in column_mapping.items():
                                # Normaliser la clé pour la comparaison
                                key_normalized = normalize_text(key)
                                
                                # Vérifier si l'en-tête normalisé correspond à la clé normalisée
                                if key_normalized in header_normalized or header_normalized in key_normalized:
                                    entry[mapped_name] = value
                                    logger.debug(f"Correspondance trouvée: '{header}' -> '{mapped_name}' avec valeur '{value}'")
                                    break
                            else:
                                # Si aucune correspondance n'est trouvée, utiliser l'en-tête original si c'est une colonne attendue
                                if header in entry:
                                    entry[header] = value
                                    logger.debug(f"Utilisation de l'en-tête original: '{header}' avec valeur '{value}'")
                        
                        # Si le paramètre est vide mais que nous avons une première colonne, l'utiliser comme paramètre
                        if not entry["Paramètre"] and len(parts) > 0:
                            entry["Paramètre"] = parts[0]
                            logger.debug(f"Paramètre défini à partir de la première colonne: '{parts[0]}'")
                        
                        # Si la valeur mesurée est vide mais que nous avons une deuxième colonne, l'utiliser comme valeur
                        if not entry["Valeur mesurée"] and len(parts) > 1:
                            entry["Valeur mesurée"] = parts[1]
                            logger.debug(f"Valeur mesurée définie à partir de la deuxième colonne: '{parts[1]}'")
                        
                        # Si l'unité est vide mais que nous avons une troisième colonne, l'utiliser comme unité
                        if not entry["Unité"] and len(parts) > 2:
                            entry["Unité"] = parts[2]
                            logger.debug(f"Unité définie à partir de la troisième colonne: '{parts[2]}'")
                        
                        # Vérifier que nous avons au moins un paramètre qui n'est pas un en-tête
                        # Utiliser la normalisation pour la comparaison
                        param_value = normalize_text(entry["Paramètre"])
                        if param_value and param_value not in ["parametre", "parameter", "param", "milieu", "medium"]:
                            data.append(entry)
                            logger.info(f"Ligne de données ajoutée: {entry}")
                        else:
                            logger.info(f"Ligne ignorée (en-tête ou invalide): {parts}")
                    else:
                        logger.info(f"Ligne ignorée (trop peu de colonnes): {parts}")
            else:
                logger.warning("Structure de tableau incomplète: en-têtes ou séparateur manquant")
                
                # Essayer une approche alternative si la structure est incomplète
                for i, line in enumerate(table_lines):
                    # Ignorer les lignes de séparation
                    if re.search(r'\|\s*[-:]+\s*\|', line):
                        continue
                    
                    # Extraire les parties de la ligne
                    parts = [p.strip() for p in line.split('|')]
                    parts = [p for p in parts if p]  # Supprimer les éléments vides
                    
                    # Vérifier que nous avons au moins 2 colonnes (paramètre et valeur)
                    if len(parts) >= 2:
                        # Extraire les valeurs
                        param_name = parts[0].strip() if len(parts) > 0 else ""
                        param_value = parts[1].strip() if len(parts) > 1 else ""
                        param_unit = parts[2].strip() if len(parts) > 2 else ""
                        
                        # Nettoyer les valeurs
                        param_name = param_name.replace('\n', ' ').strip()
                        param_value = param_value.replace('\n', ' ').strip()
                        param_unit = param_unit.replace('\n', ' ').strip()
                        
                        # Ignorer les lignes qui semblent être des en-têtes
                        # Utiliser la normalisation pour la comparaison
                        param_name_normalized = normalize_text(param_name)
                        if param_name_normalized in ["parametre", "parameter", "milieu", "medium"]:
                            logger.info(f"En-tête ignoré: {param_name}")
                            continue
                        
                        logger.info(f"Paramètre extrait du tableau (méthode alternative): {param_name} = {param_value} {param_unit}")
                        
                        # Créer une entrée standardisée
                        entry = {
                            "Milieu": "Eau",  # Valeur par défaut
                            "Paramètre": param_name,
                            "Unité": param_unit,
                            "Intervalle acceptable": "",
                            "Valeur mesurée": param_value,
                            "Résultat conformité": "",
                            "Score": 0,  # Initialiser avec une valeur numérique
                            "Observations": ""
                        }
                        data.append(entry)
                        logger.info(f"Ligne de données ajoutée (méthode alternative): {entry}")
        
        # Si aucun tableau n'a été trouvé, essayer d'autres formats
        if not data:
            logger.debug("Aucun tableau structuré trouvé, recherche de formats alternatifs")
            
            # 1. Chercher des listes à puces avec paires clé-valeur
            bullet_pattern = re.compile(r'^\s*[-*•]\s+(.+)$')
            parameter_pattern = re.compile(r'([^:=]+)[:=]\s*(.+)')
            
            # Journaliser pour le débogage
            logger.info("Recherche de paramètres dans les listes à puces...")
            
            for i, line in enumerate(lines):
                line = line.strip()
                bullet_match = bullet_pattern.match(line)
                
                # Journaliser chaque ligne pour le débogage
                logger.debug(f"Analyse de la ligne {i}: '{line}'")
                
                # Vérifier si c'est une ligne avec puce
                if bullet_match:
                    content = bullet_match.group(1).strip()
                    logger.info(f"Puce trouvée: '{content}'")
                    
                    # Essayer de trouver un format "Paramètre: Valeur"
                    param_match = parameter_pattern.match(content)
                    
                    if param_match:
                        # Format: - Paramètre: Valeur Unité
                        param_name = param_match.group(1).strip()
                        param_value = param_match.group(2).strip()
                        
                        # Extraire la valeur et l'unité
                        value, unit = _extract_value_and_unit(param_value)
                        
                        logger.info(f"Paramètre trouvé dans liste à puces: {param_name} = {str(value)} {str(unit)}")
                        
                        # Chercher des informations supplémentaires dans les lignes suivantes
                        description = ""
                        evaluation = ""
                        intervalle = ""
                        
                        # Vérifier si la ligne suivante contient des informations supplémentaires
                        if i < len(lines) - 1:
                            next_line = lines[i+1].strip()
                            # Si la ligne suivante n'est pas une liste à puces et ne contient pas de séparateur
                            if not (bullet_pattern.match(next_line) or ':' in next_line or '=' in next_line):
                                if param_name.lower() in next_line.lower() and len(next_line) < 200:
                                    description = next_line
                                elif "norme" in next_line.lower() or "acceptable" in next_line.lower():
                                    intervalle = next_line
                                elif "conforme" in next_line.lower() or "évaluation" in next_line.lower():
                                    evaluation = next_line
                        
                        # Extraire l'intervalle acceptable si présent dans la valeur
                        if "entre" in param_value.lower() or "-" in param_value or "à" in param_value:
                            # Essayer d'extraire un intervalle comme "entre 6.5 et 8.5" ou "6.5-8.5"
                            interval_match = re.search(r'entre\s+([\d,.]+)\s+et\s+([\d,.]+)|([\d,.]+)\s*-\s*([\d,.]+)|([\d,.]+)\s+à\s+([\d,.]+)', param_value.lower())
                            if interval_match:
                                groups = [str(g) for g in interval_match.groups() if g]
                                if len(groups) >= 2:
                                    intervalle = f"{groups[0]} - {groups[1]}"
                        
                        entry = {
                            "Milieu": "",
                            "Paramètre": param_name,
                            "Unité": unit,
                            "Intervalle acceptable": intervalle,
                            "Valeur mesurée": value,
                            "Résultat conformité": "",
                            "Score": "",
                            "Observations": "",
                            "Description": description,
                            "Évaluation": evaluation
                        }
                        data.append(entry)
                    else:
                        # Essayer de trouver un format "Paramètre Valeur Unité" sans séparateur explicite
                        # Par exemple: "- pH 7.5 unités"
                        parts = content.split()
                        if len(parts) >= 2:
                            # Supposer que le premier élément est le paramètre
                            param_name = parts[0].strip()
                            # Le reste pourrait être la valeur et l'unité
                            param_value = " ".join(parts[1:]).strip()
                            
                            # Extraire la valeur et l'unité
                            value, unit = _extract_value_and_unit(param_value)
                            
                            logger.info(f"Paramètre trouvé dans format alternatif: {param_name} = {str(value)} {str(unit)}")
                            
                            # Créer une entrée standardisée
                            entry = {
                                "Milieu": "",
                                "Paramètre": param_name,
                                "Unité": unit,
                                "Intervalle acceptable": "",
                                "Valeur mesurée": value,
                                "Résultat conformité": "",
                                "Score": "",
                                "Observations": ""
                            }
                            data.append(entry)
        
        # Créer un DataFrame à partir des données extraites
        if data:
            df = pd.DataFrame(data)
            
            # Nettoyer les valeurs
            for col in df.columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # S'assurer que toutes les colonnes attendues sont présentes
            expected_columns = [
                "Milieu", "Paramètre", "Unité", "Intervalle acceptable", 
                "Valeur mesurée", "Résultat conformité", "Score", "Observations",
                "Description", "Évaluation"
            ]
            
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Réorganiser les colonnes
            df = df[expected_columns]
            
            # Supprimer les doublons
            df = df.drop_duplicates(subset=["Milieu", "Paramètre"])
            
            return df
        else:
            # Si aucune donnée structurée n'a été trouvée, créer un DataFrame avec des paramètres environnementaux courants et des valeurs estimées
            logger.warning("Aucune donnée structurée n'a été extraite de la réponse.")
            # Créer un DataFrame avec des paramètres environnementaux courants et des valeurs estimées
            default_params = [
                {
                    "Milieu": "Eau",
                    "Paramètre": "pH",
                    "Unité": "pH",
                    "Intervalle acceptable": "6.5 - 8.5",
                    "Valeur mesurée": "7.2 (estimé)",
                    "Résultat conformité": "Conforme (estimé)",
                    "Score": "1",
                    "Observations": "Valeur typique estimée pour les eaux naturelles",
                    "Description": "Mesure de l'acidité/basicité de l'eau",
                    "Évaluation": "Valeur estimée - à confirmer par mesure réelle"
                },
                {
                    "Milieu": "Eau",
                    "Paramètre": "Température",
                    "Unité": "°C",
                    "Intervalle acceptable": "10 - 25",
                    "Valeur mesurée": "18 (estimé)",
                    "Résultat conformité": "Conforme (estimé)",
                    "Score": "1",
                    "Observations": "Valeur typique estimée pour les eaux de surface",
                    "Description": "Température de l'eau",
                    "Évaluation": "Valeur estimée - à confirmer par mesure réelle"
                },
                {
                    "Milieu": "Eau",
                    "Paramètre": "Conductivité",
                    "Unité": "µS/cm",
                    "Intervalle acceptable": "< 1000",
                    "Valeur mesurée": "500 (estimé)",
                    "Résultat conformité": "Conforme (estimé)",
                    "Score": "1",
                    "Observations": "Valeur typique estimée pour les eaux douces",
                    "Description": "Mesure des ions dissous dans l'eau",
                    "Évaluation": "Valeur estimée - à confirmer par mesure réelle"
                }
            ]
            return pd.DataFrame(default_params)
                
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des paramètres: {str(e)}")
        # Retourner un DataFrame avec une structure minimale en cas d'erreur
        return pd.DataFrame([{
            "Milieu": "Erreur",
            "Paramètre": "Erreur d'extraction",
            "Unité": "",
            "Intervalle acceptable": "",
            "Valeur mesurée": "",
            "Résultat conformité": "",
            "Score": "",
            "Observations": f"Erreur: {str(e)}",
            "Description": "Erreur d'extraction",
            "Évaluation": "Erreur"
        }])

def _extract_value_and_unit(text):
    """Extrait la valeur numérique et l'unité d'une chaîne de texte.
    
    Args:
        text (str): Texte contenant potentiellement une valeur et une unité
        
    Returns:
        tuple: (valeur, unité)
    """
    if not text or not isinstance(text, str):
        return "", ""
        
    # Nettoyer le texte
    text = text.strip()
    
    # Cas spécial: texte vide ou trop court
    if len(text) < 1:
        return "", ""
    
    # Rechercher un nombre suivi potentiellement d'une unité
    # Exemples: "7.5", "7.5 pH", "7,5 unités", "7.5 (estimé)"
    value_match = re.search(r'([+-]?\d+[.,]?\d*)', text)
    
    if value_match:
        value = value_match.group(1)
        # Standardiser le format du nombre (remplacer la virgule par un point)
        value = value.replace(',', '.')
        
        # Extraire l'unité qui suit potentiellement la valeur
        unit_match = re.search(r'[+-]?\d+[.,]?\d*\s*([^\d\s,.()][^,.()]*)', text)
        unit = unit_match.group(1).strip() if unit_match else ""
        
        # Nettoyer l'unité
        unit = re.sub(r'^\s*de\s+', '', unit)  # Supprimer "de" au début
        unit = re.sub(r'^\s*en\s+', '', unit)  # Supprimer "en" au début
        
        return value, unit
    else:
        return "", ""