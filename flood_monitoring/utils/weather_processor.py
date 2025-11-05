import requests
import streamlit as st
from config import Config

class WeatherProcessor:
    def __init__(self):
        self.base_url = Config.OPENMETEO_URL
        self.timeout = Config.WEATHER_TIMEOUT
    
    def get_weather_data(self, latitude, longitude, days=3):
        """Récupère les données météorologiques depuis OpenMeteo"""
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'temperature_2m,relative_humidity_2m,precipitation,rain',
                'daily': 'precipitation_sum',
                'timezone': 'auto',
                'forecast_days': days
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"⚠️ API météo indisponible pour ({latitude}, {longitude})")
                return self._get_fallback_data()
                
        except Exception as e:
            st.warning(f"⚠️ Erreur API météo: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self):
        """Données de fallback en cas d'indisponibilité de l'API"""
        return {
            'hourly': {
                'precipitation': [0] * 24,
                'rain': [0] * 24,
                'temperature_2m': [25] * 24,
                'relative_humidity_2m': [60] * 24
            },
            'daily': {
                'precipitation_sum': [0] * 3
            }
        }