import os

class Config:
    # Configuration de l'application
    PAGE_TITLE = "🌊 Plateforme Avancée de Suivi des Risques d'Inondation au Cameroun"
    PAGE_ICON = "🌊"
    LAYOUT = "wide"
    
    # Fichiers de données
    AVAILABLE_DATA_FILES = ["database/localites.xlsx"]
    
    # Seuils d'alerte du document
    PRECIPITATION_THRESHOLDS = {
        'intensity_hourly': 50,    # mm/heure
        'cumul_3h': 100,           # mm/3h
        'cumul_daily': 200,        # mm/jour
        'soil_moisture': 85        # % saturation
    }
    
    # Niveaux d'alerte
    ALERT_LEVELS = {
        'Vigilance': {'color': 'green', 'delay': '72-48h', 'actions': 'Surveillance renforcée'},
        'Pré-alerte': {'color': 'yellow', 'delay': '48-24h', 'actions': 'Préparation communautaire'},
        'Alerte': {'color': 'orange', 'delay': '24-6h', 'actions': 'Mise en sécurité biens/matériels'},
        'Alerte Maximale': {'color': 'red', 'delay': '<6h', 'actions': 'Évacuation populations'}
    }
    
    # Types d'inondation
    FLOOD_TYPES = {
        'Fluviale': {
            'causes': ['Débordement des cours d\'eau'],
            'triggers': ['Précipitations prolongées', 'Rupture de berges', 'Colmatage du lit mineur'],
            'locations': ['Wouri à Douala', 'Logone à l\'Extrême-Nord']
        },
        'Pluviale': {
            'causes': ['Ruissellement urbain intense'],
            'triggers': ['Pluies convectives intenses', 'Saturation des sols', 'Imperméabilisation des surfaces'],
            'locations': ['Zones urbaines']
        },
        'Côtière': {
            'causes': ['Combinaison marée haute + surcote'],
            'triggers': ['Élévation du niveau marin', 'Subsidence des terrains'],
            'locations': ['Douala', 'Limbé', 'Kribi']
        }
    }
    
    # Facteurs d'aggravation
    AGGRAVATING_FACTORS = {
        'Naturels': [
            'Régime pluviométrique tropical intense',
            'Topographie plate (bassin de Douala)',
            'Convergence de masses d\'air humide',
            'Cyclicité ENSO (El Niño/La Niña)'
        ],
        'Anthropiques': [
            'Urbanisation non maîtrisée',
            'Défrichement des bassins versants',
            'Systèmes de drainage insuffisants',
            'Gestion inadéquate des déchets solides',
            'Absence de plans d\'occupation des sols'
        ]
    }
    
    # Modèles et indices
    PREDICTION_MODELS = {
        'Indices': ['FFG (Flash Flood Guidance)', 'IFS (Indice de Fuite Superficielle)', 'Indice de Saturation des Sols'],
        'Modèles': ['GR4H', 'TOPMODEL', 'HEC-RAS', 'LISFLOOD', 'SWAT', 'Modèle couple météo-hydrologique']
    }
    
    # Technologies de surveillance
    MONITORING_TECHNOLOGIES = {
        'Capteurs Terrain': ['Pluviomètres automatiques', 'Limnigraphes', 'Capteurs d\'humidité des sols', 'Caméras surveillance'],
        'Télédétection': ['Radar météorologique', 'Satellites (GPM, Sentinel-1,2, Landsat, Modis)', 'Drones']
    }
    
    # Recommandations par ville pilote
    CITY_RECOMMENDATIONS = {
        'Douala': [
            'Surveillance renforcée marée + pluie',
            'Modélisation hydraulique urbaine',
            'Capteurs dans les quartiers précaires'
        ],
        'Extrême-Nord': [
            'Système d\'alerte communautaire',
            'Surveillance crues éclair',
            'Intégration connaissances traditionnelles'
        ],
        'Zones Montagneuses': [
            'Surveillance glissements de terrain',
            'Alertes basées sur cumuls pluviométriques critiques'
        ]
    }