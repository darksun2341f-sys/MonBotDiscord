"""Discord OAuth2 authentication helpers and routes.

This module implements a lightweight OAuth flow for admins to sign in with
Discord. It's modular so you can swap to a different auth provider later.
"""
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.status import HTTP_303_SEE_OTHER
from . import config
from .services import discord_oauth
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory=str(config.BASE_DIR / 'templates'))


@router.get('/auth/login')
async def login_page(request: Request):
    """Render a login page with a Discord OAuth2 button and CSRF state.

    We store a random `state` in the session and include it in the authorize URL
    to guard against CSRF attacks.
    """
    state = discord_oauth.generate_state()
    request.session['oauth_state'] = state
    authorize_url = discord_oauth.build_authorize_url(state=state)
    return templates.TemplateResponse('auth_login.html', {'request': request, 'authorize_url': authorize_url})


@router.get('/auth/callback')
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    """Exchange code, fetch user and guilds, and store auth info in session.

    Security:
    - Validate `state` matches session value.
    - Use server-side token exchange (no secrets in front-end).
    """
    if not code:
        return HTMLResponse('Missing code', status_code=400)
    expected = request.session.pop('oauth_state', None)
    if not expected or state != expected:
        return HTMLResponse('Invalid state (possible CSRF)', status_code=400)

    # Exchange code for token
    token = await discord_oauth.exchange_code(code)
    access_token = token.get('access_token')
    if not access_token:
        return HTMLResponse('Failed to obtain access token', status_code=400)

    # Fetch the user and their guilds
    user = await discord_oauth.get_user(access_token)
    guilds = await discord_oauth.filter_guilds_with_bot_and_perms(access_token)

    # Store minimal user info and allowed guilds in session
    request.session['user'] = {
        'id': user.get('id'),
        'username': f"{user.get('username')}#{user.get('discriminator')}",
    }
    request.session['access_token'] = access_token
    request.session['allowed_guilds'] = guilds
    request.session['authed'] = True

    return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)


def require_auth(request: Request):
    """Require a valid authenticated session for protected API routes."""
    if not request.session.get('authed'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return request.session['user']


@router.get('/dashboard/guilds')
async def guilds_page(request: Request):
    """Render the guild selection page for authenticated users."""
    if not request.session.get('authed'):
        return RedirectResponse(url='/auth/login')
    guilds = request.session.get('allowed_guilds', [])
    return templates.TemplateResponse('guilds.html', {'request': request, 'guilds': guilds})


@router.post('/dashboard/select_guild')
async def select_guild(request: Request, guild_id: str = Form(...)):
    if not request.session.get('authed'):
        return RedirectResponse(url='/auth/login')
    allowed = request.session.get('allowed_guilds', [])
    if not any(g.get('id') == str(guild_id) for g in allowed):
        return HTMLResponse('Guild not allowed', status_code=403)
    request.session['selected_guild'] = str(guild_id)
    return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)
