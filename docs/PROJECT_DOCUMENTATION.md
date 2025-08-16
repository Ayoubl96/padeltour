# PadelTour API - Complete Documentation

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Models & Relationships](#data-models--relationships)
- [API Endpoints](#api-endpoints)
- [Core Flows](#core-flows)
- [Services Architecture](#services-architecture)
- [Setup & Deployment](#setup--deployment)
- [Monitoring & Logging](#monitoring--logging)

## 🏓 Project Overview

**PadelTour API** is a comprehensive FastAPI-based backend system for managing padel tournaments. It provides complete tournament lifecycle management from registration and player management to match scheduling and result tracking.

### Key Features
- 🏢 **Company Management**: Multi-tenant system with company registration and authentication
- 👥 **Player Management**: Player profiles with integration to Playtomic platform
- 🏆 **Tournament Management**: Complete tournament lifecycle with stages, groups, and brackets
- 📅 **Match Scheduling**: Advanced scheduling system with court availability and time management
- 📊 **Statistics Tracking**: Real-time couple statistics and tournament standings
- 🎾 **Court Integration**: Court management with availability tracking
- ✉️ **Email Services**: Automated notifications and verification emails
- 📈 **Monitoring**: Advanced logging and Grafana integration

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
│              (Web App, Mobile App, etc.)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                         │
│                   (app/main.py)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  CORS Middleware │  │ Enhanced Logging │  │ Auth Guard  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (v1)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Auth         │ │ Tournaments  │ │ Players      │      │
│  │ Endpoints    │ │ Endpoints    │ │ Endpoints    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Companies    │ │ Courts       │ │ Staging      │      │
│  │ Endpoints    │ │ Endpoints    │ │ Endpoints    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Service Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Tournament      │  │ Match Scheduling │  │ Player      │ │
│  │ Service         │  │ Service          │  │ Service     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Company         │  │ Email           │  │ Storage     │ │
│  │ Service         │  │ Service         │  │ Service     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Repository Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Tournament      │  │ Match           │  │ Couple Stats│ │
│  │ Repository      │  │ Repository      │  │ Repository  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ PostgreSQL      │  │ Supabase        │  │ Alembic     │ │
│  │ Database        │  │ Storage         │  │ Migrations  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘

External Integrations:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Playtomic API   │  │ Loops Email     │  │ Grafana         │
│ (Player Data)   │  │ Service         │  │ Monitoring      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 💻 Tech Stack

### Backend
- **Framework**: FastAPI 0.111.0
- **Language**: Python 3.8+
- **Database**: PostgreSQL with SQLAlchemy 2.0.36
- **Authentication**: JWT tokens with bcrypt
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **ASGI Server**: Uvicorn

### External Services
- **Storage**: Supabase (file storage)
- **Email**: Loops Email Service
- **Player Data**: Playtomic API integration
- **Monitoring**: Grafana dashboards

### Development Tools
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: Type hints with Pydantic
- **Container**: Docker & Docker Compose
- **Deployment**: Heroku (Procfile included)

## 🗄️ Data Models & Relationships

### Entity Relationship Diagram

```
Companies
├── id (PK)
├── email (unique)
├── name
├── login (8-digit code)
└── vat_number

Players                     Tournaments
├── id (PK)                ├── id (PK)
├── nickname              ├── name
├── email                 ├── company_id (FK)
├── playtomic_id          ├── start_date
├── level                 ├── end_date
└── gender                └── players_number

Tournament Stages           Tournament Groups
├── id (PK)                ├── id (PK)
├── tournament_id (FK)     ├── stage_id (FK)
├── name                   ├── name
├── stage_type             └── config
├── order
└── config

Tournament Couples          Matches
├── id (PK)                ├── id (PK)
├── tournament_id (FK)     ├── tournament_id (FK)
├── first_player_id (FK)   ├── couple1_id (FK)
├── second_player_id (FK)  ├── couple2_id (FK)
└── name                   ├── winner_couple_id (FK)
                          ├── stage_id (FK)
                          ├── group_id (FK)
                          ├── bracket_id (FK)
                          ├── court_id (FK)
                          ├── scheduled_start
                          └── games (JSONB)

Courts                      Couple Stats
├── id (PK)                ├── id (PK)
├── company_id (FK)        ├── tournament_id (FK)
├── name                   ├── couple_id (FK)
├── surface_type           ├── matches_played
└── location              ├── matches_won
                          ├── games_won
                          └── total_points
```

### Relationship Flows

```
Company (1) ──→ (N) Tournaments
Company (1) ──→ (N) Courts
Company (1) ──→ (N) Players (via PlayerCompany)

Tournament (1) ──→ (N) Tournament Stages
Tournament (1) ──→ (N) Tournament Couples
Tournament (1) ──→ (N) Matches

Stage (1) ──→ (N) Groups (for group stages)
Stage (1) ──→ (N) Brackets (for elimination stages)

Player (N) ──→ (N) Tournament Couples (as first or second player)
Court (1) ──→ (N) Matches (scheduling)
```

## 🔗 API Endpoints

### Authentication & Registration
```
POST   /api/v1/login                 # Company authentication
POST   /api/v1/refresh               # Token refresh
POST   /api/v1/register              # Company registration
POST   /api/v1/verify-email          # Email verification
```

### Company Management
```
GET    /api/v1/companies/me          # Get current company profile
PUT    /api/v1/companies/me          # Update company profile
```

### Player Management
```
GET    /api/v1/players               # List players
POST   /api/v1/players               # Create player
GET    /api/v1/players/{id}          # Get player details
PUT    /api/v1/players/{id}          # Update player
DELETE /api/v1/players/{id}          # Delete player
POST   /api/v1/players/search        # Search players
```

### Tournament Management
```
GET    /api/v1/tournaments           # List tournaments
POST   /api/v1/tournaments           # Create tournament
GET    /api/v1/tournaments/{id}      # Get tournament details
PUT    /api/v1/tournaments/{id}      # Update tournament
DELETE /api/v1/tournaments/{id}      # Delete tournament

POST   /api/v1/tournaments/{id}/players    # Add players
POST   /api/v1/tournaments/{id}/couples    # Create couples
GET    /api/v1/tournaments/{id}/couples    # List couples
GET    /api/v1/tournaments/{id}/matches    # List matches
GET    /api/v1/tournaments/{id}/stats      # Tournament statistics
```

### Tournament Staging (Advanced Features)
```
POST   /api/v1/staging/{tournament_id}/stages     # Create stage
GET    /api/v1/staging/{tournament_id}/stages     # List stages
PUT    /api/v1/staging/stages/{stage_id}          # Update stage
DELETE /api/v1/staging/stages/{stage_id}          # Delete stage

POST   /api/v1/staging/stages/{stage_id}/groups       # Create groups
POST   /api/v1/staging/stages/{stage_id}/brackets     # Create brackets
POST   /api/v1/staging/generate-matches/{stage_id}    # Generate matches
```

### Court Management
```
GET    /api/v1/courts               # List courts
POST   /api/v1/courts               # Create court
PUT    /api/v1/courts/{id}          # Update court
DELETE /api/v1/courts/{id}          # Delete court
```

### Match Management
```
GET    /api/v1/matches              # List matches (separate endpoint)
POST   /api/v1/matches/{id}/schedule # Schedule match
POST   /api/v1/matches/{id}/result   # Submit match result
```

## 🔄 Core Flows

### 1. Company Registration & Setup Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Register  │───▶│   Verify    │───▶│   Setup     │───▶│   Ready     │
│   Company   │    │   Email     │    │   Profile   │    │   to Use    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   • Email                • Click           • Add courts         • Create
   • Password             verification      • Company info       tournaments
   • Company name         link              • Upload logo        • Add players
   • Generate login       • Account         • Set preferences    • Start matches
     code (8 digits)      activated
```

### 2. Tournament Creation & Management Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Create    │───▶│   Add       │───▶│   Create    │───▶│   Generate  │
│ Tournament  │    │  Players    │    │  Couples    │    │   Stages    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   • Name & dates         • Search existing   • Pair players      • Group stage
   • Description          • Create new        • Auto-generate     • Elimination
   • Player count         • Import from       • Manual selection   • Bracket setup
   • Company courts       Playtomic          • Validate pairs

        ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
        │  Schedule   │───▶│   Track     │───▶│   Complete  │
        │   Matches   │    │  Results    │    │ Tournament  │
        └─────────────┘    └─────────────┘    └─────────────┘
               │                   │                   │
               ▼                   ▼                   ▼
           • Assign courts        • Enter scores      • Final rankings
           • Set times            • Update stats      • Generate reports
           • Auto-schedule        • Progress stages   • Archive results
```

### 3. Match Scheduling Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Available  │───▶│   Match     │───▶│  Schedule   │
│   Courts    │    │ Generation  │    │   Match     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   • Court list           • Stage matches     • Assign court
   • Time slots           • Group matches     • Set start time
   • Availability         • Bracket matches   • Set duration
                         • Priority rules     • Conflict check

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Match     │───▶│   Update    │───▶│   Stats     │
│  Execution  │    │   Results   │    │   Update    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   • Real-time play       • Game scores       • Couple stats
   • Time tracking        • Set winner        • Group standings
   • Court usage          • Match status      • Tournament progress
```

### 4. Authentication Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Login     │───▶│   Verify    │───▶│   Access    │
│ Credentials │    │ & Generate  │    │   Token     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   • Email/Login          • Check password    • JWT token
   • Password             • Company exists    • Refresh token
                         • Generate tokens    • Protected routes

┌─────────────┐    ┌─────────────┐
│   Token     │───▶│   Logout/   │
│   Refresh   │    │   Expire    │
└─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
   • Refresh token        • Clear tokens
   • New access token     • Session end
   • Extended session
```

## 🛠️ Services Architecture

### Service Layer Structure

```
BaseService (Abstract)
├── TournamentService
│   ├── create_tournament()
│   ├── get_tournaments()
│   ├── add_players()
│   ├── create_couples()
│   └── generate_matches()
│
├── MatchSchedulingService
│   ├── schedule_match()
│   ├── get_available_courts()
│   ├── auto_schedule_round()
│   └── update_match_result()
│
├── PlayerService
│   ├── create_player()
│   ├── search_players()
│   ├── import_from_playtomic()
│   └── update_player()
│
├── CompanyService
│   ├── register_company()
│   ├── verify_email()
│   ├── update_profile()
│   └── manage_courts()
│
├── EmailService
│   ├── send_verification()
│   ├── send_tournament_invite()
│   └── send_match_notification()
│
└── StorageService
    ├── upload_file()
    ├── delete_file()
    └── get_file_url()
```

### Key Service Responsibilities

**TournamentService**
- Tournament CRUD operations
- Player and couple management
- Stage and group creation
- Match generation logic

**MatchSchedulingService**
- Advanced match scheduling algorithms
- Court availability management
- Time conflict resolution
- Automatic scheduling optimization

**PlayerService**
- Player profile management
- Playtomic API integration
- Search and filtering
- Company player relationships

**CompanyService**
- Company registration and authentication
- Profile management
- Court management
- Multi-tenant security

## 🚀 Setup & Deployment

### Local Development Setup

```bash
# 1. Clone and setup environment
git clone <repository>
cd padeltour
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Environment configuration
cp .env.example .env
# Edit .env with your database and service credentials

# 4. Database setup
alembic upgrade head

# 5. Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or individual Docker commands
docker build -t padeltour-api .
docker run -p 8000:8000 padeltour-api
```

### Production Deployment (Heroku)

```bash
# Deploy to Heroku
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
heroku run alembic upgrade head
```

### Environment Variables

```env
# Database
DB_HOST=localhost
DB_NAME=padeltour
DB_USER=postgres
DB_PASSWORD=your-password

# Security
SECRET_KEY=your-jwt-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXP_MINUTES=30
REFRESH_TOKEN_EXP_DAYS=7

# External Services
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET=your-bucket-name

PLAYTOMIC_API_URL=https://api.playtomic.io
PLAYTOMIC_EMAIL=your-playtomic-email
PLAYTOMIC_PASSWORD=your-playtomic-password

# Email Service (Optional)
LOOPS_API_KEY=your-loops-api-key
LOOPS_VERIFICATION_TEMPLATE_ID=template-id
LOOPS_LOGIN_INFO_TEMPLATE_ID=template-id
```

## 📊 Monitoring & Logging

### Grafana Integration

The application includes advanced monitoring with Grafana dashboards:

**Available Dashboards:**
- `api-monitoring.json` - API performance metrics
- `business-metrics.json` - Tournament and user analytics
- `advanced.json` - Detailed system metrics
- `debug.json` - Development debugging
- `simple.json` - Overview dashboard

**Enhanced Logging Features:**
- Structured JSON logging
- Request/response tracking
- Performance metrics
- Error monitoring
- Business event tracking

### Key Metrics Tracked

```
API Metrics:
├── Request rate per endpoint
├── Response times (P50, P95, P99)
├── Error rates by status code
└── Active connections

Business Metrics:
├── Tournament creation rate
├── Match completion rate
├── Player registration trends
└── Company activity

System Metrics:
├── Database query performance
├── Memory usage
├── CPU utilization
└── External API response times
```

### Log Structure

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "padeltour.tournaments",
  "event_type": "tournament_created",
  "message": "Tournament created successfully",
  "extra": {
    "tournament_id": 123,
    "company_id": 45,
    "player_count": 16,
    "duration_ms": 245
  }
}
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt
- **CORS Protection**: Configurable cross-origin policies
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Input Validation**: Pydantic schema validation
- **Multi-tenant Security**: Company-based data isolation

## 📚 Additional Documentation

For more specific topics, see:
- [Company Registration API](docs/COMPANY_REGISTRATION_API_DOCUMENTATION.md)
- [Tournament Staging System](docs/tournament_staging_documentation.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

**PadelTour API** - A comprehensive tournament management solution for padel sports clubs and organizations.