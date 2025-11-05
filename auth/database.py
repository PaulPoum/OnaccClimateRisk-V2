# auth/database.py
import sqlite3
import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path: str = "onacc_users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données et crée la table users si elle n'existe pas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    institution TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    verification_code TEXT,
                    is_verified BOOLEAN DEFAULT FALSE,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Créer un admin par défaut si la table est vide
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] == 0:
                self._create_default_admin()
            
            conn.commit()
            conn.close()
            logger.info("Base de données utilisateurs initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    def _create_default_admin(self):
        """Crée un compte administrateur par défaut"""
        default_password = "onacc2024"
        password_hash = self._hash_password(default_password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (name, email, phone, institution, password_hash, role, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            "Administrateur ONACC",
            "admin@onacc.cm",
            "+237 6XX XXX XXX",
            "ONACC",
            password_hash,
            "admin",
            True
        ))
        
        conn.commit()
        conn.close()
        logger.info("Compte administrateur par défaut créé")
    
    def _hash_password(self, password: str) -> str:
        """Hash le mot de passe avec SHA-256 et salage"""
        salt = "onacc_salt_2024"  # En production, utiliser un sel unique par utilisateur
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_verification_code(self) -> str:
        """Génère un code de vérification à 6 chiffres"""
        return ''.join(secrets.choice('0123456789') for i in range(6))
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel utilisateur dans la base de données"""
        try:
            # Vérifier si l'email existe déjà
            if self.get_user_by_email(user_data['email']):
                return {"success": False, "message": "Un compte avec cet email existe déjà"}
            
            # Générer le code de vérification
            verification_code = self._generate_verification_code()
            
            # Hasher le mot de passe
            password_hash = self._hash_password(user_data['password'])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (name, email, phone, institution, password_hash, verification_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data['name'],
                user_data['email'],
                user_data.get('phone', ''),
                user_data['institution'],
                password_hash,
                verification_code
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Nouvel utilisateur créé: {user_data['email']}")
            
            return {
                "success": True, 
                "user_id": user_id,
                "verification_code": verification_code,
                "message": "Compte créé avec succès. Un code de vérification a été envoyé à votre email."
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return {"success": False, "message": f"Erreur lors de la création du compte: {str(e)}"}
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Récupère un utilisateur par son email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, email, phone, institution, password_hash, 
                       verification_code, is_verified, role, created_at, last_login, is_active
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "phone": user[3],
                    "institution": user[4],
                    "password_hash": user[5],
                    "verification_code": user[6],
                    "is_verified": bool(user[7]),
                    "role": user[8],
                    "created_at": user[9],
                    "last_login": user[10],
                    "is_active": bool(user[11])
                }
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur: {e}")
            return None
    
    def verify_user(self, email: str, verification_code: str) -> bool:
        """Vérifie un utilisateur avec le code de vérification"""
        try:
            user = self.get_user_by_email(email)
            if not user:
                return False
            
            if user['verification_code'] == verification_code:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users 
                    SET is_verified = TRUE, verification_code = NULL 
                    WHERE email = ?
                ''', (email,))
                
                conn.commit()
                conn.close()
                logger.info(f"Utilisateur vérifié: {email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return False
    
    def update_last_login(self, email: str):
        """Met à jour la date de dernière connexion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE email = ?
            ''', (email,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de last_login: {e}")
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authentifie un utilisateur"""
        user = self.get_user_by_email(email)
        
        if not user:
            return {"success": False, "message": "Email ou mot de passe incorrect"}
        
        if not user['is_active']:
            return {"success": False, "message": "Ce compte est désactivé"}
        
        if not user['is_verified']:
            return {"success": False, "message": "Veuillez vérifier votre email avant de vous connecter"}
        
        password_hash = self._hash_password(password)
        if user['password_hash'] == password_hash:
            self.update_last_login(email)
            return {
                "success": True, 
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "institution": user['institution'],
                    "role": user['role']
                }
            }
        else:
            return {"success": False, "message": "Email ou mot de passe incorrect"}
    
    def get_all_users(self):
        """Récupère tous les utilisateurs (pour l'administration)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, email, phone, institution, role, 
                       is_verified, created_at, last_login, is_active
                FROM users ORDER BY created_at DESC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "phone": user[3],
                    "institution": user[4],
                    "role": user[5],
                    "is_verified": bool(user[6]),
                    "created_at": user[7],
                    "last_login": user[8],
                    "is_active": bool(user[9])
                }
                for user in users
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []

# Instance globale de la base de données
user_db = UserDatabase()