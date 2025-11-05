import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from utils.data_loader import get_climate_data
from utils.drought_calculator import calculate_drought_indicators, assess_drought_risk

class AlertGenerator:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
    
    def generate_alerts_by_group(self, localities_df, analysis_period='30 jours', group_by='region'):
        """
        Génère des alertes groupées par région ou zone agro-écologique
        """
        alerts = []
        
        # Regroupement des localités
        if group_by == 'region':
            groups = localities_df.groupby('region')
            group_name = 'région'
        elif group_by == 'zone':
            groups = localities_df.groupby('zone')
            group_name = 'zone agro-écologique'
        else:
            # Par localité (mode détaillé)
            return self.generate_alerts_for_all_localities(localities_df, analysis_period)
        
        total_groups = len(groups)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (group_name_value, group_localities) in enumerate(groups):
            status_text.text(f"🔍 Analyse de la {group_name} : {group_name_value}...")
            
            try:
                # Générer une alerte pour le groupe
                group_alert = self.generate_group_alert(
                    group_name_value, 
                    group_localities, 
                    analysis_period, 
                    group_by
                )
                if group_alert:
                    alerts.append(group_alert)
                
                # Mettre à jour la barre de progression
                progress_bar.progress((i + 1) / total_groups)
                
            except Exception as e:
                st.error(f"Erreur pour la {group_name} {group_name_value}: {e}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        return alerts
    
    def generate_group_alert(self, group_name, group_localities, analysis_period, group_type):
        """
        Génère une alerte pour un groupe de localités (région ou zone)
        """
        # Échantillonnage stratégique : prendre 3 localités représentatives
        sample_size = min(3, len(group_localities))
        sample_localities = group_localities.sample(n=sample_size, random_state=42)
        
        group_indicators = []
        high_risk_count = 0
        total_risk_score = 0
        
        # Analyser les localités échantillons
        for _, locality in sample_localities.iterrows():
            try:
                climate_data = get_climate_data(
                    locality['latitude'],
                    locality['longitude'], 
                    analysis_period
                )
                
                if climate_data:
                    drought_indicators = calculate_drought_indicators(climate_data)
                    risk_assessment = assess_drought_risk(drought_indicators)
                    
                    group_indicators.append({
                        'localite': locality['localite'],
                        'risk_level': risk_assessment['risk_level'],
                        'risk_score': risk_assessment['risk_score'],
                        'spi': drought_indicators.get('spi_mean', 0),
                        'deficit': drought_indicators.get('precipitation_deficit', 0),
                        'dry_days': drought_indicators.get('consecutive_dry_days', 0)
                    })
                    
                    total_risk_score += risk_assessment['risk_score']
                    if risk_assessment['risk_level'] in ['Élevé', 'Très Élevé']:
                        high_risk_count += 1
                        
            except Exception as e:
                st.warning(f"Erreur pour {locality['localite']}: {e}")
                continue
        
        if not group_indicators:
            return None
        
        # Calcul des indicateurs agrégés du groupe
        avg_risk_score = total_risk_score / len(group_indicators)
        high_risk_ratio = high_risk_count / len(group_indicators)
        
        # Détermination du niveau de risque du groupe
        if high_risk_ratio >= 0.7 or avg_risk_score >= 70:
            group_risk_level = "Très Élevé"
        elif high_risk_ratio >= 0.4 or avg_risk_score >= 50:
            group_risk_level = "Élevé"
        elif high_risk_ratio >= 0.2 or avg_risk_score >= 30:
            group_risk_level = "Modéré"
        else:
            group_risk_level = "Faible"
        
        # Génération du message d'alerte pour le groupe
        alert_message = self.generate_group_ai_alert(
            group_name,
            group_type,
            group_indicators,
            group_risk_level,
            avg_risk_score,
            len(group_localities)
        )
        
        return {
            'groupe_nom': group_name,
            'groupe_type': group_type,
            'localites_echantillon': [ind['localite'] for ind in group_indicators],
            'total_localites': len(group_localities),
            'periode_analyse': analysis_period,
            'date_generation': datetime.now().isoformat(),
            'niveau_risque_groupe': group_risk_level,
            'score_risque_moyen': avg_risk_score,
            'ratio_risque_eleve': high_risk_ratio,
            'indicateurs_echantillon': group_indicators,
            'alerte': alert_message,
            'recommandations_prioritaires': self.generate_group_recommendations(group_risk_level, group_type)
        }
    
    def generate_group_ai_alert(self, group_name, group_type, indicators, risk_level, avg_score, total_localities):
        """
        Génère un message d'alerte pour un groupe avec DeepSeek
        """
        if not self.api_key:
            return self.generate_fallback_group_alert(group_name, group_type, risk_level, avg_score, indicators)
        
        try:
            prompt = self.create_group_alert_prompt(group_name, group_type, indicators, risk_level, avg_score, total_localities)
            response = self.call_deepseek_api(prompt)
            return response
        except Exception as e:
            st.warning(f"API DeepSeek non disponible: {e}")
            return self.generate_fallback_group_alert(group_name, group_type, risk_level, avg_score, indicators)
    
    def create_group_alert_prompt(self, group_name, group_type, indicators, risk_level, avg_score, total_localities):
        """
        Crée le prompt pour l'alerte de groupe
        """
        # Préparation des statistiques du groupe
        spis = [ind['spi'] for ind in indicators]
        deficits = [ind['deficit'] for ind in indicators]
        risk_levels = [ind['risk_level'] for ind in indicators]
        
        avg_spi = sum(spis) / len(spis)
        avg_deficit = sum(deficits) / len(deficits)
        high_risk_count = sum(1 for level in risk_levels if level in ['Élevé', 'Très Élevé'])
        
        prompt = f"""
        En tant qu'expert en gestion des risques de sécheresse, génère une alerte stratégique pour un groupe de localités :

        GROUPE : {group_name}
        TYPE : {group_type}
        NOMBRE DE LOCALITÉS : {total_localities}
        LOCALITÉS ÉCHANTILLONS ANALYSÉES : {', '.join([ind['localite'] for ind in indicators])}

        INDICATEURS MOYENS DU GROUPE :
        - Niveau de risque : {risk_level} (Score moyen: {avg_score:.1f}/100)
        - Indice SPI moyen : {avg_spi:.2f} ({self.get_spi_category(avg_spi)})
        - Déficit pluviométrique moyen : {avg_deficit:.1f}%
        - Localités à haut risque : {high_risk_count}/{len(indicators)} ({high_risk_count/len(indicators)*100:.1f}%)

        RÉPARTITION DES RISQUES DANS L'ÉCHANTILLON :
        {self.format_risk_distribution(risk_levels)}

        STRUCTURE DE L'ALERTE STRATÉGIQUE :
        1. Titre du groupe (max 8 mots)
        2. Évaluation globale (2-3 phrases)
        3. Zones prioritaires (2-3 points)
        4. Actions coordonnées (3-5 points)
        5. Période d'intervention
        6. Niveau d'urgence global

        IMPORTANT :
        - Adopte une perspective stratégique régionale
        - Identifie les patterns communs
        - Propose des actions coordonnées
        - Priorise les interventions
        - Utilise un ton adapté aux décideurs

        Format de réponse :
        TITRE_GROUPE: [titre]
        ÉVALUATION: [description stratégique]
        ZONES_PRIORITAIRES: [liste des priorités]
        ACTIONS_COORDONNÉES: [liste des actions]
        PÉRIODE: [période d'intervention]
        URGENCE: [niveau d'urgence]
        """
        
        return prompt
    
    def generate_fallback_group_alert(self, group_name, group_type, risk_level, avg_score, indicators):
        """
        Génère une alerte de groupe de secours
        """
        risk_templates = {
            'Très Élevé': {
                'titre': f'CRISE - {group_type} {group_name}',
                'evaluation': f'Situation de crise avec un risque moyen de {avg_score:.1f}%. Intervention coordonnée requise.',
                'zones_prioritaires': [
                    'Toute la zone affectée',
                    'Secteurs agricoles prioritaires',
                    'Zones de concentration population'
                ],
                'actions': [
                    'Plan d\'urgence régional activé',
                    'Coordination inter-services renforcée',
                    'Ressources mutualisées',
                    'Communication unifiée'
                ],
                'periode': 'Immédiate - 30 jours',
                'urgence': 'CRITIQUE'
            },
            'Élevé': {
                'titre': f'ALERTE - {group_type} {group_name}',
                'evaluation': f'Risque élevé ({avg_score:.1f}%) nécessitant une action coordonnée.',
                'zones_prioritaires': [
                    'Sous-régions les plus affectées',
                    'Bassins versants critiques'
                ],
                'actions': [
                    'Surveillance renforcée',
                    'Planification des restrictions',
                    'Coordination locale'
                ],
                'periode': '15-45 jours',
                'urgence': 'ÉLEVÉE'
            },
            'Modéré': {
                'titre': f'VIGILANCE - {group_type} {group_name}',
                'evaluation': f'Situation sous surveillance ({avg_score:.1f}%).',
                'zones_prioritaires': [
                    'Points chauds identifiés'
                ],
                'actions': [
                    'Monitoring continu',
                    'Préparation des plans'
                ],
                'periode': '1-2 mois',
                'urgence': 'MODÉRÉE'
            }
        }
        
        template = risk_templates.get(risk_level, risk_templates['Modéré'])
        
        return f"""
        TITRE_GROUPE: {template['titre']}
        ÉVALUATION: {template['evaluation']} Basé sur l'analyse de {len(indicators)} localités échantillons.
        ZONES_PRIORITAIRES: {'; '.join(template['zones_prioritaires'])}
        ACTIONS_COORDONNÉES: {'; '.join(template['actions'])}
        PÉRIODE: {template['periode']}
        URGENCE: {template['urgence']}
        """
    
    def generate_group_recommendations(self, risk_level, group_type):
        """
        Génère des recommandations prioritaires pour le groupe
        """
        recommendations = {
            'Très Élevé': {
                'coordination': 'Activation cellule de crise régionale',
                'communication': 'Alerte unifiée à toute la population',
                'ressources': 'Mobilisation ressources d\'urgence',
                'surveillance': 'Monitoring horaire des indicateurs'
            },
            'Élevé': {
                'coordination': 'Réunion hebdomadaire des acteurs',
                'communication': 'Information ciblée aux agriculteurs',
                'ressources': 'Prépositionnement des ressources',
                'surveillance': 'Surveillance quotidienne renforcée'
            },
            'Modéré': {
                'coordination': 'Point bi-hebdomadaire',
                'communication': 'Bulletin d\'information régulier',
                'ressources': 'Évaluation des stocks',
                'surveillance': 'Monitoring standard'
            },
            'Faible': {
                'coordination': 'Réunion mensuelle',
                'communication': 'Information standard',
                'ressources': 'Maintenance routine',
                'surveillance': 'Contrôle périodique'
            }
        }
        
        return recommendations.get(risk_level, recommendations['Modéré'])
    
    def format_risk_distribution(self, risk_levels):
        """
        Formate la distribution des risques pour le prompt
        """
        from collections import Counter
        counter = Counter(risk_levels)
        total = len(risk_levels)
        
        distribution = []
        for level, count in counter.items():
            percentage = (count / total) * 100
            distribution.append(f"- {level}: {count} localités ({percentage:.1f}%)")
        
        return "\n".join(distribution)
    
    def get_spi_category(self, spi_value):
        """
        Catégorise la valeur SPI
        """
        if spi_value >= 2.0:
            return "Extrêmement humide"
        elif spi_value >= 1.5:
            return "Très humide"
        elif spi_value >= 1.0:
            return "Modérément humide"
        elif spi_value >= -1.0:
            return "Proche de la normale"
        elif spi_value >= -1.5:
            return "Sécheresse modérée"
        elif spi_value >= -2.0:
            return "Sécheresse sévère"
        else:
            return "Sécheresse extrême"

def parse_group_alert_message(alert_text):
    """
    Parse le message d'alerte de groupe en structure organisée
    """
    lines = alert_text.split('\n')
    parsed_alert = {}
    
    for line in lines:
        if line.startswith('TITRE_GROUPE:'):
            parsed_alert['titre_groupe'] = line.replace('TITRE_GROUPE:', '').strip()
        elif line.startswith('ÉVALUATION:'):
            parsed_alert['evaluation'] = line.replace('ÉVALUATION:', '').strip()
        elif line.startswith('ZONES_PRIORITAIRES:'):
            zones_text = line.replace('ZONES_PRIORITAIRES:', '').strip()
            parsed_alert['zones_prioritaires'] = [zone.strip() for zone in zones_text.split(';')]
        elif line.startswith('ACTIONS_COORDONNÉES:'):
            actions_text = line.replace('ACTIONS_COORDONNÉES:', '').strip()
            parsed_alert['actions_coordonnees'] = [action.strip() for action in actions_text.split(';')]
        elif line.startswith('PÉRIODE:'):
            parsed_alert['periode'] = line.replace('PÉRIODE:', '').strip()
        elif line.startswith('URGENCE:'):
            parsed_alert['urgence'] = line.replace('URGENCE:', '').strip()
    
    return parsed_alert

def get_alert_generator():
    """
    Retourne une instance du générateur d'alertes
    """
    return AlertGenerator()