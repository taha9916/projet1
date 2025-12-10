#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de surveillance continue des sites environnementaux
Fonctionnalités :
- Traitement par lots automatisé
- Surveillance des seuils critiques
- Génération d'alertes automatiques
- Suivi des tendances temporelles
- Comparaison des plans d'action
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
import schedule
import time
import threading

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SiteMonitoring:
    """Classe principale pour la surveillance continue des sites"""
    
    def __init__(self, config_file="config/monitoring_config.json"):
        """Initialise le système de surveillance"""
        self.config_file = config_file
        self.config = self.load_config()
        self.alerts_history = []
        self.monitoring_data = {}
        self.running = False
        
    def load_config(self):
        """Charge la configuration de surveillance"""
        default_config = {
            "sites": {
                "site_exemple": {
                    "name": "Site industriel exemple",
                    "coordinates": [34.0209, -6.8416],
                    "monitoring_frequency": "daily",
                    "data_directory": "./surveillance/site_exemple",
                    "thresholds": {
                        "water": {
                            "pH": {"min": 6.5, "max": 8.5, "critical": True},
                            "DBO5": {"max": 25, "critical": True},
                            "DCO": {"max": 90, "critical": True},
                            "Plomb": {"max": 0.01, "critical": True},
                            "Cadmium": {"max": 0.005, "critical": True}
                        },
                        "air": {
                            "PM2.5": {"max": 25, "critical": True},
                            "PM10": {"max": 50, "critical": True},
                            "NO2": {"max": 40, "critical": True},
                            "SO2": {"max": 20, "critical": True}
                        },
                        "soil": {
                            "pH": {"min": 6.0, "max": 9.0, "critical": False},
                            "Plomb": {"max": 100, "critical": True},
                            "Cadmium": {"max": 1, "critical": True}
                        }
                    }
                }
            },
            "alerts": {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "monitoring@example.com",
                    "sender_password": "app_password",
                    "recipients": ["admin@example.com"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "https://hooks.slack.com/services/...",
                    "channel": "#environmental-alerts"
                }
            },
            "batch_processing": {
                "enabled": True,
                "schedule": "daily",
                "time": "08:00",
                "parallel_processes": 4,
                "file_patterns": ["*.xlsx", "*.csv", "*.pdf"]
            },
            "dashboard": {
                "enabled": True,
                "port": 8051,
                "auto_refresh": 300,  # secondes
                "data_retention_days": 365
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Fusionner avec la configuration par défaut
                return {**default_config, **config}
            else:
                # Créer le fichier de configuration
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return default_config
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")

class BatchProcessor:
    """Processeur automatisé pour l'analyse par lots"""
    
    def __init__(self, monitoring_system):
        self.monitoring = monitoring_system
        
    def process_site_data(self, site_id: str):
        """Traite automatiquement les données d'un site"""
        try:
            site_config = self.monitoring.config["sites"][site_id]
            data_dir = site_config["data_directory"]
            
            if not os.path.exists(data_dir):
                logger.warning(f"Répertoire de données introuvable: {data_dir}")
                return
            
            # Rechercher les nouveaux fichiers
            new_files = self.find_new_files(data_dir, site_id)
            
            if not new_files:
                logger.info(f"Aucun nouveau fichier pour {site_id}")
                return
            
            # Traiter chaque fichier
            results = []
            for file_path in new_files:
                try:
                    result = self.analyze_file(file_path, site_config)
                    if result:
                        results.append(result)
                        self.check_thresholds(result, site_config, site_id)
                except Exception as e:
                    logger.error(f"Erreur lors de l'analyse de {file_path}: {e}")
            
            # Sauvegarder les résultats
            if results:
                self.save_results(results, site_id)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du site {site_id}: {e}")
    
    def find_new_files(self, data_dir: str, site_id: str) -> List[str]:
        """Trouve les nouveaux fichiers à traiter"""
        patterns = self.monitoring.config["batch_processing"]["file_patterns"]
        processed_file = f"processed_files_{site_id}.json"
        
        # Charger la liste des fichiers déjà traités
        processed_files = set()
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                processed_files = set(json.load(f))
        
        # Chercher tous les fichiers correspondant aux patterns
        new_files = []
        for pattern in patterns:
            for file_path in Path(data_dir).rglob(pattern):
                if str(file_path) not in processed_files:
                    new_files.append(str(file_path))
        
        return new_files
    
    def analyze_file(self, file_path: str, site_config: Dict) -> Optional[Dict]:
        """Analyse un fichier et extrait les paramètres environnementaux"""
        try:
            # Importer les modules d'analyse
            from pipeline import AnalysisPipeline
            
            pipeline = AnalysisPipeline()
            result = pipeline.process_file(file_path, output_format="dict")
            
            if result:
                # Ajouter métadonnées
                result["timestamp"] = datetime.now().isoformat()
                result["file_path"] = file_path
                result["site_coordinates"] = site_config["coordinates"]
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse fichier {file_path}: {e}")
            return None
    
    def check_thresholds(self, data: Dict, site_config: Dict, site_id: str):
        """Vérifie les seuils et génère des alertes si nécessaire"""
        thresholds = site_config["thresholds"]
        alerts = []
        
        for medium, params in thresholds.items():
            if medium in data:
                for param_name, threshold_config in params.items():
                    if param_name in data[medium]:
                        value = data[medium][param_name]
                        
                        # Extraire la valeur numérique
                        if isinstance(value, (list, tuple)) and len(value) > 0:
                            numeric_value = float(value[0])
                        else:
                            try:
                                numeric_value = float(value)
                            except:
                                continue
                        
                        # Vérifier les seuils
                        alert = self.check_single_threshold(
                            param_name, numeric_value, threshold_config, medium, site_id
                        )
                        if alert:
                            alerts.append(alert)
        
        # Envoyer les alertes
        if alerts:
            self.send_alerts(alerts, site_id)
    
    def check_single_threshold(self, param_name: str, value: float, 
                             threshold_config: Dict, medium: str, site_id: str) -> Optional[Dict]:
        """Vérifie un seuil individuel"""
        alert = None
        
        if "max" in threshold_config and value > threshold_config["max"]:
            alert = {
                "type": "seuil_depassé",
                "parameter": param_name,
                "medium": medium,
                "value": value,
                "threshold": threshold_config["max"],
                "critical": threshold_config.get("critical", False),
                "site_id": site_id,
                "timestamp": datetime.now().isoformat()
            }
        elif "min" in threshold_config and value < threshold_config["min"]:
            alert = {
                "type": "seuil_sous-dépassé", 
                "parameter": param_name,
                "medium": medium,
                "value": value,
                "threshold": threshold_config["min"],
                "critical": threshold_config.get("critical", False),
                "site_id": site_id,
                "timestamp": datetime.now().isoformat()
            }
        
        return alert
    
    def send_alerts(self, alerts: List[Dict], site_id: str):
        """Envoie les alertes configurées"""
        alert_manager = AlertManager(self.monitoring)
        alert_manager.send_threshold_alerts(alerts, site_id)
    
    def save_results(self, results: List[Dict], site_id: str):
        """Sauvegarde les résultats d'analyse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"surveillance/{site_id}/results_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Résultats sauvegardés: {output_file}")

class AlertManager:
    """Gestionnaire d'alertes automatiques"""
    
    def __init__(self, monitoring_system):
        self.monitoring = monitoring_system
        self.config = monitoring_system.config["alerts"]
    
    def send_threshold_alerts(self, alerts: List[Dict], site_id: str):
        """Envoie les alertes de dépassement de seuils"""
        if not alerts:
            return
        
        site_name = self.monitoring.config["sites"][site_id]["name"]
        critical_alerts = [a for a in alerts if a.get("critical", False)]
        
        # Préparer le message
        subject = f"🚨 Alerte environnementale - {site_name}"
        if critical_alerts:
            subject = f"🔴 ALERTE CRITIQUE - {site_name}"
        
        message = self.format_alert_message(alerts, site_name)
        
        # Envoyer par email
        if self.config["email"]["enabled"]:
            self.send_email_alert(subject, message)
        
        # Envoyer via webhook
        if self.config["webhook"]["enabled"]:
            self.send_webhook_alert(subject, message)
        
        # Enregistrer dans l'historique
        self.monitoring.alerts_history.extend(alerts)
    
    def format_alert_message(self, alerts: List[Dict], site_name: str) -> str:
        """Formate le message d'alerte"""
        message = f"Site: {site_name}\n"
        message += f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        critical_count = sum(1 for a in alerts if a.get("critical", False))
        if critical_count > 0:
            message += f"⚠️  {critical_count} ALERTE(S) CRITIQUE(S) DÉTECTÉE(S)\n\n"
        
        for alert in alerts:
            criticality = "🔴 CRITIQUE" if alert.get("critical", False) else "🟡 Attention"
            message += f"{criticality}\n"
            message += f"Paramètre: {alert['parameter']} ({alert['medium']})\n"
            message += f"Valeur mesurée: {alert['value']}\n"
            message += f"Seuil: {alert['threshold']}\n"
            message += f"Type: {alert['type']}\n\n"
        
        message += "Actions recommandées:\n"
        if critical_count > 0:
            message += "- Intervention immédiate requise\n"
            message += "- Vérifier les équipements de mesure\n"
            message += "- Contacter les équipes techniques\n"
        else:
            message += "- Surveillance renforcée\n"
            message += "- Vérification des données\n"
        
        return message
    
    def send_email_alert(self, subject: str, message: str):
        """Envoie une alerte par email"""
        try:
            email_config = self.config["email"]
            
            msg = MIMEMultipart()
            msg['From'] = email_config["sender_email"]
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["sender_email"], email_config["sender_password"])
            
            for recipient in email_config["recipients"]:
                msg['To'] = recipient
                server.send_message(msg)
                del msg['To']
            
            server.quit()
            logger.info("Alerte email envoyée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
    
    def send_webhook_alert(self, subject: str, message: str):
        """Envoie une alerte via webhook (Slack, Teams, etc.)"""
        try:
            import requests
            webhook_config = self.config["webhook"]
            
            payload = {
                "text": f"{subject}\n\n{message}",
                "channel": webhook_config.get("channel", "#alerts")
            }
            
            response = requests.post(webhook_config["url"], json=payload)
            if response.status_code == 200:
                logger.info("Alerte webhook envoyée avec succès")
            else:
                logger.error(f"Erreur webhook: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur envoi webhook: {e}")

class TrendAnalyzer:
    """Analyseur de tendances temporelles"""
    
    def __init__(self, monitoring_system):
        self.monitoring = monitoring_system
    
    def analyze_trends(self, site_id: str, period_days: int = 30) -> Dict:
        """Analyse les tendances sur une période donnée"""
        try:
            # Charger les données historiques
            data_dir = f"surveillance/{site_id}"
            if not os.path.exists(data_dir):
                return {"error": "Aucune donnée historique disponible"}
            
            # Collecter les fichiers de résultats
            result_files = []
            for file_path in Path(data_dir).glob("results_*.json"):
                # Extraire la date du nom de fichier
                try:
                    date_str = file_path.stem.split('_')[1] + '_' + file_path.stem.split('_')[2]
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    if file_date >= datetime.now() - timedelta(days=period_days):
                        result_files.append((file_path, file_date))
                except:
                    continue
            
            if not result_files:
                return {"error": "Aucune donnée dans la période spécifiée"}
            
            # Trier par date
            result_files.sort(key=lambda x: x[1])
            
            # Analyser les tendances
            trends = self.calculate_trends(result_files, site_id)
            return trends
            
        except Exception as e:
            logger.error(f"Erreur analyse tendances: {e}")
            return {"error": str(e)}
    
    def calculate_trends(self, result_files: List, site_id: str) -> Dict:
        """Calcule les tendances pour chaque paramètre"""
        trends = {
            "site_id": site_id,
            "period": {
                "start": result_files[0][1].isoformat(),
                "end": result_files[-1][1].isoformat(),
                "measurements": len(result_files)
            },
            "parameters": {}
        }
        
        # Collecter toutes les valeurs par paramètre
        all_data = {}
        dates = []
        
        for file_path, file_date in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dates.append(file_date)
                
                # Extraire les paramètres environnementaux
                for medium in ["water", "air", "soil"]:
                    if medium in data:
                        for param, value in data[medium].items():
                            key = f"{medium}.{param}"
                            if key not in all_data:
                                all_data[key] = []
                            
                            # Extraire valeur numérique
                            try:
                                if isinstance(value, (list, tuple)):
                                    numeric_val = float(value[0])
                                else:
                                    numeric_val = float(value)
                                all_data[key].append((file_date, numeric_val))
                            except:
                                continue
            except:
                continue
        
        # Calculer les tendances
        for param_key, values in all_data.items():
            if len(values) < 2:
                continue
            
            # Trier par date
            values.sort(key=lambda x: x[0])
            
            # Calculer la tendance (régression linéaire simple)
            x_vals = [(v[0] - values[0][0]).total_seconds() for v in values]
            y_vals = [v[1] for v in values]
            
            if len(x_vals) > 1:
                slope, trend_type = self.calculate_slope(x_vals, y_vals)
                
                trends["parameters"][param_key] = {
                    "current_value": y_vals[-1],
                    "previous_value": y_vals[0],
                    "change": y_vals[-1] - y_vals[0],
                    "slope": slope,
                    "trend": trend_type,
                    "measurements": len(values),
                    "min_value": min(y_vals),
                    "max_value": max(y_vals),
                    "avg_value": sum(y_vals) / len(y_vals)
                }
        
        return trends
    
    def calculate_slope(self, x_vals: List[float], y_vals: List[float]) -> tuple:
        """Calcule la pente et détermine le type de tendance"""
        n = len(x_vals)
        if n < 2:
            return 0, "stable"
        
        # Régression linéaire simple
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        
        numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Déterminer le type de tendance
        if abs(slope) < 0.01:  # Seuil configurable
            trend_type = "stable"
        elif slope > 0:
            trend_type = "croissante"
        else:
            trend_type = "décroissante"
        
        return slope, trend_type

class MonitoringScheduler:
    """Planificateur automatique des tâches de surveillance"""
    
    def __init__(self, monitoring_system):
        self.monitoring = monitoring_system
        self.batch_processor = BatchProcessor(monitoring_system)
        self.scheduler_thread = None
        self.running = False
    
    def start(self):
        """Démarre le planificateur"""
        if self.running:
            logger.warning("Planificateur déjà en cours d'exécution")
            return
        
        self.running = True
        
        # Configurer les tâches planifiées
        batch_config = self.monitoring.config["batch_processing"]
        
        if batch_config["enabled"]:
            if batch_config["schedule"] == "daily":
                schedule.every().day.at(batch_config["time"]).do(self.run_batch_processing)
            elif batch_config["schedule"] == "hourly":
                schedule.every().hour.do(self.run_batch_processing)
        
        # Démarrer le thread du planificateur
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Planificateur de surveillance démarré")
    
    def stop(self):
        """Arrête le planificateur"""
        self.running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Planificateur de surveillance arrêté")
    
    def _run_scheduler(self):
        """Boucle principale du planificateur"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
            except Exception as e:
                logger.error(f"Erreur planificateur: {e}")
                time.sleep(60)
    
    def run_batch_processing(self):
        """Exécute le traitement par lots pour tous les sites"""
        logger.info("Début du traitement par lots automatique")
        
        for site_id in self.monitoring.config["sites"].keys():
            try:
                logger.info(f"Traitement du site: {site_id}")
                self.batch_processor.process_site_data(site_id)
            except Exception as e:
                logger.error(f"Erreur traitement site {site_id}: {e}")
        
        logger.info("Traitement par lots terminé")

def create_monitoring_system(config_file="config/monitoring_config.json"):
    """Fonction utilitaire pour créer un système de surveillance"""
    return SiteMonitoring(config_file)

if __name__ == "__main__":
    # Exemple d'utilisation
    monitoring = create_monitoring_system()
    
    # Démarrer le planificateur
    scheduler = MonitoringScheduler(monitoring)
    scheduler.start()
    
    try:
        logger.info("Système de surveillance démarré. Appuyez sur Ctrl+C pour arrêter.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Arrêt du système de surveillance...")
        scheduler.stop()
