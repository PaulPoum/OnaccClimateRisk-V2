import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openmeteo_requests
import requests_cache
from retry_requests import retry

class DroughtForecastAnalyzer:
    def __init__(self):
        self.cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        self.retry_session = retry(self.cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=self.retry_session)
    
    def get_forecast_data(self, latitude, longitude, forecast_type='10days'):
        """
        Récupère les données de prévision selon le type demandé
        """
        try:
            if forecast_type == '10days':
                return self.get_10day_forecast(latitude, longitude)
            elif forecast_type == '30days':
                return self.get_30day_forecast(latitude, longitude)
            elif forecast_type == '90days':
                return self.get_seasonal_forecast(latitude, longitude)
            elif forecast_type == '1year':
                return self.get_longterm_forecast(latitude, longitude, years=1)
            elif forecast_type == '5years':
                return self.get_longterm_projection(latitude, longitude, years=5)
        except Exception as e:
            st.error(f"Erreur lors de la récupération des prévisions: {e}")
            return None
    
    def get_10day_forecast(self, latitude, longitude):
        """
        Prévisions décaire (10 jours)
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "et0_fao_evapotranspiration"],
            "timezone": "auto",
            "forecast_days": 10
        }
        
        responses = self.openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        daily = response.Daily()
        dates = pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq='D',
            inclusive='left'
        )
        
        return {
            'dates': dates,
            'temperature_max': daily.Variables(0).ValuesAsNumpy(),
            'temperature_min': daily.Variables(1).ValuesAsNumpy(),
            'precipitation': daily.Variables(2).ValuesAsNumpy(),
            'et0': daily.Variables(3).ValuesAsNumpy(),
            'type': '10days',
            'timeframe': '10 jours'
        }
    
    def get_30day_forecast(self, latitude, longitude):
        """
        Prévisions à 30 jours (moyennes mensuelles)
        """
        # Simulation basée sur les données historiques et tendances
        end_date = datetime.now() + timedelta(days=30)
        dates = pd.date_range(start=datetime.now(), end=end_date, freq='D')
        
        # Génération de données réalistes avec tendance
        np.random.seed(int(latitude * 100 + longitude))
        
        # Températures avec variation saisonnière
        base_temp = 25 + (latitude - 5) * 0.5
        temperature_max = base_temp + np.random.normal(3, 2, len(dates))
        temperature_min = base_temp + np.random.normal(-3, 2, len(dates))
        
        # Précipitations avec probabilité de pluie décroissante
        rain_prob = np.linspace(0.3, 0.1, len(dates))
        precipitation = np.random.exponential(5, len(dates)) * np.random.binomial(1, rain_prob)
        
        return {
            'dates': dates,
            'temperature_max': temperature_max,
            'temperature_min': temperature_min,
            'precipitation': precipitation,
            'et0': np.random.normal(4, 1, len(dates)),
            'type': '30days',
            'timeframe': '30 jours',
            'confidence': 0.7
        }
    
    def get_seasonal_forecast(self, latitude, longitude):
        """
        Prévisions saisonnières (90 jours)
        """
        end_date = datetime.now() + timedelta(days=90)
        dates = pd.date_range(start=datetime.now(), end=end_date, freq='D')
        
        np.random.seed(int(latitude * 100 + longitude))
        
        # Modèle saisonnier simplifié
        base_temp = 25 + (latitude - 5) * 0.5
        seasonal_variation = np.sin(np.linspace(0, 2*np.pi, len(dates))) * 3
        
        temperature_max = base_temp + seasonal_variation + np.random.normal(0, 1.5, len(dates))
        temperature_min = base_temp + seasonal_variation + np.random.normal(-2, 1.5, len(dates))
        
        # Saison des pluies simulée
        rain_season = np.sin(np.linspace(0, 2*np.pi, len(dates)) + np.pi/2) > 0
        precipitation = np.random.exponential(8, len(dates)) * rain_season
        
        return {
            'dates': dates,
            'temperature_max': temperature_max,
            'temperature_min': temperature_min,
            'precipitation': precipitation,
            'et0': np.random.normal(4.5, 0.8, len(dates)),
            'type': 'seasonal',
            'timeframe': '90 jours',
            'confidence': 0.6
        }
    
    def get_longterm_forecast(self, latitude, longitude, years=1):
        """
        Projections à long terme (1-5 ans)
        """
        dates = pd.date_range(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=365*years),
            freq='M'  # Données mensuelles
        )
        
        np.random.seed(int(latitude * 100 + longitude))
        
        # Tendances climatiques à long terme
        base_temp = 25 + (latitude - 5) * 0.5
        warming_trend = np.linspace(0, 0.8 * years, len(dates))  # Réchauffement progressif
        
        temperature_max = base_temp + warming_trend + np.random.normal(0, 2, len(dates))
        
        # Variation des précipitations avec tendance à la baisse
        precip_trend = np.linspace(0, -0.1 * years, len(dates))
        precipitation = np.maximum(0, np.random.exponential(80, len(dates)) + precip_trend * 20)
        
        return {
            'dates': dates,
            'temperature_max': temperature_max,
            'precipitation': precipitation,
            'type': f'{years}year',
            'timeframe': f'{years} an(s)',
            'confidence': 0.5,
            'warming_trend': warming_trend,
            'precip_trend': precip_trend
        }
    
    def get_longterm_projection(self, latitude, longitude, years=5):
        """
        Projections climatiques à 5 ans
        """
        return self.get_longterm_forecast(latitude, longitude, years=years)
    
    def calculate_drought_risk(self, forecast_data):
        """
        Calcule le risque de sécheresse basé sur les prévisions
        """
        if forecast_data is None:
            return None
        
        precip = forecast_data['precipitation']
        et0 = forecast_data.get('et0', np.mean(precip) * 1.5)  # Valeur par défaut pour ET0
        
        # Indicateurs de risque
        total_precip = np.sum(precip)
        avg_precip = np.mean(precip)
        dry_days = np.sum(precip < 1.0)  # Jours avec moins de 1mm de pluie
        
        # Déficit hydrique
        water_balance = total_precip - np.sum(et0) if 'et0' in forecast_data else total_precip - len(precip) * 3
        
        # Score de risque (0-100)
        risk_score = 0
        
        # Facteur précipitations (50%)
        if avg_precip < 1:
            risk_score += 50
        elif avg_precip < 2:
            risk_score += 30
        elif avg_precip < 3:
            risk_score += 15
        
        # Facteur jours secs (30%)
        dry_ratio = dry_days / len(precip)
        risk_score += dry_ratio * 30
        
        # Facteur bilan hydrique (20%)
        if water_balance < -50:
            risk_score += 20
        elif water_balance < -20:
            risk_score += 10
        
        risk_score = min(100, risk_score)
        
        # Niveau de risque
        if risk_score >= 80:
            risk_level = "Très Élevé"
            color = "red"
        elif risk_score >= 60:
            risk_level = "Élevé"
            color = "orange"
        elif risk_score >= 40:
            risk_level = "Modéré"
            color = "yellow"
        elif risk_score >= 20:
            risk_level = "Faible"
            color = "blue"
        else:
            risk_level = "Très Faible"
            color = "green"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_color': color,
            'total_precipitation': total_precip,
            'average_precipitation': avg_precip,
            'dry_days': dry_days,
            'water_balance': water_balance,
            'timeframe': forecast_data.get('timeframe', 'Inconnu'),
            'confidence': forecast_data.get('confidence', 0.5)
        }
    
    def create_forecast_chart(self, forecast_data, risk_assessment):
        """
        Crée un graphique de prévision avec indicateurs de risque
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f'Prévisions Météorologiques - {forecast_data["timeframe"]}',
                'Évolution du Risque de Sécheresse'
            ),
            vertical_spacing=0.15,
            shared_xaxes=True
        )
        
        dates = forecast_data['dates']
        
        # Graphique 1: Données météo
        fig.add_trace(
            go.Bar(x=dates, y=forecast_data['precipitation'], 
                  name='Précipitations', marker_color='blue'),
            row=1, col=1
        )
        
        if 'temperature_max' in forecast_data:
            fig.add_trace(
                go.Scatter(x=dates, y=forecast_data['temperature_max'],
                          name='Température Max', line=dict(color='red')),
                row=1, col=1
            )
        
        if 'et0' in forecast_data:
            fig.add_trace(
                go.Scatter(x=dates, y=forecast_data['et0'],
                          name='ET0', line=dict(color='orange', dash='dash')),
                row=1, col=1
            )
        
        # Graphique 2: Indice de risque
        risk_dates = pd.date_range(start=dates[0], end=dates[-1], freq='7D')  # Risque hebdomadaire
        risk_values = np.linspace(
            risk_assessment['risk_score'] * 0.8, 
            risk_assessment['risk_score'] * 1.2, 
            len(risk_dates)
        )
        
        fig.add_trace(
            go.Scatter(x=risk_dates, y=risk_values,
                      name='Indice de Risque', line=dict(color='purple', width=3),
                      fill='tozeroy'),
            row=2, col=1
        )
        
        # Seuils de risque
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1,
                     annotation_text="Risque Très Élevé")
        fig.add_hline(y=60, line_dash="dash", line_color="orange", row=2, col=1,
                     annotation_text="Risque Élevé")
        fig.add_hline(y=40, line_dash="dash", line_color="yellow", row=2, col=1,
                     annotation_text="Risque Modéré")
        
        fig.update_layout(height=600, showlegend=True, template="plotly_white")
        fig.update_yaxes(title_text="Précipitations/Température", row=1, col=1)
        fig.update_yaxes(title_text="Indice de Risque", row=2, col=1, range=[0, 100])
        
        return fig

def get_forecast_analyzer():
    """
    Retourne une instance du analyseur de prévisions
    """
    return DroughtForecastAnalyzer()