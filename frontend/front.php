<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Organizer V2 - Connecté à YouTube</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }

        .stat {
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            display: block;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .auth-section {
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
        }

        .auth-section h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .auth-section p {
            margin-bottom: 30px;
            color: #666;
            font-size: 1.1rem;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }

        .btn-success {
            background: #4caf50;
            color: white;
        }

        .btn-success:hover {
            background: #45a049;
        }

        .btn-outline {
            background: transparent;
            color: #667eea;
            border: 2px solid #667eea;
        }

        .btn-outline:hover {
            background: #667eea;
            color: white;
        }

        .btn-outline.active {
            background: #667eea;
            color: white;
        }

        .controls {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: none;
        }

        .controls.visible {
            display: block;
        }

        .control-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 20px;
        }

        .control-row:last-child {
            margin-bottom: 0;
        }

        .search-box {
            flex: 1;
            min-width: 300px;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
        }

        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }

        .sync-section {
            padding: 20px 30px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }

        .sync-info {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }

        .sync-status {
            font-weight: 600;
            color: #1976d2;
        }

        .video-grid {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 24px;
            display: none;
        }

        .video-grid.visible {
            display: grid;
        }

        .video-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid #e9ecef;
        }

        .video-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }

        .video-card.watched {
            opacity: 0.6;
            background: #f8f9fa;
        }

        .video-thumbnail {
            position: relative;
            width: 100%;
            height: 180px;
            background: #000;
            overflow: hidden;
        }

        .video-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .video-duration {
            position: absolute;
            bottom: 8px;
            right: 8px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }

        .video-content {
            padding: 16px;
        }

        .video-title {
            font-size: 16px;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 8px;
            color: #333;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .video-channel {
            color: #666;
            font-size: 14px;
            margin-bottom: 12px;
        }

        .video-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }

        .video-category {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            background: #e9ecef;
            color: #495057;
        }

        .video-date {
            color: #999;
            font-size: 12px;
        }

        .video-actions {
            display: flex;
            gap: 8px;
        }

        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
            border-radius: 6px;
        }

        .btn-watch {
            background: #4caf50;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-watch:hover {
            background: #45a049;
        }

        .btn-mark-watched {
            background: #ff9800;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-mark-watched:hover {
            background: #f57c00;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }

        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 20px;
            border-left: 4px solid #f44336;
        }

        @media (max-width: 768px) {
            body { padding: 10px; }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .stats {
                gap: 20px;
            }
            
            .controls, .sync-section {
                padding: 20px;
            }
            
            .control-row {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-box {
                min-width: auto;
            }
            
            .video-grid {
                padding: 20px;
                grid-template-columns: 1fr;
                gap: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📺 YouTube Organizer V2</h1>
            <p>Vos vidéos "À regarder plus tard" organisées intelligemment</p>
            <div class="stats">
                <div class="stat">
                    <span class="stat-number" id="total-videos">0</span>
                    <span class="stat-label">Vidéos total</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="unwatched-videos">0</span>
                    <span class="stat-label">Non vues</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="categories-count">0</span>
                    <span class="stat-label">Catégories</span>
                </div>
            </div>
        </header>

        <!-- Section d'authentification -->
        <div class="auth-section" id="auth-section">
            <h2>🔐 Connexion à YouTube</h2>
            <p>Connectez-vous avec votre compte Google pour accéder à votre playlist "À regarder plus tard"</p>
            <a href="/auth" class="btn btn-primary">🚀 Se connecter avec Google</a>
        </div>

        <!-- Section de synchronisation -->
        <div class="sync-section" id="sync-section" style="display: none;">
            <div class="sync-info">
                <span class="sync-status" id="sync-status">✅ Connecté à YouTube</span>
                <button class="btn btn-success" id="sync-btn">🔄 Synchroniser les vidéos</button>
                <a href="/logout" class="btn btn-outline">🚪 Se déconnecter</a>
            </div>
        </div>

        <!-- Contrôles de filtrage -->
        <div class="controls" id="controls">
            <div class="control-row">
                <input type="text" class="search-box" placeholder="🔍 Rechercher une vidéo..." id="search-input">
                <button class="btn btn-primary" id="smart-pick">🎯 Choix intelligent</button>
            </div>
            
            <div class="control-row" id="category-filters">
                <!-- Les filtres de catégories seront ajoutés dynamiquement -->
            </div>
            
            <div class="control-row">
                <button class="btn btn-outline status-btn active" data-status="all">Toutes</button>
                <button class="btn btn-outline status-btn" data-status="unwatched">Non vues</button>
                <button class="btn btn-outline status-btn" data-status="watched">Vues</button>
            </div>
        </div>

        <!-- Zone de chargement -->
        <div class="loading" id="loading" style="display: none;">
            <div class="loading-spinner"></div>
            <p>Synchronisation des vidéos en cours...</p>
        </div>

        <!-- Grille des vidéos -->
        <div class="video-grid" id="video-grid">
            <!-- Les vidéos seront générées par JavaScript -->
        </div>

        <!-- État vide -->
        <div class="empty-state" id="empty-state" style="display: none;">
            <div class="empty-state-icon">📭</div>
            <h3>Aucune vidéo trouvée</h3>
            <p>Synchronisez vos vidéos YouTube ou modifiez vos filtres</p>
        </div>

        <!-- Messages d'erreur -->
        <div id="error-container"></div>
    </div>

    <script>
        let videos = [];
        let currentFilter = 'all';
        let currentStatus = 'all';
        let searchTerm = '';
        let isAuthenticated = false;

        // Configuration de l'API
        const API_BASE = window.location.origin + '/api';

        // Initialisation
        document.addEventListener('DOMContentLoaded', () => {
            checkAuthStatus();
            setupEventListeners();
        });

        async function checkAuthStatus() {
            try {
                const response = await fetch(`${API_BASE}/auth-status`);
                const data = await response.json();
                isAuthenticated = data.authenticated;
                
                if (isAuthenticated) {
                    showMainInterface();
                    loadVideos();
                } else {
                    showAuthInterface();
                }
            } catch (error) {
                showError('Erreur de connexion au serveur');
            }
        }

        function showAuthInterface() {
            document.getElementById('auth-section').style.display = 'block';
            document.getElementById('sync-section').style.display = 'none';
            document.getElementById('controls').classList.remove('visible');
            document.getElementById('video-grid').classList.remove('visible');
        }

        function showMainInterface() {
            document.getElementById('auth-section').style.display = 'none';
            document.getElementById('sync-section').style.display = 'block';
            document.getElementById('controls').classList.add('visible');
            document.getElementById('video-grid').classList.add('visible');
        }

        async function syncVideos() {
            const loadingEl = document.getElementById('loading');
            const syncBtn = document.getElementById('sync-btn');
            
            loadingEl.style.display = 'block';
            syncBtn.disabled = true;
            syncBtn.textContent = '🔄 Synchronisation...';
            
            try {
                const response = await fetch(`${API_BASE}/sync-videos`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess(`✅ ${data.videos_synced} vidéos synchronisées !`);
                    loadVideos();
                } else {
                    showError(data.error || 'Erreur lors de la synchronisation');
                }
            } catch (error) {
                showError('Erreur de connexion lors de la synchronisation');
            } finally {
                loadingEl.style.display = 'none';
                syncBtn.disabled = false;
                syncBtn.textContent = '🔄 Synchroniser les vidéos';
            }
        }

        async function loadVideos() {
            try {
                const response = await fetch(`${API_BASE}/videos`);
                videos = await response.json();
                updateCategoryFilters();
                renderVideos();
                updateStats();
            } catch (error) {
                showError('Erreur lors du chargement des vidéos');
            }
        }

        function updateCategoryFilters() {
            const categories = [...new Set(videos.map(v => v.category))].filter(c => c !== 'uncategorized');
            const filtersContainer = document.getElementById('category-filters');
            
            let filtersHTML = '<button class="btn btn-outline filter-btn active" data-category="all">Toutes</button>';
            
            categories.forEach(category => {
                const displayName = category.charAt(0).toUpperCase() + category.slice(1);
                filtersHTML += `<button class="btn btn-outline filter-btn" data-category="${category}">${displayName}</button>`;
            });
            
            filtersContainer.innerHTML = filtersHTML;
            
            // Réattacher les event listeners
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.
