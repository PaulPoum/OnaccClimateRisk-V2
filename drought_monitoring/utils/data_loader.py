# drought_monitoring/utils/data_loader.py
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import numpy as np
import streamlit as st
import os

def load_localities():
    """
    Charge les données des localités depuis le fichier Excel avec gestion d'erreur améliorée
    """
    try:
        # Chemins possibles pour le fichier Excel
        possible_paths = [
            "database/localites.xlsx",
            "drought_monitoring/database/localites.xlsx",
            os.path.join(os.path.dirname(__file__), '..', 'database', 'localites.xlsx'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'drought_monitoring', 'database', 'localites.xlsx')
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                st.success(f"✅ Fichier trouvé: {path}")
                break
        
        if file_path:
            df = pd.read_excel(file_path)
            
            # Validation des colonnes requises
            required_columns = ['localite', 'latitude', 'longitude', 'altitude', 'region', 'zone', 'country']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.warning(f"⚠️ Colonnes manquantes: {missing_columns}. Utilisation des colonnes disponibles.")
                # Utiliser les colonnes disponibles
                available_columns = [col for col in required_columns if col in df.columns]
                df = df[available_columns]
            
            st.success(f"📊 {len(df)} localités chargées avec succès")
            return df
        else:
            st.warning("📝 Fichier localites.xlsx non trouvé. Utilisation des données de démonstration.")
            return create_sample_data()
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier Excel: {e}")
        st.info("🔄 Utilisation des données de démonstration...")
        return create_sample_data()

def create_sample_data():
    """
    Crée des données d'exemple pour le Cameroun
    """
    sample_data = {
        'localite': ['Maroua', 'Ngaoundéré', 'Garoua', 'Bafoussam', 'Douala', 'Yaoundé', 'Buea', 'Ebolowa'],
        'latitude': [10.5957, 7.3167, 9.3014, 5.4667, 4.0511, 3.8667, 4.1667, 2.9167],
        'longitude': [14.3247, 13.5833, 13.3925, 10.4167, 9.7679, 11.5167, 9.2333, 11.1500],
        'altitude': [420, 1100, 230, 1520, 13, 726, 870, 580],
        'region': ['Extrême-Nord', 'Adamaoua', 'Nord', 'Ouest', 'Littoral', 'Centre', 'Sud-Ouest', 'Sud'],
        'zone': ['Soudano-Sahélienne', 'Soudano-Sahélienne', 'Soudano-Sahélienne', 
                'Hautes Terres', 'Côtière', 'Hautes Terres', 'Côtière', 'Hautes Terres'],
        'country': ['Cameroun'] * 8
    }
    
    df = pd.DataFrame(sample_data)
    
    # Ajouter un bouton pour créer le template
    with st.expander("🔧 Configuration des données", expanded=False):
        st.markdown("""
        ### 📁 Structure des données requise
        
        Créez un fichier `localites.xlsx` avec les colonnes suivantes:
        
        | Colonne | Type | Description |
        |---------|------|-------------|
        | localite | Texte | Nom de la localité |
        | latitude | Nombre | Coordonnée latitude |
        | longitude | Nombre | Coordonnée longitude |
        | altitude | Nombre | Altitude en mètres |
        | region | Texte | Région administrative |
        | zone | Texte | Zone agro-écologique |
        | country | Texte | Pays |
        
        **Emplacement recommandé:** `drought_monitoring/database/localites.xlsx`
        """)
        
        # Bouton pour créer le template
        if st.button("📥 Télécharger Template Excel"):
            template_df = pd.DataFrame({
                'localite': ['Maroua', 'Douala', 'Yaoundé'],
                'latitude': [10.5957, 4.0511, 3.8667],
                'longitude': [14.3247, 9.7679, 11.5167],
                'altitude': [420, 13, 726],
                'region': ['Extrême-Nord', 'Littoral', 'Centre'],
                'zone': ['Soudano-Sahélienne', 'Côtière', 'Hautes Terres'],
                'country': ['Cameroun', 'Cameroun', 'Cameroun']
            })
            
            # Créer le fichier Excel en mémoire
            output = pd.ExcelWriter('template_localites.xlsx', engine='xlsxwriter')
            template_df.to_excel(output, index=False, sheet_name='Localites')
            
            # Téléchargement
            with open('template_localites.xlsx', 'rb') as f:
                excel_data = f.read()
            
            st.download_button(
                label="📥 Télécharger le Template",
                data=excel_data,
                file_name="template_localites.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    return df

# Le reste de votre code reste inchangé...
def get_climate_data(latitude, longitude, period='30 jours'):
    """
    Récupère les données climatiques depuis OpenMeteo API
    Version corrigée avec les paramètres valides
    """
    try:
        # Configuration du cache et des retries
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # Détermination de la période
        end_date = datetime.now()
        if period == '7 jours':
            past_days = 7
            forecast_days = 0
        elif period == '15 jours':
            past_days = 15
            forecast_days = 0
        elif period == '90 jours':
            past_days = 90
            forecast_days = 0
        elif period == '1 an':
            past_days = 365
            forecast_days = 0
        else:  # 30 jours par défaut
            past_days = 30
            forecast_days = 0
        
        # URL de l'API OpenMeteo avec paramètres valides
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Paramètres valides pour l'API OpenMeteo
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max", 
                "temperature_2m_min", 
                "precipitation_sum", 
                "et0_fao_evapotranspiration"
            ],
            "timezone": "auto",
            "past_days": past_days,
            "forecast_days": forecast_days
        }
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Traitement des données quotidiennes
        daily = response.Daily()
        
        # Génération des dates
        daily_dates = pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq='D',
            inclusive='left'
        )
        
        # Extraction des variables quotidiennes
        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(2).ValuesAsNumpy()
        daily_et0 = daily.Variables(3).ValuesAsNumpy()
        
        # Simulation de l'humidité du sol basée sur les précipitations et l'ET0
        soil_moisture = simulate_soil_moisture(daily_precipitation_sum, daily_et0)
        
        # Simulation de l'humidité relative basée sur la localisation et la saison
        relative_humidity = simulate_relative_humidity(latitude, longitude, len(daily_dates))
        
        # Préparation des données de retour
        climate_data = {
            'dates': daily_dates,
            'temperature_2m_max': daily_temperature_2m_max,
            'temperature_2m_min': daily_temperature_2m_min,
            'temperature_2m_mean': (daily_temperature_2m_max + daily_temperature_2m_min) / 2,
            'precipitation': daily_precipitation_sum,
            'soil_moisture': soil_moisture,
            'et0': daily_et0,
            'relative_humidity': relative_humidity
        }
        
        st.success(f"✅ Données climatiques récupérées pour {len(daily_dates)} jours")
        return climate_data
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données climatiques: {e}")
        st.info("🔄 Utilisation de données simulées pour la démonstration...")
        # Retourne des données simulées en cas d'erreur
        return get_simulated_climate_data(latitude, longitude, period)

