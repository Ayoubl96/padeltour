# Tournament Staging System Documentation

## Overview

The Tournament Staging System allows organizers to structure tournaments with multiple stages (group stages, elimination brackets), manage groups, assign couples to groups, generate matches, and schedule matches on courts. This document provides a comprehensive guide for implementation.

## Core Concepts

- **Stage**: A phase of a tournament (group stage or elimination bracket)
- **Group**: A collection of couples competing against each other in a group stage
- **Bracket**: An elimination structure (main, silver, bronze) for knockout phases
- **Match**: A game between two couples, now enhanced with stage/group/bracket associations

## Data Models

### Tournament Stage

```json
{
  "id": 1,
  "tournament_id": 123,
  "name": "Group Stage",
  "stage_type": "group",
  "order": 1,
  "config": {
    "scoring_system": {
      "type": "points",
      "win": 3,
      "draw": 1,
      "loss": 0,
      "game_win": 1,
      "game_loss": 0
    },
    "match_rules": {
      "matches_per_opponent": 1,
      "games_per_match": 3,
      "win_criteria": "best_of",
      "time_limited": false,
      "time_limit_minutes": 90,
      "break_between_matches": 30
    },
    "advancement_rules": {
      "top_n": 2,
      "to_bracket": "main",
      "tiebreaker": ["points", "head_to_head", "games_diff", "games_won"]
    },
    "scheduling": {
      "auto_schedule": true,
      "overlap_allowed": false,
      "scheduling_priority": "court_efficiency"
    }
  },
  "created_at": "2023-07-20T14:00:00Z",
  "updated_at": "2023-07-20T14:00:00Z",
  "deleted_at": null
}
```

### Tournament Group

```json
{
  "id": 1,
  "stage_id": 1,
  "name": "Group A",
  "created_at": "2023-07-20T14:00:00Z",
  "updated_at": "2023-07-20T14:00:00Z",
  "deleted_at": null
}
```

### Tournament Bracket

```json
{
  "id": 1,
  "stage_id": 2,
  "bracket_type": "main",
  "created_at": "2023-07-20T14:00:00Z",
  "updated_at": "2023-07-20T14:00:00Z",
  "deleted_at": null
}
```

### Match (Extended)

```json
{
  "id": 1,
  "tournament_id": 123,
  "couple1_id": 1,
  "couple2_id": 2,
  "winner_couple_id": null,
  "games": [
    {
      "game_number": 1,
      "couple1_score": 6,
      "couple2_score": 4,
      "winner_id": 1,
      "duration_minutes": 25
    },
    {
      "game_number": 2,
      "couple1_score": 4,
      "couple2_score": 6,
      "winner_id": 2,
      "duration_minutes": 30
    }
  ],
  "stage_id": 1,
  "group_id": 1,
  "bracket_id": null,
  "court_id": 2,
  "scheduled_start": "2023-07-20T15:00:00Z",
  "scheduled_end": "2023-07-20T16:30:00Z",
  "is_time_limited": false,
  "time_limit_minutes": null,
  "match_result_status": "pending",
  "created_at": "2023-07-20T14:00:00Z",
  "updated_at": "2023-07-20T14:00:00Z"
}
```

## API Endpoints

### Stage Management

#### Create a Tournament Stage

```
POST /staging/tournament/{tournament_id}/stage
```

**Request Body:**
```json
{
  "tournament_id": 123,
  "name": "Group Stage",
  "stage_type": "group",
  "order": 1,
  "config": {
    "scoring_system": {
      "type": "points",
      "win": 3,
      "draw": 1,
      "loss": 0,
      "game_win": 1,
      "game_loss": 0
    },
    "match_rules": {
      "matches_per_opponent": 1,
      "games_per_match": 3,
      "win_criteria": "best_of",
      "time_limited": false,
      "time_limit_minutes": 90,
      "break_between_matches": 30
    },
    "advancement_rules": {
      "top_n": 2,
      "to_bracket": "main",
      "tiebreaker": ["points", "head_to_head", "games_diff", "games_won"]
    },
    "scheduling": {
      "auto_schedule": true,
      "overlap_allowed": false,
      "scheduling_priority": "court_efficiency"
    }
  }
}
```

