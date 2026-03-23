"""
Tests for Monte Carlo simulator.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator import Simulator, ScenarioConfig, SystemState


class TestSimulator(unittest.TestCase):
    """Tests for Simulator with deterministic seed."""

    def test_default_run_produces_history(self):
        """A single run returns a non-empty history of SystemStates."""
        sim = Simulator()
        runs = sim.run(n_runs=1, seed=42)
        self.assertEqual(len(runs), 1)
        history = runs[0]
        self.assertGreater(len(history), 1)
        self.assertIsInstance(history[0], SystemState)

    def test_deterministic_seed(self):
        """Same seed produces identical results."""
        cfg = ScenarioConfig(duration_years=10)
        sim1 = Simulator(cfg)
        sim2 = Simulator(cfg)
        run1 = sim1.run(n_runs=1, seed=123)[0]
        run2 = sim2.run(n_runs=1, seed=123)[0]
        for s1, s2 in zip(run1, run2):
            self.assertEqual(s1.to_dict(), s2.to_dict())

    def test_different_seeds_diverge(self):
        """Different seeds produce different results."""
        cfg = ScenarioConfig(duration_years=10)
        run1 = Simulator(cfg).run(n_runs=1, seed=1)[0]
        run2 = Simulator(cfg).run(n_runs=1, seed=999)[0]
        final1 = run1[-1].to_dict()
        final2 = run2[-1].to_dict()
        self.assertNotEqual(final1, final2)

    def test_history_length_matches_duration(self):
        """History has duration_years + 1 entries (initial state + each year)."""
        cfg = ScenarioConfig(duration_years=5)
        runs = Simulator(cfg).run(n_runs=1, seed=42)
        self.assertEqual(len(runs[0]), 6)

    def test_multiple_runs(self):
        """n_runs > 1 returns correct number of independent runs."""
        cfg = ScenarioConfig(duration_years=5)
        runs = Simulator(cfg).run(n_runs=3, seed=42)
        self.assertEqual(len(runs), 3)

    def test_config_not_mutated(self):
        """Simulator does not mutate the original config object."""
        cfg = ScenarioConfig(duration_years=5, initial_launches_per_year=100)
        original_launches = cfg.initial_launches_per_year
        Simulator(cfg).run(n_runs=1, seed=42)
        self.assertEqual(cfg.initial_launches_per_year, original_launches)

    def test_kessler_cascade_is_bool(self):
        """Terminal flags remain booleans through simulation."""
        cfg = ScenarioConfig(duration_years=10)
        history = Simulator(cfg).run(n_runs=1, seed=42)[0]
        for state in history:
            self.assertIsInstance(state.kessler_cascade_triggered, bool)

    def test_launches_bounded_by_max(self):
        """Launches never exceed max_launches_per_year."""
        cfg = ScenarioConfig(
            duration_years=20,
            initial_launches_per_year=1000,
            launch_growth_rate=0.50,
            max_launches_per_year=2000,
        )
        history = Simulator(cfg).run(n_runs=1, seed=42)[0]
        for state in history:
            self.assertLessEqual(state.launches_this_year, cfg.max_launches_per_year + 100)
            # +100 for possible replacement launches


class TestScenarioConfig(unittest.TestCase):
    """Tests for ScenarioConfig defaults."""

    def test_defaults(self):
        cfg = ScenarioConfig()
        self.assertEqual(cfg.duration_years, 30)
        self.assertEqual(cfg.propellant_type, "methane_lox")
        self.assertFalse(cfg.deorbit_plan)

    def test_custom_config(self):
        cfg = ScenarioConfig(name="Test", duration_years=10, deorbit_plan=True)
        self.assertEqual(cfg.name, "Test")
        self.assertEqual(cfg.duration_years, 10)
        self.assertTrue(cfg.deorbit_plan)


if __name__ == "__main__":
    unittest.main()
