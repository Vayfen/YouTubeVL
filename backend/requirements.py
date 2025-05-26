# YouTube Organizer - Dépendances Python
# Version 2 : Backend Flask + API YouTube

# === Core Framework ===
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1

# === YouTube API ===
google-api-python-client==2.108.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.1.0
google-auth==2.23.4

# === Base de données ===
SQLAlchemy==2.0.23

# === Utilitaires ===
python-dotenv==1.0.0
requests==2.31.0

# === Développement et debugging ===
python-dateutil==2.8.2

# === Machine Learning (pour Version 3) ===
# scikit-learn==1.3.2
# pandas==2.1.4
# numpy==1.25.2

# === Optionnel : serveur de production ===
# gunicorn==21.2.0
# waitress==2.1.2

# === Sécurité ===
cryptography==41.0.8

# === Logging avancé (optionnel) ===
# colorlog==6.8.0

# INSTALLATION :
# pip install -r requirements.txt

# NOTES DE VERSION :
# - Flask 3.0+ pour les dernières fonctionnalités
# - google-api-python-client pour l'API YouTube v3
# - google-auth-oauthlib pour l'authentification OAuth 2.0
# - SQLAlchemy 2.0+ pour la base de données moderne
# - Flask-CORS pour gérer les requêtes cross-origin
# - python-dotenv pour la gestion des variables d'environnement

# VERSIONS COMPATIBLES :
# Python 3.8+ requis
# Testé avec Python 3.9, 3.10, 3.11

# POUR LE DÉVELOPPEMENT LOCAL :
# pip install -r requirements.txt
# 
# POUR LA PRODUCTION :
# pip install -r requirements.txt gunicorn

# ENVIRONNEMENT VIRTUEL RECOMMANDÉ :
# python -m venv youtube-organizer-env
# source youtube-organizer-env/bin/activate  # Linux/Mac
# youtube-organizer-env\Scripts\activate     # Windows
# pip install -r requirements.txt