#### Get Tournament Stages

```
GET /staging/tournament/{tournament_id}/stage
```

#### Get Stage by ID

```
GET /staging/stage/{stage_id}
```

#### Update a Stage

```
PUT /staging/stage/{stage_id}
```

**Request Body:**
```json
{
  "name": "Updated Stage Name",
  "config": {
    "scoring_system": {
      "win": 4,
      "draw": 2
    }
  }
}
```

#### Delete a Stage

```
DELETE /staging/stage/{stage_id}
```

### Group Management

#### Create a Group

```
POST /staging/stage/{stage_id}/group
```

**Request Body:**
```json
{
  "stage_id": 1,
  "name": "Group A"
}
```

#### Get Stage Groups

```
GET /staging/stage/{stage_id}/group
```

#### Get Group by ID

```
GET /staging/group/{group_id}
```

#### Update a Group

```
PUT /staging/group/{group_id}
```

**Request Body:**
```json
{
  "name": "Group B"
}
```

#### Delete a Group

```
DELETE /staging/group/{group_id}
```

### Group Couple Assignment

#### Add Couple to Group

```
POST /staging/group/{group_id}/couple
```

**Request Body:**
```json
{
  "group_id": 1,
  "couple_id": 123
}
```

#### Get Group Couples

```
GET /staging/group/{group_id}/couple
```

#### Remove Couple from Group

```
DELETE /staging/group/{group_id}/couple/{couple_id}
```

#### Auto-assign Couples to Groups

```
POST /staging/stage/{stage_id}/assign-couples?method=random
```

Query parameters:
- `method`: `random` or `balanced` (default: `random`)

#### Get Group Standings

```
GET /staging/group/{group_id}/standings
```

**Response:**
```json
{
  "group_id": 1,
  "group_name": "Group A",
  "standings": [
    {
      "couple_id": 1,
      "couple_name": "Team Alpha",
      "matches_played": 3,
      "matches_won": 2,
      "matches_lost": 1,
      "matches_drawn": 0,
      "games_won": 5,
      "games_lost": 2,
      "total_points": 6,
      "games_diff": 3,
      "position": 1
    },
    {
      "couple_id": 2,
      "couple_name": "Team Beta",
      "matches_played": 3,
      "matches_won": 1, 
      "matches_lost": 2,
      "matches_drawn": 0,
      "games_won": 3,
      "games_lost": 4,
      "total_points": 3,
      "games_diff": -1,
      "position": 2
    }
  ]
}
```

### Bracket Management

#### Create a Bracket

```
POST /staging/stage/{stage_id}/bracket
```

**Request Body:**
```json
{
  "stage_id": 2,
  "bracket_type": "main"
}
```

#### Get Stage Brackets

```
GET /staging/stage/{stage_id}/bracket
```

#### Get Bracket by ID

```
GET /staging/bracket/{bracket_id}
```

#### Update a Bracket

```
PUT /staging/bracket/{bracket_id}
```

**Request Body:**
```json
{
  "bracket_type": "silver"
}
```

#### Delete a Bracket

```
DELETE /staging/bracket/{bracket_id}
```

#### Generate Bracket Matches

```
POST /staging/bracket/{bracket_id}/generate-matches
```

