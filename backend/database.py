import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class Database:
    """Gestionnaire de base de données SQLite pour YouTube Organizer"""
    
    def __init__(self, db_path: str = 'youtube_organizer.db'):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Création d'une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        return conn
    
    def init_db(self):
        """Initialisation de la base de données avec création des tables"""
        with self.get_connection() as conn:
            # Table des vidéos
            conn.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    channel_title TEXT,
                    channel_id TEXT,
                    thumbnail_url TEXT,
                    duration TEXT,
                    published_at TEXT,
                    added_to_playlist_at TEXT,
                    category TEXT DEFAULT 'uncategorized',
                    watched BOOLEAN DEFAULT FALSE,
                    watch_time INTEGER DEFAULT 0,
                    tags TEXT,  -- JSON array
                    view_count INTEGER,
                    like_count INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des catégories (pour la future version avec catégorisation automatique)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT DEFAULT '#667eea',
                    auto_generated BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table de l'historique des synchronisations
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    videos_fetched INTEGER,
                    new_videos INTEGER,
                    errors TEXT
                )
            ''')
            
            # Index pour améliorer les performances
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_category ON videos(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_watched ON videos(watched)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_added_date ON videos(added_to_playlist_at)')
            
            # Insertion des catégories par défaut
            default_categories = [
                ('dev', 'Développement personnel', '#667eea'),
                ('electronics', 'Électronique', '#ef6c00'),
                ('ai', 'Intelligence Artificielle', '#7b1fa2'),
                ('design', 'Design', '#2e7d32'),
                ('business', 'Business', '#f57f17'),
                ('uncategorized', 'Non catégorisé', '#999999')
            ]
            
            for cat_id, name, color in default_categories:
                conn.execute('''
                    INSERT OR IGNORE INTO categories (name, description, color)
                    VALUES (?, ?, ?)
                ''', (name, name, color))
            
            conn.commit()
            logger.info("Base de données initialisée avec succès")
    
    def save_video(self, video_data: Dict) -> bool:
        """Sauvegarde d'une vidéo (mise à jour si elle existe déjà)"""
        try:
            with self.get_connection() as conn:
                # Vérification si la vidéo existe déjà
                existing = conn.execute('SELECT id FROM videos WHERE id = ?', (video_data['id'],)).fetchone()
                
                if existing:
                    # Mise à jour des données existantes
                    conn.execute('''
                        UPDATE videos SET
                            title = ?, description = ?, channel_title = ?, channel_id = ?,
                            thumbnail_url = ?, duration = ?, published_at = ?,
                            tags = ?, view_count = ?, like_count = ?, updated_at = ?
                        WHERE id = ?
                    ''', (
                        video_data.get('title'),
                        video_data.get('description'),
                        video_data.get('channel_title'),
                        video_data.get('channel_id'),
                        video_data.get('thumbnail_url'),
                        video_data.get('duration'),
                        video_data.get('published_at'),
                        json.dumps(video_data.get('tags', [])),
                        video_data.get('view_count', 0),
                        video_data.get('like_count', 0),
                        datetime.now().isoformat(),
                        video_data['id']
                    ))
                    return False  # Pas une nouvelle vidéo
                else:
                    # Insertion d'une nouvelle vidéo
                    conn.execute('''
                        INSERT INTO videos (
                            id, title, description, channel_title, channel_id,
                            thumbnail_url, duration, published_at, added_to_playlist_at,
                            tags, view_count, like_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        video_data['id'],
                        video_data.get('title'),
                        video_data.get('description'),
                        video_data.get('channel_title'),
                        video_data.get('channel_id'),
                        video_data.get('thumbnail_url'),
                        video_data.get('duration'),
                        video_data.get('published_at'),
                        video_data.get('added_to_playlist_at', datetime.now().isoformat()),
                        json.dumps(video_data.get('tags', [])),
                        video_data.get('view_count', 0),
                        video_data.get('like_count', 0)
                    ))
                    return True  # Nouvelle vidéo
                    
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la vidéo {video_data.get('id')}: {e}")
            return False
    
    def get_videos(self, category: Optional[str] = None, watched: Optional[bool] = None, 
                   search: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Récupération des vidéos avec filtres optionnels"""
        try:
            query = '''
                SELECT v.*, c.name as category_name, c.color as category_color
                FROM videos v
                LEFT JOIN categories c ON v.category = c.name
                WHERE 1=1
            '''
            params = []
            
            if category and category != 'all':
                query += ' AND v.category = ?'
                params.append(category)
            
            if watched is not None:
                query += ' AND v.watched = ?'
                params.append(watched)
            
            if search:
                query += ' AND (v.title LIKE ? OR v.description LIKE ? OR v.channel_title LIKE ?)'
                search_term = f'%{search}%'
                params.extend([search_term, search_term, search_term])
            
            query += ' ORDER BY v.added_to_playlist_at DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            with self.get_connection() as conn:
                rows = conn.execute(query, params).fetchall()
                
                videos = []
                for row in rows:
                    video = dict(row)
                    # Conversion des tags JSON
                    try:
                        video['tags'] = json.loads(video['tags']) if video['tags'] else []
                    except json.JSONDecodeError:
                        video['tags'] = []
                    
                    videos.append(video)
                
                return videos
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos: {e}")
            return []
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """Récupération d'une vidéo par son ID"""
        try:
            with self.get_connection() as conn:
                row = conn.execute('''
                    SELECT v.*, c.name as category_name, c.color as category_color
                    FROM videos v
                    LEFT JOIN categories c ON v.category = c.name
                    WHERE v.id = ?
                ''', (video_id,)).fetchone()
                
                if row:
                    video = dict(row)
                    try:
                        video['tags'] = json.loads(video['tags']) if video['tags'] else []
                    except json.JSONDecodeError:
                        video['tags'] = []
                    return video
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vidéo {video_id}: {e}")
            return None
    
    def update_video_watched(self, video_id: str, watched: bool) -> bool:
        """Mise à jour du statut "vu" d'une vidéo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE videos SET watched = ?, updated_at = ?
                    WHERE id = ?
                ''', (watched, datetime.now().isoformat(), video_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut watched pour {video_id}: {e}")
            return False
    
    def update_video_category(self, video_id: str, category: str) -> bool:
        """Mise à jour de la catégorie d'une vidéo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE videos SET category = ?, updated_at = ?
                    WHERE id = ?
                ''', (category, datetime.now().isoformat(), video_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la catégorie pour {video_id}: {e}")
            return False
    
    def get_categories(self) -> List[Dict]:
        """Récupération de toutes les catégories"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT c.*, COUNT(v.id) as video_count
                    FROM categories c
                    LEFT JOIN videos v ON c.name = v.category
                    GROUP BY c.id
                    ORDER BY c.name
                ''').fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des catégories: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Récupération des statistiques globales"""
        try:
            with self.get_connection() as conn:
                # Statistiques générales
                total_videos = conn.execute('SELECT COUNT(*) as count FROM videos').fetchone()['count']
                watched_videos = conn.execute('SELECT COUNT(*) as count FROM videos WHERE watched = 1').fetchone()['count']
                unwatched_videos = total_videos - watched_videos
                
                # Statistiques par catégorie
                categories_stats = conn.execute('''
                    SELECT category, COUNT(*) as count
                    FROM videos
                    GROUP BY category
                    ORDER BY count DESC
                ''').fetchall()
                
                # Vidéos récemment ajoutées (7 derniers jours)
                recent_videos = conn.execute('''
                    SELECT COUNT(*) as count
                    FROM videos
                    WHERE added_to_playlist_at >= date('now', '-7 days')
                ''').fetchone()['count']
                
                return {
                    'total_videos': total_videos,
                    'watched_videos': watched_videos,
                    'unwatched_videos': unwatched_videos,
                    'categories_count': len(categories_stats),
                    'recent_videos': recent_videos,
                    'categories_breakdown': [dict(row) for row in categories_stats]
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {}
    
    def log_sync(self, videos_fetched: int, new_videos: int, errors: str = None):
        """Enregistrement d'une synchronisation dans l'historique"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO sync_history (videos_fetched, new_videos, errors)
                    VALUES (?, ?, ?)
                ''', (videos_fetched, new_videos, errors))
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la synchronisation: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """Nettoyage des anciennes données (optionnel)"""
        try:
            with self.get_connection() as conn:
                # Suppression des anciens logs de synchronisation
                conn.execute('''
                    DELETE FROM sync_history
                    WHERE sync_date < date('now', '-' || ? || ' days')
                ''', (days,))
                
                logger.info(f"Nettoyage des données de plus de {days} jours effectué")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
