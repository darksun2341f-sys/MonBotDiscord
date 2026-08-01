"""API routes for registered dashboard plugins."""
from fastapi import APIRouter
from ..plugins.base import plugins

router = APIRouter()

@router.get('/plugins')
async def list_plugins():
    return [plugin.__dict__ for plugin in plugins]
