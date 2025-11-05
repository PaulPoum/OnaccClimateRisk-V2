# drought_monitoring/app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import warnings
import requests
import json
import os
import sys

# CORRECTION : Ajouter le chemin du répertoire courant au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Maintenant importer les modules utils
try:
    from utils.data_loader import load_localities, get_climate_data
    from utils.drought_calculator import calculate_drought_indicators, assess_drought_risk
    from utils.deepseek_advisor import get_ai_recommendations
    from utils.satellite_processor import get_satellite_data, process_risk_zones
    from utils.forecast_analyzer import get_forecast_analyzer
    from utils.alert_generator import get_alert_generator, parse_group_alert_message
except ImportError as e:
    st.error(f"Erreur d'importation: {e}")
    st.info("""
    **Solution:**
    - Vérifiez que le dossier `utils` existe dans `drought_monitoring/`
    - Vérifiez que tous les fichiers Python sont présents dans `utils/`
    - Vérifiez que `utils/__init__.py` existe (même vide)
    """)
    # Créer des fonctions de secours pour permettre le fonctionnement
    def load_localities():
        return pd.DataFrame()
    
    def get_climate_data(*args, **kwargs):
        return None
    
    def calculate_drought_indicators(*args, **kwargs):
        return {}
    
    def assess_drought_risk(*args, **kwargs):
        return {'risk_level': 'Inconnu', 'risk_score': 0}
    
    def get_ai_recommendations(*args, **kwargs):
        return {'alerts': [], 'actions': [], 'forecast': {}}
    
    def get_satellite_data(*args, **kwargs):
        return None
    
    def process_risk_zones(*args, **kwargs):
        return []
    
    def get_forecast_analyzer():
        return None
    
    def get_alert_generator():
        return None
    
    def parse_group_alert_message(*args, **kwargs):
        return {}

import base64

warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="🌍 ONACC - Plateforme Intelligente de Suivi des Sécheresses",
    page_icon="🌵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement du style CSS avec gestion d'erreur
def load_css():
    try:
        css_path = os.path.join(current_dir, 'assets', 'style.css')
        if os.path.exists(css_path):
            with open(css_path, encoding='utf-8') as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erreur CSS: {e}")

load_css()

