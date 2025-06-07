from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.core.logging_config import setup_logging, get_logger
from app.core.middleware import LoggingMiddleware

# Setup logging first
setup_logging()
logger = get_logger("padeltour.main")

app = FastAPI(title="PadelTour API")

# Add logging middleware (should be first)
app.add_middleware(LoggingMiddleware)

# CORS middleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Log application startup
logger.info("PadelTour API starting up", extra={"event_type": "app_startup"})

@app.get("/")
async def root():
    logger.info("Root endpoint accessed", extra={"endpoint": "/", "event_type": "endpoint_access"})
    return {"message": "Welcome to PadelTour API"}


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup completed", extra={"event_type": "app_ready"})


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down", extra={"event_type": "app_shutdown"})


# For directly running the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


