from enum import Enum, auto

# Tournament Stage Types
class StageType(str, Enum):
    GROUP = "group"
    ELIMINATION = "elimination"

# Tournament Bracket Types
class BracketType(str, Enum):
    MAIN = "main"
    SILVER = "silver"
    BRONZE = "bronze"

# Scoring Types
class ScoringType(str, Enum):
    POINTS = "points"
    WINS = "wins"

# Win Criteria Types
class WinCriteria(str, Enum):
    BEST_OF = "best_of"
    FIRST_TO = "first_to"

# Assignment Methods
class AssignmentMethod(str, Enum):
    RANDOM = "random"
    SEEDED = "seeded"
    BALANCED = "balanced"

# Scheduling Priorities
class SchedulingPriority(str, Enum):
    COURT_EFFICIENCY = "court_efficiency"
    TIME_EFFICIENCY = "time_efficiency"
    GROUP_BALANCE = "group_balance"

# Tiebreaker Options
class TiebreakerOption(str, Enum):
    POINTS = "points"
    HEAD_TO_HEAD = "head_to_head"
    GAMES_DIFF = "games_diff"
    GAMES_WON = "games_won"

# Match Result Status
class MatchResultStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    TIME_EXPIRED = "time_expired"
    FORFEITED = "forfeited"

# Match Formats
class MatchFormat(str, Enum):
    ROUND_ROBIN = "round_robin"  # Every couple plays every other couple
    SINGLE_ELIMINATION = "single_elimination"  # Single knockout
    DOUBLE_ELIMINATION = "double_elimination"  # Double knockout
    SWISS_SYSTEM = "swiss_system"  # Swiss tournament system
    CUSTOM = "custom"  # Custom pairing logic

# Default Configurations
DEFAULT_SCORING_SYSTEM = {
    "type": ScoringType.POINTS,
    "win": 3,
    "draw": 1,
    "loss": 0,
    "game_win": 1,
    "game_loss": 0
}

DEFAULT_MATCH_RULES = {
    "match_format": MatchFormat.ROUND_ROBIN,
    "matches_per_opponent": 1,
    "games_per_match": 3,
    "win_criteria": WinCriteria.BEST_OF,
    "time_limited": False,
    "time_limit_minutes": 90,
    "break_between_matches": 30
}

DEFAULT_ADVANCEMENT_RULES = {
    "top_n": 2,
    "to_bracket": BracketType.MAIN,
    "tiebreaker": [
        TiebreakerOption.POINTS,
        TiebreakerOption.HEAD_TO_HEAD,
        TiebreakerOption.GAMES_DIFF,
        TiebreakerOption.GAMES_WON
    ]
}

DEFAULT_SCHEDULING = {
    "auto_schedule": True,
    "overlap_allowed": False,
    "scheduling_priority": SchedulingPriority.COURT_EFFICIENCY
}

# Default Stage Configuration
DEFAULT_STAGE_CONFIG = {
    "scoring_system": DEFAULT_SCORING_SYSTEM,
    "match_rules": DEFAULT_MATCH_RULES,
    "advancement_rules": DEFAULT_ADVANCEMENT_RULES,
    "scheduling": DEFAULT_SCHEDULING
} 