import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from config import Config
from utils.data_loader import DataLoader
from utils.weather_processor import WeatherProcessor
from utils.flood_calculator import FloodCalculator
from utils.map_generator import MapGenerator

def main():
    # Configuration de la page
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT
    )
    
    # Chargement des styles CSS
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Titre principal
    st.markdown('<h1 class="main-title">🌊 Plateforme Avancée de Suivi des Risques d\'Inondation</h1>', 
                unsafe_allow_html=True)
    st.markdown('<h3 class="subtitle">Système Intégré d\'Alerte Précoce et d\'Analyse des Risques</h3>',
                unsafe_allow_html=True)
    
    # Initialisation des modules
    data_loader = DataLoader()
    weather_processor = WeatherProcessor()
    flood_calculator = FloodCalculator()
    map_generator = MapGenerator()
    
    # Sidebar étendue
    with st.sidebar:
        st.header("🎯 Configuration Avancée")
        
        # Sélection du fichier
        data_file = st.selectbox(
            "Fichier de données localités",
            options=Config.AVAILABLE_DATA_FILES
        )
        
        # Paramètres d'analyse avancés
        st.subheader("📊 Paramètres d'Analyse")
        forecast_days = st.slider("Jours de prévision", 1, 7, 3)
        analysis_depth = st.selectbox(
            "Profondeur d'analyse",
            ['Standard', 'Avancée', 'Expert'],
            help="Niveau de détail dans le calcul des risques"
        )
        
        # Sélection des modèles
        st.subheader("🔬 Modèles d'Analyse")
        selected_models = st.multiselect(
            "Modèles à appliquer",
            options=Config.PREDICTION_MODELS['Indices'] + Config.PREDICTION_MODELS['Modèles'],
            default=['FFG (Flash Flood Guidance)', 'IFS (Indice de Fuite Superficielle)']
        )
        
        # Technologies de surveillance
        st.subheader("📡 Sources de Données")
        data_sources = st.multiselect(
            "Technologies utilisées",
            options=[tech for tech_list in Config.MONITORING_TECHNOLOGIES.values() for tech in tech_list],
            default=['Pluviomètres automatiques', 'Satellites (GPM, Sentinel-1,2, Landsat, Modis)']
        )
    
    # Chargement des données
    try:
        localities_df = data_loader.load_localities(data_file)
        
        if localities_df is not None:
            # Section d'analyse principale
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("🚀 Lancer l'Analyse Complète", type="primary", use_container_width=True):
                    with st.spinner("🔍 Analyse avancée des risques en cours..."):
                        results_df = analyze_comprehensive_risks(
                            localities_df, weather_processor, flood_calculator, forecast_days
                        )
                        display_advanced_results(results_df, map_generator, data_loader)
            
            with col2:
                if st.button("📊 Aperçu Rapide", use_container_width=True):
                    with st.spinner("Calcul rapide..."):
                        results_df = analyze_comprehensive_risks(
                            localities_df, weather_processor, flood_calculator, 1
                        )
                        display_quick_overview(results_df)
            
            # Affichage des données brutes
            with st.expander("📋 Données des Localités (Brutes)"):
                st.dataframe(localities_df, use_container_width=True)
                
        else:
            show_advanced_instructions(data_loader)
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {e}")
        show_advanced_instructions(data_loader)

