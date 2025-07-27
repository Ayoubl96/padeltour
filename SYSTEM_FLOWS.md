# PadelTour API - System Flows & Process Diagrams

## 📊 Visual System Understanding

This document provides detailed visual flows and diagrams to understand the PadelTour API system processes and data flows.

## 🔄 Complete Tournament Lifecycle Flow

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Company Setup Phase                      │
│                                                             │
│  Company Registration ──▶ Email Verification ──▶ Profile  │
│         │                       │                    │     │
│         ▼                       ▼                    ▼     │
│    • Email/Password        • Click link          • Add courts│
│    • Company name          • Activate account    • Company info│
│    • Auto-generate         • Login enabled       • Upload logo│
│      8-digit login code                                     │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                 Tournament Creation Phase                  │
│                                                             │
│  Create Tournament ──▶ Configure Settings ──▶ Add Players │
│         │                       │                    │     │
│         ▼                       ▼                    ▼     │
│    • Tournament name       • Start/End dates     • Search existing│
│    • Description           • Player count        • Create new│
│    • Upload images         • Court selection     • Import Playtomic│
│    • Full description      • Format settings     • Validate players│
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Player Pairing Phase                     │
│                                                             │
│  Create Couples ──▶ Validate Pairs ──▶ Generate Groups    │
│         │                  │                    │          │
│         ▼                  ▼                    ▼          │
│    • Manual pairing   • Check duplicates   • Auto-balance │
│    • Auto-generation  • Skill levels       • Manual assign│
│    • Player selection • Gender rules       • Group naming │
│    • Couple naming    • Availability       • Fair distribution│
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                Tournament Structure Phase                  │
│                                                             │
│  Stage Creation ──▶ Group Setup ──▶ Bracket Configuration │
│         │                │                    │            │
│         ▼                ▼                    ▼            │
│    • Group stage     • Assign couples    • Elimination    │
│    • Elimination     • Balance groups    • Seeding rules  │
│    • Final stage     • Round robin       • Bracket types  │
│    • Stage order     • Point system      • Advancement    │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Match Generation Phase                   │
│                                                             │
│  Generate Matches ──▶ Schedule Matches ──▶ Court Assignment│
│         │                    │                    │        │
│         ▼                    ▼                    ▼        │
│    • Round robin logic  • Time slots        • Available courts│
│    • Elimination tree   • Court availability • Conflict check│
│    • Fair distribution  • Player schedules  • Optimize usage│
│    • Match sequencing   • Auto-scheduling   • Manual override│
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tournament Execution                    │
│                                                             │
│  Match Play ──▶ Result Entry ──▶ Statistics Update        │
│      │              │                    │                 │
│      ▼              ▼                    ▼                 │
│  • Real-time play • Score entry      • Couple stats       │
│  • Time tracking  • Winner selection • Group standings    │
│  • Court usage    • Match validation • Tournament progress │
│  • Live updates   • Result approval  • Ranking updates    │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Tournament Completion                    │
│                                                             │
│  Final Results ──▶ Reports Generation ──▶ Archive         │
│       │                   │                    │           │
│       ▼                   ▼                    ▼           │
│   • Final rankings    • Match reports      • Save results  │
│   • Champion couple   • Player statistics • Export data    │
│   • Award ceremony   • Tournament summary • Historical data│
│   • Notifications    • Performance metrics• Cleanup       │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
END
```

## 🎾 Match Scheduling Algorithm Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Match Scheduling System                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Input Data   │
              │  Collection   │
              └───────┬───────┘
                      │
                      ▼
        ┌─────────────────────────────────────┐
        │         Available Resources         │
        │  ┌─────────────┐ ┌─────────────┐   │
        │  │   Courts    │ │Time Slots   │   │
        │  │ • Indoor    │ │• Morning    │   │
        │  │ • Outdoor   │ │• Afternoon  │   │
        │  │ • Surface   │ │• Evening    │   │
        │  └─────────────┘ └─────────────┘   │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │        Constraints Analysis         │
        │  ┌─────────────┐ ┌─────────────┐   │
        │  │Player Avail.│ │Court Limits │   │
        │  │• Work hours │ │• Maintenance│   │
        │  │• Preferences│ │• Bookings   │   │
        │  │• Conflicts  │ │• Weather    │   │
        │  └─────────────┘ └─────────────┘   │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │       Scheduling Algorithm          │
        │                                     │
        │  1. Priority Scoring                │
        │     ├── Stage importance            │
        │     ├── Player rankings             │
        │     └── Court preferences           │
        │                                     │
        │  2. Conflict Resolution             │
        │     ├── Time overlaps               │
        │     ├── Court double-booking        │
        │     └── Player availability         │
        │                                     │
        │  3. Optimization                    │
        │     ├── Minimize wait times         │
        │     ├── Balance court usage         │
        │     └── Fair time distribution      │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │         Schedule Output             │
        │  ┌─────────────┐ ┌─────────────┐   │
        │  │   Matches   │ │Notifications│   │
        │  │• Court #    │ │• Players    │   │
        │  │• Start time │ │• Companies  │   │
        │  │• Duration   │ │• Officials  │   │
        │  └─────────────┘ └─────────────┘   │
        └─────────────────────────────────────┘
```

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Web App    │ │  Mobile App  │ │  Admin Panel │      │
│  │              │ │              │ │              │      │
│  │ • Tournament │ │ • Live scores│ │ • Monitoring │      │
│  │   management │ │ • Player     │ │ • Reports    │      │
│  │ • Scheduling │ │   profiles   │ │ • Analytics  │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────┬──────────────┬──────────────┬──────────────┘
              │              │              │
              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                             │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Authentication │  │   Rate Limiting │  │   Logging   │ │
