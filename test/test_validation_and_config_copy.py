"""
Two cases ported from 00fea0f:
  1. check_proposal raises ValueError when a required field is missing
  2. Simulator keeps its own copy of the config it is given

Each test also runs the earlier behaviour, so the difference is visible.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 JinnZ2
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.checker import ConstraintChecker
from src.simulator import ScenarioConfig, Simulator

FULL = {
    "name": "t",
    "launches_per_year": 10,
    "propellant_type": "methane_lox",
    "orbital_mass_kg": 1_000_000,
    "duration_years": 5,
}


class AliasedSimulator(Simulator):
    """The constructor as it was before the change: keeps the caller's object."""

    def __init__(self, config=None):
        self.config = config or ScenarioConfig()
        self.history = []


class TestRequiredFields(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.checker = ConstraintChecker(log_file=os.path.join(self.tmp, "log.jsonl"))

    def test_full_proposal_is_accepted(self):
        self.checker.check_proposal(dict(FULL))

    def test_each_missing_field_is_named(self):
        for field in FULL:
            with self.subTest(field=field):
                p = dict(FULL)
                del p[field]
                with self.assertRaises(ValueError) as cm:
                    self.checker.check_proposal(p)
                self.assertIn(field, str(cm.exception))

    def test_empty_proposal_names_all_five(self):
        with self.assertRaises(ValueError) as cm:
            self.checker.check_proposal({})
        for field in FULL:
            self.assertIn(field, str(cm.exception))


class TestConfigIsCopied(unittest.TestCase):
    def test_mutation_after_construction(self):
        # before: the simulator follows the caller's later change
        cfg = ScenarioConfig(duration_years=30)
        old = AliasedSimulator(cfg)
        cfg.duration_years = 3
        self.assertIs(old.config, cfg)
        self.assertEqual(old.config.duration_years, 3)

        # after: it keeps the value it was built with
        cfg = ScenarioConfig(duration_years=30)
        new = Simulator(cfg)
        cfg.duration_years = 3
        self.assertIsNot(new.config, cfg)
        self.assertEqual(new.config.duration_years, 30)

    def test_run_length_follows_the_copy(self):
        cfg = ScenarioConfig(duration_years=4)
        sim = Simulator(cfg)
        cfg.duration_years = 1
        history = sim.run(n_runs=1, seed=0)[0]
        aliased = AliasedSimulator(ScenarioConfig(duration_years=1)).run(n_runs=1, seed=0)[0]
        self.assertGreater(len(history), len(aliased))

    def test_no_config_still_gives_default(self):
        self.assertEqual(Simulator().config.duration_years, ScenarioConfig().duration_years)


if __name__ == "__main__":
    unittest.main()
