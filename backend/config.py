"""Application configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Supported Languages
SUPPORTED_LANGUAGES = ['en', 'sn', 'nd', 'sw', 'zu']  # English, Shona, Ndebele, Swahili, Zulu

# External APIs
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
ZOOM_CLIENT_ID = os.environ.get('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.environ.get('ZOOM_CLIENT_SECRET')
ZOOM_ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