Optional request body:
```json
{
  "couples": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

This endpoint:
- Generates bracket matches based on the provided couples or automatically using winners from group stages
- Automatically assigns available courts to all generated matches
- Distributes matches evenly across all courts available for the tournament

### Match Retrieval and Management

#### Get Tournament Matches

```
GET /staging/tournament/{tournament_id}/matches
```

Returns all matches for a specific tournament.

#### Get Stage Matches

```
GET /staging/stage/{stage_id}/matches
```

Returns all matches for a specific stage.

#### Get Group Matches

```
GET /staging/group/{group_id}/matches
```

Returns all matches for a specific group.

#### Get Bracket Matches

```
GET /staging/bracket/{bracket_id}/matches
```

Returns all matches for a specific bracket.

#### Get Match by ID

```
GET /staging/match/{match_id}
```

Returns detailed information about a specific match.

#### Update Match Details

```
PUT /staging/match/{match_id}
```

Updates match details including results, scheduling, and status.

**Request Body:**
```json
{
  "winner_couple_id": 1,
  "games": [
    {
      "game_number": 1,
      "couple1_score": 6,
      "couple2_score": 4,
      "winner_id": 1,
      "duration_minutes": 20
    },
    {
      "game_number": 2,
      "couple1_score": 6,
      "couple2_score": 2,
      "winner_id": 1,
      "duration_minutes": 18
    }
  ],
  "match_result_status": "completed",
  "court_id": 3,
  "scheduled_start": "2023-08-15T14:00:00Z",
  "scheduled_end": "2023-08-15T15:30:00Z",
  "is_time_limited": true,
  "time_limit_minutes": 90
}
```

Note: All fields are optional. Only include the fields you want to update.

### Match Generation and Scheduling

#### Generate Stage Matches (Recommended)

```
POST /staging/stage/{stage_id}/generate-matches
```

This is the recommended endpoint for generating matches. It handles both group stages and elimination stages automatically:

- For group stages: Generates matches for all groups in the stage
- For elimination stages: Generates matches for the main bracket

Optional request body:
```json
{
  "couples": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

Notes:
- The `couples` parameter is only used for elimination stages
- Courts are automatically assigned to matches using an intelligent group-aware algorithm:
  - When there are enough courts, each group gets its own dedicated court
  - When there are more courts than groups, some matches are assigned to extra courts to allow parallel play
  - Groups with more matches get priority for parallel court assignments
  - The system balances court usage to keep all groups progressing at similar rates
- For bracket matches, courts are assigned in a round-robin fashion

#### Generate Group Matches (Legacy)

```
POST /staging/group/{group_id}/generate-matches
```

This endpoint is maintained for backward compatibility. It now calls the stage-level endpoint internally.

#### Generate Bracket Matches (Legacy)

```
POST /staging/bracket/{bracket_id}/generate-matches
```

This endpoint is maintained for backward compatibility. It now calls the stage-level endpoint internally.

Optional request body:
```json
{
  "couples": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

#### Schedule a Match

```
POST /staging/match/{match_id}/schedule?court_id=1&start_time=2023-07-20T15:00:00Z&end_time=2023-07-20T16:30:00Z&is_time_limited=false
```

Query parameters:
- `court_id`: ID of the court
- `start_time`: ISO format start time
- `end_time`: (optional) ISO format end time
- `is_time_limited`: (optional) boolean, default `false`
- `time_limit_minutes`: (optional) integer

#### Unschedule a Match

```
DELETE /staging/match/{match_id}/schedule
```

#### Get Court Availability

```
GET /staging/tournament/{tournament_id}/court-availability?date=2023-07-20
```

**Response:**
```json
[
  {
    "court_id": 1,
    "court_name": "Court 1",
    "day_availability": {
      "start": "2023-07-20T09:00:00Z",
      "end": "2023-07-20T21:00:00Z"
    },
    "scheduled_matches": [
      {
        "match_id": 1,
        "start": "2023-07-20T10:00:00Z",
        "end": "2023-07-20T11:30:00Z",
        "couple1_id": 1,
        "couple2_id": 2
      }
    ],
    "free_slots": [
      {
        "start": "2023-07-20T09:00:00Z",
        "end": "2023-07-20T10:00:00Z"
      },
      {
        "start": "2023-07-20T11:30:00Z",
        "end": "2023-07-20T21:00:00Z"
      }
    ]
  }
]
```

#### Auto-schedule Matches

```
POST /staging/tournament/{tournament_id}/auto-schedule
```

Two scheduling modes are available:

1. **Time-based Scheduling** - assigns specific start/end times to matches:

Query parameters:
- `start_date`: Required for time-based scheduling. Date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
- `end_date`: Optional end date in ISO format
- `order_only`: Set to `false` (default)

2. **Order-only Scheduling** - assigns courts and sequence order without specific times:

Query parameters:
- `order_only`: Set to `true`
- `start_date` and `end_date` are not required

Notes:
- Order-only scheduling is automatically used if matches don't have time limits configured
- Order-only scheduling is suitable when match durations are variable or unknown
- Time-based scheduling requires time limits to be configured in the stage's match rules

**Time-based Example:**
```
POST /staging/tournament/1/auto-schedule?start_date=2023-07-20&end_date=2023-07-21
```

**Order-only Example:**
```
POST /staging/tournament/1/auto-schedule?order_only=true
```

## Common Workflows

### Creating a Full Tournament with Group Stage and Elimination

1. **Create the tournament**
   ```
   POST /tournaments/
   ```

2. **Create a group stage**
   ```
   POST /staging/tournament/{tournament_id}/stage
   ```
   With stage_type = "group" and order = 1

3. **Create groups within the stage**
   ```
   POST /staging/stage/{stage_id}/group
   ```
   Repeat for each group (A, B, C, etc.)

4. **Assign couples to groups**
   Either manually:
   ```
   POST /staging/group/{group_id}/couple
   ```
   Or automatically:
   ```
   POST /staging/stage/{stage_id}/assign-couples
   ```

5. **Generate matches for the stage**
   ```
   POST /staging/stage/{stage_id}/generate-matches
   ```
   This generates matches for all groups in the stage and automatically assigns courts.

6. **Create an elimination stage**
   ```
   POST /staging/tournament/{tournament_id}/stage
   ```
   With stage_type = "elimination" and order = 2

7. **Generate matches for the elimination stage**
   ```
   POST /staging/stage/{stage_id}/generate-matches
   ```
   This automatically:
   - Uses the winners from the group stage
   - Creates the main bracket if needed
   - Assigns courts to all generated matches

8. **Schedule matches**
   Either manually:
   ```
   POST /staging/match/{match_id}/schedule
   ```
   Or automatically:
   ```
   POST /staging/tournament/{tournament_id}/auto-schedule
   ```

### Managing Match Results

1. **View all matches for a tournament**
   ```
   GET /staging/tournament/{tournament_id}/matches
   ```

2. **View matches for a specific stage**
   ```
   GET /staging/stage/{stage_id}/matches
   ```

3. **View matches for a specific group**
   ```
   GET /staging/group/{group_id}/matches
   ```

4. **View matches for a specific bracket**
   ```
   GET /staging/bracket/{bracket_id}/matches
   ```

5. **Get details for a specific match**
   ```
   GET /staging/match/{match_id}
   ```

6. **Update match results**
   ```
   PUT /staging/match/{match_id}
   ```
   With a JSON body containing the games played and scores, plus the match_result_status

7. **View updated group standings after matches**
   ```
   GET /staging/group/{group_id}/standings
   ```

### Tournament Stage Configuration Options

## Court Assignment Logic

The system uses an intelligent algorithm for court assignments during match generation:

### Group Stage Court Assignment

1. **One Court Per Group (when possible)**
   - When there are enough courts, each group is assigned its own dedicated court
   - This keeps all matches for the same group on the same court for convenience

2. **Parallel Play Optimization**
   - When there are more courts than groups, the system enables parallel play
   - Groups with more matches get priority for parallel court assignments
   - Every other match from larger groups gets assigned to extra courts
   - This maintains similar timeline progression for all groups

3. **Court Sharing**
   - When there are more groups than courts, multiple groups share courts
   - Groups are distributed evenly across available courts

### Elimination/Bracket Stage Court Assignment

For bracket matches, courts are assigned in a round-robin fashion to distribute matches evenly across all available courts.