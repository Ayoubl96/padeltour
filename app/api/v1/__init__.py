from fastapi import APIRouter
from app.api.v1.endpoints import auth, companies, players, tournaments, courts, tournament_staging, registration, password_reset, dashboard

api_router = APIRouter()
api_router.include_router(auth.router, prefix="", tags=["Authentication"])
api_router.include_router(registration.router, prefix="/register", tags=["Registration"])
api_router.include_router(password_reset.router, prefix="/password-reset", tags=["Password Reset"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(tournaments.router, prefix="/tournaments", tags=["Tournaments"])
api_router.include_router(tournament_staging.router, prefix="/staging", tags=["Tournament Staging"])
api_router.include_router(courts.router, prefix="/courts", tags=["Courts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"]) 