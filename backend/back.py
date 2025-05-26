# app.py - Flask application principale
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import sqlite3
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
CORS(app)

# Configuration OAuth Google
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
CLIENT_SECRETS_FILE = "client_secret.json"

# Configuration de la base de données
DATABASE = 'youtube_organizer.db'

def init_db():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            channel_title TEXT,
            duration TEXT,
            published_at TEXT,
            added_at TEXT,
            thumbnail_url TEXT,
            video_url TEXT,
            watched BOOLEAN DEFAULT FALSE,
            category TEXT DEFAULT 'uncategorized',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            credentials TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Obtient une connexion à la base de données"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def parse_youtube_duration(duration):
    """Convertit la durée YouTube (PT4M13S) en format lisible (4:13)"""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return "0:00"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def get_youtube_service():
    """Obtient le service YouTube API avec les credentials de l'utilisateur"""
    if 'credentials' not in session:
        return None
    
    credentials = Credentials.from_authorized_user_info(session['credentials'], SCOPES)
    
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = credentials.to_json()
    
    return build('youtube', 'v3', credentials=credentials)

@app.route('/')
def index():
    """Page d'accueil avec le frontend"""
    return render_template_string(open('frontend/index.html').read())

@app.route('/auth')
def auth():
    """Démarre le processus d'authentification OAuth"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    flow.redirect_uri = url_for('oauth_callback', _external=True)
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth/callback')
def oauth_callback():
    """Callback OAuth après authentification"""
    state = session.get('state')
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = url_for('oauth_callback', _external=True)
    
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('index'))

@app.route('/api/auth-status')
def auth_status():
    """Vérifie le statut d'authentification"""
    return jsonify({
        'authenticated': 'credentials' in session
    })

@app.route('/api/sync-videos', methods=['POST'])
def sync_videos():
    """Synchronise les vidéos de la playlist 'À regarder plus tard'"""
    if 'credentials' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'Impossible de créer le service YouTube'}), 500
        
        # Récupération de la playlist "Watch Later"
        request_playlist = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId='WL',  # WL = Watch Later
            maxResults=50
        )
        
        response = request_playlist.execute()
        videos_data = []
        
        # Récupération des détails des vidéos
        video_ids = [item['contentDetails']['videoId'] for item in response['items']]
        
        if video_ids:
            videos_request = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            )
            videos_response = videos_request.execute()
            
            conn = get_db_connection()
            
            for video in videos_response['items']:
                video_id = video['id']
                snippet = video['snippet']
                content_details = video['contentDetails']
                
                # Vérifier si la vidéo existe déjà
                existing = conn.execute(
                    'SELECT id FROM videos WHERE id = ?', (video_id,)
                ).fetchone()
                
                if not existing:
                    # Insertion nouvelle vidéo
                    conn.execute('''
                        INSERT INTO videos (
                            id, title, description, channel_title, duration,
                            published_at, added_at, thumbnail_url, video_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        video_id,
                        snippet['title'],
                        snippet.get('description', ''),
                        snippet['channelTitle'],
                        parse_youtube_duration(content_details['duration']),
                        snippet['publishedAt'],
                        datetime.now().isoformat(),
                        snippet['thumbnails']['medium']['url'],
                        f"https://www.youtube.com/watch?v={video_id}"
                    ))
                
                videos_data.append({
                    'id': video_id,
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'duration': parse_youtube_duration(content_details['duration']),
                    'thumbnail': snippet['thumbnails']['medium']['url']
                })
            
            conn.commit()
            conn.close()
        
        return jsonify({
            'success': True,
            'videos_synced': len(videos_data),
            'videos': videos_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la synchronisation: {str(e)}'}), 500

@app.route('/api/videos')
def get_videos():
    """Récupère toutes les vidéos stockées"""
    conn = get_db_connection()
    videos = conn.execute('''
        SELECT * FROM videos ORDER BY added_at DESC
    ''').fetchall()
    conn.close()
    
    videos_list = []
    for video in videos:
        videos_list.append({
            'id': video['id'],
            'title': video['title'],
            'description': video['description'],
            'channel': video['channel_title'],
            'duration': video['duration'],
            'published_at': video['published_at'],
            'added_at': video['added_at'],
            'thumbnail_url': video['thumbnail_url'],
            'video_url': video['video_url'],
            'watched': bool(video['watched']),
            'category': video['category']
        })
    
    return jsonify(videos_list)

@app.route('/api/videos/<video_id>/watched', methods=['PUT'])
def toggle_watched(video_id):
    """Bascule le statut 'vu' d'une vidéo"""
    data = request.json
    watched = data.get('watched', False)
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE videos SET watched = ? WHERE id = ?',
        (watched, video_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/videos/<video_id>/category', methods=['PUT'])
def update_category(video_id):
    """Met à jour la catégorie d'une vidéo"""
    data = request.json
    category = data.get('category', 'uncategorized')
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE videos SET category = ? WHERE id = ?',
        (category, video_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    """Récupère les statistiques"""
    conn = get_db_connection()
    
    total_videos = conn.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
    unwatched_videos = conn.execute('SELECT COUNT(*) FROM videos WHERE watched = 0').fetchone()[0]
    categories = conn.execute('SELECT COUNT(DISTINCT category) FROM videos').fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_videos': total_videos,
        'unwatched_videos': unwatched_videos,
        'categories_count': categories
    })

@app.route('/logout')
def logout():
    """Déconnexion utilisateur"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)


# requirements.txt
"""
Flask==2.3.3
flask-cors==4.0.0
google-auth==2.23.3
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
"""

# config.py - Configuration
"""
Instructions pour obtenir les clés API Google:

1. Aller sur https://console.developers.google.com/
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API YouTube Data API v3
4. Créer des identifiants OAuth 2.0 :
   - Type d'application: Application Web
   - URI de redirection autorisés: http://localhost:5000/oauth/callback
5. Télécharger le fichier JSON et le renommer en 'client_secret.json'
6. Placer le fichier dans le même dossier que app.py

Structure du fichier client_secret.json:
{
  "web": {
    "client_id": "votre-client-id",
    "project_id": "votre-projet-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "votre-client-secret",
    "redirect_uris": ["http://localhost:5000/oauth/callback"]
  }
}
"""
