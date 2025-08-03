# Dashboard API Documentation

## Overview

The Dashboard API provides comprehensive analytics and metrics for the PadelTour tournament management system. This endpoint aggregates data from tournaments, matches, players, courts, and statistics to provide real-time insights for business intelligence and operational management.

## Endpoint

```
GET /api/v1/dashboard/overview
```

## Authentication

**Required**: Bearer Token (JWT)

```javascript
// Example request headers
{
  "Authorization": "Bearer your_jwt_token_here",
  "Content-Type": "application/json"
}
```

## Response Structure

The API returns a comprehensive dashboard object with five main sections:

```typescript
interface DashboardResponse {
  tournament_management: TournamentManagementOverview;
  real_time_progress: RealTimeTournamentProgress;
  match_court_analytics: MatchCourtAnalytics;
  player_performance: PlayerCouplePerformance;
  operational_dashboard: OperationalDashboard;
  generated_at: string; // ISO datetime
}
```

## Data Sections Detailed

### 🏆 Tournament Management Overview

Key metrics for tournament administration and business intelligence.

```typescript
interface TournamentManagementOverview {
  active_tournaments: number;           // Currently running tournaments
  upcoming_tournaments: number;         // Future tournaments
  completed_this_month: number;         // Tournaments finished this month
  total_registered_players: number;     // Players registered this month
  player_change: number;                // Change from last month (+/-)
  player_change_percentage: number;     // Percentage change
  matches_played_today: number;         // Today's completed matches
  pending_matches: number;              // Unscheduled matches
  court_utilization_rate: number;       // % of court time used today
  tournament_timeline: TournamentTimelineItem[];
}

interface TournamentTimelineItem {
  id: number;
  name: string;
  start_date: string;    // ISO date
  end_date: string;      // ISO date  
  players_number: number;
  status: "active" | "upcoming" | "completed";
}
```

**Frontend Usage Example:**
```javascript
// Display key metrics cards
const { tournament_management } = dashboardData;

// Active tournaments card
<MetricCard 
  title="Active Tournaments" 
  value={tournament_management.active_tournaments}
  icon="🏆"
/>

// Player growth indicator
<MetricCard 
  title="Player Registrations" 
  value={tournament_management.total_registered_players}
  change={tournament_management.player_change}
  changePercentage={tournament_management.player_change_percentage}
  trend={tournament_management.player_change > 0 ? "up" : "down"}
/>

// Court utilization gauge
<ProgressCircle 
  percentage={tournament_management.court_utilization_rate}
  label="Court Utilization"
/>
```

### 📈 Real-Time Tournament Progress

Live tournament status and performance metrics.

```typescript
interface RealTimeTournamentProgress {
  tournament_progress: TournamentProgress[];
  match_status_distribution: MatchStatusDistribution;
  top_performing_couples: TopCouple[];
}

interface TournamentProgress {
  tournament_id: number;
  tournament_name: string;
  completion_percentage: number;    // 0-100
  total_matches: number;
  completed_matches: number;
  stages_progress: StageProgress[];
}

interface StageProgress {
  stage_id: number;
  stage_name: string;
  stage_type: "group" | "elimination";
  completion_percentage: number;
  order: number;
}

interface MatchStatusDistribution {
  scheduled: number;
  in_progress: number;
  completed: number;
  pending: number;
}

interface TopCouple {
  couple_id: number;
  couple_name: string;
  tournament_name: string;
  matches_played: number;
  matches_won: number;
  win_rate: number;        // 0-100 percentage
  total_points: number;
}
```

