"""Base API endpoints for dashboard interactions.

We keep minimal endpoints here; module-specific routers will be added under
`web/api/<module>.py` and included in `web.app` later.
"""
from fastapi import APIRouter, Depends
from ..db import get_engine
from sqlmodel import text

router = APIRouter()

@router.get('/version')
async def version():
    return {"version": "0.1.0"}
