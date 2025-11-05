import streamlit as st
import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime  # Import manquant ajouté

def get_ai_recommendations(locality_data, climate_data=None, drought_indicators=None):
    """
    Obtient des recommandations IA pour la gestion des sécheresses
    Version corrigée pour gérer les Series pandas
    """
    # Convertir locality_data en dictionnaire si c'est une Series pandas
    if hasattr(locality_data, 'to_dict'):
        locality_dict = locality_data.to_dict()
    else:
        locality_dict = locality_data if locality_data is not None else {}
    
    # Vérifier que les données minimales sont disponibles
    if not locality_dict:
        st.error("❌ Données de localité manquantes")
        return None
    
    # Utiliser le mode simulation (plus stable)
    return get_simulated_recommendations(locality_dict, climate_data, drought_indicators)

def get_simulated_recommendations(locality_data, climate_data=None, drought_indicators=None):
    """
    Recommandations simulées réalistes basées sur les données disponibles
    """
    # Convertir locality_data en dictionnaire si c'est une Series pandas
    if hasattr(locality_data, 'to_dict'):
        locality_dict = locality_data.to_dict()
    else:
        locality_dict = locality_data if locality_data is not None else {}
    
    # Gestion des données manquantes
    if drought_indicators is None:
        drought_indicators = {}
    
    # Valeurs par défaut sécurisées
    spi_value = drought_indicators.get('spi_mean', 0)
    precip_deficit = drought_indicators.get('precipitation_deficit', 0)
    soil_moisture = drought_indicators.get('soil_moisture_mean', 50)
    dry_days = drought_indicators.get('consecutive_dry_days', 0)
    
    # Récupération des informations de localité avec valeurs par défaut
    region = locality_dict.get('region', '')
    zone = locality_dict.get('zone', '')
    localite = locality_dict.get('localite', '')
    
    # Déterminer le niveau d'alerte basé sur le SPI
    if spi_value <= -2.0:
        alert_level = 'critical'
        main_alert = 'SÉCHERESSE EXTRÊME'
        confidence = 92
        color = '🔴'
    elif spi_value <= -1.5:
        alert_level = 'high'
        main_alert = 'Sécheresse sévère'
        confidence = 85
        color = '🟠'
    elif spi_value <= -1.0:
        alert_level = 'medium'
        main_alert = 'Sécheresse modérée'
        confidence = 78
        color = '🟡'
    else:
        alert_level = 'low'
        main_alert = 'Vigilance sécheresse'
        confidence = 65
        color = '🟢'

    # Messages contextuels basés sur les données
    if precip_deficit > 50:
        situation = f"Déficit pluviométrique critique de {precip_deficit:.1f}% dans la région {region}."
    elif precip_deficit > 30:
        situation = f"Déficit pluviométrique significatif de {precip_deficit:.1f}%."
    else:
        situation = "Situation sous surveillance."

    if soil_moisture < 30:
        soil_situation = f"Humidité du sol très faible ({soil_moisture:.1f}%)."
    elif soil_moisture < 50:
        soil_situation = f"Humidité du sol modérée ({soil_moisture:.1f}%)."
    else:
        soil_situation = f"Humidité du sol correcte ({soil_moisture:.1f}%)."

    recommendations = {
        'alerts': [
            {
                'title': f'{color} {main_alert}',
                'message': f"{situation} {soil_situation} L'indice SPI est de {spi_value:.2f}.",
                'level': alert_level,
                'confidence': confidence,
                'impacted_sectors': ['agriculture', 'ressources en eau', 'élevage']
            }
        ],
        'actions': [
            {
                'category': '🚰 Gestion de l\'eau',
                'description': 'Restrictions d\'eau pour usages non essentiels et optimisation de l\'irrigation',
                'priority': 'Haute',
                'urgency': 'immédiate',
                'responsible_entities': ['Municipalité', 'Services des eaux']
            },
            {
                'category': '🌱 Agriculture',
                'description': 'Promotion des cultures résistantes et techniques d\'irrigation économes',
                'priority': 'Moyenne',
                'urgency': '15 jours',
                'responsible_entities': ['Chambre d\'agriculture']
            },
            {
                'category': '📊 Surveillance',
                'description': 'Renforcement du monitoring des nappes et réservoirs',
                'priority': 'Haute',
                'urgency': 'immédiate',
                'responsible_entities': ['Direction de l\'eau']
            }
        ],
        'forecast': {
            'situation': f"Tendance à la {('dégradation' if spi_value < -1.0 else 'stabilisation')} dans la zone {zone}.",
            'trend': 'dégradation' if spi_value < -1.0 else 'stabilisation',
            'timeframe': '15-30 jours',
            'recommendation': "Mise en œuvre des mesures de restriction et activation du plan vigilance.",
            'risks': [
                'Pénurie d\'eau potable',
                'Perte de récoltes',
                'Conflits d\'usage de l\'eau'
            ]
        },
        'metadata': {
            'source': 'simulation',
            'analysis_timestamp': datetime.now().isoformat(),  # Maintenant ça fonctionne !
            'confidence_score': confidence,
            'localite': localite,
            'region': region,
            'zone': zone
        }
    }
    
    # Ajouter une alerte spécifique si les jours secs sont nombreux
    if dry_days > 30:
        recommendations['alerts'].append({
            'title': '🟠 Période sèche prolongée',
            'message': f'{dry_days} jours consécutifs sans pluie significative.',
            'level': 'medium',
            'confidence': 75,
            'impacted_sectors': ['agriculture', 'élevage']
        })
    
    return recommendations

