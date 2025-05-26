import os
from typing import Dict, List

class Config:
    """Configuration centralisée pour l'application"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Chargement de la configuration depuis les variables d'environnement"""
        
        # Configuration OAuth Google
        self.GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
        self.GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
        self.GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        # Scopes YouTube nécessaires
        self.YOUTUBE_SCOPES = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
        # URLs Google OAuth
        self.GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
        self.GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
        self.GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
        
        # Configuration YouTube API
        self.YOUTUBE_API_BASE_URL = 'https://www.googleapis.com/youtube/v3'
        self.MAX_VIDEOS_PER_REQUEST = 50  # Limite YouTube API
        
        # Configuration base de données
        self.DATABASE_PATH = os.environ.get('DATABASE_PATH', 'youtube_organizer.db')
        
        # Configuration Flask
        self.FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
        
        # Validation de la configuration critique
        self.validate_config()
    
    def validate_config(self):
        """Validation des paramètres critiques"""
        missing_vars = []
        
        if not self.GOOGLE_CLIENT_ID:
            missing_vars.append('GOOGLE_CLIENT_ID')
        
        if not self.GOOGLE_CLIENT_SECRET:
            missing_vars.append('GOOGLE_CLIENT_SECRET')
        
        if missing_vars:
            raise ValueError(
                f"Variables d'environnement manquantes: {', '.join(missing_vars)}\n"
                "Consultez le README.md pour la configuration OAuth Google"
            )
    
    def get_oauth_params(self) -> Dict[str, str]:
        """Paramètres pour la requête OAuth"""
        return {
            'client_id': self.GOOGLE_CLIENT_ID,
            'client_secret': self.GOOGLE_CLIENT_SECRET,
            'redirect_uri': self.GOOGLE_REDIRECT_URI,
            'scope': ' '.join(self.YOUTUBE_SCOPES),
            'response_type': 'code',
            'access_type': 'offline',  # Pour obtenir un refresh token
            'prompt': 'consent'  # Force l'affichage de l'écran de consentement
        }
    
    def get_token_exchange_params(self, code: str) -> Dict[str, str]:
        """Paramètres pour l'échange code -> token"""
        return {
            'client_id': self.GOOGLE_CLIENT_ID,
            'client_secret': self.GOOGLE_CLIENT_SECRET,
            'redirect_uri': self.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
            'code': code
        }
    
    def get_refresh_token_params(self, refresh_token: str) -> Dict[str, str]:
        """Paramètres pour le rafraîchissement du token"""
        return {
            'client_id': self.GOOGLE_CLIENT_ID,
            'client_secret': self.GOOGLE_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
    
    @property
    def is_development(self) -> bool:
        """Vérification si on est en mode développement"""
        return self.FLASK_ENV == 'development'
    
    @property
    def cors_origins(self) -> List[str]:
        """Origines autorisées pour CORS"""
        if self.is_development:
            return ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080']
        else:
            # En production, spécifiez votre domaine
            return [os.environ.get('FRONTEND_URL', 'https://votre-domaine.com')]
    
    def __repr__(self):
        """Représentation sécurisée de la configuration (sans les secrets)"""
        return f"""Config(
    GOOGLE_CLIENT_ID={'*' * 10 if self.GOOGLE_CLIENT_ID else 'None'},
    GOOGLE_REDIRECT_URI={self.GOOGLE_REDIRECT_URI},
    DATABASE_PATH={self.DATABASE_PATH},
    FLASK_ENV={self.FLASK_ENV}
)"""