def simulate_soil_moisture(precipitation, et0, initial_moisture=50.0):
    """
    Simule l'humidité du sol basée sur les précipitations et l'évapotranspiration
    """
    soil_moisture = [initial_moisture]
    
    for i in range(1, len(precipitation)):
        # Facteurs influençant l'humidité du sol
        precip_effect = precipitation[i] * 2.0  # Les précipitations augmentent l'humidité
        et_effect = et0[i] * 0.8  # L'évapotranspiration diminue l'humidité
        drainage = max(0, soil_moisture[-1] - 60) * 0.1  # Drainage naturel
        
        new_moisture = soil_moisture[-1] + precip_effect - et_effect - drainage
        new_moisture = max(5, min(95, new_moisture))  # Borne entre 5 et 95%
        
        soil_moisture.append(new_moisture)
    
    return np.array(soil_moisture)

def simulate_relative_humidity(latitude, longitude, n_days):
    """
    Simule l'humidité relative basée sur la localisation géographique
    """
    # Variation basée sur la latitude (plus humide près de l'équateur)
    base_humidity = 70 - abs(latitude - 4) * 2  # Maximum autour de 4°N (Cameroun)
    base_humidity = max(40, min(90, base_humidity))
    
    # Variation saisonnière simulée
    humidity_variation = np.random.normal(0, 10, n_days)
    relative_humidity = base_humidity + humidity_variation
    
    # Assurer des valeurs réalistes
    relative_humidity = np.clip(relative_humidity, 30, 95)
    
    return relative_humidity

