"""
YouTube API Manager - Gestion de la connexion et récupération des données YouTube
Gère l'authentification OAuth 2.0 et la récupération de la playlist "À regarder plus tard"
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration des scopes YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeAPI:
    """Gestionnaire principal pour l'API YouTube"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialise le gestionnaire YouTube API
        
        Args:
            credentials_file: Chemin vers le fichier credentials.json de Google
            token_file: Chemin vers le fichier de stockage du token d'accès
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """
        Authentifie l'utilisateur avec Google OAuth 2.0
        
        Returns:
            bool: True si l'authentification réussit, False sinon
        """
        try:
            # Charge les credentials existants
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )
            
            # Vérifie si les credentials sont valides
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Renouvelle le token
                    logger.info("Renouvellement du token d'accès...")
                    self.credentials.refresh(Request())
                else:
                    # Nouvelle authentification nécessaire
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Fichier credentials.json non trouvé : {self.credentials_file}")
                        return False
                    
                    logger.info("Nouvelle authentification requise...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Sauvegarde les credentials
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Initialise le service YouTube
            self.service = build('youtube', 'v3', credentials=self.credentials)
            logger.info("Authentification YouTube réussie !")
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'authentification : {e}")
            return False
    
    def get_watch_later_playlist_id(self) -> Optional[str]:
        """
        Récupère l'ID de la playlist "À regarder plus tard"
        
        Returns:
            str: ID de la playlist ou None si erreur
        """
        try:
            # Récupère les playlists de l'utilisateur
            request = self.service.playlists().list(
                part="id,snippet",
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            # Cherche la playlist "Watch Later"
            for playlist in response.get('items', []):
                if playlist['snippet']['title'] == 'Watch Later':
                    return playlist['id']
            
            # Si pas trouvée dans les playlists custom, utilise l'ID spécial
            # "WL" est l'ID spécial pour "Watch Later" de YouTube
            return "WL"
            
        except HttpError as e:
            logger.error(f"Erreur lors de la récupération de la playlist : {e}")
            return None
    
    def get_watch_later_videos(self, max_results: int = 50) -> List[Dict]:
        """
        Récupère les vidéos de la playlist "À regarder plus tard"
        
        Args:
            max_results: Nombre maximum de vidéos à récupérer
            
        Returns:
            List[Dict]: Liste des vidéos avec leurs métadonnées
        """
        if not self.service:
            logger.error("Service YouTube non initialisé. Authentifiez-vous d'abord.")
            return []
        
        try:
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                # Calcule le nombre de résultats pour cette requête
                page_size = min(50, max_results - len(videos))
                
                # Requête pour récupérer les éléments de la playlist
                request = self.service.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId="WL",  # Watch Later playlist ID
                    maxResults=page_size,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                if not response.get('items'):
                    break
                
                # Extrait les IDs des vidéos
                video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
                
                # Récupère les détails des vidéos (durée, statistiques, etc.)
                video_details = self._get_video_details(video_ids)
                
                # Combine les données
                for item in response['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_detail = video_details.get(video_id, {})
                    
                    video_data = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                        'channel_name': item['snippet']['channelTitle'],
                        'channel_id': item['snippet']['channelId'],
                        'published_at': item['snippet']['publishedAt'],
                        'added_to_playlist_at': item['snippet']['publishedAt'],
                        'duration': video_detail.get('duration', 'PT0S'),
                        'view_count': int(video_detail.get('view_count', 0)),
                        'like_count': int(video_detail.get('like_count', 0)),
                        'tags': video_detail.get('tags', []),
                        'category_id': video_detail.get('category_id', ''),
                        'watched': False,  # Par défaut, non vue
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    videos.append(video_data)
                
                # Vérifie s'il y a une page suivante
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Récupéré {len(videos)} vidéos de la playlist 'À regarder plus tard'")
            return videos
            
        except HttpError as e:
            logger.error(f"Erreur lors de la récupération des vidéos : {e}")
            return []
    
    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict]:
        """
        Récupère les détails complets des vidéos
        
        Args:
            video_ids: Liste des IDs de vidéos
            
        Returns:
            Dict: Dictionnaire avec les détails de chaque vidéo
        """
        try:
            # YouTube API limite à 50 IDs par requête
            details = {}
            
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                
                request = self.service.videos().list(
                    part="contentDetails,statistics,snippet",
                    id=','.join(batch_ids)
                )
                response = request.execute()
                
                for video in response.get('items', []):
                    video_id = video['id']
                    details[video_id] = {
                        'duration': video['contentDetails'].get('duration', 'PT0S'),
                        'view_count': video['statistics'].get('viewCount', '0'),
                        'like_count': video['statistics'].get('likeCount', '0'),
                        'tags': video['snippet'].get('tags', []),
                        'category_id': video['snippet'].get('categoryId', ''),
                        'default_language': video['snippet'].get('defaultLanguage', ''),
                        'default_audio_language': video['snippet'].get('defaultAudioLanguage', '')
                    }
            
            return details
            
        except HttpError as e:
            logger.error(f"Erreur lors de la récupération des détails : {e}")
            return {}
    
    def parse_duration(self, duration: str) -> int:
        """
        Convertit une durée ISO 8601 (PT4M13S) en secondes
        
        Args:
            duration: Durée au format ISO 8601
            
        Returns:
            int: Durée en secondes
        """
        try:
            # Supprime 'PT' du début
            duration = duration[2:]
            
            hours = 0
            minutes = 0
            seconds = 0
            
            # Parse heures
            if 'H' in duration:
                h_index = duration.index('H')
                hours = int(duration[:h_index])
                duration = duration[h_index+1:]
            
            # Parse minutes
            if 'M' in duration:
                m_index = duration.index('M')
                minutes = int(duration[:m_index])
                duration = duration[m_index+1:]
            
            # Parse secondes
            if 'S' in duration:
                s_index = duration.index('S')
                seconds = int(duration[:s_index])
            
            return hours * 3600 + minutes * 60 + seconds
            
        except (ValueError, IndexError):
            logger.warning(f"Impossible de parser la durée : {duration}")
            return 0
    
    def format_duration(self, seconds: int) -> str:
        """
        Formate une durée en secondes vers MM:SS ou HH:MM:SS
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            str: Durée formatée
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def get_channel_info(self, channel_id: str) -> Dict:
        """
        Récupère les informations d'une chaîne YouTube
        
        Args:
            channel_id: ID de la chaîne
            
        Returns:
            Dict: Informations de la chaîne
        """
        try:
            request = self.service.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'name': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'thumbnail': channel['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                    'video_count': int(channel['statistics'].get('videoCount', 0))
                }
            
            return {}
            
        except HttpError as e:
            logger.error(f"Erreur lors de la récupération des infos de chaîne : {e}")
            return {}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Recherche des vidéos YouTube
        
        Args:
            query: Terme de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            List[Dict]: Liste des vidéos trouvées
        """
        try:
            request = self.service.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order="relevance"
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'channel_name': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt']
                })
            
            return videos
            
        except HttpError as e:
            logger.error(f"Erreur lors de la recherche : {e}")
            return []

# Fonction utilitaire pour tester la connexion
def test_youtube_api():
    """Fonction de test pour vérifier la connexion YouTube"""
    api = YouTubeAPI()
    
    print("🔐 Test d'authentification YouTube...")
    if api.authenticate():
        print("✅ Authentification réussie !")
        
        print("\n📺 Récupération des vidéos 'À regarder plus tard'...")
        videos = api.get_watch_later_videos(max_results=5)
        
        if videos:
            print(f"✅ {len(videos)} vidéos récupérées !")
            for i, video in enumerate(videos[:3], 1):
                duration_seconds = api.parse_duration(video['duration'])
                duration_formatted = api.format_duration(duration_seconds)
                print(f"{i}. {video['title'][:50]}... ({duration_formatted})")
        else:
            print("❌ Aucune vidéo trouvée")
    else:
        print("❌ Échec de l'authentification")

if __name__ == "__main__":
    test_youtube_api()
