"""Simple health and meta endpoints used by monitoring and the bot."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Health(BaseModel):
    status: str

@router.get('/health', response_model=Health)
async def health():
    return Health(status='ok')
