from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime
import logging

from config import Config
from database import Database
from youtube_api import YouTubeAPI

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration CORS pour le développement
CORS(app, supports_credentials=True)

# Initialisation des services
config = Config()
db = Database()
youtube_api = YouTubeAPI(config)

@app.route('/')
def index():
    """Page d'accueil - vérification du statut d'authentification"""
    return jsonify({
        'status': 'YouTube Organizer Backend Running',
        'authenticated': 'access_token' in session,
        'version': '2.0'
    })

@app.route('/auth/login')
def login():
    """Initier le processus d'authentification OAuth Google"""
    try:
        auth_url = youtube_api.get_auth_url()
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'URL d'auth: {e}")
        return jsonify({'error': 'Erreur d\'authentification'}), 500

@app.route('/auth/callback')
def auth_callback():
    """Callback OAuth - récupération du token d'accès"""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Code d\'autorisation manquant'}), 400
    
    try:
        # Échange du code contre un token d'accès
        token_info = youtube_api.exchange_code_for_token(code)
        
        # Stockage du token en session
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info.get('refresh_token')
        session['token_expires'] = datetime.now().timestamp() + token_info.get('expires_in', 3600)
        
        logger.info("Authentification réussie")
        
        # Redirection vers le frontend (à adapter selon votre configuration)
        return redirect('http://localhost:3000?auth=success')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'échange du code: {e}")
        return jsonify({'error': 'Erreur lors de l\'authentification'}), 500

@app.route('/auth/logout')
def logout():
    """Déconnexion - suppression de la session"""
    session.clear()
    return jsonify({'message': 'Déconnecté avec succès'})

@app.route('/auth/status')
def auth_status():
    """Vérification du statut d'authentification"""
    authenticated = 'access_token' in session
    token_valid = False
    
    if authenticated:
        token_expires = session.get('token_expires', 0)
        token_valid = datetime.now().timestamp() < token_expires
    
    return jsonify({
        'authenticated': authenticated,
        'token_valid': token_valid,
        'needs_refresh': authenticated and not token_valid
    })

@app.route('/videos/sync')
def sync_videos():
    """Synchronisation des vidéos depuis YouTube"""
    if 'access_token' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Vérification/rafraîchissement du token
        if not youtube_api.is_token_valid(session):
            if not youtube_api.refresh_token(session):
                return jsonify({'error': 'Token expiré, reconnexion nécessaire'}), 401
        
        # Récupération des vidéos de la playlist "Watch Later"
        videos = youtube_api.get_watch_later_videos(session['access_token'])
        
        # Sauvegarde en base de données
        saved_count = 0
        for video in videos:
            if db.save_video(video):
                saved_count += 1
        
        logger.info(f"Synchronisation terminée: {saved_count} nouvelles vidéos")
        
        return jsonify({
            'message': 'Synchronisation réussie',
            'total_videos': len(videos),
            'new_videos': saved_count
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        return jsonify({'error': 'Erreur lors de la synchronisation'}), 500

@app.route('/videos')
def get_videos():
    """Récupération de toutes les vidéos stockées"""
    try:
        # Paramètres de filtrage optionnels
        category = request.args.get('category')
        watched = request.args.get('watched')
        search = request.args.get('search')
        
        videos = db.get_videos(
            category=category,
            watched=watched == 'true' if watched else None,
            search=search
        )
        
        return jsonify({
            'videos': videos,
            'total': len(videos)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

@app.route('/videos/<video_id>/watched', methods=['PUT'])
def update_watched_status(video_id):
    """Mise à jour du statut "vu" d'une vidéo"""
    try:
        data = request.get_json()
        watched = data.get('watched', False)
        
        success = db.update_video_watched(video_id, watched)
        
        if success:
            return jsonify({'message': 'Statut mis à jour'})
        else:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@app.route('/videos/<video_id>/category', methods=['PUT'])
def update_video_category(video_id):
    """Mise à jour de la catégorie d'une vidéo"""
    try:
        data = request.get_json()
        category = data.get('category')
        
        if not category:
            return jsonify({'error': 'Catégorie requise'}), 400
        
        success = db.update_video_category(video_id, category)
        
        if success:
            return jsonify({'message': 'Catégorie mise à jour'})
        else:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@app.route('/stats')
def get_stats():
    """Statistiques globales"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des stats'}), 500

@app.route('/categories')
def get_categories():
    """Liste des catégories utilisées"""
    try:
        categories = db.get_categories()
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des catégories: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne du serveur: {error}")
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    # Initialisation de la base de données
    db.init_db()
    
    # Lancement du serveur de développement
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Démarrage du serveur sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
