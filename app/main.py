from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .routers import auth
from .routers.court import court
from .routers.companies import companies
from .routers.player import player
from .routers.tournaments import match
from .routers.tournaments import stage
from .routers.tournaments import group
from .routers.tournaments import stats
from .routers.tournaments import stage_actions
from .routers.tournaments import templates
from .routers.tournaments import tournament
from . import models
from .db import engine

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PadelTour API",
    description="API for PadelTour tournament management system",
    version="1.0.0"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add all routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(player.router)
app.include_router(court.router)
app.include_router(tournament.router)
app.include_router(stage.router)
app.include_router(group.router)
app.include_router(stats.router)
app.include_router(match.router)
app.include_router(stage_actions.router)
app.include_router(templates.router)

@app.get("/")
def root():
    return {"message": "Welcome to PadelTour API"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


