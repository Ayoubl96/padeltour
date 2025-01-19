from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.companies import companies
from .routers import auth
from .routers.court import court
from .routers.tournaments import tournament
from .routers.player import player

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(auth.router)
app.include_router(court.router)
app.include_router(tournament.router)
app.include_router(player.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


