# auth/authentication.py
import streamlit as st
import re
from typing import Dict, Any, Optional
from .database import user_db
from .email_sender import email_sender
import logging

logger = logging.getLogger(__name__)

class AuthenticationSystem:
    def __init__(self):
        self.session = st.session_state
        
    def is_authenticated(self) -> bool:
        """Vérifie si l'utilisateur est authentifié"""
        return self.session.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Récupère les informations de l'utilisateur connecté"""
        return self.session.get('user')
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Tente de connecter l'utilisateur"""
        result = user_db.authenticate_user(email, password)
        
        if result['success']:
            self.session.authenticated = True
            self.session.user = result['user']
            logger.info(f"Utilisateur connecté: {email}")
        
        return result
    
    def logout(self):
        """Déconnecte l'utilisateur"""
        if 'authenticated' in self.session:
            self.session.authenticated = False
        if 'user' in self.session:
            user_email = self.session.user['email']
            del self.session.user
            logger.info(f"Utilisateur déconnecté: {user_email}")
    
    def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inscrit un nouvel utilisateur"""
        # Validation des données
        validation_result = self._validate_registration_data(user_data)
        if not validation_result['success']:
            return validation_result
        
        # Création de l'utilisateur
        result = user_db.create_user(user_data)
        
        if result['success']:
            # Envoi de l'email de vérification
            email_sent = email_sender.send_verification_email(
                user_data['email'],
                user_data['name'],
                result['verification_code']
            )
            
            if not email_sent:
                logger.warning(f"Email non envoyé pour: {user_data['email']}")
                # On pourrait stocker cela pour réessayer plus tard
        
        return result
    
    def verify_account(self, email: str, verification_code: str) -> Dict[str, Any]:
        """Vérifie un compte utilisateur"""
        if user_db.verify_user(email, verification_code):
            return {"success": True, "message": "Compte vérifié avec succès! Vous pouvez maintenant vous connecter."}
        else:
            return {"success": False, "message": "Code de vérification invalide ou expiré."}
    
    def _validate_registration_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les données d'inscription"""
        
        # Validation du nom
        if len(user_data['name'].strip()) < 2:
            return {"success": False, "message": "Le nom doit contenir au moins 2 caractères"}
        
        # Validation de l'email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, user_data['email']):
            return {"success": False, "message": "Format d'email invalide"}
        
        # Validation du mot de passe
        if len(user_data['password']) < 8:
            return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
        
        # Validation de l'institution
        if len(user_data['institution'].strip()) < 2:
            return {"success": False, "message": "Le nom de l'institution est requis"}
        
        # Validation du téléphone (optionnel mais doit être valide si fourni)
        if user_data.get('phone'):
            phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
            if not re.match(phone_pattern, user_data['phone']):
                return {"success": False, "message": "Format de téléphone invalide"}
        
        return {"success": True}

# Instance globale du système d'authentification
auth_system = AuthenticationSystem()

# Fonctions d'interface Streamlit
def show_login_register():
    """Affiche l'interface de connexion/inscription"""
    
    if auth_system.is_authenticated():
        show_user_profile()
        return True
    
    # Onglets pour connexion/inscription/vérification
    tab1, tab2, tab3 = st.tabs(["🔐 Connexion", "📝 Inscription", "✅ Vérification"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    with tab3:
        show_verification_form()
    
    return False

def show_login_form():
    """Affiche le formulaire de connexion"""
    st.subheader("Connexion à la plateforme")
    
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="votre@email.com")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            login_button = st.form_submit_button("Se connecter", use_container_width=True)
        with col2:
            if st.form_submit_button("🔑 Mot de passe oublié?", use_container_width=True):
                st.info("Fonctionnalité en cours de développement")
        
        if login_button:
            if not email or not password:
                st.error("Veuillez remplir tous les champs")
                return
            
            result = auth_system.login(email, password)
            if result['success']:
                st.success(f"Bienvenue {result['user']['name']}!")
                st.rerun()
            else:
                st.error(result['message'])

def show_register_form():
    """Affiche le formulaire d'inscription"""
    st.subheader("Créer un compte")
    st.info("""
    Pour accéder à la plateforme ONACC, créez un compte avec vos informations professionnelles.
    Un code de vérification vous sera envoyé par email.
    """)
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Nom complet*", placeholder="Votre nom et prénom")
            email = st.text_input("📧 Email professionnel*", placeholder="votre@institution.cm")
            phone = st.text_input("📞 Téléphone", placeholder="+237 XXX XXX XXX")
        
        with col2:
            institution = st.text_input("🏢 Institution*", placeholder="Votre institution/organisation")
            password = st.text_input("🔒 Mot de passe*", type="password", placeholder="Minimum 8 caractères")
            confirm_password = st.text_input("🔒 Confirmer le mot de passe*", type="password", placeholder="Retapez votre mot de passe")
        
        # Sélection du rôle (pour usage futur)
        role = st.selectbox(
            "🎯 Domaine d'activité principal",
            ["Gestion des risques", "Agriculture", "Recherche", "Administration", "Autre"]
        )
        
        agree_terms = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité")
        
        register_button = st.form_submit_button("Créer mon compte", use_container_width=True)
        
        if register_button:
            if not all([name, email, institution, password, confirm_password]):
                st.error("Veuillez remplir tous les champs obligatoires (*)")
                return
            
            if password != confirm_password:
                st.error("Les mots de passe ne correspondent pas")
                return
            
            if not agree_terms:
                st.error("Veuillez accepter les conditions d'utilisation")
                return
            
            user_data = {
                "name": name.strip(),
                "email": email.lower().strip(),
                "phone": phone.strip(),
                "institution": institution.strip(),
                "password": password
            }
            
            result = auth_system.register(user_data)
            if result['success']:
                st.success(result['message'])
                st.balloons()
            else:
                st.error(result['message'])

def show_verification_form():
    """Affiche le formulaire de vérification de compte"""
    st.subheader("Vérification du compte")
    st.info("Entrez votre email et le code de vérification reçu par email")
    
    with st.form("verification_form"):
        email = st.text_input("📧 Email", placeholder="votre@email.com")
        verification_code = st.text_input("🔢 Code de vérification", placeholder="XXXXXX")
        
        verify_button = st.form_submit_button("Vérifier mon compte", use_container_width=True)
        
        if verify_button:
            if not email or not verification_code:
                st.error("Veuillez remplir tous les champs")
                return
            
            result = auth_system.verify_account(email, verification_code)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])

def show_user_profile():
    """Affiche le profil utilisateur et le bouton de déconnexion"""
    user = auth_system.get_current_user()
    
    if user:
        with st.sidebar:
            st.markdown("---")
            st.subheader(f"👤 {user['name']}")
            st.write(f"**Institution:** {user['institution']}")
            st.write(f"**Rôle:** {user['role']}")
            st.write(f"**Email:** {user['email']}")
            
            if st.button("🚪 Déconnexion", use_container_width=True):
                auth_system.logout()
                st.rerun()

def authenticate_user():
    """Fonction principale d'authentification - à utiliser dans main.py"""
    return auth_system.is_authenticated()

def get_current_user():
    """Récupère l'utilisateur actuel"""
    return auth_system.get_current_user()