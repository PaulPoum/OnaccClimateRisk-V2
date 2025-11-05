# drought_monitoring/config.py - Version sécurisée
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de base
class Config:
    # Paramètres de base
    APP_NAME = "ONACC+ Drought Monitoring"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Paramètres de données
    DATA_PATH = os.path.join(os.path.dirname(__file__), 'database')
    LOCALITIES_FILE = os.path.join(DATA_PATH, 'localites.xlsx')
    
    # Paramètres API
    API_KEY = os.getenv('DROUGHT_API_KEY', '')
    API_URL = os.getenv('DROUGHT_API_URL', '')
    
    # Paramètres de calcul
    DROUGHT_THRESHOLD = float(os.getenv('DROUGHT_THRESHOLD', '0.5'))
    ALERT_LEVEL = os.getenv('ALERT_LEVEL', 'medium')
    
    # Clé API DeepSeek - Version sécurisée
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-2dda8c4bc42b43969af10ffeef9694b2')

# Instance de configuration
config = Config()