│  │     Middleware  │  │    Middleware   │  │  Middleware │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │      CORS       │  │    Validation   │  │  Error      │ │
│  │   Middleware    │  │   Middleware    │  │  Handling   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Route Handlers                           │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│ │    Auth     │ │  Companies  │ │   Players   │ │ Courts │ │
│ │  /login     │ │    /me      │ │   /search   │ │  /list │ │
│ │  /refresh   │ │  /profile   │ │   /create   │ │ /create│ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│ │Tournaments  │ │   Staging   │ │   Matches   │ │ Stats  │ │
│ │  /create    │ │  /stages    │ │ /schedule   │ │ /live  │ │
│ │  /manage    │ │  /groups    │ │  /results   │ │/summary│ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                      │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│ │ TournamentSvc   │  │ MatchScheduling │  │ PlayerSvc   │  │
│ │ • CRUD ops      │  │ • Auto schedule │  │ • Profiles  │  │
│ │ • Validation    │  │ • Conflict res. │  │ • Search    │  │
│ │ • State mgmt    │  │ • Optimization  │  │ • Playtomic │  │
│ └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│ │   CompanySvc    │  │   EmailSvc      │  │ StorageSvc  │  │
│ │ • Registration  │  │ • Notifications │  │ • File mgmt │  │
│ │ • Multi-tenant  │  │ • Templates     │  │ • Images    │  │
│ │ • Court mgmt    │  │ • Verification  │  │ • Documents │  │
│ └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Repository Layer                           │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│ │ TournamentRepo  │  │   MatchRepo     │  │ StatsRepo   │  │
│ │ • Query build   │  │ • Scheduling    │  │ • Analytics │  │
│ │ • Relationships │  │ • Result track  │  │ • Reports   │  │
│ │ • Filtering     │  │ • Court mgmt    │  │ • Metrics   │  │
│ └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                PostgreSQL Database                      │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ │
│ │ │ Companies   │ │ Tournaments │ │   Players   │       │ │
│ │ │ • Auth data │ │ • Metadata  │ │ • Profiles  │       │ │
│ │ │ • Profiles  │ │ • Stages    │ │ • Stats     │       │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘       │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ │
│ │ │   Matches   │ │   Courts    │ │    Stats    │       │ │
│ │ │ • Schedules │ │ • Locations │ │ • Live data │       │ │
│ │ │ • Results   │ │ • Bookings  │ │ • Trends    │       │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

