from fastapi import APIRouter
from app.api.v1.endpoints import companies, auth, courts, tournaments, players

api_router = APIRouter()

api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(courts.router, prefix="/courts", tags=["courts"])
api_router.include_router(tournaments.router, prefix="/tournaments", tags=["tournaments"])
api_router.include_router(players.router, prefix="/players", tags=["players"]) 