**Frontend Usage Example:**
```javascript
// Tournament progress bars
{dashboardData.real_time_progress.tournament_progress.map(tournament => (
  <TournamentCard key={tournament.tournament_id}>
    <h3>{tournament.tournament_name}</h3>
    <ProgressBar 
      percentage={tournament.completion_percentage}
      label={`${tournament.completed_matches}/${tournament.total_matches} matches`}
    />
    
    {/* Stage indicators */}
    <StageIndicators stages={tournament.stages_progress} />
  </TournamentCard>
))}

// Match status pie chart
<PieChart 
  data={[
    { name: "Completed", value: match_status_distribution.completed },
    { name: "Scheduled", value: match_status_distribution.scheduled },
    { name: "In Progress", value: match_status_distribution.in_progress },
    { name: "Pending", value: match_status_distribution.pending }
  ]}
/>

// Top couples leaderboard
<Leaderboard 
  couples={dashboardData.real_time_progress.top_performing_couples}
  renderItem={(couple, rank) => (
    <LeaderboardItem key={couple.couple_id}>
      <span>#{rank}</span>
      <span>{couple.couple_name}</span>
      <span>{couple.win_rate}%</span>
      <span>{couple.total_points} pts</span>
    </LeaderboardItem>
  )}
/>
```

### 🎾 Match & Court Analytics

Operational analytics for match scheduling and court management.

```typescript
interface MatchCourtAnalytics {
  matches_per_day_30d: Record<string, number>;     // date -> count
  average_match_duration_minutes: number;
  court_efficiency_matches_per_court_per_day: number;
  peak_playing_hours: Record<string, number>;      // hour -> count
  match_results_distribution: MatchResultsDistribution;
}

interface MatchResultsDistribution {
  wins: number;
  draws: number;
  time_expired: number;
  forfeited: number;
}
```

**Frontend Usage Example:**
```javascript
// Matches per day line chart
const chartData = Object.entries(match_court_analytics.matches_per_day_30d)
  .map(([date, count]) => ({ date, matches: count }));

<LineChart data={chartData} xDataKey="date" yDataKey="matches" />

// Court efficiency metrics
<MetricGrid>
  <MetricCard 
    title="Avg Match Duration"
    value={`${match_court_analytics.average_match_duration_minutes} min`}
    icon="⏱️"
  />
  <MetricCard 
    title="Court Efficiency" 
    value={`${match_court_analytics.court_efficiency_matches_per_court_per_day} matches/court/day`}
    icon="🏟️"
  />
</MetricGrid>

// Peak hours heatmap
const heatmapData = Object.entries(peak_playing_hours)
  .map(([hour, count]) => ({ hour: parseInt(hour), matches: count }));

<HeatMap 
  data={heatmapData}
  xAxis="hour"
  yAxis="matches"
  colorScale="blues"
/>
```

### 👥 Player & Couple Performance

Player engagement and performance analytics.

```typescript
interface PlayerCouplePerformance {
  most_active_players: ActivePlayer[];
  best_performing_couples: PerformingCouple[];
  player_level_distribution: Record<string, number>;  // level -> count
  player_registration_trends: PlayerRegistrationTrends;
}

interface ActivePlayer {
  player_id: number;
  name: string;
  tournament_count: number;
}

interface PerformingCouple {
  couple_id: number;
  couple_name: string;
  tournament_name: string;
  matches_played: number;
  win_rate: number;
  total_points: number;
}

interface PlayerRegistrationTrends {
  current_month: number;
  last_month: number;
  change: number;
}
```

**Frontend Usage Example:**
```javascript
// Active players list
<PlayersList>
  {player_performance.most_active_players.map(player => (
    <PlayerCard key={player.player_id}>
      <span>{player.name}</span>
      <Badge>{player.tournament_count} tournaments</Badge>
    </PlayerCard>
  ))}
</PlayersList>

// Level distribution chart
const levelData = Object.entries(player_level_distribution)
  .map(([level, count]) => ({ level: `Level ${level}`, players: count }));

<BarChart data={levelData} xDataKey="level" yDataKey="players" />

// Registration trends
<TrendIndicator 
  current={player_registration_trends.current_month}
  previous={player_registration_trends.last_month}
  change={player_registration_trends.change}
  label="Monthly Registrations"
/>
```

### 🚨 Operational Dashboard

Critical operational alerts and upcoming events.

