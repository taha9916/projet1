import pandas as pd
import sys
import os
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Import des fonctions pour les données environnementales
from export_api_to_excel import get_coordinates, get_nearby_features

def load_data(risk_file, recommendations_file, action_plan_file):
    """Charge les données depuis les fichiers Excel."""
    try:
        risk_df = pd.read_excel(risk_file)
        recommendations_df = pd.read_excel(recommendations_file)
        action_plan_df = pd.read_excel(action_plan_file)
        
        # Préparer les données OSM pour la carte interactive
        osm_data = []
        for _, row in risk_df.iterrows():
            if 'latitude' in row and 'longitude' in row and pd.notna(row['latitude']) and pd.notna(row['longitude']):
                # Récupérer les caractéristiques environnementales à proximité
                try:
                    nearby_features = get_nearby_features(row['latitude'], row['longitude'], radius=5000)
                    
                    # Ajouter le site lui-même
                    osm_data.append({
                        'lat': row['latitude'],
                        'lon': row['longitude'],
                        'type': 'Site',
                        'name': row['nom_site'],
                        'risk_level': row.get('niveau_risque', 'Non défini'),
                        'marker_size': 15
                    })
                    
                    # Ajouter les points d'eau à proximité (simulés)
                    water_count = nearby_features.get('Points d\'eau', (0, ''))[0] or 0
                    if water_count > 0:
                        for i in range(min(water_count, 3)):  # Limiter à 3 points pour éviter la surcharge
                            offset = (i + 1) * 0.005  # Décalage pour la visualisation
                            osm_data.append({
                                'lat': row['latitude'] + offset,
                                'lon': row['longitude'] + offset,
                                'type': 'Point d\'eau',
                                'name': f'Point d\'eau près de {row["nom_site"]}',
                                'marker_size': 10
                            })
                    
                    # Ajouter les espaces verts à proximité (simulés)
                    park_count = nearby_features.get('Espaces verts', (0, ''))[0] or 0
                    if park_count > 0:
                        for i in range(min(park_count, 3)):  # Limiter à 3 points
                            offset = (i + 1) * 0.005
                            osm_data.append({
                                'lat': row['latitude'] - offset,
                                'lon': row['longitude'] + offset,
                                'type': 'Espace vert',
                                'name': f'Espace vert près de {row["nom_site"]}',
                                'marker_size': 10
                            })
                    
                    # Ajouter les zones industrielles à proximité (simulées)
                    industrial_count = nearby_features.get('Zones industrielles', (0, ''))[0] or 0
                    if industrial_count > 0:
                        for i in range(min(industrial_count, 3)):  # Limiter à 3 points
                            offset = (i + 1) * 0.005
                            osm_data.append({
                                'lat': row['latitude'] + offset,
                                'lon': row['longitude'] - offset,
                                'type': 'Zone industrielle',
                                'name': f'Zone industrielle près de {row["nom_site"]}',
                                'marker_size': 10
                            })
                except Exception as e:
                    print(f"Erreur lors de la récupération des caractéristiques pour {row['nom_site']}: {e}")
        
        return risk_df, recommendations_df, action_plan_df, pd.DataFrame(osm_data)
    except Exception as e:
        print(f"Erreur lors de la lecture des fichiers: {e}")
        sys.exit(1)

