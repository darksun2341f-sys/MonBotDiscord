"""Configuration for the web dashboard.

Reads environment variables and exposes typed configuration values.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR.parent / '.env'

# Load .env if present (simple loader compatible with project's approach)
if ENV_PATH.exists():
    with open(ENV_PATH, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

# Secrets and OAuth
SECRET_KEY = os.getenv('WEB_SECRET') or os.getenv('FLASK_SECRET') or 'change-me'
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:8080/auth/callback')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR.parent / "database" / "dashboard.db"}')
DISCORD_BOT_ID = os.getenv('DISCORD_BOT_ID')

# Web
HOST = os.getenv('WEB_HOST', '127.0.0.1')
PORT = int(os.getenv('WEB_PORT', 8080))
DEBUG = os.getenv('WEB_DEBUG', 'false').lower() in ('1', 'true', 'yes')
