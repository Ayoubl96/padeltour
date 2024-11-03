from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.companies import companies
from .routers import auth

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


@app.get("/")
async def root():
    return {"message": "Hello World"}


