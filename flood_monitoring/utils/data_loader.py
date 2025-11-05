import pandas as pd
import streamlit as st
import io
import os
from config import Config

class DataLoader:
    def __init__(self):
        self.required_columns = [
            'localite', 'latitude', 'longitude', 
            'altitude', 'region', 'zone', 'country',
            'type_inondation', 'facteurs_aggravation'
        ]
    
    def load_localities(self, file_path):
        """Charge les données des localités avec validation avancée"""
        try:
            if not os.path.exists(file_path):
                st.error(f"❌ Fichier non trouvé: {file_path}")
                return self.create_sample_data()
            
            df = pd.read_excel(file_path)
            
            # Validation des colonnes de base
            base_columns = ['localite', 'latitude', 'longitude', 'altitude', 'region', 'zone', 'country']
            missing_base = [col for col in base_columns if col not in df.columns]
            if missing_base:
                st.warning(f"⚠️ Colonnes de base manquantes: {missing_base}. Utilisation des valeurs par défaut.")
                df = self._add_missing_columns(df, base_columns)
            
            # Colonnes avancées
            if 'type_inondation' not in df.columns:
                df['type_inondation'] = df.apply(self._determine_flood_type, axis=1)
            
            if 'facteurs_aggravation' not in df.columns:
                df['facteurs_aggravation'] = df.apply(self._determine_aggravating_factors, axis=1)
            
            # Validation des données
            if df.empty:
                st.error("❌ Le fichier est vide")
                return self.create_sample_data()
            
            st.success(f"✅ {len(df)} localités chargées avec analyse des risques spécifiques")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur de chargement: {e}")
            return self.create_sample_data()
    
    def _add_missing_columns(self, df, required_columns):
        """Ajoute les colonnes manquantes avec des valeurs par défaut"""
        for col in required_columns:
            if col not in df.columns:
                if col == 'altitude':
                    df[col] = 100  # Valeur par défaut
                elif col == 'zone':
                    df[col] = 'Urbaine'  # Valeur par défaut
                elif col == 'country':
                    df[col] = 'Cameroun'
        return df
    
    def _determine_flood_type(self, row):
        """Détermine le type d'inondation prédominant selon la localisation"""
        region = str(row.get('region', '')).lower()
        zone = str(row.get('zone', '')).lower()
        
        if any(loc in region for loc in ['douala', 'limbé', 'kribi', 'littoral']):
            return 'Côtière'
        elif any(loc in region for loc in ['extrême-nord', 'nord', 'adamaoua']):
            return 'Fluviale'
        elif any(loc in region for loc in ['ouest', 'sud-ouest', 'montagne']):
            return 'Pluviale'
        else:
            return 'Mixte'
    
    def _determine_aggravating_factors(self, row):
        """Détermine les facteurs d'aggravation selon la zone"""
        zone = str(row.get('zone', '')).lower()
        region = str(row.get('region', '')).lower()
        
        factors = []
        
        if 'urbain' in zone:
            factors.extend(['Urbanisation non maîtrisée', 'Systèmes de drainage insuffisants'])
        if any(reg in region for reg in ['extrême-nord', 'nord']):
            factors.append('Défrichement des bassins versants')
        if 'littoral' in region:
            factors.append('Gestion inadéquate des déchets solides')
        
        return ', '.join(factors) if factors else 'Facteurs naturels prédominants'
    
    def create_template(self):
        """Crée un template Excel complet avec données d'exemple"""
        template_data = {
            'localite': ['Douala', 'Maroua', 'Buea', 'Yaoundé', 'Garoua'],
            'latitude': [4.0511, 10.5957, 4.1667, 3.8480, 9.3012],
            'longitude': [9.7679, 14.3247, 9.2333, 11.5021, 13.3925],
            'altitude': [13, 420, 870, 726, 242],
            'region': ['Littoral', 'Extrême-Nord', 'Sud-Ouest', 'Centre', 'Nord'],
            'zone': ['Urbaine Côtière', 'Rurale Soudano-Sahélienne', 'Urbaine Montagneuse', 'Urbaine', 'Rurale'],
            'country': ['Cameroun'] * 5,
            'type_inondation': ['Côtière', 'Fluviale', 'Pluviale', 'Mixte', 'Fluviale'],
            'facteurs_aggravation': [
                'Urbanisation non maîtrisée, Systèmes de drainage insuffisants',
                'Défrichement des bassins versants',
                'Urbanisation non maîtrisée',
                'Urbanisation non maîtrisée, Gestion inadéquate des déchets',
                'Défrichement des bassins versants'
            ]
        }
        
        df = pd.DataFrame(template_data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Localites', index=False)
        
        return output.getvalue()

# Fonctions existantes conservées
def load_localities():
    data_loader = DataLoader()
    return data_loader.load_localities("database/localites.xlsx")

def create_sample_data():
    data_loader = DataLoader()
    return data_loader.create_sample_data()