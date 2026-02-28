"""
Monte Carlo scenario simulator.

Runs space infrastructure proposals forward in time, tracking all
constraint margins and cascade interactions year by year.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
import json


@dataclass
class SystemState:
    """Current state of all coupled subsystems at a point in time."""
    year: int = 0

    # Orbital
    orbital_mass_kg: float = 1e7
    debris_mass_kg: float = 1e6
    tracked_objects: int = 40_000
    kessler_margin_pct: float = 80.0

    # Atmospheric
    bc_accumulated_kg: float = 0.0
    alumina_accumulated_kg: float = 0.0
    h2o_injected_kg: float = 0.0
    thermospheric_heating_w_m2: float = 0.0
    thermosphere_contraction_km: float = 0.0

    # Material
    rare_earth_consumed_kg: float = 0.0
    copper_consumed_kg: float = 0.0
    gallium_consumed_kg: float = 0.0
    mineral_margin_pct: float = 100.0

    # Operations
    launches_this_year: int = 0
    launch_failures: int = 0
    satellites_lost_to_debris: int = 0
    replacement_launches_needed: int = 0

    # Economic
    insurance_coverage_pct: float = 100.0
    cost_per_launch_factor: float = 1.0

    # Infrastructure
    launch_site_disruption_days: int = 0
    safety_margin_pct: float = 100.0

    # Flags
    kessler_cascade_triggered: bool = False
    insurance_market_collapsed: bool = False
    feedback_loop_runaway: bool = False

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class ScenarioConfig:
    """Configuration for a simulation scenario."""
    name: str = "Default"
    duration_years: int = 30

    # Launch program
    initial_launches_per_year: int = 100
    launch_growth_rate: float = 0.15
    max_launches_per_year: int = 5000
    propellant_type: str = "methane_lox"
    payload_per_launch_kg: float = 100_000

    # Space infrastructure
    modules_deployed_per_year: int = 1
    module_mass_kg: float = 700_000
    hardware_lifetime_years: int = 4
    recycling_rate: float = 0.0
    deorbit_plan: bool = False
    active_debris_removal: bool = False

    # Stochastic events
    hurricane_probability: float = 0.15
    debris_collision_probability: float = 0.02
    cyber_incident_probability: float = 0.10
    insurance_review_probability: float = 0.20

    # Feedback parameters
    soot_per_launch_kg: float = 50.0
    debris_generation_rate: float = 0.001
    ore_grade_decline_rate: float = 0.02


class Simulator:
    """
    Run forward simulations of space infrastructure build-out
    against planetary constraints with stochastic events.
    """

    def __init__(self, config: ScenarioConfig = None):
        self.config = config or ScenarioConfig()
        self.history: List[SystemState] = []

    def run(self, n_runs: int = 1, seed: int = None) -> List[List[SystemState]]:
        """
        Run n_runs Monte Carlo simulations.

        Returns list of state histories, one per run.
        """
        all_runs = []
        for run_idx in range(n_runs):
            if seed is not None:
                random.seed(seed + run_idx)
            history = self._run_single()
            all_runs.append(history)
        return all_runs

    def _run_single(self) -> List[SystemState]:
        """Run a single simulation."""
        state = SystemState()
        history = [deepcopy(state)]
        cfg = self.config

        for year in range(1, cfg.duration_years + 1):
            state.year = year

            # ── Launch cadence (with terrestrial bottleneck) ──
            planned_launches = min(
                cfg.initial_launches_per_year * (1 + cfg.launch_growth_rate) ** year,
                cfg.max_launches_per_year
            )

            # Add replacement launches for radiation-degraded hardware
            if year > cfg.hardware_lifetime_years:
                modules_needing_replacement = cfg.modules_deployed_per_year
                replacement_mass = modules_needing_replacement * cfg.module_mass_kg
                state.replacement_launches_needed = int(
                    replacement_mass / cfg.payload_per_launch_kg
                )
                planned_launches += state.replacement_launches_needed

            # Add replacement for debris-destroyed satellites
            planned_launches += state.satellites_lost_to_debris

            # Launch site disruptions (stochastic)
            state.launch_site_disruption_days = 0
            if random.random() < cfg.hurricane_probability:
                state.launch_site_disruption_days += random.randint(14, 60)
            available_days = 365 - state.launch_site_disruption_days
            max_cadence = available_days * 3  # max 3 launches/day
            actual_launches = min(int(planned_launches), max_cadence)
            state.launches_this_year = actual_launches

            # ── Safety margin erosion ──
            cadence_pressure = actual_launches / max(cfg.max_launches_per_year, 1)
            economic_pressure = state.cost_per_launch_factor
            state.safety_margin_pct = max(
                0,
                100 * (1 - cadence_pressure * 0.5
                       - (economic_pressure - 1) * 0.3)
            )

            # Launch failures
            base_failure_rate = 0.02
            adjusted_rate = base_failure_rate * (
                1 + (100 - state.safety_margin_pct) / 100
            )
            state.launch_failures = sum(
                1 for _ in range(actual_launches)
                if random.random() < adjusted_rate
            )

            # ── Orbital environment ──
            new_orbital_mass = cfg.modules_deployed_per_year * cfg.module_mass_kg
            state.orbital_mass_kg += new_orbital_mass

            # Debris generation
            new_debris = (
                state.orbital_mass_kg * cfg.debris_generation_rate
                + state.launch_failures * cfg.payload_per_launch_kg * 0.5
            )

            # Debris collision events
            collision_prob = cfg.debris_collision_probability * (
                state.debris_mass_kg / 1e6
            )
            if random.random() < min(collision_prob, 0.5):
                collision_debris = random.uniform(1000, 50000)
                new_debris += collision_debris
                state.satellites_lost_to_debris += random.randint(1, 5)
                state.tracked_objects += random.randint(100, 5000)

            state.debris_mass_kg += new_debris

            # Active debris removal (if enabled)
            if cfg.active_debris_removal:
                state.debris_mass_kg *= 0.95  # remove 5% per year

            # Kessler threshold check
            kessler_threshold = 5e6
            state.kessler_margin_pct = max(
                0,
                (1 - state.debris_mass_kg / kessler_threshold) * 100
            )
            if state.kessler_margin_pct <= 0:
                state.kessler_cascade_triggered = True

            # ── Atmospheric effects ──
            state.bc_accumulated_kg += actual_launches * cfg.soot_per_launch_kg
            state.thermospheric_heating_w_m2 = (
                state.bc_accumulated_kg * 1e-6
            )
            state.h2o_injected_kg += actual_launches * 1_800_000

            # Thermospheric feedback
            if state.thermospheric_heating_w_m2 > 0.005:
                state.feedback_loop_runaway = True
                cfg.hardware_lifetime_years = max(
                    1, cfg.hardware_lifetime_years - 1
                )

            # ── Mineral consumption ──
            re_per_module = 7500  # midpoint kg rare earths per module
            annual_re = (
                cfg.modules_deployed_per_year * re_per_module
                * (1 - cfg.recycling_rate)
            )
            state.rare_earth_consumed_kg += annual_re
            re_ceiling = 350_000_000 * 0.0001  # 0.01% of production
            state.mineral_margin_pct = max(
                0, (1 - annual_re / re_ceiling) * 100
            )

            # Ore grade decline → cost escalation
            state.cost_per_launch_factor *= (
                1 + cfg.ore_grade_decline_rate * 0.1
            )

            # ── Insurance market ──
            risk_score = (
                (1 - state.kessler_margin_pct / 100) * 0.3
                + state.launch_failures / max(actual_launches, 1) * 0.3
                + (1 if state.satellites_lost_to_debris > 0 else 0) * 0.2
                + (1 if random.random() < cfg.cyber_incident_probability
                   else 0) * 0.2
            )
            if risk_score > 0.5:
                state.insurance_coverage_pct *= 0.8
            if state.insurance_coverage_pct < 20:
                state.insurance_market_collapsed = True
                state.cost_per_launch_factor *= 2.0

            history.append(deepcopy(state))

            # Check for terminal states
            if (state.kessler_cascade_triggered
                    and state.insurance_market_collapsed):
                break

        return history

    def summarize_run(self, history: List[SystemState]) -> Dict:
        """Generate summary statistics from a simulation run."""
        final = history[-1]
        return {
            "duration_simulated": final.year,
            "total_launches": sum(s.launches_this_year for s in history),
            "total_failures": sum(s.launch_failures for s in history),
            "final_orbital_mass_kg": final.orbital_mass_kg,
            "final_debris_mass_kg": final.debris_mass_kg,
            "kessler_triggered": final.kessler_cascade_triggered,
            "kessler_triggered_year": next(
                (s.year for s in history if s.kessler_cascade_triggered),
                None
            ),
            "insurance_collapsed": final.insurance_market_collapsed,
            "insurance_collapsed_year": next(
                (s.year for s in history if s.insurance_market_collapsed),
                None
            ),
            "feedback_runaway": final.feedback_loop_runaway,
            "feedback_runaway_year": next(
                (s.year for s in history if s.feedback_loop_runaway),
                None
            ),
            "final_cost_factor": final.cost_per_launch_factor,
            "bc_accumulated_kg": final.bc_accumulated_kg,
            "rare_earth_consumed_kg": final.rare_earth_consumed_kg,
        }

    def print_summary(self, history: List[SystemState]):
        """Pretty-print simulation results."""
        s = self.summarize_run(history)
        print(f"\n{'='*60}")
        print(f"SIMULATION: {self.config.name}")
        print(f"{'='*60}")
        print(f"Duration: {s['duration_simulated']} years")
        print(f"Total launches: {s['total_launches']:,}")
        print(f"Total failures: {s['total_failures']:,}")
        print(f"Final orbital mass: {s['final_orbital_mass_kg']:.2e} kg")
        print(f"Final debris mass: {s['final_debris_mass_kg']:.2e} kg")
        print(f"Cost escalation factor: {s['final_cost_factor']:.1f}x")
        print(f"\nTERMINAL EVENTS:")
        if s["kessler_triggered"]:
            print(f"  ✗ Kessler cascade: Year {s['kessler_triggered_year']}")
        if s["insurance_collapsed"]:
            print(
                f"  ✗ Insurance market collapse: "
                f"Year {s['insurance_collapsed_year']}"
            )
        if s["feedback_runaway"]:
            print(
                f"  ✗ Thermospheric feedback runaway: "
                f"Year {s['feedback_runaway_year']}"
            )
        if not any([s["kessler_triggered"], s["insurance_collapsed"],
                    s["feedback_runaway"]]):
            print(f"  No terminal events in simulation period")
        print(f"{'='*60}\n")
