# pages/2_☀️_Surveillance_Secheresse.py
import streamlit as st
import sys
import os
import importlib.util

# Configuration de la page
st.set_page_config(
    page_title="Surveillance Sécheresse - ONACC+",
    page_icon="☀️",
    layout="wide"
)

def load_drought_module():
    """Charge dynamiquement le module drought_monitoring"""
    try:
        # Chemin vers le module drought_monitoring
        drought_path = os.path.join(os.path.dirname(__file__), '..', 'drought_monitoring', 'app.py')
        
        if not os.path.exists(drought_path):
            st.error("Module drought_monitoring non trouvé")
            return False
            
        # Chargement dynamique du module
        spec = importlib.util.spec_from_file_location("drought_monitoring.app", drought_path)
        drought_module = importlib.util.module_from_spec(spec)
        sys.modules["drought_monitoring.app"] = drought_module
        spec.loader.exec_module(drought_module)
        
        # Exécution de l'application
        drought_module.main()
        return True
        
    except Exception as e:
        st.error(f"Erreur lors du chargement du module: {e}")
        return False

def show_demo_interface():
    """Affiche une interface de démonstration"""
    st.title("☀️ Surveillance de la Sécheresse - Mode Démonstration")
    
    st.info("""
    **Module en cours de chargement...**
    
    En attendant le chargement complet du module, voici une prévisualisation des fonctionnalités disponibles.
    """)
    
    # Onglets pour la démonstration
    tab1, tab2, tab3 = st.tabs(["📊 Indices de Sécheresse", "🛰️ Données Satellitaires", "🌾 Impact Agricole"])
    
    with tab1:
        st.subheader("Indices de sécheresse calculés")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("SPI (Standardized Precipitation Index)", "-1.8", "Sécheresse modérée")
        with col2:
            st.metric("VCI (Vegetation Condition Index)", "35%", "Stress végétal")
        with col3:
            st.metric("TSI (Temperature Severity Index)", "72%", "Élevé")
        
        # Graphique simulé
        st.area_chart({
            'Précipitations': [120, 80, 45, 30, 25, 20, 15],
            'Moyenne historique': [100, 95, 90, 85, 80, 85, 90]
        })
    
    with tab2:
        st.subheader("Données satellitaires NDVI")
        st.image("https://via.placeholder.com/800x400/ea580c/ffffff?text=Données+Satellitaires+NDVI", 
                caption="Indice de végétation par satellite")
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "Saison en cours"])
        with col2:
            st.selectbox("Région", ["Extrême-Nord", "Nord", "Adamaoua"])
    
    with tab3:
        st.subheader("Impact sur l'agriculture")
        st.warning("⚠️ Alerte Sécheresse - Région Nord")
        st.write("**Impact:** Réduction des rendements attendue")
        st.write("**Culture principale:** Mil et sorgho")
        st.write("**Recommandation:** Irrigation d'appoint nécessaire")
        
        progress_col1, progress_col2 = st.columns(2)
        with progress_col1:
            st.progress(0.3, label="Stress hydrique")
        with progress_col2:
            st.progress(0.6, label="Stress thermique")

def main():
    # Bouton de retour
    if st.button("← Retour au Tableau de Bord"):
        st.switch_page("pages/dashboard.py")
    
    # Essayer de charger le module principal
    if not load_drought_module():
        st.warning("Le module principal n'a pas pu être chargé. Affichage de la version de démonstration.")
        show_demo_interface()

if __name__ == "__main__":
    main()