class ModernDroughtPlatform:
    def __init__(self):
        self.localities_df = None
        self.satellite_layers = {
            "NDVI": {"name": "Indice de Végétation", "color": "viridis"},
            "Température": {"name": "Température de Surface", "color": "hot"},
            "Humidité": {"name": "Humidité du Sol", "color": "blues"},
            "Risque": {"name": "Niveau de Risque", "color": "reds"}
        }
    
    def load_data(self):
        """Charge les données des localités"""
        try:
            self.localities_df = load_localities()
            return True
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {e}")
            return False
    
    def create_sidebar(self):
        """Crée la sidebar moderne"""
        with st.sidebar:
            st.markdown("""
            <div class="sidebar-header">
                <h2>CONFIGURATION</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Sélection de la région
            st.subheader("📍 Sélection Géographique")
            regions = ['Toutes'] + sorted(self.localities_df['region'].unique().tolist())
            selected_region = st.selectbox("Région:", regions)
            
            # Filtrage des localités
            if selected_region != 'Toutes':
                filtered_localities = self.localities_df[self.localities_df['region'] == selected_region]
            else:
                filtered_localities = self.localities_df
            
            selected_locality = st.selectbox(
                "Localité:", 
                filtered_localities['localite'].unique()
            )
            
            # Paramètres d'analyse
            st.subheader("📊 Paramètres d'Analyse")
            analysis_period = st.selectbox(
                "Période d'analyse:",
                ['7 jours', '15 jours', '30 jours', '90 jours', '1 an']
            )
            
            # Couches satellites
            st.subheader("🛰️ Couches Satellites")
            satellite_layer = st.selectbox(
                "Données satellite:",
                list(self.satellite_layers.keys())
            )
            
            # Seuils d'alerte
            st.subheader("⚡ Seuils d'Alerte")
            spi_threshold = st.slider("Seuil SPI critique:", -2.5, 0.0, -1.5)
            precip_threshold = st.slider("Déficit pluviométrique (%):", 0, 100, 40)
            
            # Bouton d'analyse
            if st.button("🚀 Lancer l'Analyse Complète", use_container_width=True):
                st.session_state.analyze_clicked = True
                st.session_state.selected_locality = selected_locality
                st.session_state.analysis_period = analysis_period
                st.session_state.satellite_layer = satellite_layer
            
            st.markdown("---")
            st.markdown("""
            <div class="sidebar-footer">
                <p><strong>Sources de données:</strong></p>
                <p>• OpenMeteo 🌤️</p>
                <p>• Sentinel-2 🛰️</p>
                <p>• Landsat 8-9 📡</p>
                <p>• MODIS 🌍</p>
            </div>
            """, unsafe_allow_html=True)
        
        return selected_locality, analysis_period, satellite_layer
    
    def create_dashboard(self):
        """Crée le tableau de bord moderne"""
        
        # Header avec métriques principales
        st.markdown("""
        <div class="main-header">
            <h1>ANALYSE ET SUIVI DES SÉCHERESSES</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar
        selected_locality, analysis_period, satellite_layer = self.create_sidebar()
        
        if not hasattr(st.session_state, 'analyze_clicked'):
            self.show_landing_page()
            return
        
        # Récupération des données de la localité
        locality_data = self.localities_df[
            self.localities_df['localite'] == selected_locality
        ].iloc[0]
        
        # Création des onglets principaux
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 ANALYSE TEMPS RÉEL", 
            "🗺️ CARTOGRAPHIE", 
            "🔮 PRÉVISIONS",
            "🚨 ALERTES AUTO",
            "🤖 RECOMMANDATIONS IA"
        ])
        
        with tab1:
            # Section d'analyse en temps réel
            climate_data, drought_indicators, risk_assessment = self.show_real_time_analysis(locality_data, analysis_period)
            
            # Stocker les données pour les autres onglets
            st.session_state.climate_data = climate_data
            st.session_state.drought_indicators = drought_indicators
        
        with tab2:
            # Section cartographique avancée
            self.show_advanced_map(locality_data, satellite_layer)
            
            # Section d'analyse satellitaire
            self.show_satellite_analysis(locality_data, satellite_layer)
        
        with tab3:
            # Section prévisions
            self.show_forecast_analysis(locality_data)
        
        with tab4:
            # Section alertes automatiques
            self.show_alert_dashboard()
        
        with tab5:
            # Section recommandations IA
            climate_data = st.session_state.get('climate_data')
            drought_indicators = st.session_state.get('drought_indicators')
            
            if climate_data is not None and drought_indicators is not None:
                self.show_ai_recommendations(locality_data, climate_data, drought_indicators)
            else:
                st.warning("⚠️ Veuillez d'abord effectuer l'analyse en temps réel")
    
    def show_landing_page(self):
        """Affiche la page d'accueil"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="landing-content">
                <h2>🚨 Système d'Alerte Précoce aux Sécheresses</h2>
                <p>Plateforme intégrée combinant données satellitaires, météorologiques 
                et intelligence artificielle pour la surveillance et la prévention des risques de sécheresse.</p>
                
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>🛰️ Surveillance Satellite</h3>
                        <p>Données Sentinel, Landsat et MODIS en temps réel</p>
                    </div>
                    <div class="feature-card">
                        <h3>🤖 IA Prédictive</h3>
                        <p>Recommandations DeepSeek pour les alertes</p>
                    </div>
                    <div class="feature-card">
                        <h3>🌡️ Analyse Multi-paramètres</h3>
                        <p>SPI, NDVI, température, humidité, etc.</p>
                    </div>
                    <div class="feature-card">
                        <h3>🗺️ Cartographie Dynamique</h3>
                        <p>Visualisation des zones à risque</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="quick-stats">
                <h3>📈 Statistiques Globales</h3>
                <div class="stat-card">
                    <span class="stat-number">12</span>
                    <span class="stat-label">Régions surveillées</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">47</span>
                    <span class="stat-label">Localités actives</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">3</span>
                    <span class="stat-label">Alertes actives</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_real_time_analysis(self, locality_data, analysis_period):
        """Affiche l'analyse en temps réel et retourne les données"""
        st.markdown("## 📊 ANALYSE EN TEMPS RÉEL")
        
        with st.spinner("🛰️ Récupération des données satellitaires et climatiques..."):
            # Récupération des données
            climate_data = get_climate_data(
                locality_data['latitude'], 
                locality_data['longitude'], 
                analysis_period
            )
            
            if climate_data:
                # Calcul des indicateurs
                drought_indicators = calculate_drought_indicators(climate_data)
                risk_assessment = assess_drought_risk(drought_indicators)
                
                # Métriques principales
                self.display_risk_metrics(risk_assessment, locality_data)
                
                # Graphiques avancés
                self.display_advanced_charts(climate_data, drought_indicators)
                
                # Tableau de bord des indicateurs
                self.display_indicators_dashboard(drought_indicators)
                
                return climate_data, drought_indicators, risk_assessment
            else:
                st.error("❌ Impossible de récupérer les données climatiques")
                return None, None, None
    
    def display_risk_metrics(self, risk_assessment, locality_data):
        """Affiche les métriques de risque"""
        col1, col2, col3, col4 = st.columns(4)
        
        risk_color = {
            'Très Élevé': '#ff0000',
            'Élevé': '#ff6b6b', 
            'Modéré': '#ffa500',
            'Faible': '#4CAF50',
            'Très Faible': '#2E8B57'
        }.get(risk_assessment['risk_level'], '#808080')
        
        with col1:
            st.markdown(f"""
            <div class="metric-card risk-card">
                <div class="metric-title">NIVEAU DE RISQUE</div>
                <div class="metric-value" style="color: {risk_color}">{risk_assessment['risk_level']}</div>
                <div class="metric-desc">Score: {risk_assessment['risk_score']}/100</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">INDICE SPI</div>
                <div class="metric-value">{risk_assessment['spi_value']:.2f}</div>
                <div class="metric-desc">{self.get_spi_interpretation(risk_assessment['spi_value'])}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">DÉFICIT PLUVIOMÉTRIQUE</div>
                <div class="metric-value">{risk_assessment['precipitation_deficit']:.1f}%</div>
                <div class="metric-desc">Par rapport à la normale</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">ZONE AGRO-ÉCOLOGIQUE</div>
                <div class="metric-value">{locality_data['zone']}</div>
                <div class="metric-desc">{locality_data['region']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def display_advanced_charts(self, climate_data, drought_indicators):
        """Affiche les graphiques avancés"""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Évolution Temporelle", 
            "🌡️ Bilans Hydriques", 
            "🌵 Poches de Sécheresse",
            "🗓️ Heatmap Mensuelle",
            "📊 Indicateurs Clés"
        ])
        
        with tab1:
            self.create_temporal_charts(climate_data, drought_indicators)
        
        with tab2:
            self.create_water_balance_charts(climate_data)
        
        with tab3:
            self.create_drought_pockets_chart(climate_data, drought_indicators)
        
        with tab4:
            self.create_drought_heatmap(climate_data, drought_indicators)
        
        with tab5:
            self.create_indicators_radar(drought_indicators)
    
    def create_temporal_charts(self, climate_data, drought_indicators):
        """Crée les graphiques temporels"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Précipitations et Évapotranspiration', 
                'Températures Moyennes',
                'Humidité du Sol', 
                'Indice de Sécheresse (SPI)'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        # Graphique 1: Précipitations et ET0
        fig.add_trace(
            go.Bar(x=climate_data['dates'], y=climate_data['precipitation'], 
                  name='Précipitations', marker_color='#1f77b4'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=climate_data['dates'], y=climate_data['et0'], 
                      name='ET0', line=dict(color='red'), yaxis='y2'),
            row=1, col=1
        )
        
        # Graphique 2: Températures
        fig.add_trace(
            go.Scatter(x=climate_data['dates'], y=climate_data['temperature_2m_max'], 
                      name='Temp Max', line=dict(color='#ff7f0e')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=climate_data['dates'], y=climate_data['temperature_2m_min'], 
                      name='Temp Min', line=dict(color='#1f77b4')),
            row=1, col=2
        )
        
        # Graphique 3: Humidité du sol
        fig.add_trace(
            go.Scatter(x=climate_data['dates'], y=climate_data['soil_moisture'], 
                      name='Humidité Sol', line=dict(color='brown'), fill='tozeroy'),
            row=2, col=1
        )
        
        # Graphique 4: SPI
        if drought_indicators['spi']:
            spi_dates = list(drought_indicators['spi'].keys())
            spi_values = list(drought_indicators['spi'].values())
            fig.add_trace(
                go.Scatter(x=[climate_data['dates'][i] for i in spi_dates], 
                          y=spi_values,
                          name='SPI', line=dict(color='purple')),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    def create_water_balance_charts(self, climate_data):
        """Crée les graphiques de bilan hydrique"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Bilan hydrique cumulé
            water_balance = np.cumsum(climate_data['precipitation'] - climate_data['et0'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=climate_data['dates'], y=water_balance,
                fill='tozeroy', line=dict(color='blue'),
                name='Bilan Hydrique'
            ))
            fig.update_layout(
                title="Bilan Hydrique Cumulé",
                xaxis_title="Date",
                yaxis_title="Bilan (mm)",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Diagramme en camembert des déficits
            total_precip = np.sum(climate_data['precipitation'])
            total_et0 = np.sum(climate_data['et0'])
            deficit = max(0, total_et0 - total_precip)
            
            fig = go.Figure(data=[go.Pie(
                labels=['Précipitations', 'Déficit'],
                values=[total_precip, deficit],
                hole=0.4,
                marker_colors=['#1f77b4', '#ff6b6b']
            )])
            fig.update_layout(
                title="Répartition Précipitations/Déficit",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_drought_pockets_chart(self, climate_data, drought_indicators):
        """
        Crée un graphique combiné pour identifier les poches de sécheresse
        """
        st.markdown("### 🌵 Identification des Poches de Sécheresse")
        
        # Création du graphique combiné
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Précipitations vs Évapotranspiration (Déficit Hydrique)',
                'Identification des Périodes de Sécheresse'
            ),
            vertical_spacing=0.15,
            shared_xaxes=True
        )
        
        # Graphique 1: Précipitations vs ET0
        dates = climate_data['dates']
        
        # Barres de précipitations
        fig.add_trace(
            go.Bar(
                x=dates, 
                y=climate_data['precipitation'],
                name='Précipitations',
                marker_color='#1f77b4',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Ligne d'évapotranspiration
        fig.add_trace(
            go.Scatter(
                x=dates, 
                y=climate_data['et0'],
                name='Évapotranspiration (ET0)',
                line=dict(color='red', width=2),
                yaxis='y1'
            ),
            row=1, col=1
        )
        
        # Zones de déficit (où ET0 > Précipitations)
        for i in range(len(dates)):
            if climate_data['et0'][i] > climate_data['precipitation'][i]:
                fig.add_vrect(
                    x0=dates[i] - timedelta(hours=12),
                    x1=dates[i] + timedelta(hours=12),
                    fillcolor="red",
                    opacity=0.2,
                    line_width=0,
                    row=1, col=1
                )
        
        # Graphique 2: Indicateurs de sécheresse combinés
        # SPI
        if drought_indicators['spi']:
            spi_dates = [dates[i] for i in drought_indicators['spi'].keys()]
            spi_values = list(drought_indicators['spi'].values())
            fig.add_trace(
                go.Scatter(
                    x=spi_dates, 
                    y=spi_values,
                    name='SPI',
                    line=dict(color='purple', width=3),
                    yaxis='y2'
                ),
                row=2, col=1
            )
        
        # Humidité du sol (normalisée)
        soil_moisture_norm = (climate_data['soil_moisture'] - np.min(climate_data['soil_moisture'])) / \
                             (np.max(climate_data['soil_moisture']) - np.min(climate_data['soil_moisture']))
        fig.add_trace(
            go.Scatter(
                x=dates, 
                y=soil_moisture_norm * 2 - 1,  # Normalisation entre -1 et 1 pour comparer avec SPI
                name='Humidité Sol (normalisée)',
                line=dict(color='brown', width=2),
                yaxis='y2'
            ),
            row=2, col=1
        )
        
        # Seuils de sécheresse
        fig.add_hline(y=-1, line_dash="dash", line_color="orange", row=2, col=1,
                     annotation_text="Sécheresse modérée")
        fig.add_hline(y=-1.5, line_dash="dash", line_color="red", row=2, col=1,
                     annotation_text="Sécheresse sévère")
        fig.add_hline(y=-2, line_dash="dash", line_color="darkred", row=2, col=1,
                     annotation_text="Sécheresse extrême")
        
        # Mise en forme
        fig.update_layout(
            height=600,
            title_text="Identification des Poches de Sécheresse",
            showlegend=True,
            template="plotly_white"
        )
        
        # Mise à jour des axes
        fig.update_yaxes(title_text="Précipitations/ET0 (mm)", row=1, col=1)
        fig.update_yaxes(title_text="Indice de Sécheresse", row=2, col=1, range=[-2.5, 2.5])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analyse des poches de sécheresse détectées
        self.analyze_drought_periods(climate_data, drought_indicators)
        
    def validate_drought_period(self, period):
        """
        Valide et complète une période de sécheresse avec des valeurs par défaut
        """
        if not isinstance(period, dict):
            return None
        
        # Clés requises avec valeurs par défaut
        required_keys = {
            'start_date': 'Date inconnue',
            'end_date': 'Date inconnue', 
            'dry_days': 0,
            'avg_deficit': 0,
            'intensity': 'inconnue'
        }
        
        validated_period = period.copy()
        for key, default_value in required_keys.items():
            if key not in validated_period:
                validated_period[key] = default_value
        
        return validated_period

    def analyze_drought_periods(self, climate_data, drought_indicators):
        """
        Analyse et affiche les périodes de sécheresse détectées
        """
        # Détection des périodes de sécheresse
        drought_periods = self.detect_drought_periods(climate_data, drought_indicators)
        
        if drought_periods:
            st.markdown("#### 📅 Périodes de Sécheresse Identifiées")
            
            for i, period in enumerate(drought_periods, 1):
                # Valider la période
                validated_period = self.validate_drought_period(period)
                if not validated_period:
                    continue
                    
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    start_date = validated_period['start_date']
                    end_date = validated_period['end_date']
                    dry_days = validated_period['dry_days']
                    
                    # Formater les dates
                    start_str = start_date.strftime('%d/%m/%Y') if hasattr(start_date, 'strftime') else str(start_date)
                    end_str = end_date.strftime('%d/%m/%Y') if hasattr(end_date, 'strftime') else str(end_date)
                    
                    st.write(f"**Période {i}:** {start_str} - {end_str}")
                    st.write(f"Durée: {dry_days} jours")
                
                with col2:
                    avg_deficit = validated_period['avg_deficit']
                    st.metric("Déficit moyen", f"{avg_deficit:.1f} mm/jour")
                
                with col3:
                    intensity = validated_period['intensity']
                    risk_color = {
                        'faible': '🟢',
                        'modérée': '🟡', 
                        'sévère': '🟠',
                        'extrême': '🔴'
                    }.get(intensity, '⚫')
                    st.write(f"Intensité: {risk_color} {intensity}")
        
        # Statistiques récapitulatives
        self.display_drought_statistics(climate_data, drought_indicators, drought_periods)
        
        # Statistiques récapitulatives
        self.display_drought_statistics(climate_data, drought_indicators, drought_periods)

    def detect_drought_periods(self, climate_data, drought_indicators, dry_threshold=0.1):
        """
        Détecte les périodes de sécheresse continues
        """
        precipitation = climate_data['precipitation']
        dates = climate_data['dates']
        
        drought_periods = []
        current_period = None
        
        for i, (date, precip) in enumerate(zip(dates, precipitation)):
            # Vérifier si c'est un jour sec
            is_dry_day = precip < dry_threshold
            
            if is_dry_day and current_period is None:
                # Début d'une nouvelle période de sécheresse
                current_period = {
                    'start_date': date,
                    'start_index': i,
                    'dry_days': 1,  # Utiliser 'dry_days' au lieu de 'duration'
                    'total_precip': precip
                }
            elif is_dry_day and current_period is not None:
                # Continuation de la période de sécheresse
                current_period['dry_days'] += 1
                current_period['total_precip'] += precip
            elif not is_dry_day and current_period is not None:
                # Fin de la période de sécheresse
                current_period['end_date'] = date - timedelta(days=1)
                current_period['end_index'] = i - 1
                current_period['avg_precip'] = current_period['total_precip'] / current_period['dry_days']
                current_period['avg_deficit'] = dry_threshold - current_period['avg_precip']
                current_period['intensity'] = self.assess_drought_intensity(
                    current_period['dry_days'], 
                    current_period['avg_deficit']
                )
                
                # Ne garder que les périodes significatives (au moins 3 jours)
                if current_period['dry_days'] >= 3:
                    drought_periods.append(current_period)
                
                current_period = None
        
        # Gérer la période en cours à la fin des données
        if current_period is not None and current_period['dry_days'] >= 3:
            current_period['end_date'] = dates[-1]
            current_period['end_index'] = len(dates) - 1
            current_period['avg_precip'] = current_period['total_precip'] / current_period['dry_days']
            current_period['avg_deficit'] = dry_threshold - current_period['avg_precip']
            current_period['intensity'] = self.assess_drought_intensity(
                current_period['dry_days'], 
                current_period['avg_deficit']
            )
            drought_periods.append(current_period)
        
        return drought_periods
        
        # Gérer la période en cours à la fin des données
        if current_period is not None and current_period['dry_days'] >= 3:
            current_period['end_date'] = dates[-1]
            current_period['end_index'] = len(dates) - 1
            current_period['avg_precip'] = current_period['total_precip'] / current_period['dry_days']
            current_period['avg_deficit'] = dry_threshold - current_period['avg_precip']
            current_period['intensity'] = self.assess_drought_intensity(
                current_period['dry_days'], 
                current_period['avg_deficit']
            )
            drought_periods.append(current_period)
        
        return drought_periods

    def assess_drought_intensity(self, duration, deficit):
        """
        Évalue l'intensité d'une période de sécheresse
        """
        intensity_score = duration * deficit
        
        if intensity_score > 10:
            return "extrême"
        elif intensity_score > 5:
            return "sévère"
        elif intensity_score > 2:
            return "modérée"
        else:
            return "faible"

    def display_drought_statistics(self, climate_data, drought_indicators, drought_periods):
        """
        Affiche les statistiques récapitulatives sur les sécheresses
        """
        st.markdown("#### 📊 Statistiques des Sécheresses")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_dry_days = sum(1 for precip in climate_data['precipitation'] if precip < 0.1)
            total_days = len(climate_data['precipitation'])
            st.metric("Jours sans pluie", f"{total_dry_days}/{total_days}")
        
        with col2:
            total_drought_days = sum(period.get('dry_days', 0) for period in drought_periods) if drought_periods else 0
            st.metric("Jours de sécheresse", total_drought_days)
        
        with col3:
            if drought_periods:
                longest_period = max([period.get('dry_days', 0) for period in drought_periods])
            else:
                longest_period = 0
            st.metric("Période sèche la plus longue", f"{longest_period} jours")
        
        with col4:
            if drought_periods:
                severe_periods = sum(1 for period in drought_periods if period.get('intensity') in ['sévère', 'extrême'])
            else:
                severe_periods = 0
            st.metric("Périodes sévères", severe_periods)

    def create_drought_heatmap(self, climate_data, drought_indicators):
        """
        Crée une heatmap pour visualiser l'évolution des sécheresses dans le temps
        """
        st.markdown("### 🗓️ Heatmap des Sécheresses Mensuelles")
        
        # Préparation des données pour la heatmap
        df = pd.DataFrame({
            'date': climate_data['dates'],
            'precipitation': climate_data['precipitation'],
            'temperature': climate_data['temperature_2m_mean'],
            'soil_moisture': climate_data['soil_moisture']
        })
        
        # Agrégation par mois
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        monthly_data = df.groupby(['year', 'month']).agg({
            'precipitation': 'sum',
            'temperature': 'mean',
            'soil_moisture': 'mean'
        }).reset_index()
        
        # Calcul d'un indice de sécheresse mensuel
        monthly_data['drought_index'] = (
            (monthly_data['precipitation'] / monthly_data['precipitation'].mean()) +
            (monthly_data['soil_moisture'] / monthly_data['soil_moisture'].mean()) +
            (monthly_data['temperature'] / monthly_data['temperature'].mean())
        ) / 3
        
        # Création de la heatmap
        pivot_data = monthly_data.pivot(index='month', columns='year', values='drought_index')
        
        fig = px.imshow(
            pivot_data,
            title="Indice de Sécheresse Mensuel (Plus la couleur est chaude, plus la sécheresse est sévère)",
            color_continuous_scale="RdYlBu_r",  # Rouge pour la sécheresse, bleu pour l'humidité
            aspect="auto"
        )
        
        fig.update_layout(
            xaxis_title="Année",
            yaxis_title="Mois",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_indicators_radar(self, drought_indicators):
        """Crée un graphique radar des indicateurs"""
        indicators = ['SPI', 'Déficit Pluie', 'Jours Secs', 'Stress Thermique', 'Humidité Sol']
        values = [
            drought_indicators.get('spi_mean', 0),
            drought_indicators.get('precipitation_deficit', 0) / 100,
            min(drought_indicators.get('consecutive_dry_days', 0) / 30, 1),
            drought_indicators.get('heat_stress', 0) / 100,
            drought_indicators.get('soil_moisture_mean', 50) / 100
        ]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=indicators,
            fill='toself',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1])
            ),
            showlegend=False,
            title="Profil des Indicateurs de Sécheresse",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_indicators_dashboard(self, drought_indicators):
        """Affiche le tableau de bord des indicateurs"""
        st.markdown("### 📋 TABLEAU DE BORD DES INDICATEURS")
        
        cols = st.columns(4)
        indicators = [
            ("SPI Moyen", f"{drought_indicators.get('spi_mean', 0):.2f}", 
             self.get_spi_interpretation(drought_indicators.get('spi_mean', 0))),
            ("Déficit Pluviométrique", f"{drought_indicators.get('precipitation_deficit', 0):.1f}%", 
             "Par rapport à la normale"),
            ("Jours Sans Pluie", f"{drought_indicators.get('consecutive_dry_days', 0)}", 
             "Consécutifs"),
            ("Humidité Sol Moy", f"{drought_indicators.get('soil_moisture_mean', 0):.1f}%", 
             "Capacité au champ"),
            ("ET0 Moyen", f"{drought_indicators.get('et0_mean', 0):.1f} mm/j", 
             "Évapotranspiration"),
            ("Stress Thermique", f"{drought_indicators.get('heat_stress', 0):.1f}%", 
             "Jours > 35°C"),
            ("Bilan Hydrique", f"{drought_indicators.get('water_balance', 0):.1f} mm", 
             "Cumulé"),
            ("Humidité Relative", f"{drought_indicators.get('humidity_mean', 0):.1f}%", 
             "Moyenne")
        ]
        
        for idx, (title, value, desc) in enumerate(indicators):
            with cols[idx % 4]:
                st.metric(title, value, help=desc)
    
    def show_advanced_map(self, locality_data, satellite_layer):
        """Affiche la carte avancée avec données satellites"""
        st.markdown("## 🗺️ CARTOGRAPHIE DES RISQUES")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Carte Folium avancée
            m = folium.Map(
                location=[locality_data['latitude'], locality_data['longitude']],
                zoom_start=10,
                tiles='CartoDB positron'
            )
            
            # Ajout des couches satellites
            satellite_data = get_satellite_data(
                locality_data['latitude'], 
                locality_data['longitude'],
                satellite_layer
            )
            
            if satellite_data:
                # Création de heatmap basée sur les données satellites
                risk_zones = process_risk_zones(satellite_data)
                
                for zone in risk_zones:
                    folium.Circle(
                        location=zone['coordinates'],
                        radius=zone['radius'],
                        popup=f"""
                        <b>{zone['name']}</b><br>
                        Niveau de risque: {zone['risk_level']}<br>
                        Indicateur: {zone['value']:.2f}
                        """,
                        color=zone['color'],
                        fill=True,
                        fillOpacity=0.6
                    ).add_to(m)
            
            # Marqueur principal
            folium.Marker(
                [locality_data['latitude'], locality_data['longitude']],
                popup=f"""
                <b>{locality_data['localite']}</b><br>
                <b>Région:</b> {locality_data['region']}<br>
                <b>Zone:</b> {locality_data['zone']}<br>
                <b>Altitude:</b> {locality_data['altitude']}m
                """,
                tooltip=locality_data['localite'],
                icon=folium.Icon(color='red', icon='info-sign', prefix='fa')
            ).add_to(m)
            
            # Affichage de la carte
            st_folium(m, width=800, height=500)
        
        with col2:
            st.markdown("### 🛰️ Légende")
            st.info(f"**Couche active:** {self.satellite_layers[satellite_layer]['name']}")
            
            st.markdown("**Niveaux de risque:**")
            risk_levels = [
                ("🟢 Très faible", "#4CAF50"),
                ("🟡 Faible", "#FFEB3B"),
                ("🟠 Modéré", "#FF9800"),
                ("🔴 Élevé", "#F44336"),
                ("⚫ Très élevé", "#000000")
            ]
            
            for level, color in risk_levels:
                st.markdown(f"<span style='color: {color}; font-weight: bold;'>{level}</span>", 
                           unsafe_allow_html=True)
    
    def show_satellite_analysis(self, locality_data, satellite_layer):
        """Affiche l'analyse des données satellitaires"""
        st.markdown("## 🛰️ ANALYSE SATELLITAIRE")
        
        with st.spinner("Traitement des images satellites..."):
            satellite_data = get_satellite_data(
                locality_data['latitude'],
                locality_data['longitude'], 
                satellite_layer
            )
            
            if satellite_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Graphique des données satellitaires
                    fig = px.imshow(
                        satellite_data['image_data'],
                        title=f"{self.satellite_layers[satellite_layer]['name']} - {locality_data['localite']}",
                        color_continuous_scale=self.satellite_layers[satellite_layer]['color']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Statistiques satellitaires
                    st.markdown("### 📊 Statistiques Satellite")
                    
                    stats = [
                        ("Valeur moyenne", f"{satellite_data['stats']['mean']:.2f}"),
                        ("Écart-type", f"{satellite_data['stats']['std']:.2f}"),
                        ("Minimum", f"{satellite_data['stats']['min']:.2f}"),
                        ("Maximum", f"{satellite_data['stats']['max']:.2f}"),
                        ("Zone couverte", f"{satellite_data['stats']['area']} km²")
                    ]
                    
                    for stat_name, stat_value in stats:
                        st.metric(stat_name, stat_value)
    
    def show_ai_recommendations(self, locality_data, climate_data=None, drought_indicators=None):
        """Affiche les recommandations IA"""
        st.markdown("## 🤖 RECOMMANDATIONS INTELLIGENTES")
        
        with st.spinner("Analyse IA en cours..."):
            recommendations = get_ai_recommendations(
                locality_data, 
                climate_data, 
                drought_indicators
            )
            
            if recommendations:
                tab1, tab2, tab3 = st.tabs(["🚨 Alertes", "💡 Actions", "📈 Prévisions"])
                
                with tab1:
                    st.markdown("### Système d'Alerte Précoce")
                    for alert in recommendations.get('alerts', []):
                        emoji = {
                            'low': '🟢',
                            'medium': '🟡',
                            'high': '🟠',
                            'critical': '🔴'
                        }.get(alert.get('level', 'medium'), '⚪')
                        
                        st.markdown(f"""
                        <div class="alert-card {alert.get('level', 'medium')}">
                            {emoji} <strong>{alert.get('title', 'Alerte')}</strong>
                            <p>{alert.get('message', '')}</p>
                            <small>Confiance: {alert.get('confidence', 0)}%</small>
                            {f"<br><small>Secteurs impactés: {', '.join(alert.get('impacted_sectors', []))}</small>" if alert.get('impacted_sectors') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                
                with tab2:
                    st.markdown("### Plan d'Action Recommandé")
                    for action in recommendations.get('actions', []):
                        priority_icon = {
                            'Basse': '🔵',
                            'Moyenne': '🟡',
                            'Haute': '🟠',
                            'Critique': '🔴'
                        }.get(action.get('priority', 'Moyenne'), '⚪')
                        
                        st.markdown(f"""
                        <div class="action-card">
                            <h4>{priority_icon} {action.get('category', 'Action')}</h4>
                            <p>{action.get('description', '')}</p>
                            <div class="priority-container">
                                <span class="priority">Priorité: {action.get('priority', 'Moyenne')}</span>
                                <span class="urgency">Urgence: {action.get('urgency', 'Non spécifiée')}</span>
                            </div>
                            {f"<p><small>Entités responsables: {', '.join(action.get('responsible_entities', []))}</small></p>" if action.get('responsible_entities') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                
                with tab3:
                    st.markdown("### Tendances et Prévisions")
                    forecast = recommendations.get('forecast', {})
                    if forecast:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📊 Situation prévue")
                            st.write(forecast.get('situation', ''))
                            st.write(f"**Tendance:** {forecast.get('trend', 'Non spécifiée')}")
                            st.write(f"**Échéance:** {forecast.get('timeframe', 'Non spécifiée')}")
                        
                        with col2:
                            st.subheader("💡 Recommandation principale")
                            st.info(forecast.get('recommendation', ''))
                        
                        if forecast.get('risks'):
                            st.subheader("⚠️ Risques identifiés")
                            for risk in forecast['risks']:
                                st.write(f"• {risk}")
                    else:
                        st.info(recommendations.get('forecast', 'Analyse en cours...'))
    
    def get_spi_interpretation(self, spi_value):
        """Retourne l'interprétation de la valeur SPI"""
        if spi_value >= 2.0:
            return "Extrêmement humide"
        elif spi_value >= 1.5:
            return "Très humide"
        elif spi_value >= 1.0:
            return "Modérément humide"
        elif spi_value >= -1.0:
            return "Proche de la normale"
        elif spi_value >= -1.5:
            return "Sécheresse modérée"
        elif spi_value >= -2.0:
            return "Sécheresse sévère"
        else:
            return "Sécheresse extrême"

    def show_forecast_analysis(self, locality_data):
        """
        Affiche l'analyse des prévisions de sécheresse
        """
        st.markdown("## 🔮 PRÉVISIONS DES RISQUES DE SÉCHERESSE")
        
        # Sélection du type de prévision
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            forecast_type = st.selectbox(
                "Période de prévision:",
                [
                    "Prévisions décadaires (10 jours)",
                    "Prévisions à 30 jours", 
                    "Prévisions saisonnières (90 jours)",
                    "Projections à 1 an",
                    "Projections à 5 ans"
                ]
            )
        
        with col2:
            confidence_threshold = st.slider("Seuil de confiance:", 0.0, 1.0, 0.7)
        
        with col3:
            if st.button("📊 Générer les prévisions", use_container_width=True):
                st.session_state.generate_forecast = True
        
        if not hasattr(st.session_state, 'generate_forecast'):
            return
        
        # Mapping des types de prévision
        forecast_mapping = {
            "Prévisions décadaires (10 jours)": "10days",
            "Prévisions à 30 jours": "30days", 
            "Prévisions saisonnières (90 jours)": "90days",
            "Projections à 1 an": "1year",
            "Projections à 5 ans": "5years"
        }
        
        selected_type = forecast_mapping[forecast_type]
        
        with st.spinner(f"🔄 Génération des prévisions {forecast_type}..."):
            analyzer = get_forecast_analyzer()
            
            # Récupération des données de prévision
            forecast_data = analyzer.get_forecast_data(
                locality_data['latitude'],
                locality_data['longitude'],
                selected_type
            )
            
            if forecast_data:
                # Calcul du risque
                risk_assessment = analyzer.calculate_drought_risk(forecast_data)
                
                # Affichage des résultats
                self.display_forecast_results(forecast_data, risk_assessment, locality_data)
                
                # Graphique des prévisions
                fig = analyzer.create_forecast_chart(forecast_data, risk_assessment)
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommandations basées sur les prévisions
                self.display_forecast_recommendations(risk_assessment, forecast_data)

    def display_forecast_results(self, forecast_data, risk_assessment, locality_data):
        """
        Affiche les résultats des prévisions
        """
        st.markdown("### 📈 Résultats des Prévisions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_color = risk_assessment['risk_color']
            st.markdown(f"""
            <div class="metric-card risk-card">
                <div class="metric-title">RISQUE PRÉVU</div>
                <div class="metric-value" style="color: {risk_color}">{risk_assessment['risk_level']}</div>
                <div class="metric-desc">Score: {risk_assessment['risk_score']:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                "Précipitations totales", 
                f"{risk_assessment['total_precipitation']:.0f} mm",
                delta=f"{risk_assessment['average_precipitation']:.1f} mm/jour"
            )
        
        with col3:
            st.metric(
                "Jours secs prévus", 
                f"{risk_assessment['dry_days']}",
                delta=f"{(risk_assessment['dry_days']/len(forecast_data['dates'])*100):.0f}%"
            )
        
        with col4:
            balance = risk_assessment['water_balance']
            balance_color = "red" if balance < 0 else "green"
            st.metric(
                "Bilan hydrique", 
                f"{balance:.0f} mm",
                delta_color="inverse"
            )

    def display_forecast_recommendations(self, risk_assessment, forecast_data):
        """
        Affiche les recommandations basées sur les prévisions
        """
        st.markdown("### 💡 Recommandations Stratégiques")
        
        risk_level = risk_assessment['risk_level']
        timeframe = risk_assessment['timeframe']
        confidence = risk_assessment['confidence']
        
        recommendations = {
            "Très Élevé": [
                "Activation immédiate du plan d'urgence sécheresse",
                "Restrictions strictes de l'usage de l'eau",
                "Préparation des systèmes d'irrigation d'urgence",
                "Stockage stratégique des ressources en eau",
                "Communication d'urgence à la population"
            ],
            "Élevé": [
                "Renforcement de la surveillance des indicateurs",
                "Mise en place de restrictions d'eau préventives",
                "Planification des cultures résistantes à la sécheresse",
                "Optimisation des systèmes d'irrigation existants"
            ],
            "Modéré": [
                "Surveillance accrue des paramètres climatiques",
                "Sensibilisation des agriculteurs aux économies d'eau",
                "Évaluation des stocks d'eau disponibles",
                "Planification des mesures préventives"
            ],
            "Faible": [
                "Maintenance de la surveillance de routine",
                "Actualisation des plans de contingence",
                "Promotion des bonnes pratiques hydriques"
            ],
            "Très Faible": [
                "Surveillance standard des indicateurs",
                "Maintien des bonnes pratiques de gestion"
            ]
        }
        
        tab1, tab2, tab3 = st.tabs(["🚨 Actions Immédiates", "📅 Planification", "📊 Surveillance"])
        
        with tab1:
            st.markdown("#### Actions à mettre en œuvre")
            for action in recommendations.get(risk_level, []):
                st.write(f"• {action}")
        
        with tab2:
            st.markdown("#### Planification stratégique")
            st.write(f"**Échéance:** {timeframe}")
            st.write(f"**Niveau de confiance:** {confidence*100:.0f}%")
            
            if risk_level in ["Très Élevé", "Élevé"]:
                st.warning("⚠️ Planification d'urgence requise")
                st.write("• Identification des zones prioritaires")
                st.write("• Mobilisation des ressources d'urgence")
                st.write("• Coordination inter-agences")
            else:
                st.info("📋 Planification préventive recommandée")
        
        with tab3:
            st.markdown("#### Surveillance recommandée")
            monitoring_freq = {
                "Très Élevé": "Quotidienne",
                "Élevé": "Quotidienne", 
                "Modéré": "Hebdomadaire",
                "Faible": "Mensuelle",
                "Très Faible": "Trimestrielle"
            }
            
            st.write(f"**Fréquence de surveillance:** {monitoring_freq.get(risk_level, 'Variable')}")
            st.write("**Indicateurs clés à surveiller:**")
            st.write("• Niveaux des nappes phréatiques")
            st.write("• État des réservoirs et barrages")
            st.write("• Humidité des sols")
            st.write("• Stress hydrique des cultures")

    def show_alert_dashboard(self):
        """
        Affiche le tableau de bord des alertes générées
        """
        st.markdown("## 🚨 TABLEAU DE BORD DES ALERTES AUTOMATIQUES")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            analysis_period = st.selectbox(
                "Période d'analyse:",
                ['15 jours', '30 jours', '60 jours', '90 jours'],
                key='alert_period'
            )
        
        with col2:
            group_by = st.selectbox(
                "Regrouper par:",
                ['région', 'zone agro-écologique', 'localité (détaillé)'],
                key='group_by'
            )
        
        with col3:
            min_risk_level = st.selectbox(
                "Risque minimum:",
                ['Tous', 'Modéré', 'Élevé', 'Très Élevé'],
                key='min_risk'
            )
        
        with col4:
            if st.button("🚀 Générer alertes groupées", use_container_width=True):
                st.session_state.generate_group_alerts = True
        
        if not hasattr(st.session_state, 'generate_group_alerts'):
            st.info("""
            **💡 Analyse groupée recommandée :**
            - **Région** : Pour une vision stratégique
            - **Zone agro-écologique** : Pour des actions adaptées  
            - **Localité** : Pour un suivi détaillé
            """)
            return
        
        # Mapping des types de regroupement
        group_mapping = {
            'région': 'region',
            'zone agro-écologique': 'zone', 
            'localité (détaillé)': 'localite'
        }
        
        selected_group = group_mapping[group_by]
        
        # Génération des alertes
        alert_generator = get_alert_generator()
        
        with st.spinner(f"🤖 DeepSeek analyse les {group_by}..."):
            alerts = alert_generator.generate_alerts_by_group(
                self.localities_df, 
                analysis_period,
                selected_group
            )
        
        if not alerts:
            st.error("❌ Aucune alerte générée")
            return
        
        # Affichage des résultats
        self.display_group_alert_statistics(alerts, group_by)
        
        # Affichage des alertes groupées
        self.display_group_alerts(alerts, group_by)
        
        # Carte des alertes
        self.display_group_alerts_map(alerts, group_by)
        
        # Export des alertes
        self.export_group_alerts(alerts, group_by)

    def display_group_alert_statistics(self, alerts, group_type):
        """
        Affiche les statistiques des alertes groupées
        """
        st.markdown("### 📊 Statistiques des Alertes Groupées")
        
        total_groups = len(alerts)
        high_risk_groups = len([a for a in alerts if a['niveau_risque_groupe'] in ['Élevé', 'Très Élevé']])
        total_localites = sum([a['total_localites'] for a in alerts])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(f"{group_type.capitalize()}s analysées", total_groups)
        
        with col2:
            st.metric(f"{group_type.capitalize()}s à haut risque", high_risk_groups)
        
        with col3:
            st.metric("Localités couvertes", total_localites)
        
        with col4:
            avg_risk = sum(a['score_risque_moyen'] for a in alerts) / total_groups if total_groups > 0 else 0
            st.metric("Risque moyen", f"{avg_risk:.1f}/100")

    def display_group_alerts(self, alerts, group_type):
        """
        Affiche les alertes groupées
        """
        st.markdown(f"### 📋 Alertes par {group_type.capitalize()}")
        
        # Tri par niveau de risque
        risk_order = {'Très Élevé': 3, 'Élevé': 2, 'Modéré': 1, 'Faible': 0}
        alerts_sorted = sorted(alerts, key=lambda x: risk_order.get(x['niveau_risque_groupe'], 0), reverse=True)
        
        for alert in alerts_sorted:
            self.display_single_group_alert(alert, group_type)

    def display_single_group_alert(self, alert, group_type):
        """
        Affiche une alerte de groupe individuelle
        """
        risk_color = {
            'Très Élevé': 'red',
            'Élevé': 'orange',
            'Modéré': 'yellow',
            'Faible': 'green'
        }.get(alert['niveau_risque_groupe'], 'gray')
        
        # Parsing du message d'alerte
        parsed_alert = parse_group_alert_message(alert['alerte'])
        
        with st.container():
            # En-tête du groupe
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="border-left: 4px solid {risk_color}; padding-left: 15px; margin: 10px 0;">
                    <h4 style="color: {risk_color}; margin-bottom: 5px;">
                        {parsed_alert.get('titre_groupe', f'Alerte {group_type}')}
                    </h4>
                    <p><strong>📍 {alert['groupe_nom']}</strong> | {alert['total_localites']} localités | 
                    Échantillon: {', '.join(alert['localites_echantillon'])}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric(
                    "Risque groupe", 
                    alert['niveau_risque_groupe'],
                    delta=f"Moyenne: {alert['score_risque_moyen']:.1f}"
                )
                st.write(f"**Urgence:** {parsed_alert.get('urgence', 'N/A')}")
            
            # Évaluation stratégique
            with st.expander("📊 Évaluation stratégique", expanded=False):
                st.write(parsed_alert.get('evaluation', ''))
                
                # Indicateurs de l'échantillon
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    avg_spi = sum(ind['spi'] for ind in alert['indicateurs_echantillon']) / len(alert['indicateurs_echantillon'])
                    st.metric("SPI moyen", f"{avg_spi:.2f}")
                with col_b:
                    avg_deficit = sum(ind['deficit'] for ind in alert['indicateurs_echantillon']) / len(alert['indicateurs_echantillon'])
                    st.metric("Déficit moyen", f"{avg_deficit:.1f}%")
                with col_c:
                    st.metric("Ratio haut risque", f"{alert['ratio_risque_eleve']*100:.1f}%")
            
            # Zones prioritaires
            st.markdown("#### 🎯 Zones Prioritaires")
            zones = parsed_alert.get('zones_prioritaires', [])
            for zone in zones:
                st.write(f"• {zone}")
            
            # Actions coordonnées
            st.markdown("#### 🤝 Actions Coordonnées")
            actions = parsed_alert.get('actions_coordonnees', [])
            for action in actions:
                st.write(f"• {action}")
            
            # Recommandations prioritaires
            st.markdown("#### 📋 Plan d'Action Prioritaire")
            reco = alert.get('recommandations_prioritaires', {})
            for category, recommendation in reco.items():
                st.write(f"**{category.title()}:** {recommendation}")
            
            st.markdown("---")

    def display_alerts_map(self, alerts):
        """
        Affiche les alertes sur une carte
        """
        st.markdown("### 🗺️ Carte des Alertes")
        
        # Création de la carte
        m = folium.Map(
            location=[self.localities_df['latitude'].mean(), self.localities_df['longitude'].mean()],
            zoom_start=6,
            tiles='CartoDB positron'
        )
        
        # Ajout des marqueurs d'alerte
        for alert in alerts:
            risk_color = {
                'Très Élevé': 'red',
                'Élevé': 'darkred',
                'Modéré': 'orange',
                'Faible': 'green'
            }.get(alert['niveau_risque'], 'gray')
            
            # Parsing du message pour le popup
            parsed_alert = parse_group_alert_message(alert['alerte'])
            
            folium.Marker(
                [alert['latitude'], alert['longitude']],
                popup=f"""
                <b>{alert['localite']}</b><br>
                <b>Risque:</b> {alert['niveau_risque']}<br>
                <b>SPI:</b> {alert['spi']:.2f}<br>
                <b>Déficit:</b> {alert['deficit_pluviometrique']:.1f}%<br>
                <b>Actions:</b> {', '.join(parsed_alert.get('actions', ['N/A'])[:2])}...
                """,
                tooltip=f"{alert['localite']} - {alert['niveau_risque']}",
                icon=folium.Icon(color=risk_color, icon='exclamation-triangle', prefix='fa')
            ).add_to(m)
        
        # Affichage de la carte
        st_folium(m, width=800, height=500)

    def export_alerts(self, alerts):
        """
        Permet l'export des alertes
        """
        st.markdown("### 💾 Export des Alertes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Exporter en CSV", use_container_width=True):
                df = pd.DataFrame(alerts)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"alertes_secheresse_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Exporter en JSON", use_container_width=True):
                json_data = json.dumps(alerts, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Télécharger JSON",
                    data=json_data,
                    file_name=f"alertes_secheresse_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
def main():
    # Initialisation de la plateforme
    platform = ModernDroughtPlatform()
    
    # Chargement des données
    if platform.load_data():
        platform.create_dashboard()
    else:
        st.error("Impossible de charger les données de localités.")

if __name__ == "__main__":
    main()