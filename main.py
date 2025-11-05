# main.py
import streamlit as st
import pandas as pd
from auth.authentication import authenticate_user, get_current_user
import warnings
import random
from datetime import datetime
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="ONACC+ - Intelligence Climatique",
    page_icon="🌍",
    #layout="wide",
    initial_sidebar_state="collapsed"
)

# Application du style CSS personnalisé
# main.py (extrait des améliorations)
def load_css():
    with open("assets/styles/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Style additionnel pour le thème moderne
    st.markdown("""
    <style>
    /* Animation de pulse subtile pour les éléments importants */
    @keyframes gentlePulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .hero-logo-icon-light {
        animation: float 6s ease-in-out infinite, gentlePulse 4s ease-in-out infinite;
    }
    
    /* Amélioration de la lisibilité */
    .form-title-light {
        background: linear-gradient(135deg, #1e293b, #475569) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }
    
    /* Effets de profondeur améliorés */
    .auth-card-light {
        backdrop-filter: blur(20px) saturate(180%) !important;
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Amélioration des transitions */
    .stButton>button {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    /* États de focus améliorés pour l'accessibilité */
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_modern_login_form():
    """Affiche le formulaire de connexion moderne et clair"""
    st.markdown('<div class="form-container-light">', unsafe_allow_html=True)
    
    with st.form("modern_login_form", clear_on_submit=False):
        st.markdown("""
        <div class="form-header-light">
            <div class="form-title-light">🚀 Accédez à votre espace</div>
        </div>
        """, unsafe_allow_html=True)
        
        email = st.text_input(
            "📧 Adresse email", 
            placeholder="votre@email.com",
            help="Votre email professionnel"
        )
        
        password = st.text_input(
            "🔒 Mot de passe", 
            type="password",
            placeholder="Votre mot de passe sécurisé"
        )
        
        # Options supplémentaires
        col1, col2 = st.columns([1, 1])
        with col1:
            remember_me = st.checkbox("Se souvenir de moi", value=True)
        with col2:
            st.markdown("""
            <div class="forgot-password-light">
                <a href="#" onclick="showPasswordReset()">Mot de passe oublié ?</a>
            </div>
            """, unsafe_allow_html=True)
        
        # Bouton de connexion
        login_button = st.form_submit_button(
            "🚀 Se connecter", 
            use_container_width=True,
            type="primary"
        )
        
        if login_button:
            if not email or not password:
                st.error("❌ Veuillez remplir tous les champs obligatoires")
            else:
                from auth.authentication import auth_system
                with st.spinner("🔍 Vérification de vos identifiants..."):
                    result = auth_system.login(email, password)
                    if result['success']:
                        st.success(f"🎉 Bienvenue {result['user']['name']}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"🚫 {result['message']}")
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <p style="color: #64748b;">Pas encore de compte ? 
        <a href="#" onclick="switchToRegister()" style="color: #3b82f6; text-decoration: none; font-weight: 600;">Créer un compte</a></p>
    </div>
    
    <script>
    function showPasswordReset() {
        alert('Fonctionnalité de réinitialisation de mot de passe - À implémenter');
        return false;
    }
    function switchToRegister() {
        const registerTab = document.querySelector('[data-baseweb="tab"]:nth-child(2)');
        if (registerTab) registerTab.click();
        return false;
    }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_modern_register_form():
    """Affiche le formulaire d'inscription moderne et clair"""
    st.markdown('<div class="form-container-light">', unsafe_allow_html=True)
    
    with st.form("modern_register_form", clear_on_submit=False):
        st.markdown("""
        <div class="form-header-light">
            <div class="form-title-light">🌌 Rejoignez notre communauté</div>
        </div>
        """, unsafe_allow_html=True)

        # Informations personnelles
        st.markdown("""
        <div class="form-section">
            <div class="form-section-title">👤 Informations personnelles</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nom complet *", 
                placeholder="Votre nom et prénom",
                key="register_name"
            )
            email = st.text_input(
                "Email professionnel *", 
                placeholder="votre@institution.cm",
                key="register_email"
            )
        
        with col2:
            institution = st.text_input(
                "Institution *", 
                placeholder="Votre organisation",
                key="register_institution"
            )
            phone = st.text_input(
                "Téléphone", 
                placeholder="+237 XXX XXX XXX",
                key="register_phone"
            )

        # Sécurité
        st.markdown("""
        <div class="form-section">
            <div class="form-section-title">🔒 Sécurité du compte</div>
        </div>
        """, unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            password = st.text_input(
                "Mot de passe *", 
                type="password",
                placeholder="Minimum 8 caractères",
                key="register_password"
            )
        
        with col4:
            confirm_password = st.text_input(
                "Confirmation *", 
                type="password",
                placeholder="Retapez votre mot de passe",
                key="register_confirm_password"
            )

        # Indicateur de force du mot de passe
        if password:
            if len(password) >= 12:
                strength_class = "strength-strong"
                strength_text = "Fort"
            elif len(password) >= 8:
                strength_class = "strength-medium"
                strength_text = "Moyen"
            else:
                strength_class = "strength-weak"
                strength_text = "Faible"
            
            st.markdown(f'<div class="password-strength {strength_class}">🔒 Force du mot de passe: {strength_text}</div>', unsafe_allow_html=True)

        # Domaine d'expertise
        st.markdown("""
        <div class="form-section">
            <div class="form-section-title">🎯 Domaine d'activité</div>
        </div>
        """, unsafe_allow_html=True)
        
        role = st.selectbox(
            "Sélectionnez votre domaine principal *",
            [
                "🌊 Gestion des risques climatiques",
                "🌾 Agriculture et sécurité alimentaire", 
                "🔬 Recherche scientifique",
                "🏛️ Administration publique",
                "🏢 Secteur privé",
                "🌍 ONG et coopération internationale",
                "🎓 Éducation et recherche",
                "🏥 Santé et environnement"
            ],
            key="register_role"
        )

        # Conditions
        st.markdown("""
        <div class="form-section">
            <div class="form-section-title">📄 Conditions d'utilisation</div>
        </div>
        """, unsafe_allow_html=True)
        
        col5, col6 = st.columns([3, 1])
        
        with col5:
            agree_terms = st.checkbox(
                "J'accepte les conditions d'utilisation et la politique de confidentialité *",
                key="register_terms"
            )
            newsletter = st.checkbox(
                "📧 Je souhaite recevoir les alertes importantes et les nouveautés",
                value=True,
                key="register_newsletter"
            )

        # Bouton d'inscription
        register_button = st.form_submit_button(
            "✨ Créer mon compte", 
            use_container_width=True,
            type="primary"
        )
        
        if register_button:
            errors = []
            
            if not all([name, email, institution, password, confirm_password]):
                errors.append("❌ Veuillez remplir tous les champs obligatoires (*)")
            
            if password != confirm_password:
                errors.append("🔒 Les mots de passe ne correspondent pas")
            
            if len(password) < 8:
                errors.append("🔒 Le mot de passe doit contenir au moins 8 caractères")
            
            if not agree_terms:
                errors.append("📄 Veuillez accepter les conditions d'utilisation")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                user_data = {
                    "name": name.strip(),
                    "email": email.lower().strip(),
                    "phone": phone.strip(),
                    "institution": institution.strip(),
                    "password": password,
                    "role": role,
                    "newsletter": newsletter,
                    "registration_date": datetime.now().isoformat()
                }
                
                from auth.authentication import auth_system
                with st.spinner("🎯 Création de votre compte en cours..."):
                    result = auth_system.register(user_data)
                    if result['success']:
                        st.success(f"🎊 {result['message']}")
                        st.balloons()
                    else:
                        st.error(f"🚫 {result['message']}")
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <p style="color: #64748b;">Déjà un compte ? 
        <a href="#" onclick="switchToLogin()" style="color: #3b82f6; text-decoration: none; font-weight: 600;">Se connecter</a></p>
    </div>
    
    <script>
    function switchToLogin() {
        const loginTab = document.querySelector('[data-baseweb="tab"]:first-child');
        if (loginTab) loginTab.click();
        return false;
    }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_modern_verification_form():
    """Affiche le formulaire de vérification moderne et clair"""
    st.markdown('<div class="form-container-light">', unsafe_allow_html=True)
    
    with st.form("modern_verification_form", clear_on_submit=False):
        st.markdown("""
        <div class="form-header-light">
            <div class="form-title-light">🛰️ Vérification de sécurité</div>
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input(
            "📧 Email de vérification", 
            placeholder="votre@email.com",
            key="verify_email"
        )
        
        # Code de vérification
        col1, col2 = st.columns([2, 1])
        with col1:
            verification_code = st.text_input(
                "🔢 Code de vérification *", 
                placeholder="XXXXXX",
                help="Code à 6 chiffres envoyé par email",
                key="verify_code"
            )
        with col2:
            st.markdown('<div class="resend-container-light">', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<p style="color: #64748b; font-size: 0.85rem; text-align: center;">Renvoyer le code ?</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Bouton de vérification
        verify_button = st.form_submit_button(
            "✅ Vérifier mon compte", 
            use_container_width=True,
            type="primary"
        )
        
        if verify_button:
            if not email or not verification_code:
                st.error("❌ Veuillez remplir tous les champs")
            else:
                from auth.authentication import auth_system
                with st.spinner("🔎 Vérification en cours..."):
                    result = auth_system.verify_account(email, verification_code)
                    if result['success']:
                        st.success(f"🎊 {result['message']}")
                        st.balloons()
                    else:
                        st.error(f"🚫 {result['message']}")
    
    # Bouton "Renvoyer le code" fonctionnel en dehors du formulaire
    st.markdown("""
    <div style="text-align: center; margin-top: 1.5rem;">
        <button onclick="resendVerificationCode()" style="
            background: transparent; 
            border: 2px solid #3b82f6; 
            color: #3b82f6; 
            cursor: pointer; 
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 500;
            width: 100%;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.2)';" 
        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">🔄 Renvoyer le code</button>
    </div>
    
    <script>
    function resendVerificationCode() {
        alert('Fonctionnalité de renvoi de code - À implémenter');
    }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_auth_interface():
    """Affiche l'interface d'authentification avec le thème spatial"""
    
    # En-tête de la carte
    st.markdown("""
    <div class="auth-header-light">
        <div class="auth-logo-light">
            <div class="logo-text-light">
                <h1 class="auth-title-light">ONACC Climate Risk Platform</h1>
                <p class="auth-subtitle-light">Plateforme de suivi des risques de catastrophes climatiques</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Onglets modernes
    tab1, tab2, tab3 = st.tabs(["🔐 Connexion", "🚀 Inscription", "✅ Vérification"])
    
    with tab1:
        show_modern_login_form()
    
    with tab2:
        show_modern_register_form()
    
    with tab3:
        show_modern_verification_form()

def handle_authentication():
    """Gère le processus d'authentification"""
    if authenticate_user():
        return True
    
    show_auth_interface()
    return False

def main():
    # Chargement du CSS avec le fond d'espace
    load_css()
    
    # Vérification de l'authentification
    if not handle_authentication():
        return
    
    # Si authentifié, redirection
    st.success("🎉 Authentification réussie! Redirection en cours...")
    st.switch_page("pages/dashboard.py")

if __name__ == "__main__":
    main()