def display_recommendations(recommendations: Dict):
    """
    Affiche les recommandations de manière structurée dans Streamlit
    """
    if not recommendations:
        st.error("Aucune recommandation disponible")
        return
    
    # Alertes
    st.header("🚨 Alertes et Évaluations des Risques")
    for alert in recommendations.get('alerts', []):
        level_color = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🟠',
            'critical': '🔴'
        }.get(alert.get('level', 'medium'), '⚪')
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{alert.get('title', 'Alerte')}")
                st.write(alert.get('message', ''))
                if alert.get('impacted_sectors'):
                    st.write(f"**Secteurs impactés:** {', '.join(alert['impacted_sectors'])}")
            with col2:
                st.metric("Confiance", f"{alert.get('confidence', 0)}%")
    
    # Actions recommandées
    st.header("📋 Plan d'Action Recommandé")
    for action in recommendations.get('actions', []):
        priority_icon = {
            'Basse': '🔵',
            'Moyenne': '🟡',
            'Haute': '🟠', 
            'Critique': '🔴'
        }.get(action.get('priority', 'Moyenne'), '⚪')
        
        with st.expander(f"{priority_icon} {action.get('category', 'Action')} - Priorité {action.get('priority', 'Moyenne')}"):
            st.write(f"**Description:** {action.get('description', '')}")
            st.write(f"**Urgence:** {action.get('urgency', 'Non spécifiée')}")
            if action.get('responsible_entities'):
                st.write(f"**Entités responsables:** {', '.join(action['responsible_entities'])}")
    
    # Prévisions
    forecast = recommendations.get('forecast', {})
    if forecast:
        st.header("🔮 Prévisions et Tendances")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Situation prévue")
            st.write(forecast.get('situation', ''))
            st.write(f"**Tendance:** {forecast.get('trend', 'Non spécifiée')}")
            st.write(f"**Échéance:** {forecast.get('timeframe', 'Non spécifiée')}")
            
        with col2:
            st.subheader("Recommandation principale")
            st.info(forecast.get('recommendation', ''))
            
            if forecast.get('risks'):
                st.subheader("Risques identifiés")
                for risk in forecast['risks']:
                    st.write(f"• {risk}")

# Exemple d'utilisation dans Streamlit
def main():
    st.title("🌍 Système d'Alerte Précoce Sécheresse - DeepSeek AI")
    
    # Données d'exemple
    locality_data = {
        'localite': 'Maroua',
        'region': 'Extrême-Nord', 
        'zone': 'Soudano-Sahélienne'
    }
    
    climate_data = {
        'temperature_mean': 32.5,
        'precipitation_total': 450,
        'evapotranspiration': 1200
    }
    
    drought_indicators = {
        'spi_mean': -1.8,
        'precipitation_deficit': 45.2,
        'consecutive_dry_days': 45,
        'soil_moisture_mean': 25.7
    }
    
    if st.button("🔄 Obtenir l'analyse DeepSeek"):
        recommendations = get_ai_recommendations(
            locality_data, 
            climate_data, 
            drought_indicators
        )
        
        if recommendations:
            display_recommendations(recommendations)

if __name__ == "__main__":
    main()