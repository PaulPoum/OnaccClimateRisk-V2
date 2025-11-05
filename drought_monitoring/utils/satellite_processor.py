import numpy as np
import streamlit as st

def get_satellite_data(latitude, longitude, layer_type):
    """
    Simule la récupération de données satellitaires
    """
    try:
        # Simulation de données satellitaires
        if layer_type == "NDVI":
            data = simulate_ndvi_data(latitude, longitude)
        elif layer_type == "Température":
            data = simulate_temperature_data(latitude, longitude)
        elif layer_type == "Humidité":
            data = simulate_soil_moisture_data(latitude, longitude)
        else:  # Risque
            data = simulate_risk_data(latitude, longitude)
        
        return data
    except Exception as e:
        st.error(f"Erreur lors du traitement des données satellites: {e}")
        return None

def simulate_ndvi_data(lat, lon):
    """Simule des données NDVI"""
    # Création d'une grille 10x10 simulant une image satellite
    grid_size = 10
    image_data = np.random.rand(grid_size, grid_size) * 0.6 + 0.2  # NDVI entre 0.2 et 0.8
    
    return {
        'image_data': image_data,
        'stats': {
            'mean': np.mean(image_data),
            'std': np.std(image_data),
            'min': np.min(image_data),
            'max': np.max(image_data),
            'area': 25  # km²
        },
        'type': 'NDVI'
    }

def simulate_temperature_data(lat, lon):
    """Simule des données de température de surface"""
    grid_size = 10
    # Température basée sur la latitude
    base_temp = 25 + (lat - 5) * 0.5
    image_data = np.random.normal(base_temp, 3, (grid_size, grid_size))
    
    return {
        'image_data': image_data,
        'stats': {
            'mean': np.mean(image_data),
            'std': np.std(image_data),
            'min': np.min(image_data),
            'max': np.max(image_data),
            'area': 25
        },
        'type': 'Temperature'
    }

def simulate_soil_moisture_data(lat, lon):
    """Simule des données d'humidité du sol"""
    grid_size = 10
    # Humidité plus faible dans les zones nord
    base_moisture = 60 - abs(lat - 4) * 5
    image_data = np.random.normal(base_moisture, 10, (grid_size, grid_size))
    image_data = np.clip(image_data, 5, 95)
    
    return {
        'image_data': image_data,
        'stats': {
            'mean': np.mean(image_data),
            'std': np.std(image_data),
            'min': np.min(image_data),
            'max': np.max(image_data),
            'area': 25
        },
        'type': 'Soil_Moisture'
    }

def simulate_risk_data(lat, lon):
    """Simule des données de risque de sécheresse"""
    grid_size = 10
    # Risque plus élevé dans les zones nord
    base_risk = 0.3 + abs(lat - 4) * 0.1
    image_data = np.random.normal(base_risk, 0.2, (grid_size, grid_size))
    image_data = np.clip(image_data, 0, 1)
    
    return {
        'image_data': image_data,
        'stats': {
            'mean': np.mean(image_data),
            'std': np.std(image_data),
            'min': np.min(image_data),
            'max': np.max(image_data),
            'area': 25
        },
        'type': 'Risk'
    }

def process_risk_zones(satellite_data):
    """Traite les zones à risque basées sur les données satellites"""
    risk_zones = []
    
    # Simulation de zones à risque
    coordinates = [
        [10.5957, 14.3247],  # Maroua
        [10.6000, 14.3300],
        [10.5900, 14.3200]
    ]
    
    for i, coord in enumerate(coordinates):
        risk_levels = ['low', 'medium', 'high', 'very_high']
        colors = ['green', 'yellow', 'orange', 'red']
        
        risk_zones.append({
            'name': f'Zone Risque {i+1}',
            'coordinates': coord,
            'radius': 1000 + i * 500,
            'risk_level': risk_levels[i % 4],
            'value': np.random.uniform(0.1, 0.9),
            'color': colors[i % 4]
        })
    
    return risk_zones