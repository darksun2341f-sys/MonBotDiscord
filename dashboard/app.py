from pathlib import Path
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Load .env manually (project uses this approach)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', '').strip()
if not ADMIN_TOKEN:
    print('⚠️ Warning: ADMIN_TOKEN is not set in .env. Set it to protect the dashboard.')

SECRET_KEY = os.getenv('FLASK_SECRET') or os.urandom(24)

app = Flask(__name__)
app.secret_key = SECRET_KEY

DB_PATH = Path(__file__).parent.parent / 'database' / 'command_config.json'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_config():
    if DB_PATH.exists():
        with open(DB_PATH, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    return {"guilds": {}}


def save_config(data):
    with open(DB_PATH, 'w', encoding='utf-8-sig') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    if not session.get('authed'):
        return redirect(url_for('login'))

    config = load_config()
    guilds = config.get('guilds', {})
    return render_template('index.html', guilds=guilds)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if token and ADMIN_TOKEN and token == ADMIN_TOKEN:
            session['authed'] = True
            return redirect(url_for('index'))
        flash('Token invalide', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/guild/<guild_id>', methods=['GET', 'POST'])
def guild_view(guild_id):
    if not session.get('authed'):
        return redirect(url_for('login'))

    config = load_config()
    guild = config.setdefault('guilds', {}).setdefault(str(guild_id), {'commands': {}})
    commands = guild.get('commands', {})

    if request.method == 'POST':
        # Expect form fields: command names and values like enabled_commandname, role_commandname, channel_commandname
        for key, value in request.form.items():
            if key.startswith('enabled_'):
                cmd = key[len('enabled_'):]
                cmd_settings = commands.setdefault(cmd, {'enabled': True, 'required_role': None, 'required_channel': None})
                cmd_settings['enabled'] = value == 'on' or value.lower() in ('true', '1', 'on')
            elif key.startswith('role_'):
                cmd = key[len('role_'):]
                cmd_settings = commands.setdefault(cmd, {'enabled': True, 'required_role': None, 'required_channel': None})
                cmd_settings['required_role'] = int(value) if value.strip() else None
            elif key.startswith('channel_'):
                cmd = key[len('channel_'):]
                cmd_settings = commands.setdefault(cmd, {'enabled': True, 'required_role': None, 'required_channel': None})
                cmd_settings['required_channel'] = int(value) if value.strip() else None

        save_config(config)
        flash('Sauvegardé', 'success')
        return redirect(url_for('guild_view', guild_id=guild_id))

    return render_template('guild.html', guild_id=guild_id, commands=commands)


if __name__ == '__main__':
    # Run on localhost:8080
    app.run(host='127.0.0.1', port=8080, debug=True)