def create_dashboard(risk_df, recommendations_df, action_plan_df, osm_data):
    """Crée un tableau de bord interactif avec Dash."""
    # Initialiser l'application Dash
    app = dash.Dash(__name__, title="Tableau de Bord d'Analyse Environnementale")
    
    # Fusionner les DataFrames pour l'analyse
    merged_df = pd.merge(risk_df, recommendations_df, on='nom_site', how='left', suffixes=('', '_rec'))
    
    # Préparer les options pour les filtres
    site_options = [{'label': site, 'value': site} for site in risk_df['nom_site'].unique()]
    risk_level_options = [{'label': level, 'value': level} for level in risk_df['niveau_risque'].unique()]
    type_options = [{'label': type_val, 'value': type_val} for type_val in risk_df['type'].unique()]
    
    # Préparer les options pour les filtres du plan d'action
    priority_options = [{'label': priority, 'value': priority} for priority in action_plan_df['priorite'].unique()]
    category_options = [{'label': category, 'value': category} for category in action_plan_df['categorie'].unique()]
    status_options = [{'label': status, 'value': status} for status in action_plan_df['statut'].unique()]
    
    # Créer la mise en page du tableau de bord
    app.layout = html.Div([
        html.H1("Tableau de Bord d'Analyse Environnementale", style={'textAlign': 'center', 'color': '#2c3e50'}),
        
        # Onglets pour naviguer entre les différentes sections
        dcc.Tabs([
            # Onglet 1: Vue d'ensemble des risques
            dcc.Tab(label="Vue d'ensemble des risques", children=[
                html.Div([
                    html.H2("Filtres", style={'marginTop': '20px'}),
                    html.Div([
                        html.Div([
                            html.Label("Site:"),
                            dcc.Dropdown(
                                id='site-filter',
                                options=site_options,
                                multi=True,
                                placeholder="Sélectionner un ou plusieurs sites"
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Niveau de risque:"),
                            dcc.Dropdown(
                                id='risk-level-filter',
                                options=risk_level_options,
                                multi=True,
                                placeholder="Sélectionner un ou plusieurs niveaux de risque"
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Type de site:"),
                            dcc.Dropdown(
                                id='type-filter',
                                options=type_options,
                                multi=True,
                                placeholder="Sélectionner un ou plusieurs types de site"
                            )
                        ], style={'width': '30%', 'display': 'inline-block'})
                    ]),
                    
                    html.H2("Résumé des risques", style={'marginTop': '30px'}),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='risk-distribution-pie')
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        
                        html.Div([
                            dcc.Graph(id='risk-scores-bar')
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    
                    html.H2("Tableau des sites", style={'marginTop': '30px'}),
                    dash_table.DataTable(
                        id='sites-table',
                        columns=[
                            {'name': 'Site', 'id': 'nom_site'},
                            {'name': 'Type', 'id': 'type'},
                            {'name': 'Score Air', 'id': 'score_air'},
                            {'name': 'Score Eau', 'id': 'score_eau'},
                            {'name': 'Score Sol', 'id': 'score_sol'},
                            {'name': 'Score Humain', 'id': 'score_humain'},
                            {'name': 'Score Global', 'id': 'score_global'},
                            {'name': 'Niveau de Risque', 'id': 'niveau_risque'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'whiteSpace': 'normal',
                            'height': 'auto'
                        },
                        style_header={
                            'backgroundColor': '#f2f2f2',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{niveau_risque} = "Élevé"'},
                                'backgroundColor': '#ffcccc',
                                'color': '#990000'
                            },
                            {
                                'if': {'filter_query': '{niveau_risque} = "Moyen"'},
                                'backgroundColor': '#ffffcc',
                                'color': '#999900'
                            },
                            {
                                'if': {'filter_query': '{niveau_risque} = "Faible"'},
                                'backgroundColor': '#ccffcc',
                                'color': '#009900'
                            }
                        ]
                    )
                ])
            ]),
            
            # Onglet 2: Détails des recommandations
            dcc.Tab(label="Détails des recommandations", children=[
                html.Div([
                    html.H2("Sélectionner un site", style={'marginTop': '20px'}),
                    dcc.Dropdown(
                        id='site-selector',
                        options=site_options,
                        placeholder="Sélectionner un site"
                    ),
                    
                    html.Div(id='site-recommendations')
                ])
            ]),
            
            # Onglet 3: Plan d'action
            dcc.Tab(label="Plan d'action", children=[
                html.Div([
                    html.H2("Filtres du plan d'action", style={'marginTop': '20px'}),
                    html.Div([
                        html.Div([
                            html.Label("Site:"),
                            dcc.Dropdown(
                                id='action-site-filter',
                                options=site_options,
                                multi=True,
                                placeholder="Sélectionner un ou plusieurs sites"
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Priorité:"),
                            dcc.Dropdown(
                                id='priority-filter',
                                options=priority_options,
                                multi=True,
                                placeholder="Sélectionner une ou plusieurs priorités"
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Catégorie:"),
                            dcc.Dropdown(
                                id='category-filter',
                                options=category_options,
                                multi=True,
                                placeholder="Sélectionner une ou plusieurs catégories"
                            )
                        ], style={'width': '30%', 'display': 'inline-block'})
                    ]),
                    
                    html.Div([
                        html.Div([
                        html.Label("Statut:"),
                        dcc.Dropdown(
                            id='status-filter',
                            options=status_options,
                            multi=True,
                            placeholder="Sélectionner un ou plusieurs statuts"
                        )
                    ], style={'width': '30%', 'display': 'inline-block', 'marginTop': '10px'})
                ]),
                
                # Nouvelle section pour la carte interactive et les indicateurs
                html.Div([
                    html.Div([
                        html.H3("Carte interactive des sites et caractéristiques environnementales", style={'textAlign': 'center'}),
                        dcc.Graph(id='interactive-map')
                    ], style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                    
                    html.Div([
                        html.H3("Indicateur de risque global", style={'textAlign': 'center'}),
                        dcc.Graph(id='global-risk-indicator')
                    ], style={'width': '35%', 'display': 'inline-block', 'verticalAlign': 'top'})
                ]),
                
                # Nouvelle section pour le graphique des propriétés du sol
                html.Div([
                    html.H3("Propriétés du sol par site", style={'textAlign': 'center'}),
                    dcc.Graph(id='soil-properties-bar')
                ], style={'marginTop': '30px'}),
                    
                    html.H2("Résumé du plan d'action", style={'marginTop': '30px'}),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='action-priority-pie')
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        
                        html.Div([
                            dcc.Graph(id='action-category-bar')
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    
                    html.H2("Tableau du plan d'action", style={'marginTop': '30px'}),
                    dash_table.DataTable(
                        id='action-plan-table',
                        columns=[
                            {'name': 'Site', 'id': 'site'},
                            {'name': 'Action', 'id': 'action'},
                            {'name': 'Catégorie', 'id': 'categorie'},
                            {'name': 'Priorité', 'id': 'priorite'},
                            {'name': 'Responsable', 'id': 'responsable'},
                            {'name': 'Date de début', 'id': 'date_debut'},
                            {'name': 'Date de fin', 'id': 'date_fin'},
                            {'name': 'Budget estimé', 'id': 'budget_estime', 'type': 'numeric', 'format': {'specifier': ',.0f €'}},
                            {'name': 'Statut', 'id': 'statut'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'whiteSpace': 'normal',
                            'height': 'auto'
                        },
                        style_header={
                            'backgroundColor': '#f2f2f2',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{priorite} = "Haute"'},
                                'backgroundColor': '#ffcccc',
                                'color': '#990000'
                            },
                            {
                                'if': {'filter_query': '{priorite} = "Moyenne"'},
                                'backgroundColor': '#ffffcc',
                                'color': '#999900'
                            },
                            {
                                'if': {'filter_query': '{priorite} = "Basse"'},
                                'backgroundColor': '#ccffcc',
                                'color': '#009900'
                            }
                        ],
                        sort_action='native',
                        filter_action='native',
                        page_size=10
                    )
                ])
            ])
        ])
    ], style={'margin': '20px', 'fontFamily': 'Arial'})
    
    # Callback pour mettre à jour le graphique de distribution des risques
    @app.callback(
        Output('risk-distribution-pie', 'figure'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_risk_distribution(selected_sites, selected_risk_levels, selected_types):
        filtered_df = filter_dataframe(risk_df, selected_sites, selected_risk_levels, selected_types)
        risk_counts = filtered_df['niveau_risque'].value_counts().reset_index()
        risk_counts.columns = ['Niveau de risque', 'Nombre de sites']
        
        fig = px.pie(
            risk_counts, 
            values='Nombre de sites', 
            names='Niveau de risque',
            title='Distribution des niveaux de risque',
            color='Niveau de risque',
            color_discrete_map={
                'Élevé': '#e74c3c',
                'Moyen': '#f39c12',
                'Faible': '#27ae60'
            }
        )
        
        fig.update_layout(
            legend_title_text='Niveau de risque',
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    # Callback pour la carte interactive
    @app.callback(
        Output('interactive-map', 'figure'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_interactive_map(selected_sites, selected_risk_levels, selected_types):
        # Filtrer les données OSM en fonction des sites sélectionnés
        filtered_osm_data = osm_data.copy()
        if selected_sites:
            # Filtrer les sites
            site_mask = filtered_osm_data['type'] == 'Site'
            filtered_sites = filtered_osm_data[site_mask & filtered_osm_data['name'].isin(selected_sites)]
            
            # Filtrer les caractéristiques environnementales associées aux sites sélectionnés
            env_features = filtered_osm_data[~site_mask]
            env_features_filtered = pd.DataFrame()
            
            for site in selected_sites:
                site_features = env_features[env_features['name'].str.contains(site, na=False)]
                env_features_filtered = pd.concat([env_features_filtered, site_features])
            
            # Combiner les sites filtrés et leurs caractéristiques
            filtered_osm_data = pd.concat([filtered_sites, env_features_filtered])
        
        # Filtrer par niveau de risque si applicable (uniquement pour les sites)
        if selected_risk_levels:
            site_mask = filtered_osm_data['type'] == 'Site'
            sites = filtered_osm_data[site_mask]
            sites_filtered = sites[sites['risk_level'].isin(selected_risk_levels)]
            
            # Récupérer les caractéristiques des sites filtrés
            env_features = filtered_osm_data[~site_mask]
            env_features_filtered = pd.DataFrame()
            
            for site in sites_filtered['name'].unique():
                site_features = env_features[env_features['name'].str.contains(site, na=False)]
                env_features_filtered = pd.concat([env_features_filtered, site_features])
            
            filtered_osm_data = pd.concat([sites_filtered, env_features_filtered])
        
        # Créer la carte avec Plotly Express
        fig = px.scatter_mapbox(
            filtered_osm_data,
            lat="lat",
            lon="lon",
            color="type",
            size="marker_size",
            hover_name="name",
            hover_data={"type": True, "risk_level": True, "marker_size": False},
            color_discrete_map={
                "Site": "#FF0000",
                "Point d'eau": "#0000FF",
                "Espace vert": "#00FF00",
                "Zone industrielle": "#FF00FF"
            },
            zoom=5,
            height=500
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0},
            legend_title_text="Type d'élément"
        )
        
        return fig
    
    # Callback pour le graphique des propriétés du sol
    @app.callback(
        Output('soil-properties-bar', 'figure'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_soil_properties(selected_sites, selected_risk_levels, selected_types):
        filtered_df = filter_dataframe(risk_df, selected_sites, selected_risk_levels, selected_types)
        
        # Simuler des données de propriétés du sol pour chaque site
        soil_data = []
        for _, row in filtered_df.iterrows():
            site_name = row['nom_site']
            # Générer des valeurs simulées basées sur le niveau de risque
            risk_factor = 1.0
            if row['niveau_risque'] == 'Élevé':
                risk_factor = 1.5
            elif row['niveau_risque'] == 'Faible':
                risk_factor = 0.7
            
            # Simuler différentes propriétés du sol
            soil_data.append({
                'Site': site_name,
                'Propriété': 'pH',
                'Valeur': 6.5 + (risk_factor - 1) * 2
            })
            soil_data.append({
                'Site': site_name,
                'Propriété': 'Matière organique (%)',
                'Valeur': 3.0 * risk_factor
            })
            soil_data.append({
                'Site': site_name,
                'Propriété': 'Argile (%)',
                'Valeur': 25.0 * risk_factor
            })
            soil_data.append({
                'Site': site_name,
                'Propriété': 'Sable (%)',
                'Valeur': 40.0 / risk_factor
            })
        
        soil_df = pd.DataFrame(soil_data)
        
        # Créer le graphique en barres
        fig = px.bar(
            soil_df,
            x='Site',
            y='Valeur',
            color='Propriété',
            barmode='group',
            title='Propriétés du sol par site',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig.update_layout(
            xaxis_title='Site',
            yaxis_title='Valeur',
            legend_title='Propriété du sol',
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    # Callback pour l'indicateur de risque global
    @app.callback(
        Output('global-risk-indicator', 'figure'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_global_risk_indicator(selected_sites, selected_risk_levels, selected_types):
        filtered_df = filter_dataframe(risk_df, selected_sites, selected_risk_levels, selected_types)
        
        # Calculer le score moyen global
        avg_global_score = filtered_df['score_global'].mean() if not filtered_df.empty else 0
        
        # Calculer les scores moyens par catégorie
        avg_air = filtered_df['score_air'].mean() if not filtered_df.empty else 0
        avg_water = filtered_df['score_eau'].mean() if not filtered_df.empty else 0
        avg_soil = filtered_df['score_sol'].mean() if not filtered_df.empty else 0
        
        # Créer un indicateur de jauge
        fig = go.Figure()
        
        # Ajouter la jauge principale pour le score global
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=avg_global_score,
            domain={'x': [0, 1], 'y': [0, 0.5]},
            title={'text': "Score de risque global"},
            delta={'reference': 5, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 3.33], 'color': 'green'},
                    {'range': [3.33, 6.66], 'color': 'yellow'},
                    {'range': [6.66, 10], 'color': 'red'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': avg_global_score
                }
            }
        ))
        
        # Ajouter des indicateurs pour chaque catégorie
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=avg_air,
            domain={'x': [0, 0.3], 'y': [0.6, 1]},
            title={'text': "Air"},
            gauge={
                'axis': {'range': [0, 10]},
                'steps': [
                    {'range': [0, 3.33], 'color': 'green'},
                    {'range': [3.33, 6.66], 'color': 'yellow'},
                    {'range': [6.66, 10], 'color': 'red'}
                ]
            }
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=avg_water,
            domain={'x': [0.35, 0.65], 'y': [0.6, 1]},
            title={'text': "Eau"},
            gauge={
                'axis': {'range': [0, 10]},
                'steps': [
                    {'range': [0, 3.33], 'color': 'green'},
                    {'range': [3.33, 6.66], 'color': 'yellow'},
                    {'range': [6.66, 10], 'color': 'red'}
                ]
            }
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=avg_soil,
            domain={'x': [0.7, 1], 'y': [0.6, 1]},
            title={'text': "Sol"},
            gauge={
                'axis': {'range': [0, 10]},
                'steps': [
                    {'range': [0, 3.33], 'color': 'green'},
                    {'range': [3.33, 6.66], 'color': 'yellow'},
                    {'range': [6.66, 10], 'color': 'red'}
                ]
            }
        ))
        
        fig.update_layout(
            height=500,
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    # Callback pour mettre à jour le graphique des scores de risque
    @app.callback(
        Output('risk-scores-bar', 'figure'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_risk_scores(selected_sites, selected_risk_levels, selected_types):
        filtered_df = filter_dataframe(risk_df, selected_sites, selected_risk_levels, selected_types)
        
        fig = go.Figure()
        
        for category, color in zip(['score_air', 'score_eau', 'score_sol', 'score_humain', 'score_global'],
                                  ['#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#34495e']):
            fig.add_trace(go.Bar(
                x=filtered_df['nom_site'],
                y=filtered_df[category],
                name=category.replace('score_', '').capitalize(),
                marker_color=color
            ))
        
        fig.update_layout(
            title='Scores de risque par catégorie et par site',
            xaxis_title='Site',
            yaxis_title='Score',
            barmode='group',
            legend_title_text='Catégorie',
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    # Callback pour mettre à jour le tableau des sites
    @app.callback(
        Output('sites-table', 'data'),
        [Input('site-filter', 'value'),
         Input('risk-level-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_sites_table(selected_sites, selected_risk_levels, selected_types):
        filtered_df = filter_dataframe(risk_df, selected_sites, selected_risk_levels, selected_types)
        return filtered_df.to_dict('records')
    
    # Callback pour afficher les recommandations d'un site
    @app.callback(
        Output('site-recommendations', 'children'),
        [Input('site-selector', 'value')]
    )
    def display_site_recommendations(selected_site):
        if not selected_site:
            return html.Div([html.P("Veuillez sélectionner un site pour voir ses recommandations.")])
        
        site_data = merged_df[merged_df['nom_site'] == selected_site].iloc[0]
        
        # Créer le contenu des recommandations
        recommendations_content = []
        
        # Informations générales sur le site
        recommendations_content.append(html.Div([
            html.H3(f"{site_data['nom_site']} ({site_data['type']})"),
            html.P(f"Niveau de risque: {site_data['niveau_risque']}"),
            html.P(f"Score global: {site_data['score_global']:.2f}")
        ], style={'marginTop': '20px', 'marginBottom': '20px'}))
        
        # Scores par catégorie
        recommendations_content.append(html.Div([
            html.H4("Scores par catégorie"),
            html.Table([
                html.Thead(
                    html.Tr([html.Th("Air"), html.Th("Eau"), html.Th("Sol"), html.Th("Humain")])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(f"{site_data['score_air']:.2f}"),
                        html.Td(f"{site_data['score_eau']:.2f}"),
                        html.Td(f"{site_data['score_sol']:.2f}"),
                        html.Td(f"{site_data['score_humain']:.2f}")
                    ])
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginBottom': '20px'})
        ]))
        
        # Recommandations par catégorie
        categories = [
            ('Recommandations générales', 'recommandations_generales'),
            ('Recommandations pour l\'air', 'recommandations_air'),
            ('Recommandations pour l\'eau', 'recommandations_eau'),
            ('Recommandations pour le sol', 'recommandations_sol'),
            ('Recommandations pour le milieu humain', 'recommandations_humain')
        ]
        
        for cat_title, cat_field in categories:
            if cat_field in site_data and pd.notna(site_data[cat_field]) and site_data[cat_field].strip():
                recommendations_list = []
                for rec in site_data[cat_field].split('\n'):
                    if rec.strip():
                        recommendations_list.append(html.Li(rec))
                
                if recommendations_list:
                    recommendations_content.append(html.Div([
                        html.H4(cat_title),
                        html.Ul(recommendations_list)
                    ], style={'marginBottom': '20px'}))
        
        # Priorité d'action
        if 'priorite_action' in site_data and pd.notna(site_data['priorite_action']):
            priority_style = {
                'padding': '5px 10px',
                'borderRadius': '3px',
                'color': 'white',
                'fontWeight': 'bold',
                'display': 'inline-block'
            }
            
            if site_data['priorite_action'] == 'Haute':
                priority_style['backgroundColor'] = '#e74c3c'
            elif site_data['priorite_action'] == 'Moyenne':
                priority_style['backgroundColor'] = '#f39c12'
            else:  # Basse
                priority_style['backgroundColor'] = '#27ae60'
            
            recommendations_content.append(html.Div([
                html.H4("Priorité d'action"),
                html.Div(site_data['priorite_action'], style=priority_style)
            ], style={'marginBottom': '20px'}))
        
        return html.Div(recommendations_content, style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '5px'})
    
    # Callbacks pour l'onglet Plan d'action
    @app.callback(
        Output('action-priority-pie', 'figure'),
        [Input('action-site-filter', 'value'),
         Input('priority-filter', 'value'),
         Input('category-filter', 'value'),
         Input('status-filter', 'value')]
    )
    def update_action_priority_pie(selected_sites, selected_priorities, selected_categories, selected_statuses):
        filtered_df = filter_action_plan(action_plan_df, selected_sites, selected_priorities, selected_categories, selected_statuses)
        priority_counts = filtered_df['priorite'].value_counts().reset_index()
        priority_counts.columns = ['Priorité', 'Nombre d\'actions']
        
        fig = px.pie(
            priority_counts, 
            values='Nombre d\'actions', 
            names='Priorité',
            title='Distribution des priorités d\'action',
            color='Priorité',
            color_discrete_map={
                'Haute': '#e74c3c',
                'Moyenne': '#f39c12',
                'Basse': '#27ae60'
            }
        )
        
        fig.update_layout(
            legend_title_text='Priorité',
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    @app.callback(
        Output('action-category-bar', 'figure'),
        [Input('action-site-filter', 'value'),
         Input('priority-filter', 'value'),
         Input('category-filter', 'value'),
         Input('status-filter', 'value')]
    )
    def update_action_category_bar(selected_sites, selected_priorities, selected_categories, selected_statuses):
        filtered_df = filter_action_plan(action_plan_df, selected_sites, selected_priorities, selected_categories, selected_statuses)
        category_counts = filtered_df['categorie'].value_counts().reset_index()
        category_counts.columns = ['Catégorie', 'Nombre d\'actions']
        
        fig = px.bar(
            category_counts, 
            x='Catégorie', 
            y='Nombre d\'actions',
            title='Nombre d\'actions par catégorie',
            color='Catégorie',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            xaxis_title='Catégorie',
            yaxis_title='Nombre d\'actions',
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    @app.callback(
        Output('action-plan-table', 'data'),
        [Input('action-site-filter', 'value'),
         Input('priority-filter', 'value'),
         Input('category-filter', 'value'),
         Input('status-filter', 'value')]
    )
    def update_action_plan_table(selected_sites, selected_priorities, selected_categories, selected_statuses):
        filtered_df = filter_action_plan(action_plan_df, selected_sites, selected_priorities, selected_categories, selected_statuses)
        
        # Convertir les dates en chaînes de caractères pour l'affichage
        filtered_df['date_debut'] = filtered_df['date_debut'].dt.strftime('%d/%m/%Y')
        filtered_df['date_fin'] = filtered_df['date_fin'].dt.strftime('%d/%m/%Y')
        
        return filtered_df.to_dict('records')
    
    return app

def filter_dataframe(df, selected_sites, selected_risk_levels, selected_types):
    """Filtre le DataFrame en fonction des sélections."""
    filtered_df = df.copy()
    
    if selected_sites:
        filtered_df = filtered_df[filtered_df['nom_site'].isin(selected_sites)]
    
    if selected_risk_levels:
        filtered_df = filtered_df[filtered_df['niveau_risque'].isin(selected_risk_levels)]
    
    if selected_types:
        filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]
    
    return filtered_df

def filter_action_plan(df, selected_sites, selected_priorities, selected_categories, selected_statuses):
    """Filtre le DataFrame du plan d'action en fonction des sélections."""
    filtered_df = df.copy()
    
    if selected_sites:
        filtered_df = filtered_df[filtered_df['site'].isin(selected_sites)]
    
    if selected_priorities:
        filtered_df = filtered_df[filtered_df['priorite'].isin(selected_priorities)]
    
    if selected_categories:
        filtered_df = filtered_df[filtered_df['categorie'].isin(selected_categories)]
    
    if selected_statuses:
        filtered_df = filtered_df[filtered_df['statut'].isin(selected_statuses)]
    
    return filtered_df

def main():
    # Vérifier les arguments
    if len(sys.argv) < 4:
        print("Usage: python create_dashboard.py <fichier_risques> <fichier_recommandations> <fichier_plan_action>")
        print("Exemple: python create_dashboard.py resultats/analyse_risques.xlsx resultats/recommandations.xlsx resultats/plan_action.xlsx")
        sys.exit(1)
    
    # Récupérer les arguments
    risk_file = sys.argv[1]
    recommendations_file = sys.argv[2]
    action_plan_file = sys.argv[3]
    
    try:
        # Charger les données
        print(f"Chargement des données...")
        risk_df, recommendations_df, action_plan_df, osm_data = load_data(risk_file, recommendations_file, action_plan_file)
        print(f"Données chargées avec succès.")
        
        # Créer le tableau de bord
        print("Création du tableau de bord...")
        app = create_dashboard(risk_df, recommendations_df, action_plan_df, osm_data)
        
        # Lancer l'application
        print("\nLancement du tableau de bord...")
        print("Accédez au tableau de bord à l'adresse: http://127.0.0.1:8050/")
        app.run_server(debug=True)
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()