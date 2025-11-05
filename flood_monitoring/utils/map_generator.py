import folium
import pandas as pd
from config import Config

class MapGenerator:
    def __init__(self):
        self.center = Config.MAP_CENTER
        self.zoom = Config.DEFAULT_ZOOM
        self.tiles = Config.MAP_TILES
        self.colors = Config.RISK_COLORS
    
    def create_risk_map(self, data_df):
        """Crée une carte interactive des risques d'inondation"""
        # Création de la carte de base
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom,
            tiles=self.tiles
        )
        
        # Ajout des marqueurs pour chaque localité
        for _, row in data_df.iterrows():
            self._add_risk_marker(m, row)
        
        return m
    
    def _add_risk_marker(self, map_obj, row):
        """Ajoute un marqueur de risque à la carte"""
        # Configuration du marqueur selon le niveau de risque
        risk_level = row['risk_level']
        color = self.colors.get(risk_level, '#808080')
        
        # Taille basée sur le score de risque
        radius = 8 + (row['risk_score'] * 12)
        
        # Popup avec informations détaillées
        popup_content = self._create_popup_content(row)
        
        # Création du marqueur circulaire
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{row['localite']} - Risque: {risk_level}",
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=1
        ).add_to(map_obj)
    
    def _create_popup_content(self, row):
        """Crée le contenu HTML du popup"""
        return f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="color: #1f77b4; margin-bottom: 10px;">{row['localite']}</h4>
            <p><strong>Région:</strong> {row['region']}</p>
            <p><strong>Zone:</strong> {row['zone']}</p>
            <p><strong>Altitude:</strong> {row['altitude']} m</p>
            <hr>
            <p><strong>Niveau de risque:</strong> 
            <span style="color: {self.colors.get(row['risk_level'], '#808080')}; font-weight: bold;">
                {row['risk_level']}
            </span>
            </p>
            <p><strong>Score:</strong> {row['risk_score']:.2f}</p>
        </div>
        """