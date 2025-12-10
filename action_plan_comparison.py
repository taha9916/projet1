#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de comparaison temporelle des plans d'action
Permet de comparer l'évolution des plans d'action dans le temps
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ActionPlanMetrics:
    """Métriques d'un plan d'action"""
    total_actions: int
    completed_actions: int
    in_progress_actions: int
    planned_actions: int
    overdue_actions: int
    total_budget: float
    spent_budget: float
    critical_actions: int
    completion_rate: float
    budget_utilization: float

class ActionPlanComparator:
    """Comparateur de plans d'action temporels"""
    
    def __init__(self):
        self.comparison_results = {}
        
    def compare_action_plans(self, plan1_path: str, plan2_path: str, 
                           plan1_date: str = None, plan2_date: str = None) -> Dict:
        """Compare deux plans d'action"""
        try:
            # Charger les plans d'action
            plan1 = self.load_action_plan(plan1_path)
            plan2 = self.load_action_plan(plan2_path)
            
            if plan1 is None or plan2 is None:
                return {"error": "Impossible de charger les plans d'action"}
            
            # Calculer les métriques
            metrics1 = self.calculate_metrics(plan1)
            metrics2 = self.calculate_metrics(plan2)
            
            # Effectuer la comparaison
            comparison = self.generate_comparison(
                metrics1, metrics2, 
                plan1_date or "Plan 1", plan2_date or "Plan 2"
            )
            
            # Analyser l'évolution des actions individuelles
            action_evolution = self.analyze_action_evolution(plan1, plan2)
            
            # Générer les visualisations
            charts = self.create_comparison_charts(metrics1, metrics2, action_evolution)
            
            result = {
                "comparison_date": datetime.now().isoformat(),
                "plan1": {
                    "path": plan1_path,
                    "date": plan1_date,
                    "metrics": metrics1.__dict__
                },
                "plan2": {
                    "path": plan2_path, 
                    "date": plan2_date,
                    "metrics": metrics2.__dict__
                },
                "comparison": comparison,
                "action_evolution": action_evolution,
                "charts": charts,
                "recommendations": self.generate_recommendations(comparison, action_evolution)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison: {e}")
            return {"error": str(e)}
    
    def load_action_plan(self, file_path: str) -> Optional[pd.DataFrame]:
        """Charge un plan d'action depuis un fichier Excel ou CSV"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Fichier introuvable: {file_path}")
                return None
            
            # Déterminer le format du fichier
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                logger.error(f"Format de fichier non supporté: {file_path}")
                return None
            
            # Standardiser les noms de colonnes
            df.columns = df.columns.str.lower().str.strip()
            
            # Colonnes requises pour l'analyse
            required_columns = ['action_id', 'description', 'status', 'priority']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.warning(f"Colonnes manquantes: {missing_columns}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur chargement plan d'action {file_path}: {e}")
            return None
    
    def calculate_metrics(self, plan_df: pd.DataFrame) -> ActionPlanMetrics:
        """Calcule les métriques d'un plan d'action"""
        try:
            total_actions = len(plan_df)
            
            # Analyse du statut des actions
            if 'status' in plan_df.columns:
                status_counts = plan_df['status'].value_counts()
                completed = status_counts.get('completed', 0) + status_counts.get('terminé', 0)
                in_progress = status_counts.get('in_progress', 0) + status_counts.get('en_cours', 0)
                planned = status_counts.get('planned', 0) + status_counts.get('planifié', 0)
            else:
                completed = in_progress = planned = 0
            
            # Analyse des retards
            overdue = 0
            if 'deadline' in plan_df.columns and 'status' in plan_df.columns:
                current_date = datetime.now()
                for idx, row in plan_df.iterrows():
                    try:
                        deadline = pd.to_datetime(row['deadline'])
                        if deadline < current_date and row['status'] not in ['completed', 'terminé']:
                            overdue += 1
                    except:
                        continue
            
            # Analyse budgétaire
            total_budget = 0
            spent_budget = 0
            if 'budget' in plan_df.columns:
                total_budget = plan_df['budget'].fillna(0).sum()
            if 'spent' in plan_df.columns:
                spent_budget = plan_df['spent'].fillna(0).sum()
            
            # Actions critiques
            critical_actions = 0
            if 'priority' in plan_df.columns:
                critical_actions = len(plan_df[plan_df['priority'].isin(['high', 'élevé', 'critique'])])
            
            # Taux de completion
            completion_rate = (completed / total_actions * 100) if total_actions > 0 else 0
            
            # Utilisation budgétaire
            budget_utilization = (spent_budget / total_budget * 100) if total_budget > 0 else 0
            
            return ActionPlanMetrics(
                total_actions=total_actions,
                completed_actions=completed,
                in_progress_actions=in_progress,
                planned_actions=planned,
                overdue_actions=overdue,
                total_budget=total_budget,
                spent_budget=spent_budget,
                critical_actions=critical_actions,
                completion_rate=completion_rate,
                budget_utilization=budget_utilization
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques: {e}")
            return ActionPlanMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def generate_comparison(self, metrics1: ActionPlanMetrics, metrics2: ActionPlanMetrics, 
                          period1: str, period2: str) -> Dict:
        """Génère la comparaison entre deux ensembles de métriques"""
        comparison = {
            "periods": {"period1": period1, "period2": period2},
            "evolution": {},
            "summary": {},
            "alerts": []
        }
        
        # Évolution des métriques clés
        comparison["evolution"] = {
            "total_actions": {
                "period1": metrics1.total_actions,
                "period2": metrics2.total_actions,
                "change": metrics2.total_actions - metrics1.total_actions,
                "change_pct": ((metrics2.total_actions - metrics1.total_actions) / metrics1.total_actions * 100) 
                             if metrics1.total_actions > 0 else 0
            },
            "completion_rate": {
                "period1": round(metrics1.completion_rate, 1),
                "period2": round(metrics2.completion_rate, 1),
                "change": round(metrics2.completion_rate - metrics1.completion_rate, 1),
                "change_pct": round(metrics2.completion_rate - metrics1.completion_rate, 1)
            },
            "budget_utilization": {
                "period1": round(metrics1.budget_utilization, 1),
                "period2": round(metrics2.budget_utilization, 1),
                "change": round(metrics2.budget_utilization - metrics1.budget_utilization, 1),
                "change_pct": round(metrics2.budget_utilization - metrics1.budget_utilization, 1)
            },
            "overdue_actions": {
                "period1": metrics1.overdue_actions,
                "period2": metrics2.overdue_actions,
                "change": metrics2.overdue_actions - metrics1.overdue_actions,
                "change_pct": ((metrics2.overdue_actions - metrics1.overdue_actions) / metrics1.overdue_actions * 100)
                             if metrics1.overdue_actions > 0 else 0
            }
        }
        
        # Résumé de l'évolution
        completion_change = metrics2.completion_rate - metrics1.completion_rate
        if completion_change > 5:
            comparison["summary"]["completion"] = "Amélioration significative du taux de completion"
        elif completion_change < -5:
            comparison["summary"]["completion"] = "Détérioration du taux de completion"
        else:
            comparison["summary"]["completion"] = "Taux de completion stable"
        
        # Alertes
        if metrics2.overdue_actions > metrics1.overdue_actions:
            comparison["alerts"].append({
                "type": "warning",
                "message": f"Augmentation des actions en retard: {metrics2.overdue_actions - metrics1.overdue_actions}"
            })
        
        if metrics2.completion_rate < 50 and metrics2.completion_rate < metrics1.completion_rate:
            comparison["alerts"].append({
                "type": "critical",
                "message": f"Taux de completion faible et en baisse: {metrics2.completion_rate:.1f}%"
            })
        
        if metrics2.budget_utilization > 90:
            comparison["alerts"].append({
                "type": "warning", 
                "message": f"Budget presque épuisé: {metrics2.budget_utilization:.1f}%"
            })
        
        return comparison
    
    def analyze_action_evolution(self, plan1_df: pd.DataFrame, plan2_df: pd.DataFrame) -> Dict:
        """Analyse l'évolution des actions individuelles"""
        evolution = {
            "new_actions": [],
            "completed_actions": [],
            "status_changes": [],
            "priority_changes": []
        }
        
        try:
            # Identifier les actions par ID si disponible
            if 'action_id' not in plan1_df.columns or 'action_id' not in plan2_df.columns:
                return evolution
            
            plan1_ids = set(plan1_df['action_id'])
            plan2_ids = set(plan2_df['action_id'])
            
            # Nouvelles actions
            new_ids = plan2_ids - plan1_ids
            for action_id in new_ids:
                action = plan2_df[plan2_df['action_id'] == action_id].iloc[0]
                evolution["new_actions"].append({
                    "id": action_id,
                    "description": action.get('description', ''),
                    "priority": action.get('priority', ''),
                    "status": action.get('status', '')
                })
            
            # Actions communes - analyser les changements
            common_ids = plan1_ids & plan2_ids
            for action_id in common_ids:
                action1 = plan1_df[plan1_df['action_id'] == action_id].iloc[0]
                action2 = plan2_df[plan2_df['action_id'] == action_id].iloc[0]
                
                # Changement de statut
                if 'status' in action1 and 'status' in action2:
                    if action1['status'] != action2['status']:
                        evolution["status_changes"].append({
                            "id": action_id,
                            "description": action1.get('description', ''),
                            "old_status": action1['status'],
                            "new_status": action2['status']
                        })
                        
                        # Actions completées
                        if action2['status'] in ['completed', 'terminé']:
                            evolution["completed_actions"].append({
                                "id": action_id,
                                "description": action1.get('description', ''),
                                "completion_date": action2.get('completion_date', '')
                            })
                
                # Changement de priorité
                if 'priority' in action1 and 'priority' in action2:
                    if action1['priority'] != action2['priority']:
                        evolution["priority_changes"].append({
                            "id": action_id,
                            "description": action1.get('description', ''),
                            "old_priority": action1['priority'],
                            "new_priority": action2['priority']
                        })
            
        except Exception as e:
            logger.error(f"Erreur analyse évolution: {e}")
        
        return evolution
    
    def create_comparison_charts(self, metrics1: ActionPlanMetrics, 
                               metrics2: ActionPlanMetrics, evolution: Dict) -> Dict:
        """Crée les graphiques de comparaison"""
        charts = {}
        
        try:
            # Graphique d'évolution des métriques clés
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('Évolution des Métriques du Plan d\'Action', fontsize=16)
            
            # Taux de completion
            axes[0,0].bar(['Période 1', 'Période 2'], 
                         [metrics1.completion_rate, metrics2.completion_rate],
                         color=['lightblue', 'darkblue'])
            axes[0,0].set_title('Taux de Completion (%)')
            axes[0,0].set_ylim(0, 100)
            
            # Actions par statut
            statuses = ['Completed', 'In Progress', 'Planned', 'Overdue']
            period1_values = [metrics1.completed_actions, metrics1.in_progress_actions, 
                             metrics1.planned_actions, metrics1.overdue_actions]
            period2_values = [metrics2.completed_actions, metrics2.in_progress_actions,
                             metrics2.planned_actions, metrics2.overdue_actions]
            
            x = np.arange(len(statuses))
            width = 0.35
            
            axes[0,1].bar(x - width/2, period1_values, width, label='Période 1', alpha=0.7)
            axes[0,1].bar(x + width/2, period2_values, width, label='Période 2', alpha=0.7)
            axes[0,1].set_title('Actions par Statut')
            axes[0,1].set_xticks(x)
            axes[0,1].set_xticklabels(statuses)
            axes[0,1].legend()
            
            # Utilisation budgétaire
            axes[1,0].bar(['Période 1', 'Période 2'],
                         [metrics1.budget_utilization, metrics2.budget_utilization],
                         color=['lightgreen', 'darkgreen'])
            axes[1,0].set_title('Utilisation du Budget (%)')
            axes[1,0].set_ylim(0, 100)
            
            # Actions critiques
            axes[1,1].bar(['Période 1', 'Période 2'],
                         [metrics1.critical_actions, metrics2.critical_actions],
                         color=['orange', 'red'])
            axes[1,1].set_title('Actions Critiques')
            
            plt.tight_layout()
            chart_path = 'surveillance/comparison_charts.png'
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            charts["metrics_evolution"] = chart_path
            
            # Graphique d'évolution des actions
            if evolution["new_actions"] or evolution["completed_actions"]:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                categories = ['Nouvelles Actions', 'Actions Terminées', 'Changements Statut', 'Changements Priorité']
                values = [len(evolution["new_actions"]), len(evolution["completed_actions"]),
                         len(evolution["status_changes"]), len(evolution["priority_changes"])]
                
                colors = ['green', 'blue', 'orange', 'purple']
                bars = ax.bar(categories, values, color=colors, alpha=0.7)
                
                # Ajouter les valeurs sur les barres
                for bar, value in zip(bars, values):
                    if value > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                               str(value), ha='center', va='bottom')
                
                ax.set_title('Évolution des Actions Entre les Périodes')
                ax.set_ylabel('Nombre d\'Actions')
                
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                evolution_chart_path = 'surveillance/action_evolution.png'
                plt.savefig(evolution_chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                charts["action_evolution"] = evolution_chart_path
            
        except Exception as e:
            logger.error(f"Erreur création graphiques: {e}")
            
        return charts
    
    def generate_recommendations(self, comparison: Dict, evolution: Dict) -> List[str]:
        """Génère des recommandations basées sur la comparaison"""
        recommendations = []
        
        try:
            # Recommandations basées sur l'évolution du taux de completion
            completion_change = comparison["evolution"]["completion_rate"]["change"]
            if completion_change < -10:
                recommendations.append(
                    "🔴 CRITIQUE: Le taux de completion a chuté significativement. "
                    "Réviser la planification et identifier les blocages."
                )
            elif completion_change < 0:
                recommendations.append(
                    "🟡 ATTENTION: Légère baisse du taux de completion. "
                    "Surveiller les actions en retard et réajuster les priorités."
                )
            elif completion_change > 10:
                recommendations.append(
                    "✅ EXCELLENT: Amélioration notable du taux de completion. "
                    "Maintenir cette dynamique positive."
                )
            
            # Recommandations sur les actions en retard
            overdue_change = comparison["evolution"]["overdue_actions"]["change"]
            if overdue_change > 0:
                recommendations.append(
                    f"⏰ RETARDS: {overdue_change} nouvelles actions en retard. "
                    "Réajuster les échéances ou allouer plus de ressources."
                )
            
            # Recommandations budgétaires
            budget_util = comparison["evolution"]["budget_utilization"]["period2"]
            if budget_util > 90:
                recommendations.append(
                    "💰 BUDGET: Utilisation budgétaire élevée (>90%). "
                    "Prévoir des fonds supplémentaires ou prioriser les actions critiques."
                )
            elif budget_util < 30:
                recommendations.append(
                    "💰 BUDGET: Faible utilisation budgétaire (<30%). "
                    "Accélérer la mise en œuvre ou réallouer les ressources."
                )
            
            # Recommandations sur les nouvelles actions
            if len(evolution["new_actions"]) > 5:
                recommendations.append(
                    f"📋 PLANIFICATION: {len(evolution['new_actions'])} nouvelles actions ajoutées. "
                    "Vérifier que les ressources sont suffisantes pour toutes les actions."
                )
            
            # Recommandations par défaut
            if not recommendations:
                recommendations.append(
                    "📊 SUIVI: Continuer le suivi régulier des indicateurs. "
                    "L'évolution du plan d'action semble maîtrisée."
                )
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            recommendations.append("Erreur lors de la génération des recommandations.")
        
        return recommendations
    
    def export_comparison_report(self, comparison_result: Dict, output_path: str):
        """Exporte le rapport de comparaison"""
        try:
            # Créer un rapport Excel détaillé
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Feuille de synthèse
                summary_data = []
                for metric, data in comparison_result["comparison"]["evolution"].items():
                    summary_data.append({
                        "Métrique": metric.replace('_', ' ').title(),
                        "Période 1": data["period1"],
                        "Période 2": data["period2"],
                        "Changement": data["change"],
                        "Changement %": f"{data.get('change_pct', 0):.1f}%"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Synthèse', index=False)
                
                # Feuille des nouvelles actions
                if comparison_result["action_evolution"]["new_actions"]:
                    new_actions_df = pd.DataFrame(comparison_result["action_evolution"]["new_actions"])
                    new_actions_df.to_excel(writer, sheet_name='Nouvelles Actions', index=False)
                
                # Feuille des actions terminées
                if comparison_result["action_evolution"]["completed_actions"]:
                    completed_df = pd.DataFrame(comparison_result["action_evolution"]["completed_actions"])
                    completed_df.to_excel(writer, sheet_name='Actions Terminées', index=False)
                
                # Feuille des recommandations
                recommendations_df = pd.DataFrame({
                    "Recommandations": comparison_result["recommendations"]
                })
                recommendations_df.to_excel(writer, sheet_name='Recommandations', index=False)
            
            logger.info(f"Rapport de comparaison exporté: {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur export rapport: {e}")

def compare_action_plans_cli(plan1_path: str, plan2_path: str, 
                            plan1_date: str = None, plan2_date: str = None,
                            output_dir: str = "surveillance/comparisons"):
    """Interface en ligne de commande pour comparer les plans d'action"""
    
    comparator = ActionPlanComparator()
    
    # Effectuer la comparaison
    result = comparator.compare_action_plans(plan1_path, plan2_path, plan1_date, plan2_date)
    
    if "error" in result:
        print(f"Erreur: {result['error']}")
        return None
    
    # Créer le répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"{output_dir}/comparison_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Exporter le rapport Excel
    report_file = f"{output_dir}/comparison_report_{timestamp}.xlsx"
    comparator.export_comparison_report(result, report_file)
    
    print(f"Comparaison terminée:")
    print(f"- Résultats JSON: {results_file}")
    print(f"- Rapport Excel: {report_file}")
    if result.get("charts"):
        print(f"- Graphiques: {result['charts']}")
    
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python action_plan_comparison.py <plan1.xlsx> <plan2.xlsx> [date1] [date2]")
        sys.exit(1)
    
    plan1 = sys.argv[1]
    plan2 = sys.argv[2]
    date1 = sys.argv[3] if len(sys.argv) > 3 else None
    date2 = sys.argv[4] if len(sys.argv) > 4 else None
    
    compare_action_plans_cli(plan1, plan2, date1, date2)
