# PadelTour API

A FastAPI application for managing padel tournaments.

## Project Structure

```
app/
├── api/                 # API endpoints
│   └── v1/              # API version 1
│       └── endpoints/   # API route handlers
├── core/                # Core functionality
│   ├── config.py        # Application configuration
│   └── security.py      # Authentication & security
├── db/                  # Database setup and configuration
│   └── database.py      # SQLAlchemy setup
├── models/              # Database models
│   ├── company.py       # Company model
│   ├── court.py         # Court model
│   ├── player.py        # Player models
│   └── tournament.py    # Tournament models
├── schemas/             # Pydantic schemas for validation
├── services/            # Business logic
│   ├── company_service.py
│   ├── court_service.py
│   ├── player_service.py
│   └── tournament_service.py
├── utils/               # Utility functions
└── main.py              # Application entry point
```

## Running the Application

1. Create and activate a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Run database migrations: `alembic upgrade head`
4. Start the server: `uvicorn app.main:app --reload`

## API Documentation

When the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`