def analyze_comprehensive_risks(localities_df, weather_processor, flood_calculator, forecast_days):
    """Exécute l'analyse complète des risques avec progression"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    total = len(localities_df)
    
    for i, (_, locality) in enumerate(localities_df.iterrows()):
        status_text.text(f"🔍 Analyse de {locality['localite']}...")
        
        # Données météo
        weather_data = weather_processor.get_weather_data(
            locality['latitude'], locality['longitude'], forecast_days
        )
        
        # Calcul du risque avancé
        alert_level, risk_score, details = flood_calculator.calculate_risk(weather_data, locality)
        
        results.append({
            **locality,
            'risk_level': alert_level,
            'risk_score': risk_score,
            **details
        })
        
        progress_bar.progress((i + 1) / total)
    
    status_text.text("✅ Analyse terminée!")
    return pd.DataFrame(results)

def display_advanced_results(results_df, map_generator, data_loader):
    """Affiche les résultats avancés de l'analyse"""
    
    # Tableau de bord complet
    st.header("📊 Tableau de Bord Complet")
    
    # Métriques principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total = len(results_df)
        st.metric("Localités Analysées", total)
    
    with col2:
        high_risk = len(results_df[results_df['risk_level'] == 'Alerte Maximale'])
        st.metric("🔴 Alerte Maximale", high_risk, f"{(high_risk/total)*100:.1f}%")
    
    with col3:
        medium_risk = len(results_df[results_df['risk_level'] == 'Alerte'])
        st.metric("🟠 Alerte", medium_risk, f"{(medium_risk/total)*100:.1f}%")
    
    with col4:
        low_risk = len(results_df[results_df['risk_level'] == 'Pré-alerte'])
        st.metric("🟡 Pré-alerte", low_risk, f"{(low_risk/total)*100:.1f}%")
    
    with col5:
        vigilance = len(results_df[results_df['risk_level'] == 'Vigilance'])
        st.metric("🟢 Vigilance", vigilance, f"{(vigilance/total)*100:.1f}%")
    
    # Carte interactive avancée
    st.header("🗺️ Carte Interactive des Risques")
    risk_map = map_generator.create_advanced_risk_map(results_df)
    st_folium(risk_map, width=1200, height=600)
    
    # Analyse détaillée par région
    st.header("📈 Analyse par Région")
    display_regional_analysis(results_df)
    
    # Tableau détaillé avec filtres avancés
    st.header("🔍 Détail des Analyses")
    display_detailed_analysis(results_df)
    
    # Recommandations spécifiques
    st.header("💡 Recommandations par Zone")
    display_city_recommendations(results_df)
    
    # Export des résultats
    st.sidebar.header("💾 Export Avancé")
    if st.sidebar.button("📥 Exporter Rapport Complet"):
        export_data = data_loader.export_comprehensive_report(results_df)
        st.sidebar.download_button(
            label="Télécharger Rapport",
            data=export_data,
            file_name="rapport_inondation_complet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def display_regional_analysis(results_df):
    """Affiche l'analyse par région"""
    regional_stats = results_df.groupby('region').agg({
        'risk_score': 'mean',
        'localite': 'count',
        'risk_level': lambda x: (x == 'Alerte Maximale').sum()
    }).round(3)
    
    regional_stats.columns = ['Score Moyen', 'Nb Localités', 'Alertes Maximales']
    regional_stats = regional_stats.sort_values('Score Moyen', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Statistiques par Région")
        st.dataframe(regional_stats, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Top Zones à Risque")
        high_risk_zones = results_df.nlargest(5, 'risk_score')[['localite', 'region', 'risk_score', 'risk_level']]
        for _, zone in high_risk_zones.iterrows():
            st.write(f"**{zone['localite']}** ({zone['region']})")
            st.write(f"Score: {zone['risk_score']:.2f} | Niveau: {zone['risk_level']}")
            st.progress(zone['risk_score'])

def display_detailed_analysis(results_df):
    """Affiche l'analyse détaillée avec filtres"""
    
    # Filtres avancés
    col1, col2, col3 = st.columns(3)
    
    with col1:
        regions = ["Toutes"] + sorted(results_df['region'].unique().tolist())
        selected_region = st.selectbox("Région", regions)
    
    with col2:
        risk_levels = ["Tous"] + sorted(results_df['risk_level'].unique().tolist())
        selected_risk = st.selectbox("Niveau d'alerte", risk_levels)
    
    with col3:
        flood_types = ["Tous"] + sorted(results_df['type_inondation'].unique().tolist())
        selected_type = st.selectbox("Type d'inondation", flood_types)
    
    # Application des filtres
    filtered_df = results_df.copy()
    if selected_region != "Toutes":
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    if selected_risk != "Tous":
        filtered_df = filtered_df[filtered_df['risk_level'] == selected_risk]
    if selected_type != "Tous":
        filtered_df = filtered_df[filtered_df['type_inondation'] == selected_type]
    
    # Affichage du tableau
    display_columns = [
        'localite', 'region', 'type_inondation', 'risk_level', 
        'risk_score', 'ffg_score', 'ifs_score', 'soil_saturation'
    ]
    
    st.dataframe(
        filtered_df[display_columns].sort_values('risk_score', ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Détails pour une localité sélectionnée
    if not filtered_df.empty:
        selected_locality = st.selectbox(
            "📋 Voir les détails pour:",
            filtered_df['localite'].unique()
        )
        
        if selected_locality:
            locality_data = filtered_df[filtered_df['localite'] == selected_locality].iloc[0]
            display_locality_details(locality_data)

def display_locality_details(locality_data):
    """Affiche les détails pour une localité spécifique"""
    st.subheader(f"🔍 Analyse Détaillée: {locality_data['localite']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Niveau d'Alerte", locality_data['risk_level'])
        st.metric("Score de Risque", f"{locality_data['risk_score']:.2f}")
        st.metric("Type d'Inondation", locality_data['type_inondation'])
    
    with col2:
        st.metric("Indice FFG", f"{locality_data.get('ffg_score', 0):.2f}")
        st.metric("Indice IFS", f"{locality_data.get('ifs_score', 0):.2f}")
        st.metric("Saturation Sols", f"{locality_data.get('soil_saturation', 0):.2f}")
    
    # Alertes et actions
    alert_details = locality_data.get('alert_details', {})
    if alert_details:
        st.info(f"**Délai d'alerte:** {alert_details.get('delay', 'N/A')}")
        st.warning(f"**Actions recommandées:** {alert_details.get('actions', 'N/A')}")

def display_city_recommendations(results_df):
    """Affiche les recommandations spécifiques par ville pilote"""
    city_recommendations = Config.CITY_RECOMMENDATIONS
    
    for city, recommendations in city_recommendations.items():
        # Vérifier si la ville est dans les résultats
        city_data = results_df[results_df['localite'].str.contains(city, case=False, na=False)]
        
        if not city_data.empty:
            st.subheader(f"🏙️ Recommandations pour {city}")
            
            for recommendation in recommendations:
                st.write(f"• {recommendation}")
            
            # Statistiques spécifiques
            city_risk = city_data['risk_score'].mean()
            st.metric(f"Risque Moyen à {city}", f"{city_risk:.2f}")

def display_quick_overview(results_df):
    """Affiche un aperçu rapide des résultats"""
    st.header("⚡ Aperçu Rapide")
    
    # Métriques clés
    col1, col2, col3 = st.columns(3)
    
    with col1:
        high_risk = len(results_df[results_df['risk_level'] == 'Alerte Maximale'])
        st.metric("🔴 Alertes Maximales", high_risk)
    
    with col2:
        total = len(results_df)
        avg_risk = results_df['risk_score'].mean()
        st.metric("📊 Risque Moyen", f"{avg_risk:.2f}")
    
    with col3:
        top_risk = results_df.loc[results_df['risk_score'].idxmax()]
        st.metric("🎯 Zone la plus à risque", top_risk['localite'])
    
    # Carte simplifiée
    st.header("🗺️ Carte des Risques")
    risk_map = MapGenerator().create_risk_map(results_df)
    st_folium(risk_map, width=1200, height=400)

def show_advanced_instructions(data_loader):
    """Affiche les instructions avancées"""
    st.info("""
    ## 🎯 Plateforme Avancée de Suivi des Inondations
    
    Cette plateforme intègre les fonctionnalités avancées du document d'analyse:
    
    ### 📋 Fonctionnalités Implémentées:
    
    **🎯 Mécanismes d'Inondation:**
    - Analyse des 3 typologies: Fluviales, Pluviales, Côtières
    - Facteurs déclencheurs spécifiques à chaque type
    
    **📊 Indices Avancés:**
    - FFG (Flash Flood Guidance)
    - IFS (Indice de Fuite Superficielle) 
    - Indice de Saturation des Sols
    
    **🚨 Système d'Alerte:**
    - 4 niveaux: Vigilance, Pré-alerte, Alerte, Alerte Maximale
    - Délais et actions spécifiques
    - Couleurs standards internationales
    
    **🛰️ Technologies:**
    - Intégration données satellites (Sentinel, Landsat, Modis)
    - Capteurs terrain virtuels
    - Modèles prédictifs (HEC-RAS, SWAT, etc.)
    """)
    
    # Téléchargement du template avancé
    if st.button("📥 Télécharger Template Avancé"):
        template_data = data_loader.create_template()
        st.download_button(
            label="Télécharger le template complet",
            data=template_data,
            file_name="template_localites_avance.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()