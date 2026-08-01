# Dashboard Flask pour MonBotDiscord

Ce dossier contient un petit dashboard Flask pour visualiser et modifier le fichier `database/command_config.json`.

Prérequis

- Python 3.14 (utilisé dans ce projet)
- Dépendances listées dans `requirements.txt` (ajouter Flask si besoin)

Variables d'environnement (dans `.env`)

- `ADMIN_TOKEN`: token simple pour protéger l'accès au dashboard (requis)
- `FLASK_SECRET` (optionnel): secret Flask pour les sessions

Lancer en local

```bash
python -m pip install -r requirements.txt
# Mettre ADMIN_TOKEN=quelquechose dans .env
python dashboard/app.py
```

Puis ouvrir http://127.0.0.1:8080

Notes

- Les changements modifient directement `database/command_config.json`, le bot les chargera la prochaine fois qu'il relira ou modifiera la config.
- La synchronisation Google Sheets se fait via les commandes du bot (`/command-sync-google`, `/command-export-google`) si tu as configuré Google Service Account dans `.env`.
