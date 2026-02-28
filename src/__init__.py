"""
Planetary Conservation Framework

A physics-based constraint system for evaluating space infrastructure
proposals against Earth's remaining planetary margins.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from .checker import ConstraintChecker
from .simulator import Simulator, ScenarioConfig
from .cascade import CascadeEngine
from .materials import MaterialLedger
from .constraints import evaluate_all, ALL_CONSTRAINTS
from .locations import ALL_SITES, print_site_comparison

__version__ = "0.1.0"
__all__ = [
    "ConstraintChecker",
    "Simulator",
    "ScenarioConfig",
    "CascadeEngine",
    "MaterialLedger",
    "evaluate_all",
    "ALL_CONSTRAINTS",
    "ALL_SITES",
    "print_site_comparison",
]