```typescript
interface OperationalDashboard {
  upcoming_matches_24h: UpcomingMatch[];
  court_conflicts: CourtConflict[];
  incomplete_match_results: number;
  tournament_deadlines: TournamentDeadline[];
  system_alerts: SystemAlerts;
}

interface UpcomingMatch {
  match_id: number;
  tournament_name: string;
  couple1_name: string;
  couple2_name: string;
  scheduled_start: string | null;  // ISO datetime
  court_name: string | null;
}

interface CourtConflict {
  court_name: string;
  conflict_matches: ConflictMatch[];
}

interface ConflictMatch {
  match_id: number;
  tournament: string;
  start_time: string;  // ISO datetime
  end_time: string;    // ISO datetime
}

interface TournamentDeadline {
  tournament_id: number;
  tournament_name: string;
  end_date: string;    // ISO datetime
  days_remaining: number;
}

interface SystemAlerts {
  court_conflicts: number;
  incomplete_matches: number;
  upcoming_deadlines: number;
  matches_next_24h: number;
}
```

**Frontend Usage Example:**
```javascript
// Upcoming matches timeline
<Timeline>
  {operational_dashboard.upcoming_matches_24h.map(match => (
    <TimelineItem key={match.match_id} time={match.scheduled_start}>
      <MatchCard>
        <h4>{match.tournament_name}</h4>
        <p>{match.couple1_name} vs {match.couple2_name}</p>
        <p>Court: {match.court_name || "TBD"}</p>
      </MatchCard>
    </TimelineItem>
  ))}
</Timeline>

// Court conflicts alert
{operational_dashboard.court_conflicts.length > 0 && (
  <AlertCard severity="warning">
    <h3>⚠️ Court Conflicts Detected</h3>
    {operational_dashboard.court_conflicts.map(conflict => (
      <ConflictItem key={conflict.court_name}>
        <strong>{conflict.court_name}</strong>
        {conflict.conflict_matches.map(match => (
          <p key={match.match_id}>
            {match.tournament} - {formatTime(match.start_time)} to {formatTime(match.end_time)}
          </p>
        ))}
      </ConflictItem>
    ))}
  </AlertCard>
)}

// System alerts summary
<AlertsSummary>
  <AlertBadge count={system_alerts.court_conflicts} type="warning" label="Conflicts" />
  <AlertBadge count={system_alerts.incomplete_matches} type="info" label="Incomplete" />
  <AlertBadge count={system_alerts.upcoming_deadlines} type="urgent" label="Deadlines" />
</AlertsSummary>
```

## Complete Integration Example

```javascript
// React component example
import { useState, useEffect } from 'react';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/v1/dashboard/overview', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setDashboardData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();

    // Refresh every 5 minutes
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!dashboardData) return <NoDataMessage />;

  return (
    <DashboardLayout>
      {/* Tournament Management Section */}
      <Section title="Tournament Overview">
        <MetricsGrid data={dashboardData.tournament_management} />
        <TournamentTimeline tournaments={dashboardData.tournament_management.tournament_timeline} />
      </Section>

      {/* Real-time Progress */}
      <Section title="Tournament Progress">
        <TournamentProgressCharts data={dashboardData.real_time_progress} />
      </Section>

      {/* Analytics */}
      <Section title="Match & Court Analytics">
        <AnalyticsCharts data={dashboardData.match_court_analytics} />
      </Section>

      {/* Performance */}
      <Section title="Player Performance">
        <PerformanceMetrics data={dashboardData.player_performance} />
      </Section>

      {/* Operational */}
      <Section title="Operations">
        <OperationalAlerts data={dashboardData.operational_dashboard} />
      </Section>
    </DashboardLayout>
  );
};

export default Dashboard;
```

## Error Handling

The API may return the following HTTP status codes:

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 200 | Success | Dashboard data object |
| 401 | Unauthorized | `{"detail": "Could not validate credentials"}` |
| 403 | Forbidden | `{"detail": "Not enough permissions"}` |
| 500 | Server Error | `{"detail": "Error generating dashboard data: {error_message}"}` |

