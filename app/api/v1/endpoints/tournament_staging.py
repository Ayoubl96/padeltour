"""
Tournament Staging API Entry Point

This module imports and re-exports the tournament staging router from the
tournament_staging package. This maintains backward compatibility while
providing a clean modular structure.

All tournament staging functionality is now organized in the tournament_staging/
folder with focused sub-modules for better maintainability and scalability.
"""

# Import the consolidated router from the tournament_staging package
from .tournament_staging import router

# Re-export for backward compatibility
__all__ = ["router"]
