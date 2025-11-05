# pages/dashboard.py
import streamlit as st
import sys
import os
from datetime import datetime

# Configuration des chemins pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configuration de la page
st.set_page_config(
    page_title="ONACC+ - Tableau de Bord",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application du style CSS
def load_dashboard_css():
    """Charge les styles CSS pour le dashboard"""
    st.markdown("""
    <style>
    /* Styles généraux pour le dashboard */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    
    .module-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        height: 100%;
        cursor: pointer;
    }
    
    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    
    .risk-high { border-left: 4px solid #ef4444; }
    .risk-medium { border-left: 4px solid #f59e0b; }
    .risk-low { border-left: 4px solid #10b981; }
    
    .user-info {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .nav-button {
        width: 100%;
        margin: 0.2rem 0;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

def get_user_info():
    """Récupère les informations de l'utilisateur connecté"""
    try:
        from auth.authentication import get_current_user
        return get_current_user()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des informations utilisateur: {e}")
        return None

def show_sidebar():
    """Affiche la sidebar avec navigation et informations utilisateur"""
    with st.sidebar:
        # Informations utilisateur
        user = get_user_info()
        if user:
            st.markdown(f"""
            <div class="user-info">
                <h3>👤 {user.get('name', 'Utilisateur')}</h3>
                <p><strong>Institution:</strong> {user.get('institution', 'Non spécifiée')}</p>
                <p><strong>Rôle:</strong> {user.get('role', 'Utilisateur')}</p>
                <p><small>Connecté depuis {datetime.now().strftime('%d/%m/%Y')}</small></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Navigation principale
        st.markdown("### 📊 Navigation")
        
        # Boutons de navigation
        if st.button("🏠 Tableau de Bord", key="nav_home", use_container_width=True):
            st.rerun()
            
        if st.button("🌊 Surveillance Inondations", key="nav_flood", use_container_width=True):
            st.switch_page("pages/1_🌊_Surveillance_Inondations.py")
            
        if st.button("☀️ Surveillance Sécheresse", key="nav_drought", use_container_width=True):
            st.switch_page("pages/2_☀️_Surveillance_Secheresse.py")
            
        if st.button("⚙️ Paramètres", key="nav_settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
        
        # Bouton de déconnexion
        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            try:
                from auth.authentication import logout
                logout()
                st.success("Déconnexion réussie!")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la déconnexion: {e}")

def show_dashboard_home():
    """Affiche la page d'accueil du dashboard"""
    
    # En-tête du dashboard
    st.markdown("""
    <div class="dashboard-header">
        <h1>🌍 ONACC+ - Plateforme de Suivi des Risques Climatiques</h1>
        <p>Surveillance en temps réel des risques d'inondations et de sécheresse au Cameroun</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques en temps réel
    st.subheader("📈 Vue d'ensemble des risques")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card risk-high">
            <h3>🚨 Alertes Actives</h3>
            <h2>3</h2>
            <p>Dont 2 inondations, 1 sécheresse</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card risk-medium">
            <h3>📍 Zones Surveillées</h3>
            <h2>24</h2>
            <p>Réparties sur 10 régions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card risk-low">
            <h3>📊 Données Traitées</h3>
            <h2>1.2M</h2>
            <p>Points de données aujourd'hui</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🕒 Dernière MAJ</h3>
            <h2>Maintenant</h2>
            <p>Système opérationnel</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Modules de surveillance
    st.markdown("---")
    st.subheader("🎯 Modules de Surveillance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="module-card" onclick="switchToFlood()">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <span style="font-size: 3rem;">🌊</span>
            </div>
            <h3 style="text-align: center; color: #1e40af;">Surveillance des Inondations</h3>
            <p style="text-align: center; color: #64748b;">
                Surveillance en temps réel des risques d'inondation, analyse des précipitations, 
                et système d'alerte précoce.
            </p>
            <ul style="color: #475569;">
                <li>📡 Données satellitaires en temps réel</li>
                <li>🗺️ Cartographie des zones à risque</li>
                <li>⚡ Système d'alerte précoce</li>
                <li>📈 Analyse des tendances</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🌊 Accéder au module Inondations", key="flood_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/1_🌊_Surveillance_Inondations.py")
    
    with col2:
        st.markdown("""
        <div class="module-card" onclick="switchToDrought()">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <span style="font-size: 3rem;">☀️</span>
            </div>
            <h3 style="text-align: center; color: #ea580c;">Surveillance de la Sécheresse</h3>
            <p style="text-align: center; color: #64748b;">
                Suivi des indices de sécheresse, analyse des données climatiques, 
                et prévisions des risques agricoles.
            </p>
            <ul style="color: #475569;">
                <li>🌡️ Indices de sécheresse calculés</li>
                <li>🛰️ Données satellitaires NDVI</li>
                <li>🔮 Prévisions à 30 jours</li>
                <li>🌾 Impact agricole analysé</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("☀️ Accéder au module Sécheresse", key="drought_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/2_☀️_Surveillance_Secheresse.py")
    
    # Alertes récentes
    st.markdown("---")
    st.subheader("🚨 Alertes Récentes")
    
    alert_col1, alert_col2, alert_col3 = st.columns(3)
    
    with alert_col1:
        st.error("""
        **🌊 Alerte Inondation - Niveau Élevé**
        - Région: Littoral
        - Localité: Douala
        - Risque: Élevé
        - Dernière mise à jour: Aujourd'hui 14:30
        """)
    
    with alert_col2:
        st.warning("""
        **☀️ Alerte Sécheresse - Niveau Moyen**
        - Région: Extrême-Nord
        - Localité: Maroua
        - Risque: Moyen
        - Dernière mise à jour: Hier 09:15
        """)
    
    with alert_col3:
        st.info("""
        **📡 Maintenance Système**
        - Prochaine maintenance: 15/12/2024
        - Durée estimée: 2 heures
        - Impact: Aucun sur les alertes
        """)
    
    # Script JavaScript pour la navigation
    st.markdown("""
    <script>
    function switchToFlood() {
        window.location.href = "pages/1_🌊_Surveillance_Inondations.py";
    }
    function switchToDrought() {
        window.location.href = "pages/2_☀️_Surveillance_Secheresse.py";
    }
    </script>
    """, unsafe_allow_html=True)

def show_settings():
    """Affiche la page des paramètres"""
    st.title("⚙️ Paramètres du Compte")
    
    user = get_user_info()
    if user:
        with st.form("profile_settings"):
            st.subheader("👤 Profil Utilisateur")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nom complet", value=user.get('name', ''))
                email = st.text_input("Email", value=user.get('email', ''))
            
            with col2:
                institution = st.text_input("Institution", value=user.get('institution', ''))
                phone = st.text_input("Téléphone", value=user.get('phone', ''))
            
            st.subheader("🔔 Préférences de notifications")
            
            notif_col1, notif_col2 = st.columns(2)
            
            with notif_col1:
                email_alerts = st.checkbox("Alertes par email", value=True)
                sms_alerts = st.checkbox("Alertes par SMS", value=False)
            
            with notif_col2:
                push_notifications = st.checkbox("Notifications push", value=True)
                newsletter = st.checkbox("Bulletin d'information", value=user.get('newsletter', False))
            
            if st.form_submit_button("💾 Sauvegarder les modifications", type="primary"):
                st.success("Paramètres mis à jour avec succès!")

def main():
    """Fonction principale du dashboard"""
    
    # Charger les styles CSS
    load_dashboard_css()
    
    # Vérifier l'authentification
    user = get_user_info()
    if not user:
        st.error("❌ Accès non autorisé. Veuillez vous connecter.")
        st.stop()
    
    # Afficher la sidebar
    show_sidebar()
    
    # Gérer l'affichage de la page courante
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # Afficher le contenu en fonction de la page courante
    if st.session_state.current_page == "home":
        show_dashboard_home()
    elif st.session_state.current_page == "settings":
        show_settings()

if __name__ == "__main__":
    main()