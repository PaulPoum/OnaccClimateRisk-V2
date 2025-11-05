# pages/1_🌊_Surveillance_Inondations.py
import streamlit as st
import sys
import os
import importlib.util

# Configuration de la page
st.set_page_config(
    page_title="Surveillance Inondations - ONACC+",
    page_icon="🌊",
    layout="wide"
)

def load_flood_module():
    """Charge dynamiquement le module flood_monitoring"""
    try:
        # Chemin vers le module flood_monitoring
        flood_path = os.path.join(os.path.dirname(__file__), '..', 'flood_monitoring', 'app.py')
        
        if not os.path.exists(flood_path):
            st.error("Module flood_monitoring non trouvé")
            return False
            
        # Chargement dynamique du module
        spec = importlib.util.spec_from_file_location("flood_monitoring.app", flood_path)
        flood_module = importlib.util.module_from_spec(spec)
        sys.modules["flood_monitoring.app"] = flood_module
        spec.loader.exec_module(flood_module)
        
        # Exécution de l'application
        flood_module.main()
        return True
        
    except Exception as e:
        st.error(f"Erreur lors du chargement du module: {e}")
        return False

def show_demo_interface():
    """Affiche une interface de démonstration"""
    st.title("🌊 Surveillance des Inondations - Mode Démonstration")
    
    st.info("""
    **Module en cours de chargement...**
    
    En attendant le chargement complet du module, voici une prévisualisation des fonctionnalités disponibles.
    """)
    
    # Onglets pour la démonstration
    tab1, tab2, tab3 = st.tabs(["📊 Données en Temps Réel", "🗺️ Cartographie", "⚡ Alertes"])
    
    with tab1:
        st.subheader("Données de précipitations")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Précipitations (24h)", "45 mm", "+12%")
            st.metric("Niveau des rivières", "2.3 m", "Stable")
        with col2:
            st.metric("Risque inondation", "Élevé", "-")
            st.metric("Prochaines 48h", "60 mm", "⚠️")
        
        # Graphique simulé
        st.line_chart({
            'Précipitations': [10, 25, 45, 30, 15, 5, 20],
            'Seuil alerte': [30, 30, 30, 30, 30, 30, 30]
        })
    
    with tab2:
        st.subheader("Cartographie des zones à risque")
        st.image("https://via.placeholder.com/800x400/1e40af/ffffff?text=Carte+des+Risques+Inondation", 
                caption="Carte interactive des zones inondables")
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Région", ["Littoral", "Centre", "Sud", "Ouest"])
        with col2:
            st.selectbox("Type de risque", ["Élevé", "Moyen", "Faible"])
    
    with tab3:
        st.subheader("Système d'alerte")
        st.warning("🚨 Alerte Inondation - Douala")
        st.write("**Niveau:** Élevé")
        st.write("**Localisation:** Zone industrielle")
        st.write("**Recommandation:** Évacuation préventive recommandée")
        
        st.button("📧 Envoyer l'alerte aux autorités")

def main():
    # Bouton de retour
    if st.button("← Retour au Tableau de Bord"):
        st.switch_page("pages/dashboard.py")
    
    # Essayer de charger le module principal
    if not load_flood_module():
        st.warning("Le module principal n'a pas pu être chargé. Affichage de la version de démonstration.")
        show_demo_interface()

if __name__ == "__main__":
    main()