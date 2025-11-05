import streamlit as st
import numpy as np
from config import Config

class FloodCalculator:
    def __init__(self):
        self.thresholds = Config.PRECIPITATION_THRESHOLDS
        self.alert_levels = Config.ALERT_LEVELS
    
    def calculate_risk(self, weather_data, locality_data):
        """Calcule le risque d'inondation avec indices avancés"""
        try:
            # Extraction des données météo
            hourly_data = weather_data.get('hourly', {})
            daily_data = weather_data.get('daily', {})
            
            precipitation = hourly_data.get('precipitation', [0])[:24]
            temperature = hourly_data.get('temperature_2m', [25])[:24]
            humidity = hourly_data.get('relative_humidity_2m', [60])[:24]
            
            # Calcul des indices avancés
            flood_type = locality_data.get('type_inondation', 'Mixte')
            
            # FFG (Flash Flood Guidance)
            ffg_score = self._calculate_ffg(precipitation, flood_type)
            
            # IFS (Indice de Fuite Superficielle)
            ifs_score = self._calculate_ifs(precipitation, humidity, locality_data)
            
            # Indice de Saturation des Sols
            soil_saturation = self._calculate_soil_saturation(weather_data, locality_data)
            
            # Facteurs spécifiques selon le type d'inondation
            type_factor = self._get_flood_type_factor(flood_type, locality_data)
            
            # Score de risque composite avancé
            risk_score = (
                ffg_score * 0.4 +
                ifs_score * 0.3 +
                soil_saturation * 0.2 +
                type_factor * 0.1
            )
            
            # Détermination du niveau d'alerte
            alert_level, alert_details = self._determine_alert_level(risk_score, precipitation)
            
            # Détails du calcul
            details = {
                'ffg_score': ffg_score,
                'ifs_score': ifs_score,
                'soil_saturation': soil_saturation,
                'type_factor': type_factor,
                'precipitation_24h': sum(precipitation),
                'max_hourly_precip': max(precipitation) if precipitation else 0,
                'flood_type': flood_type,
                'alert_details': alert_details
            }
            
            return alert_level, risk_score, details
            
        except Exception as e:
            st.error(f"Erreur dans le calcul du risque: {e}")
            return "Inconnu", 0.0, {}
    
    def _calculate_ffg(self, precipitation, flood_type):
        """Calcule le Flash Flood Guidance"""
        total_precip = sum(precipitation)
        max_hourly = max(precipitation) if precipitation else 0
        
        # Adaptation selon le type d'inondation
        if flood_type == 'Côtière':
            threshold_factor = 0.8  # Plus sensible
        elif flood_type == 'Pluviale':
            threshold_factor = 1.0
        else:  # Fluviale
            threshold_factor = 1.2  # Moins sensible
            
        ffg_score = min(
            (max_hourly / (self.thresholds['intensity_hourly'] * threshold_factor)) * 0.6 +
            (total_precip / (self.thresholds['cumul_daily'] * threshold_factor)) * 0.4,
            1.0
        )
        
        return ffg_score
    
    def _calculate_ifs(self, precipitation, humidity, locality_data):
        """Calcule l'Indice de Fuite Superficielle"""
        # Basé sur l'imperméabilisation et la saturation
        zone = str(locality_data.get('zone', '')).lower()
        factors = str(locality_data.get('facteurs_aggravation', '')).lower()
        
        # Facteur d'imperméabilisation
        impermeability_factor = 1.0
        if any(word in zone for word in ['urbain', 'côtière']):
            impermeability_factor = 1.3
        if 'urbanisation' in factors:
            impermeability_factor = 1.5
        
        # Calcul de l'IFS
        avg_humidity = np.mean(humidity) if humidity else 60
        humidity_factor = avg_humidity / 100
        
        precip_intensity = np.mean(precipitation) if precipitation else 0
        intensity_factor = min(precip_intensity / 20, 1.0)
        
        ifs_score = min(impermeability_factor * (intensity_factor * 0.7 + humidity_factor * 0.3), 1.0)
        
        return ifs_score
    
    def _calculate_soil_saturation(self, weather_data, locality_data):
        """Calcule l'indice de saturation des sols"""
        soil_moisture = weather_data.get('soil_moisture', [50])[0]
        altitude = locality_data.get('altitude', 100)
        
        # Adaptation selon l'altitude
        altitude_factor = max(0.5, 1 - (altitude / 1000))
        
        saturation = min(soil_moisture / self.thresholds['soil_moisture'], 1.0)
        return saturation * altitude_factor
    
    def _get_flood_type_factor(self, flood_type, locality_data):
        """Facteur spécifique selon le type d'inondation"""
        base_factors = {
            'Côtière': 1.2,  # Risque accru
            'Pluviale': 1.1,
            'Fluviale': 1.0,
            'Mixte': 1.15
        }
        
        base_factor = base_factors.get(flood_type, 1.0)
        
        # Facteurs d'aggravation supplémentaires
        factors = str(locality_data.get('facteurs_aggravation', '')).lower()
        if any(factor in factors for factor in ['drainage insuffisant', 'défrichement']):
            base_factor *= 1.2
        
        return min(base_factor, 1.5) / 1.5  # Normalisation
    
    def _determine_alert_level(self, risk_score, precipitation):
        """Détermine le niveau d'alerte selon le score et les précipitations"""
        max_precip = max(precipitation) if precipitation else 0
        
        # Ajustement basé sur l'intensité des précipitations
        intensity_factor = min(max_precip / self.thresholds['intensity_hourly'], 2.0)
        adjusted_score = min(risk_score * intensity_factor, 1.0)
        
        if adjusted_score >= 0.8:
            level = 'Alerte Maximale'
        elif adjusted_score >= 0.6:
            level = 'Alerte'
        elif adjusted_score >= 0.4:
            level = 'Pré-alerte'
        else:
            level = 'Vigilance'
        
        alert_details = self.alert_levels[level]
        return level, alert_details