External Services:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Playtomic  │  │  Supabase   │  │    Loops    │  │   Grafana   │
│     API     │  │   Storage   │  │    Email    │  │ Monitoring  │
│ • Player DB │  │ • Images    │  │ • Templates │  │ • Metrics   │
│ • Stats     │  │ • Documents │  │ • Delivery  │  │ • Alerts    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

## 🔐 Authentication & Security Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Flow                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Client Request│
              │  (Credentials)│
              └───────┬───────┘
                      │
                      ▼
        ┌─────────────────────────────────────┐
        │       Input Validation              │
        │ • Email format check                │
        │ • Password strength                 │
        │ • SQL injection prevention          │
        │ • XSS protection                    │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │     Database Lookup                 │
        │ • Find company by email             │
        │ • Check account status              │
        │ • Verify email confirmation         │
        │ • Load company profile              │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │     Password Verification           │
        │ • bcrypt hash comparison            │
        │ • Timing attack prevention          │
        │ • Failed attempt tracking           │
        │ • Account lockout logic             │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │       Token Generation              │
        │ • JWT access token (30 min)         │
        │ • Refresh token (7 days)            │
        │ • Company ID in payload             │
        │ • Role-based claims                 │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │     Security Headers                │
        │ • CORS configuration                │
        │ • Content Security Policy           │
        │ • Rate limiting                     │
        │ • Request logging                   │
        └─────────────────┬───────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │      Response Delivery              │
        │ • Access token                      │
        │ • Refresh token (HttpOnly)          │
        │ • Company profile                   │
        │ • Session information               │
        └─────────────────────────────────────┘

For Protected Endpoints:
┌─────────────────────────────────────────────────────────────┐
│                Authorization Flow                           │
│                                                             │
│  Request ──▶ Extract Token ──▶ Validate ──▶ Authorize     │
│     │              │              │            │           │
│     ▼              ▼              ▼            ▼           │
│ • Headers      • JWT decode   • Signature  • Company      │
│ • Bearer       • Expiry       • Issuer     • Resource     │
│ • Format       • Claims       • Audience   • Permission   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Multi-Tenant Security                  │   │
│  │ • Each company sees only their data                 │   │
│  │ • Database queries filtered by company_id           │   │
│  │ • Resource ownership validation                     │   │
│  │ • Cross-tenant access prevention                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Real-time Statistics Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Match Result Processing Flow                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Match Completion                          │
│                                                             │
│  User Input ──▶ Validation ──▶ Score Processing            │
│      │              │              │                       │
│      ▼              ▼              ▼                       │
│  • Game scores  • Format check • Set calculation          │
│  • Set scores   • Rule validation • Match winner          │
│  • Match winner • Data integrity • Points allocation      │
│                                                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Statistics Update Chain                     │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Couple Stats    │ │ Group Standings │ │Tournament Progress││
│ │ • Matches played│ │ • Points total  │ │ • Completion %   ││
│ │ • Wins/losses   │ │ • Position      │ │ • Next round     ││
│ │ │ Games won/lost │ │ • Tiebreakers   │ │ • Stage status   ││
│ │ • Points earned │ │ • Qualification │ │ • Schedule update││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Real-time Updates                          │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Live Dashboard  │ │ Player Profiles │ │  Notifications  ││
│ │ • Current scores│ │ • Updated stats │ │ • Result alerts ││
│ │ • Leaderboards  │ │ • New rankings  │ │ • Next matches  ││
│ │ • Match status  │ │ • Achievement   │ │ • Schedule      ││
│ │ • Progress bars │ │   badges        │ │   changes       ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Database Transactions                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             ACID Compliance                         │   │
│  │ • Atomic updates (all or nothing)                   │   │
│  │ • Consistent state (referential integrity)         │   │
│  │ • Isolated transactions (no interference)          │   │
│  │ • Durable commits (permanent storage)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Rollback Scenarios                        │   │
│  │ • Validation failures                               │   │
│  │ • Concurrent modification                           │   │
│  │ • System errors                                     │   │
│  │ • Data integrity violations                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Error Handling & Recovery Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Detection                         │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Request Errors  │ │Business Errors  │ │ System Errors   ││
│ │ • Validation    │ │ • Rule violations│ │ • DB connection ││
│ │ • Authentication│ │ • State conflicts│ │ • External APIs ││
│ │ • Authorization │ │ • Resource limits│ │ • Memory issues ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Error Classification                       │
│                                                             │
│  Critical (500) ──▶ Alert & Log ──▶ Admin Notification     │
│      │                  │                    │             │
│      ▼                  ▼                    ▼             │
│  • System down      • Structured         • Email/SMS      │
│  • Data corruption  • Error details      • Dashboard      │
│  • Security breach  • Stack trace        • Escalation     │
│                                                             │
│  Warning (400-499) ──▶ Log & Respond ──▶ User Feedback    │
│      │                      │                    │         │
│      ▼                      ▼                    ▼         │
│  • Bad requests         • Error message       • Clear msg │
│  • Auth failures        • Suggested fix       • Action    │
│  • Resource not found   • Help links          • Recovery  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Recovery Mechanisms                         │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │   Automatic     │ │   Graceful      │ │   Manual        ││
│ │   Recovery      │ │   Degradation   │ │   Intervention  ││
│ │ • Retry logic   │ │ • Feature flags │ │ • Admin tools   ││
│ │ • Fallback data │ │ • Backup systems│ │ • Data repair   ││
│ │ • Circuit break │ │ • Read-only mode│ │ • Emergency fix ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 📱 API Request/Response Flow

