Dashboard FastAPI pour MonBotDiscord

Architecture initiale

- `web/` : code web (FastAPI)
  - `app.py` : app entry
  - `config.py` : configuration
  - `db.py` : async DB wiring (SQLModel)
  - `models/` : SQLModel models
  - `api/` : API routers
  - `auth.py` : Discord OAuth placeholder
  - `templates/`, `static/` : frontend assets

Lancer

1) Installer dépendances :

```bash
python -m pip install -r requirements.txt
```

2) Définir variables dans `.env` :

- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`
- `WEB_SECRET`
- `DATABASE_URL` (optionnel)

3) Lancer l'app (dev) :

```bash
uvicorn web.app:app --reload --host 127.0.0.1 --port 8080
```

Prochaine étape

- Implémenter les modèles détaillés pour chaque module
- Ajouter les API routers pour la lecture/écriture des réglages
- Mettre en place le pont entre le bot (Discord) et le dashboard (websocket ou polling)
