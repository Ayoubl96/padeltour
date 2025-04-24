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

Optional request body (if not using automatic advancement from group stage):
```json
{
  "couples": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

### Match Generation and Scheduling

#### Generate Group Matches

```
POST /staging/group/{group_id}/generate-matches
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
POST /staging/tournament/{tournament_id}/auto-schedule?start_date=2023-07-20&end_date=2023-07-21
```

Query parameters:
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: (optional) End date (YYYY-MM-DD)

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

5. **Generate matches for each group**
   ```
   POST /staging/group/{group_id}/generate-matches
   ```
   Repeat for each group

6. **Create an elimination stage**
   ```
   POST /staging/tournament/{tournament_id}/stage
   ```
   With stage_type = "elimination" and order = 2

7. **Generate bracket matches**
   ```
   POST /staging/bracket/{bracket_id}/generate-matches
   ```
   This automatically uses the winners from the group stage

8. **Schedule matches**
   Either manually:
   ```
   POST /staging/match/{match_id}/schedule
   ```
   Or automatically:
   ```
   POST /staging/tournament/{tournament_id}/auto-schedule
   ```

### Tournament Stage Configuration Options

#### Scoring System
- `type`: Scoring method (`points`, `games`, `both`)
- `win`: Points for win (default: 3)
- `draw`: Points for draw (default: 1)
- `loss`: Points for loss (default: 0)
- `game_win`: Points per game won (default: 1)
- `game_loss`: Points per game lost (default: 0)

#### Match Rules
- `matches_per_opponent`: Number of matches against each opponent (default: 1)
- `games_per_match`: Number of games per match (default: 3)
- `win_criteria`: How to determine the winner (`best_of`, `all_games`, `time_based`)
- `time_limited`: Whether matches have a time limit (default: false)
- `time_limit_minutes`: Duration of time-limited matches (default: 90)
- `break_between_matches`: Minutes between matches (default: 30)

#### Advancement Rules
- `top_n`: Number of couples to advance from each group (default: 2)
- `to_bracket`: Bracket type to advance to (`main`, `silver`, `bronze`)
- `tiebreaker`: Array of tiebreaker methods in order of application

#### Scheduling Options
- `auto_schedule`: Whether to auto-schedule matches (default: true)
- `overlap_allowed`: Whether to allow overlapping matches (default: false)
- `scheduling_priority`: Scheduling priority (`court_efficiency`, `player_rest`)

## Tiebreaker Rules

The system supports the following tiebreaker options:

1. `points`: Total points accumulated
2. `head_to_head`: Results of matches between tied couples
3. `games_diff`: Difference between games won and lost
4. `games_won`: Total number of games won
5. `matches_won`: Total number of matches won

## Bracket Types

The system supports three types of brackets:

1. `main`: Main bracket for tournament winners
2. `silver`: Secondary bracket (e.g., for 3rd-4th place in groups)
3. `bronze`: Tertiary bracket (e.g., for 5th-6th place in groups)

## Court Availability

The system tracks court availability and prevents double-booking. When scheduling matches:

1. Each court can have a specific availability timeframe
2. The system checks for conflicts with existing scheduled matches
3. Auto-scheduling attempts to optimize court usage based on the priority setting

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing the issue"
}
```

Common error status codes:
- `400`: Bad Request (invalid input)
- `403`: Forbidden (unauthorized access)
- `404`: Not Found (resource doesn't exist)

## Match Result Status

Matches can have the following statuses:

- `pending`: Not yet played
- `completed`: Finished normally
- `time_expired`: Ended due to time limit
- `forfeited`: One team forfeited

## Frontend Implementation Guidelines

### Tournament Structure Visualization

For visualizing tournament structures, consider:

1. **Group Stage**: 
   - Display groups in a table format showing standings
   - Each group should show couples, match counts, points, and positions
   - Use color coding to highlight advancement positions

2. **Elimination Brackets**:
   - Implement a traditional bracket visualization
   - Show upcoming matches with scheduled times
   - Display completed match results within the bracket
   - Highlight the path to the final

### Match Scheduling Interface

For the scheduling interface:

1. **Calendar View**:
   - Show a daily/weekly calendar view of courts and schedules
   - Display color-coded time blocks for matches
   - Visually represent free slots for manual scheduling

2. **Scheduling Form**:
   - Provide time pickers with validation based on court availability
   - Include clear error messages for scheduling conflicts
   - Allow drag-and-drop scheduling where possible

### Configuration Forms

For tournament configuration:

1. **Stage Creation**:
   - Use steppers or wizards for complex configuration
   - Provide sensible defaults for all configuration options
   - Include tooltips explaining each configuration option

2. **Group Management**:
   - Provide interface to create multiple groups at once
   - Include drag-and-drop interfaces for couple assignment
   - Display warnings for uneven group assignments

### Real-time Updates

Consider implementing:

1. WebSocket connections for real-time match results
2. Automatic standings updates as matches complete
3. Push notifications for scheduled matches
