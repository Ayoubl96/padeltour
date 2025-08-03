"""
Tournament Staging Module

This module consolidates all tournament staging functionality into organized sub-modules:

- stages.py: Tournament stage CRUD operations
- groups.py: Tournament group operations and couple assignments  
- brackets.py: Tournament bracket CRUD operations
- matches.py: Match generation and retrieval
- scheduling.py: Match scheduling and ordering
- stats.py: Couple statistics and standings

This modular approach improves code organization, maintainability, and scalability.
Each sub-module focuses on a specific domain, following the single responsibility principle.
"""

from fastapi import APIRouter

# Import all sub-routers
from .stages import router as stages_router
from .groups import router as groups_router
from .brackets import router as brackets_router
from .matches import router as matches_router
from .scheduling import router as scheduling_router
from .stats import router as stats_router

# Create the main router for this module
router = APIRouter()

# Include all sub-routers with appropriate tags for documentation
router.include_router(
    stages_router, 
    tags=["Tournament Stages"],
    prefix=""
)

router.include_router(
    groups_router, 
    tags=["Tournament Groups"],
    prefix=""
)

router.include_router(
    brackets_router, 
    tags=["Tournament Brackets"],
    prefix=""
)

router.include_router(
    matches_router, 
    tags=["Tournament Matches"],
    prefix=""
)

router.include_router(
    scheduling_router, 
    tags=["Match Scheduling"],
    prefix=""
)

router.include_router(
    stats_router, 
    tags=["Tournament Statistics"],
    prefix=""
)

# Export the router for external use
__all__ = ["router"]