def get_simulated_climate_data(latitude, longitude, period='30 jours'):
    """
    Génère des données climatiques simulées en cas d'échec de l'API
    """
    # Détermination du nombre de jours
    if period == '7 jours':
        n_days = 7
    elif period == '15 jours':
        n_days = 15
    elif period == '90 jours':
        n_days = 90
    elif period == '1 an':
        n_days = 365
    else:
        n_days = 30
    
    # Génération de dates
    end_date = datetime.now()
    dates = [end_date - timedelta(days=x) for x in range(n_days, 0, -1)]
    
    # Simulation basée sur la latitude (climat tropical)
    base_temp = 25 + (latitude - 5) * 0.5  # Variation avec la latitude
    
    # Simulation des données météorologiques avec variation réaliste
    np.random.seed(int(latitude * 100 + longitude))  # Seed reproductible par localisation
    
    # Températures avec tendance réaliste
    temperature_2m_max = base_temp + np.random.normal(5, 2, n_days)
    temperature_2m_min = base_temp + np.random.normal(-5, 2, n_days)
    
    # Ajustement pour les zones côtières (moins de variation)
    if longitude > 9 and latitude < 5:  # Zone côtière
        temperature_2m_max = base_temp + np.random.normal(3, 1, n_days)
        temperature_2m_min = base_temp + np.random.normal(-3, 1, n_days)
    
    # Simulation des précipitations (saison des pluies/sèche)
    if latitude > 8:  # Zone nord plus sèche
        precipitation = np.random.exponential(2, n_days)
        # Périodes de sécheresse plus longues
        dry_spells = np.random.choice([0, 1], size=n_days, p=[0.3, 0.7])
        precipitation = precipitation * dry_spells
    else:
        precipitation = np.random.exponential(5, n_days)
        # Plus de jours de pluie
        rain_days = np.random.choice([0, 1], size=n_days, p=[0.2, 0.8])
        precipitation = precipitation * rain_days
    
    # Simulation de l'évapotranspiration
    et0 = np.random.normal(4, 1, n_days)
    
    # Simulation de l'humidité du sol
    soil_moisture = simulate_soil_moisture(precipitation, et0)
    
    # Simulation de l'humidité relative
    relative_humidity = simulate_relative_humidity(latitude, longitude, n_days)
    
    # Ajustement final des données pour cohérence
    temperature_2m_max = np.clip(temperature_2m_max, 20, 45)
    temperature_2m_min = np.clip(temperature_2m_min, 15, 30)
    precipitation = np.clip(precipitation, 0, 50)
    
    st.info(f"📊 Données simulées générées pour {n_days} jours (localisation: {latitude:.2f}°N, {longitude:.2f}°E)")
    
    return {
        'dates': dates,
        'temperature_2m_max': temperature_2m_max,
        'temperature_2m_min': temperature_2m_min,
        'temperature_2m_mean': (temperature_2m_max + temperature_2m_min) / 2,
        'precipitation': precipitation,
        'soil_moisture': soil_moisture,
        'et0': et0,
        'relative_humidity': relative_humidity
    }

def get_historical_data(latitude, longitude, years=5):
    """
    Récupère les données historiques (fonction manquante)
    """
    try:
        # Simulation de données historiques
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        
        # Simulation de données historiques réalistes
        np.random.seed(int(latitude * 100 + longitude))
        
        # Tendances avec variabilité saisonnière
        base_temp = 25 + (latitude - 5) * 0.5
        temperature = base_temp + np.random.normal(0, 3, len(dates))
        
        # Précipitations avec saisonnalité
        if latitude > 8:  # Nord plus sec
            precipitation = np.random.exponential(30, len(dates))
        else:
            precipitation = np.random.exponential(80, len(dates))
        
        # SPI historique
        spi = np.random.normal(0, 1, len(dates))
        
        historical_data = {
            'dates': dates,
            'temperature': temperature,
            'precipitation': precipitation,
            'spi': spi,
            'soil_moisture': np.random.uniform(30, 70, len(dates))
        }
        
        return historical_data
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données historiques: {e}")
        return None

def validate_climate_data(climate_data):
    """
    Valide l'intégrité des données climatiques
    """
    if climate_data is None:
        return False
    
    required_keys = ['dates', 'temperature_2m_max', 'temperature_2m_min', 'precipitation', 'soil_moisture', 'et0']
    
    for key in required_keys:
        if key not in climate_data:
            st.warning(f"Clé manquante dans les données climatiques: {key}")
            return False
        
        if len(climate_data[key]) == 0:
            st.warning(f"Données vides pour: {key}")
            return False
    
    # Vérification de la cohérence des longueurs
    data_lengths = [len(climate_data[key]) for key in required_keys]
    if len(set(data_lengths)) != 1:
        st.warning("Longueurs incohérentes dans les données climatiques")
        return False
    
    return True

def get_available_periods():
    """
    Retourne les périodes d'analyse disponibles
    """
    return ['7 jours', '15 jours', '30 jours', '90 jours', '1 an']

def get_zone_climate_characteristics(zone):
    """
    Retourne les caractéristiques climatiques typiques par zone
    """
    characteristics = {
        'Soudano-Sahélienne': {
            'precip_avg': 600,
            'temp_avg': 28,
            'dry_season': 'Octobre-Mai',
            'risk_level': 'Élevé'
        },
        'Hautes Terres': {
            'precip_avg': 1500,
            'temp_avg': 22,
            'dry_season': 'Novembre-Mars',
            'risk_level': 'Modéré'
        },
        'Côtière': {
            'precip_avg': 3000,
            'temp_avg': 26,
            'dry_season': 'Décembre-Février',
            'risk_level': 'Faible'
        }
    }
    return characteristics.get(zone, {})