**Error Handling Example:**
```javascript
const handleApiError = (error, response) => {
  switch (response?.status) {
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
    case 403:
      // Show permission error
      showErrorToast('You do not have permission to access this dashboard');
      break;
    case 500:
      // Show server error
      showErrorToast('Server error occurred. Please try again later.');
      break;
    default:
      showErrorToast('An unexpected error occurred');
  }
};
```

## Performance Considerations

1. **Caching**: Consider implementing client-side caching with appropriate TTL (5-10 minutes)
2. **Loading States**: Always show loading indicators as data aggregation may take 1-3 seconds
3. **Error Recovery**: Implement retry logic for failed requests
4. **Pagination**: The API returns top 10 items for lists - no pagination needed
5. **Real-time Updates**: Refresh data every 5-10 minutes for near real-time experience

## Data Refresh Strategy

```javascript
// Recommended refresh intervals
const REFRESH_INTERVALS = {
  dashboard_overview: 5 * 60 * 1000,      // 5 minutes
  operational_alerts: 2 * 60 * 1000,      // 2 minutes (more critical)
  tournament_progress: 3 * 60 * 1000      // 3 minutes
};

// Smart refresh based on user activity
const useSmartRefresh = (interval) => {
  useEffect(() => {
    let refreshInterval;
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        clearInterval(refreshInterval);
      } else {
        refreshData(); // Immediate refresh when user returns
        refreshInterval = setInterval(refreshData, interval);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    refreshInterval = setInterval(refreshData, interval);

    return () => {
      clearInterval(refreshInterval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [interval]);
};
```

## Sample Response

<details>
<summary>Click to view complete sample response</summary>

```json
{
  "tournament_management": {
    "active_tournaments": 3,
    "upcoming_tournaments": 7,
    "completed_this_month": 12,
    "total_registered_players": 156,
    "player_change": 23,
    "player_change_percentage": 17.29,
    "matches_played_today": 8,
    "pending_matches": 45,
    "court_utilization_rate": 67.5,
    "tournament_timeline": [
      {
        "id": 1,
        "name": "Summer Championship 2024",
        "start_date": "2024-07-15T09:00:00Z",
        "end_date": "2024-07-17T18:00:00Z",
        "players_number": 32,
        "status": "active"
      }
    ]
  },
  "real_time_progress": {
    "tournament_progress": [
      {
        "tournament_id": 1,
        "tournament_name": "Summer Championship 2024",
        "completion_percentage": 65.5,
        "total_matches": 47,
        "completed_matches": 31,
        "stages_progress": [
          {
            "stage_id": 1,
            "stage_name": "Group Stage",
            "stage_type": "group",
            "completion_percentage": 100.0,
            "order": 1
          },
          {
            "stage_id": 2,
            "stage_name": "Quarterfinals",
            "stage_type": "elimination",
            "completion_percentage": 25.0,
            "order": 2
          }
        ]
      }
    ],
    "match_status_distribution": {
      "scheduled": 12,
      "in_progress": 3,
      "completed": 31,
      "pending": 1
    },
    "top_performing_couples": [
      {
        "couple_id": 15,
        "couple_name": "Rodriguez/Martinez",
        "tournament_name": "Summer Championship 2024",
        "matches_played": 5,
        "matches_won": 5,
        "win_rate": 100.0,
        "total_points": 15
      }
    ]
  },
  "generated_at": "2024-07-27T14:30:00Z"
}
```

</details>

## Security Notes

- **Authentication Required**: All requests must include valid JWT token
- **Company Isolation**: Data is automatically filtered by company ID from JWT
- **Rate Limiting**: Standard API rate limits apply (if implemented)
- **CORS**: Ensure your frontend domain is whitelisted

## Testing the API

You can test the endpoint using curl:

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/overview" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json"
```

Or use tools like Postman, Thunder Client, or your browser's developer tools.

---

**Need Help?** 
- Check the main API documentation for authentication setup
- Verify your JWT token is valid and not expired
- Ensure your company has tournaments/matches data for meaningful dashboard results