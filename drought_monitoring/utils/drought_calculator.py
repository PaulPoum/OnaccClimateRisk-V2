import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

def calculate_drought_indicators(climate_data):
    """
    Calcule les indicateurs de sécheresse à partir des données climatiques
    Version robuste avec gestion des erreurs
    """
    indicators = {}
    
    try:
        # Vérification que les données sont disponibles
        if climate_data is None or len(climate_data['dates']) == 0:
            return get_default_indicators()
        
        precipitation = climate_data['precipitation']
        dates = climate_data['dates']
        
        # Calcul du SPI (Standardized Precipitation Index)
        indicators['spi'] = calculate_spi(precipitation, dates)
        indicators['spi_mean'] = np.mean(list(indicators['spi'].values())) if indicators['spi'] else 0
        
        # Déficit pluviométrique
        avg_precipitation = np.mean(precipitation) if len(precipitation) > 0 else 0
        normal_precipitation = calculate_normal_precipitation(len(precipitation))
        indicators['precipitation_deficit'] = max(0, (1 - (avg_precipitation / normal_precipitation)) * 100) if normal_precipitation > 0 else 0
        
        # Jours consécutifs sans pluie
        indicators['consecutive_dry_days'] = calculate_consecutive_dry_days(precipitation)
        
        # Indicateurs de température
        indicators['avg_temperature'] = np.mean(climate_data['temperature_2m_mean']) if len(climate_data['temperature_2m_mean']) > 0 else 25
        indicators['max_temperature'] = np.max(climate_data['temperature_2m_max']) if len(climate_data['temperature_2m_max']) > 0 else 30
        indicators['heat_stress'] = calculate_heat_stress(climate_data['temperature_2m_max'])
        
        # Humidité du sol
        indicators['soil_moisture_mean'] = np.mean(climate_data['soil_moisture']) if len(climate_data['soil_moisture']) > 0 else 50
        indicators['soil_moisture_min'] = np.min(climate_data['soil_moisture']) if len(climate_data['soil_moisture']) > 0 else 30
        
        # Évapotranspiration
        indicators['et0_mean'] = np.mean(climate_data['et0']) if len(climate_data['et0']) > 0 else 4
        indicators['water_balance'] = np.sum(precipitation) - np.sum(climate_data['et0']) if len(precipitation) > 0 else 0
        
        # Humidité relative
        indicators['humidity_mean'] = np.mean(climate_data['relative_humidity']) if len(climate_data['relative_humidity']) > 0 else 65
        
    except Exception as e:
        st.warning(f"Certains indicateurs n'ont pas pu être calculés: {e}")
        # Retourne des indicateurs par défaut en cas d'erreur
        indicators = get_default_indicators()
    
    return indicators

def get_default_indicators():
    """Retourne des indicateurs par défaut en cas d'erreur"""
    return {
        'spi': {0: 0},
        'spi_mean': 0,
        'precipitation_deficit': 0,
        'consecutive_dry_days': 0,
        'avg_temperature': 25,
        'max_temperature': 30,
        'heat_stress': 0,
        'soil_moisture_mean': 50,
        'soil_moisture_min': 30,
        'et0_mean': 4,
        'water_balance': 0,
        'humidity_mean': 65
    }

def calculate_spi(precipitation, dates, period=30):
    """
    Calcule le Standardized Precipitation Index
    Version simplifiée et robuste
    """
    spi_values = {}
    
    try:
        if len(precipitation) < 7:  # Minimum de données requises
            # Calcul SPI simple pour petites périodes
            mean_precip = np.mean(precipitation)
            std_precip = np.std(precipitation) if len(precipitation) > 1 else 1
            
            for i, precip in enumerate(precipitation):
                spi = (precip - mean_precip) / std_precip if std_precip > 0 else 0
                spi_values[i] = spi
                
        else:
            # Version plus sophistiquée pour les périodes plus longues
            for i in range(len(precipitation)):
                if i < period - 1:
                    # Pour le début, on utilise les données disponibles
                    window = precipitation[:i+1]
                else:
                    window = precipitation[i-period+1:i+1]
                
                if len(window) >= 7:  # Minimum de 7 jours pour un calcul fiable
                    total_precip = np.sum(window)
                    
                    # Simulation d'une distribution gamma
                    try:
                        shape, loc, scale = stats.gamma.fit([max(0.1, x) for x in window])
                        cdf = stats.gamma.cdf(total_precip, shape, loc, scale)
                        spi = stats.norm.ppf(cdf)
                        spi_values[i] = spi if not np.isinf(spi) and not np.isnan(spi) else 0
                    except:
                        # Fallback en cas d'erreur de calcul
                        mean_window = np.mean(window)
                        std_window = np.std(window) if len(window) > 1 else 1
                        spi_values[i] = (total_precip - mean_window) / std_window if std_window > 0 else 0
                
    except Exception as e:
        st.warning(f"Erreur dans le calcul du SPI: {e}")
        # Valeur par défaut
        for i in range(len(precipitation)):
            spi_values[i] = 0
    
    return spi_values

def calculate_normal_precipitation(days):
    """
    Calcule les précipitations normales pour la période
    Valeurs de référence pour le Cameroun (en mm/jour)
    """
    # Valeurs moyennes par jour selon les zones (simplifié)
    return 3.0 * days  # 3mm/jour en moyenne

