#!/usr/bin/env python3
"""
Example: Check a space data center proposal against planetary constraints.

Usage:
    python -m examples.check_proposal

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.checker import ConstraintChecker
from src.simulator import Simulator, ScenarioConfig
from src.cascade import CascadeEngine
from src.locations import print_site_comparison


def check_orbital_datacenter():
    """Check a typical space data center proposal."""
    print("\n" + "="*70)
    print("EXAMPLE: Orbital Data Center Proposal — Phase 1")
    print("="*70)

    checker = ConstraintChecker()

    proposal = {
        "name": "Orbital Data Center Phase 1 (10% hyperscale)",
        "launches_per_year": 500,
        "propellant_type": "methane_lox",
        "propellant_per_launch_kg": 4_600_000,
        "payload_mass_kg": 100_000,
        "orbital_mass_kg": 5_000_000_000,
        "duration_years": 10,
        "modules_per_year": 7,
        "deorbit_plan": False,
        "deorbit_timeline_years": 0,
        "active_debris_removal": False,
        "deorbit_bond_funded": False,
        "recycling_rate": 0.0,
    }

    result = checker.check_proposal(proposal)
    result.print_report()
    return result


def check_compliant_proposal():
    """Check a conservation-compliant proposal for comparison."""
    print("\n" + "="*70)
    print("EXAMPLE: Conservation-Compliant Proposal")
    print("="*70)

    checker = ConstraintChecker()

    proposal = {
        "name": "Compliant Orbital Research Station",
        "launches_per_year": 10,
        "propellant_type": "methane_lox",
        "propellant_per_launch_kg": 4_600_000,
        "payload_mass_kg": 100_000,
        "orbital_mass_kg": 500_000,
        "duration_years": 10,
        "modules_per_year": 1,
        "deorbit_plan": True,
        "deorbit_timeline_years": 15,
        "active_debris_removal": True,
        "deorbit_bond_funded": True,
        "recycling_rate": 0.5,
    }

    result = checker.check_proposal(proposal)
    result.print_report()
    return result


def run_scenario_comparison():
    """Run Monte Carlo simulations across scenarios."""
    print("\n" + "="*70)
    print("SCENARIO COMPARISON: 30-Year Monte Carlo (10 runs each)")
    print("="*70)

    scenarios = [
        ScenarioConfig(
            name="Aggressive Buildout (No Conservation)",
            initial_launches_per_year=500,
            launch_growth_rate=0.20,
            max_launches_per_year=5000,
            modules_deployed_per_year=5,
            deorbit_plan=False,
            active_debris_removal=False,
            recycling_rate=0.0
        ),
        ScenarioConfig(
            name="Constrained Buildout (Partial Compliance)",
            initial_launches_per_year=300,
            launch_growth_rate=0.05,
            max_launches_per_year=1000,
            modules_deployed_per_year=1,
            deorbit_plan=True,
            active_debris_removal=True,
            recycling_rate=0.5
        ),
        ScenarioConfig(
            name="Fully Compliant (Future Tech)",
            initial_launches_per_year=100,
            launch_growth_rate=0.03,
            max_launches_per_year=500,
            modules_deployed_per_year=2,
            module_mass_kg=500_000,
            hardware_lifetime_years=10,
            deorbit_plan=True,
            active_debris_removal=True,
            recycling_rate=0.95,
            soot_per_launch_kg=0.0  # non-combustion launch
        ),
    ]

    for config in scenarios:
        sim = Simulator(config)
        runs = sim.run(n_runs=10, seed=42)

        kessler_count = sum(
            1 for r in runs if r[-1].kessler_cascade_triggered
        )
        insurance_count = sum(
            1 for r in runs if r[-1].insurance_market_collapsed
        )
        feedback_count = sum(
            1 for r in runs if r[-1].feedback_loop_runaway
        )

        print(f"\n  {config.name}")
        print(f"    Kessler cascade: {kessler_count}/10 runs")
        print(f"    Insurance collapse: {insurance_count}/10 runs")
        print(f"    Feedback runaway: {feedback_count}/10 runs")

        # Show one representative run
        sim.print_summary(runs[0])


def show_cascade():
    """Show cascade effects from increased launch cadence."""
    print("\n" + "="*70)
    print("CASCADE ANALYSIS: 10x Launch Cadence Increase")
    print("="*70)

    engine = CascadeEngine()
    engine.print_cascade("launch_cadence", perturbation=1.0)


def show_feedback_loops():
    """Identify all positive feedback loops in the system."""
    print("\n" + "="*70)
    print("FEEDBACK LOOP IDENTIFICATION​​​​​​​​​​​​​​​​
