"""
Admiral's Gambit Arcade - A naval battle game bot
"""

from .config import Config
from .data_loader import DataLoader
from .models import (
    HULLS, HULL_MODIFIERS, MATERIALS, GUNS, MISSILES, TORPEDOES,
    ENERGY_WEAPONS, ARMORS, ACTIVE_DEFENSES, SPECIAL_MODULES,
    ARENAS, KILL_STREAKS, ARENA_HAZARDS, ALL_WEAPONS
)
from .rate_limiter import RateLimiter
from .battle import Battle

__version__ = "1.0.0"
__all__ = [
    "Config",
    "DataLoader",
    "HULLS", "HULL_MODIFIERS", "MATERIALS", "GUNS", "MISSILES", "TORPEDOES",
    "ENERGY_WEAPONS", "ARMORS", "ACTIVE_DEFENSES", "SPECIAL_MODULES",
    "ARENAS", "KILL_STREAKS", "ARENA_HAZARDS", "ALL_WEAPONS",
    "RateLimiter",
    "Battle",
]