```
Client Request
      │
      ▼
┌─────────────────────────────────────┐
│          Request Pipeline           │
│                                     │
│  CORS Check ──▶ Rate Limit ──▶ Auth│
│      │              │          │   │
│      ▼              ▼          ▼   │
│  • Origin        • Quota     • JWT │
│  • Methods       • Window    • Role│
│  • Headers       • IP track  • Exp │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         Route Resolution            │
│                                     │
│  Path Match ──▶ Method ──▶ Handler  │
│      │             │         │     │
│      ▼             ▼         ▼     │
│  • URL pattern  • GET/POST • Function│
│  • Parameters   • PUT/DEL  • Service│
│  • Validation   • PATCH    • Logic │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        Business Processing          │
│                                     │
│ Validation ──▶ Service ──▶ Database │
│     │            │          │      │
│     ▼            ▼          ▼      │
│ • Schema      • Logic    • Query   │
│ • Rules       • Calc     • Update  │
│ • Transform   • Verify   • Results │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         Response Pipeline           │
│                                     │
│ Format ──▶ Headers ──▶ Logging ──▶ Send│
│   │          │          │         │ │
│   ▼          ▼          ▼         ▼ │
│ • JSON     • Status   • Request  • Client│
│ • Schema   • Cache    • Response • Data │
│ • Filter   • CORS     • Timing   • Code │
└─────────────────────────────────────────┘
```

---

## 🎯 Key Takeaways

### For Developers
1. **Multi-layered Architecture**: Clear separation of concerns with API, Service, Repository, and Data layers
2. **Security First**: JWT authentication, multi-tenant isolation, input validation
3. **Scalable Design**: Service-oriented architecture with external integrations
4. **Monitoring Ready**: Built-in logging, metrics, and Grafana dashboards

### For Business Users
1. **Complete Lifecycle**: From company registration to tournament completion
2. **Automated Scheduling**: Smart match scheduling with conflict resolution
3. **Real-time Updates**: Live statistics and progress tracking
4. **Multi-tenant**: Secure isolation between different companies

### For System Administrators
1. **Error Handling**: Comprehensive error detection and recovery
2. **Performance Monitoring**: Built-in metrics and alerting
3. **Deployment Ready**: Docker, Heroku, and environment configuration
4. **Database Migrations**: Alembic for schema evolution

This visual guide should help you understand the complete flow and architecture of the PadelTour API system!