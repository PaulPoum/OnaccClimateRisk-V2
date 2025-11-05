# auth/email_sender.py
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import logging
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_config = self._load_smtp_config()
    
    def _load_smtp_config(self) -> Dict[str, Any]:
        """Charge la configuration SMTP depuis les secrets Streamlit"""
        return {
            "smtp_server": st.secrets.get("SMTP_SERVER", "mx-dc03.ewodi.net"),
            "smtp_port": st.secrets.get("SMTP_PORT", 587),
            "sender_email": st.secrets.get("SMTP_EMAIL", "support@onacc.cm"),
            "sender_password": st.secrets.get("SMTP_PASSWORD", "t2sU_cqFtjJ#"),
            "use_tls": st.secrets.get("SMTP_USE_TLS", True),
            "sender_name": "ONACC Plateforme Alerte"
        }
    
    def send_verification_email(self, user_email: str, user_name: str, verification_code: str) -> bool:
        """Envoie un email de vérification"""
        
        subject = "ONACC - Vérification de votre compte"
        
        # Template HTML
        html_content = self._create_verification_email_html(user_name, verification_code)
        
        # Version texte simple
        text_content = self._create_verification_email_text(user_name, verification_code)
        
        return self._send_email_simple(user_email, subject, text_content, html_content)
    
    def _create_verification_email_html(self, user_name: str, verification_code: str) -> str:
        """Crée le contenu HTML de l'email de vérification"""
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vérification de compte ONACC</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px;
                }}
                .container {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px; 
                    border: 1px solid #e1e8ed;
                }}
                .header {{ 
                    background: #1f77b4; 
                    color: white; 
                    padding: 20px; 
                    text-align: center; 
                    border-radius: 10px 10px 0 0; 
                    margin: -20px -20px 20px -20px;
                }}
                .verification-code {{ 
                    background: #1f77b4; 
                    color: white; 
                    padding: 15px; 
                    font-size: 24px; 
                    font-weight: bold; 
                    text-align: center; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                    letter-spacing: 2px;
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 20px; 
                    font-size: 12px; 
                    color: #666; 
                    border-top: 1px solid #e1e8ed;
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌍 ONACC Cameroun</h1>
                    <p>Plateforme de Suivi des Risques Climatiques</p>
                </div>
                
                <h2>Bonjour {user_name},</h2>
                
                <p>Merci de vous être inscrit à la plateforme ONACC de suivi des risques climatiques.</p>
                
                <p><strong>Votre compte a été créé avec succès.</strong> Pour activer votre compte, veuillez utiliser le code de vérification ci-dessous :</p>
                
                <div class="verification-code">
                    {verification_code}
                </div>
                
                <p><strong>Instructions :</strong></p>
                <ol>
                    <li>Retournez sur la plateforme ONACC</li>
                    <li>Rendez-vous dans l'onglet "Vérification du compte"</li>
                    <li>Entrez votre email et le code de vérification ci-dessus</li>
                    <li>Cliquez sur "Vérifier mon compte"</li>
                </ol>
                
                <p><strong>Important : Ce code expirera dans 24 heures.</strong></p>
                
                <p>Cordialement,<br>
                <strong>L'équipe ONACC</strong><br>
                Observatoire National sur les Changements Climatiques<br>
                République du Cameroun</p>
                
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement. Merci de ne pas y répondre.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_verification_email_text(self, user_name: str, verification_code: str) -> str:
        """Crée la version texte de l'email de vérification"""
        return f"""
ONACC - Plateforme de Suivi des Risques Climatiques

Bonjour {user_name},

Merci de vous être inscrit à la plateforme ONACC.

VOTRE CODE DE VÉRIFICATION : {verification_code}

INSTRUCTIONS :
1. Retournez sur la plateforme ONACC
2. Rendez-vous dans l'onglet "Vérification du compte"
3. Entrez votre email et le code de vérification
4. Cliquez sur "Vérifier mon compte"

Ce code expirera dans 24 heures.

Cordialement,
L'équipe ONACC
Observatoire National sur les Changements Climatiques
République du Cameroun

Cet email a été envoyé automatiquement. Merci de ne pas y répondre.
        """
    
    def _send_email_simple(self, recipient: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """Envoie un email avec une méthode simplifiée et robuste"""
        try:
            # Création du message
            msg = MIMEMultipart('alternative')
            
            # En-têtes simples et corrects
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_config['sender_name']} <{self.smtp_config['sender_email']}>"
            msg['To'] = recipient
            
            # Partie texte
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
            
            # Partie HTML si fournie
            if html_content:
                part2 = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(part2)
            
            # Connexion au serveur SMTP
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            
            if self.smtp_config['use_tls']:
                server.starttls()  # Chiffrement TLS
            
            # Authentification
            server.login(self.smtp_config['sender_email'], self.smtp_config['sender_password'])
            
            # Envoi de l'email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email envoyé avec succès à: {recipient}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Erreur d'authentification SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Erreur SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}")
            return False

# Instance globale de l'email sender
email_sender = EmailSender()