def calculate_consecutive_dry_days(precipitation, threshold=0.1):
    """
    Calcule le nombre maximum de jours consécutifs sans pluie
    """
    if len(precipitation) == 0:
        return 0
        
    max_dry_days = 0
    current_dry_days = 0
    
    for precip in precipitation:
        if precip < threshold:  # Jour sec
            current_dry_days += 1
            max_dry_days = max(max_dry_days, current_dry_days)
        else:
            current_dry_days = 0
    
    return max_dry_days

def calculate_heat_stress(temperatures, threshold=35):
    """
    Calcule un indice de stress thermique
    """
    if len(temperatures) == 0:
        return 0
        
    hot_days = sum(1 for temp in temperatures if temp > threshold)
    return hot_days / len(temperatures) * 100

def assess_drought_risk(indicators):
    """
    Évalue le risque global de sécheresse basé sur les indicateurs
    Version robuste
    """
    try:
        risk_score = 0
        factors = []
        
        # Évaluation basée sur le SPI
        spi_mean = indicators.get('spi_mean', 0)
        if spi_mean <= -2.0:
            risk_score += 40
            factors.append("SPI très bas (sécheresse extrême)")
        elif spi_mean <= -1.5:
            risk_score += 30
            factors.append("SPI bas (sécheresse sévère)")
        elif spi_mean <= -1.0:
            risk_score += 20
            factors.append("SPI modérément bas")
        elif spi_mean <= -0.5:
            risk_score += 10
            factors.append("SPI légèrement bas")
        
        # Déficit pluviométrique
        deficit = indicators.get('precipitation_deficit', 0)
        if deficit > 60:
            risk_score += 30
            factors.append("Déficit pluviométrique extrême")
        elif deficit > 40:
            risk_score += 20
            factors.append("Déficit pluviométrique sévère")
        elif deficit > 20:
            risk_score += 10
            factors.append("Déficit pluviométrique modéré")
        
        # Jours secs consécutifs
        dry_days = indicators.get('consecutive_dry_days', 0)
        if dry_days > 20:
            risk_score += 20
            factors.append("Longue période sans pluie")
        elif dry_days > 10:
            risk_score += 10
            factors.append("Période sèche prolongée")
        
        # Stress thermique
        heat_stress = indicators.get('heat_stress', 0)
        if heat_stress > 50:
            risk_score += 10
            factors.append("Fort stress thermique")
        
        # Humidité du sol
        soil_moisture = indicators.get('soil_moisture_mean', 50)
        if soil_moisture < 20:
            risk_score += 15
            factors.append("Humidité du sol très critique")
        elif soil_moisture < 30:
            risk_score += 10
            factors.append("Humidité du sol faible")
        
        # Détermination du niveau de risque
        if risk_score >= 70:
            risk_level = "Très Élevé"
            color = "red"
        elif risk_score >= 50:
            risk_level = "Élevé"
            color = "orange"
        elif risk_score >= 30:
            risk_level = "Modéré"
            color = "yellow"
        elif risk_score >= 15:
            risk_level = "Faible"
            color = "blue"
        else:
            risk_level = "Très Faible"
            color = "green"
        
        # Recommandations basées sur le risque
        recommendations = generate_recommendations(risk_level, indicators)
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_color': color,
            'factors': factors,
            'spi_value': spi_mean,
            'precipitation_deficit': deficit,
            'avg_temperature': indicators.get('avg_temperature', 0),
            'recommendations': recommendations
        }
        
    except Exception as e:
        st.warning(f"Erreur dans l'évaluation du risque: {e}")
        return get_default_risk_assessment()

def get_default_risk_assessment():
    """Retourne une évaluation de risque par défaut"""
    return {
        'risk_level': "Indéterminé",
        'risk_score': 0,
        'risk_color': "gray",
        'factors': ["Données insuffisantes pour l'analyse"],
        'spi_value': 0,
        'precipitation_deficit': 0,
        'avg_temperature': 25,
        'recommendations': ["Collecter plus de données pour une analyse fiable"]
    }

def generate_recommendations(risk_level, indicators):
    """
    Génère des recommandations basées sur le niveau de risque
    """
    recommendations = []
    
    if risk_level in ["Élevé", "Très Élevé"]:
        recommendations.extend([
            "Activation des plans d'urgence sécheresse",
            "Restrictions d'eau obligatoires",
            "Mise en place de systèmes d'irrigation d'urgence",
            "Surveillance renforcée des ressources en eau",
            "Préparation à la distribution d'aide humanitaire"
        ])
    elif risk_level == "Modéré":
        recommendations.extend([
            "Sensibilisation des agriculteurs aux économies d'eau",
            "Promotion des pratiques agricoles résilientes",
            "Surveillance accrue des indicateurs climatiques",
            "Planification des mesures de restriction volontaire"
        ])
    else:
        recommendations.extend([
            "Surveillance de routine des paramètres climatiques",
            "Maintien des bonnes pratiques de gestion de l'eau",
            "Planification à long terme de l'adaptation climatique"
        ])
    
    # Recommandations spécifiques basées sur les indicateurs
    soil_moisture = indicators.get('soil_moisture_mean', 100)
    if soil_moisture < 30:
        recommendations.append("Irrigation de sauvegarde recommandée pour les cultures sensibles")
    
    dry_days = indicators.get('consecutive_dry_days', 0)
    if dry_days > 15:
        recommendations.append("Évaluation des besoins en fourrage pour le bétail")
    
    heat_stress = indicators.get('heat_stress', 0)
    if heat_stress > 40:
        recommendations.append("Mise en place de zones d'ombre et d'abreuvement pour le bétail")
    
    return recommendations