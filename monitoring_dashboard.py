#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tableau de bord avancé pour la surveillance continue des sites
Intègre les tendances temporelles, KPI et alertes automatiques
"""

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging
from site_monitoring import SiteMonitoring, TrendAnalyzer
from action_plan_comparison import ActionPlanComparator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringDashboard:
    """Tableau de bord de surveillance environnementale avancé"""
    
    def __init__(self, port=8051):
        self.port = port
        self.app = dash.Dash(__name__)
        self.monitoring = SiteMonitoring()
        self.trend_analyzer = TrendAnalyzer(self.monitoring)
        self.action_comparator = ActionPlanComparator()
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Configure la mise en page du tableau de bord"""
        
        # Styles CSS personnalisés
        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
        
        self.app.layout = html.Div([
            # En-tête
            html.Div([
                html.H1("🌍 Surveillance Continue - Sites Environnementaux", 
                       className="header-title",
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
                
                html.Div([
                    html.Div([
                        html.Label("Sélectionner un site:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='site-selector',
                            options=self.get_site_options(),
                            value=list(self.monitoring.config["sites"].keys())[0] if self.monitoring.config["sites"] else None,
                            style={'marginBottom': 10}
                        )
                    ], className="four columns"),
                    
                    html.Div([
                        html.Label("Période d'analyse:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='period-selector',
                            options=[
                                {'label': '7 derniers jours', 'value': 7},
                                {'label': '30 derniers jours', 'value': 30},
                                {'label': '90 derniers jours', 'value': 90},
                                {'label': '1 an', 'value': 365}
                            ],
                            value=30,
                            style={'marginBottom': 10}
                        )
                    ], className="four columns"),
                    
                    html.Div([
                        html.Button("🔄 Actualiser", id="refresh-button", 
                                   className="button-primary", style={'marginTop': 25})
                    ], className="four columns")
                ], className="row"),
                
            ], style={'padding': 20, 'backgroundColor': '#ecf0f1'}),
            
            # Indicateurs KPI
            html.Div(id="kpi-section", children=[
                html.H2("📊 Indicateurs Clés de Performance (KPI)", 
                       style={'color': '#34495e', 'marginBottom': 20}),
                html.Div(id="kpi-cards", className="row")
            ], style={'padding': 20}),
            
            # Alertes actives
            html.Div(id="alerts-section", children=[
                html.H2("🚨 Alertes Actives", 
                       style={'color': '#e74c3c', 'marginBottom': 20}),
                html.Div(id="alerts-display")
            ], style={'padding': 20, 'backgroundColor': '#fdf2f2'}),
            
            # Graphiques de tendances
            html.Div([
                html.H2("📈 Tendances Temporelles", 
                       style={'color': '#27ae60', 'marginBottom': 20}),
                
                dcc.Tabs(id="trends-tabs", value='water-trends', children=[
                    dcc.Tab(label='💧 Paramètres Eau', value='water-trends'),
                    dcc.Tab(label='🌬️ Qualité Air', value='air-trends'),
                    dcc.Tab(label='🌱 Paramètres Sol', value='soil-trends'),
                    dcc.Tab(label='⚡ Actions & Plans', value='action-trends')
                ]),
                
                html.Div(id='trends-content')
            ], style={'padding': 20}),
            
            # Comparaison temporelle des plans d'action
            html.Div([
                html.H2("🔄 Comparaison Temporelle des Plans d'Action", 
                       style={'color': '#8e44ad', 'marginBottom': 20}),
                
                html.Div([
                    html.Div([
                        html.Label("Plan d'action période 1:", style={'fontWeight': 'bold'}),
                        dcc.Upload(
                            id='upload-plan1',
                            children=html.Div(['Glissez-déposez ou ', html.A('sélectionnez un fichier')]),
                            style={
                                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                                'borderWidth': '1px', 'borderStyle': 'dashed',
                                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                            }
                        )
                    ], className="six columns"),
                    
                    html.Div([
                        html.Label("Plan d'action période 2:", style={'fontWeight': 'bold'}),
                        dcc.Upload(
                            id='upload-plan2',
                            children=html.Div(['Glissez-déposez ou ', html.A('sélectionnez un fichier')]),
                            style={
                                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                                'borderWidth': '1px', 'borderStyle': 'dashed',
                                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                            }
                        )
                    ], className="six columns"),
                ], className="row"),
                
                html.Div(id="plan-comparison-results")
            ], style={'padding': 20, 'backgroundColor': '#f8f9fa'}),
            
            # Actualisation automatique
            dcc.Interval(
                id='interval-component',
                interval=300*1000,  # 5 minutes
                n_intervals=0
            ),
            
            # Store pour les données
            dcc.Store(id='site-data-store'),
            dcc.Store(id='trends-data-store')
        ])
    
    def get_site_options(self):
        """Récupère les options de sites disponibles"""
        return [
            {'label': config['name'], 'value': site_id}
            for site_id, config in self.monitoring.config["sites"].items()
        ]
    
    def setup_callbacks(self):
        """Configure les callbacks interactifs"""
        
        @self.app.callback(
            [Output('site-data-store', 'data'),
             Output('trends-data-store', 'data')],
            [Input('site-selector', 'value'),
             Input('period-selector', 'value'),
             Input('refresh-button', 'n_clicks'),
             Input('interval-component', 'n_intervals')]
        )
        def update_data_stores(site_id, period_days, refresh_clicks, n_intervals):
            """Met à jour les données du site sélectionné"""
            if not site_id:
                return {}, {}
            
            try:
                # Charger les données de surveillance
                site_data = self.load_site_data(site_id, period_days)
                
                # Analyser les tendances
                trends_data = self.trend_analyzer.analyze_trends(site_id, period_days)
                
                return site_data, trends_data
                
            except Exception as e:
                logger.error(f"Erreur chargement données: {e}")
                return {}, {}
        
        @self.app.callback(
            Output('kpi-cards', 'children'),
            [Input('site-data-store', 'data'),
             Input('trends-data-store', 'data')]
        )
        def update_kpi_cards(site_data, trends_data):
            """Met à jour les cartes KPI"""
            if not site_data or not trends_data:
                return html.Div("Aucune donnée disponible", style={'textAlign': 'center'})
            
            cards = []
            
            # KPI 1: Nombre de mesures
            if 'measurements' in trends_data.get('period', {}):
                cards.append(self.create_kpi_card(
                    "📊", "Mesures Collectées", 
                    trends_data['period']['measurements'],
                    f"Sur {trends_data['period'].get('period_days', 30)} jours"
                ))
            
            # KPI 2: Alertes actives
            active_alerts = self.count_active_alerts(site_data)
            cards.append(self.create_kpi_card(
                "🚨", "Alertes Actives", 
                active_alerts,
                "Seuils dépassés" if active_alerts > 0 else "Tout conforme"
            ))
            
            # KPI 3: Taux de conformité
            compliance_rate = self.calculate_compliance_rate(site_data)
            cards.append(self.create_kpi_card(
                "✅", "Taux de Conformité", 
                f"{compliance_rate:.1f}%",
                "Paramètres conformes"
            ))
            
            # KPI 4: Tendance générale
            overall_trend = self.calculate_overall_trend(trends_data)
            trend_icon = "📈" if overall_trend == "positive" else "📉" if overall_trend == "negative" else "➡️"
            cards.append(self.create_kpi_card(
                trend_icon, "Tendance Générale", 
                overall_trend.upper(),
                "Évolution des paramètres"
            ))
            
            return cards
        
        @self.app.callback(
            Output('alerts-display', 'children'),
            [Input('site-data-store', 'data')]
        )
        def update_alerts_display(site_data):
            """Met à jour l'affichage des alertes"""
            if not site_data:
                return html.Div("Aucune alerte", style={'textAlign': 'center'})
            
            alerts = self.get_current_alerts(site_data)
            
            if not alerts:
                return html.Div([
                    html.I(className="fa fa-check-circle", style={'color': 'green', 'fontSize': 20}),
                    html.Span(" Aucune alerte active - Tous les paramètres sont conformes", 
                             style={'marginLeft': 10, 'color': 'green', 'fontWeight': 'bold'})
                ])
            
            alert_components = []
            for alert in alerts:
                alert_style = {
                    'padding': 10, 'margin': 5, 'borderRadius': 5,
                    'backgroundColor': '#ffebee' if alert.get('critical') else '#fff3e0'
                }
                
                alert_components.append(html.Div([
                    html.Strong(f"🔴 {alert['parameter']}" if alert.get('critical') else f"🟡 {alert['parameter']}"),
                    html.Br(),
                    html.Span(f"Valeur: {alert['value']} (Seuil: {alert['threshold']})"),
                    html.Br(),
                    html.Small(f"Détecté: {alert.get('timestamp', 'N/A')}")
                ], style=alert_style))
            
            return alert_components
        
        @self.app.callback(
            Output('trends-content', 'children'),
            [Input('trends-tabs', 'value'),
             Input('trends-data-store', 'data')]
        )
        def update_trends_content(active_tab, trends_data):
            """Met à jour le contenu des tendances selon l'onglet actif"""
            if not trends_data or 'parameters' not in trends_data:
                return html.Div("Aucune donnée de tendance disponible")
            
            if active_tab == 'water-trends':
                return self.create_trends_chart(trends_data, 'water', '💧 Paramètres de l\'Eau')
            elif active_tab == 'air-trends':
                return self.create_trends_chart(trends_data, 'air', '🌬️ Qualité de l\'Air')
            elif active_tab == 'soil-trends':
                return self.create_trends_chart(trends_data, 'soil', '🌱 Paramètres du Sol')
            elif active_tab == 'action-trends':
                return self.create_action_trends_chart()
            
            return html.Div("Sélectionnez un onglet")
    
    def load_site_data(self, site_id: str, period_days: int) -> dict:
        """Charge les données d'un site pour la période spécifiée"""
        try:
            data_dir = f"surveillance/{site_id}"
            if not os.path.exists(data_dir):
                return {}
            
            # Charger les fichiers de données récents
            current_time = datetime.now()
            cutoff_date = current_time - timedelta(days=period_days)
            
            site_data = {
                'measurements': [],
                'alerts': [],
                'parameters': {}
            }
            
            # Parcourir les fichiers de résultats
            for file_path in Path(data_dir).glob("results_*.json"):
                try:
                    # Extraire la date du fichier
                    date_str = file_path.stem.split('_')[1] + '_' + file_path.stem.split('_')[2]
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    
                    if file_date >= cutoff_date:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                site_data['measurements'].extend(data)
                            else:
                                site_data['measurements'].append(data)
                except Exception as e:
                    logger.warning(f"Erreur lecture fichier {file_path}: {e}")
                    continue
            
            return site_data
            
        except Exception as e:
            logger.error(f"Erreur chargement données site {site_id}: {e}")
            return {}
    
    def create_kpi_card(self, icon: str, title: str, value: str, subtitle: str):
        """Crée une carte KPI"""
        return html.Div([
            html.Div([
                html.Div([
                    html.H3(icon, style={'fontSize': 40, 'margin': 0, 'textAlign': 'center'}),
                    html.H4(str(value), style={'margin': 5, 'textAlign': 'center', 'color': '#2c3e50'}),
                    html.P(title, style={'margin': 0, 'textAlign': 'center', 'fontWeight': 'bold'}),
                    html.P(subtitle, style={'margin': 0, 'textAlign': 'center', 'fontSize': 12, 'color': '#7f8c8d'})
                ], style={'padding': 15})
            ], style={
                'backgroundColor': 'white',
                'borderRadius': 10,
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'height': 150
            })
        ], className="three columns")
    
    def count_active_alerts(self, site_data: dict) -> int:
        """Compte les alertes actives"""
        # Logique simplifiée - à adapter selon la structure des données
        return len(site_data.get('alerts', []))
    
    def calculate_compliance_rate(self, site_data: dict) -> float:
        """Calcule le taux de conformité"""
        total_params = 0
        compliant_params = 0
        
        for measurement in site_data.get('measurements', []):
            for medium in ['water', 'air', 'soil']:
                if medium in measurement:
                    for param, value in measurement[medium].items():
                        total_params += 1
                        # Vérifier conformité (logique simplifiée)
                        if isinstance(value, (list, tuple)) and len(value) > 1:
                            if '✓' in str(value[1]) or 'conforme' in str(value[1]).lower():
                                compliant_params += 1
        
        return (compliant_params / total_params * 100) if total_params > 0 else 0
    
    def calculate_overall_trend(self, trends_data: dict) -> str:
        """Calcule la tendance générale"""
        if 'parameters' not in trends_data:
            return "stable"
        
        positive_trends = 0
        negative_trends = 0
        
        for param_data in trends_data['parameters'].values():
            trend = param_data.get('trend', 'stable')
            if trend == 'croissante':
                positive_trends += 1
            elif trend == 'décroissante':
                negative_trends += 1
        
        if positive_trends > negative_trends:
            return "positive"
        elif negative_trends > positive_trends:
            return "negative"
        else:
            return "stable"
    
    def get_current_alerts(self, site_data: dict) -> list:
        """Récupère les alertes actuelles"""
        # Logique simplifiée pour les alertes
        alerts = []
        
        for measurement in site_data.get('measurements', []):
            for medium in ['water', 'air', 'soil']:
                if medium in measurement:
                    for param, value in measurement[medium].items():
                        # Vérifier si c'est une alerte (logique simplifiée)
                        if isinstance(value, (list, tuple)) and len(value) > 1:
                            if '✗' in str(value[1]) or 'non conforme' in str(value[1]).lower():
                                alerts.append({
                                    'parameter': f"{param} ({medium})",
                                    'value': value[0] if isinstance(value, (list, tuple)) else value,
                                    'threshold': 'Seuil dépassé',
                                    'critical': True,
                                    'timestamp': measurement.get('timestamp', 'N/A')
                                })
        
        return alerts[:10]  # Limiter à 10 alertes
    
    def create_trends_chart(self, trends_data: dict, medium: str, title: str):
        """Crée un graphique de tendances pour un milieu donné"""
        try:
            # Filtrer les paramètres par milieu
            medium_params = {
                k: v for k, v in trends_data.get('parameters', {}).items() 
                if k.startswith(f"{medium}.")
            }
            
            if not medium_params:
                return html.Div(f"Aucune donnée disponible pour {title}")
            
            # Créer le graphique
            fig = go.Figure()
            
            for param_key, param_data in medium_params.items():
                param_name = param_key.split('.', 1)[1]  # Enlever le préfixe du milieu
                
                # Données de tendance simplifiées
                x_data = ['Début période', 'Fin période']
                y_data = [param_data.get('previous_value', 0), param_data.get('current_value', 0)]
                
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='lines+markers',
                    name=param_name,
                    line=dict(width=3)
                ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Période",
                yaxis_title="Valeurs",
                hovermode='x unified',
                height=400
            )
            
            return dcc.Graph(figure=fig)
            
        except Exception as e:
            logger.error(f"Erreur création graphique tendances: {e}")
            return html.Div(f"Erreur lors de la création du graphique: {str(e)}")
    
    def create_action_trends_chart(self):
        """Crée un graphique des tendances des plans d'action"""
        # Données d'exemple - à remplacer par des données réelles
        fig = go.Figure()
        
        # Exemple de données de progression des actions
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun']
        completed = [5, 8, 12, 18, 22, 25]
        in_progress = [10, 12, 8, 6, 8, 10]
        planned = [15, 10, 15, 12, 8, 5]
        
        fig.add_trace(go.Scatter(x=months, y=completed, mode='lines+markers', 
                                name='Actions Terminées', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=months, y=in_progress, mode='lines+markers', 
                                name='En Cours', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=months, y=planned, mode='lines+markers', 
                                name='Planifiées', line=dict(color='blue')))
        
        fig.update_layout(
            title="⚡ Évolution des Plans d'Action",
            xaxis_title="Mois",
            yaxis_title="Nombre d'Actions",
            hovermode='x unified',
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def run(self, debug=False):
        """Lance le tableau de bord"""
        logger.info(f"Lancement du tableau de bord de surveillance sur le port {self.port}")
        self.app.run_server(debug=debug, port=self.port, host='0.0.0.0')

if __name__ == "__main__":
    dashboard = MonitoringDashboard(port=8051)
    dashboard.run(debug=True)
