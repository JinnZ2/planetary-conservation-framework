"""
Basic tests for constraint evaluation.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.constraints import (
    PlanetaryWaterBudget, AtmosphericComposition, AngularMomentumBudget,
    OrbitalCommons, CrustalMaterialThroughput, ThermosphericBalance,
    ConstraintStatus, evaluate_all
)
from src.cascade import CascadeEngine
from src.materials import MaterialLedger, MaterialEntry
from src.checker import ConstraintChecker


class TestWaterBudget(unittest.TestCase):
    def test_zero_launches_safe(self):
        c = PlanetaryWaterBudget()
        result = c.evaluate({
            "launches_per_year": 0,
            "propellant_type": "methane_lox"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_electric_launch_safe(self):
        c = PlanetaryWaterBudget()
        result = c.evaluate({
            "launches_per_year": 10000,
            "propellant_type": "electromagnetic"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_massive_combustion_violates(self):
        c = PlanetaryWaterBudget()
        result = c.evaluate({
            "launches_per_year": 5000,
            "propellant_type": "methane_lox",
            "propellant_per_launch_kg": 4_600_000
        })
        self.assertIn(result.status, [
            ConstraintStatus.WARNING,
            ConstraintStatus.CRITICAL,
            ConstraintStatus.VIOLATED
        ])

    def test_moderate_launches_not_violated(self):
        c = PlanetaryWaterBudget()
        result = c.evaluate({
            "launches_per_year": 50,
            "propellant_type": "methane_lox",
            "propellant_per_launch_kg": 4_600_000
        })
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)


class TestAtmosphericComposition(unittest.TestCase):
    def test_zero_launches_safe(self):
        c = AtmosphericComposition()
        result = c.evaluate({
            "launches_per_year": 0,
            "propellant_type": "methane_lox"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_electric_launch_safe(self):
        c = AtmosphericComposition()
        result = c.evaluate({
            "launches_per_year": 10000,
            "propellant_type": "electromagnetic"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_solid_high_cadence_violates_alumina(self):
        c = AtmosphericComposition()
        result = c.evaluate({
            "launches_per_year": 1000,
            "propellant_type": "solid"
        })
        # 1000 * 300 = 300,000 kg alumina vs 100,000 ceiling
        self.assertEqual(result.status, ConstraintStatus.VIOLATED)


class TestAngularMomentum(unittest.TestCase):
    def test_small_mass_with_deorbit_safe(self):
        c = AngularMomentumBudget()
        result = c.evaluate({
            "orbital_mass_kg": 100_000,
            "duration_years": 10,
            "deorbit_plan": True,
            "deorbit_timeline_years": 10
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_no_deorbit_plan_violates(self):
        c = AngularMomentumBudget()
        result = c.evaluate({
            "orbital_mass_kg": 100_000,
            "duration_years": 10,
            "deorbit_plan": False
        })
        self.assertEqual(result.status, ConstraintStatus.VIOLATED)


class TestOrbitalCommons(unittest.TestCase):
    def test_no_deorbit_plan_violates(self):
        c = OrbitalCommons()
        result = c.evaluate({
            "orbital_mass_kg": 1_000_000,
            "duration_years": 10,
            "deorbit_plan": False,
            "active_debris_removal": False,
            "deorbit_bond_funded": False
        })
        self.assertEqual(result.status, ConstraintStatus.VIOLATED)

    def test_full_compliance_not_violated(self):
        c = OrbitalCommons()
        result = c.evaluate({
            "orbital_mass_kg": 100_000,
            "duration_years": 5,
            "deorbit_plan": True,
            "active_debris_removal": True,
            "deorbit_bond_funded": True
        })
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)


class TestMinerals(unittest.TestCase):
    def test_one_module_within_limits(self):
        c = CrustalMaterialThroughput()
        result = c.evaluate({
            "modules_per_year": 1,
            "recycling_rate": 0.0
        })
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)

    def test_many_modules_violates(self):
        c = CrustalMaterialThroughput()
        result = c.evaluate({
            "modules_per_year": 50,
            "recycling_rate": 0.0
        })
        self.assertEqual(result.status, ConstraintStatus.VIOLATED)

    def test_recycling_helps(self):
        c = CrustalMaterialThroughput()
        no_recycle = c.evaluate({
            "modules_per_year": 10,
            "recycling_rate": 0.0
        })
        with_recycle = c.evaluate({
            "modules_per_year": 10,
            "recycling_rate": 0.9
        })
        self.assertGreater(
            with_recycle.margin_remaining_pct,
            no_recycle.margin_remaining_pct
        )


class TestThermosphericBalance(unittest.TestCase):
    def test_zero_launches_safe(self):
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 0,
            "propellant_type": "methane_lox"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)

    def test_electric_safe(self):
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 10000,
            "propellant_type": "electromagnetic"
        })
        self.assertEqual(result.status, ConstraintStatus.SAFE)


class TestEvaluateAll(unittest.TestCase):
    def test_benign_proposal(self):
        results = evaluate_all({
            "launches_per_year": 10,
            "propellant_type": "methane_lox",
            "orbital_mass_kg": 100_000,
            "duration_years": 5,
            "deorbit_plan": True,
            "deorbit_timeline_years": 10,
            "active_debris_removal": True,
            "deorbit_bond_funded": True,
            "modules_per_year": 1,
            "recycling_rate": 0.5
        })
        violations = [r for r in results
                      if r.status == ConstraintStatus.VIOLATED]
        self.assertEqual(len(violations), 0)

    def test_aggressive_proposal_has_violations(self):
        results = evaluate_all({
            "launches_per_year": 5000,
            "propellant_type": "methane_lox",
            "orbital_mass_kg": 5_000_000_000,
            "duration_years": 10,
            "deorbit_plan": False,
            "active_debris_removal": False,
            "deorbit_bond_funded": False,
            "modules_per_year": 50,
            "recycling_rate": 0.0
        })
        violations = [r for r in results
                      if r.status == ConstraintStatus.VIOLATED]
        self.assertGreater(len(violations), 0)


class TestCascadeEngine(unittest.TestCase):
    def test_cascade_from_launch_cadence(self):
        engine = CascadeEngine()
        paths = engine.trace_cascade("launch_cadence")
        self.assertGreater(len(paths), 0)

    def test_cascade_finds_loops(self):
        engine = CascadeEngine()
        paths = engine.trace_cascade("launch_cadence", max_depth=8)
        loops = [p for p in paths if p["is_loop"]]
        self.assertGreater(len(loops), 0)

    def test_cascade_json_export(self):
        engine = CascadeEngine()
        j = engine.to_json()
        data = json.loads(j)
        self.assertIn("links", data)
        self.assertIn("subsystems", data)


class TestMaterialLedger(unittest.TestCase):
    def test_record_and_retrieve(self):
        ledger = MaterialLedger()
        ledger.record(MaterialEntry(
            material="rare_earths",
            mass_kg=5000,
            origin="mine",
            destination="orbit",
            timestamp="2026-01-15T00:00:00"
        ))
        self.assertEqual(
            ledger.get_annual_consumption("rare_earths", 2026),
            5000
        )

    def test_cumulative_tracking(self):
        ledger = MaterialLedger()
        ledger.record(MaterialEntry(
            material="gallium",
            mass_kg=10,
            origin="mine",
            destination="factory",
            timestamp="2026-01-01T00:00:00"
        ))
        ledger.record(MaterialEntry(
            material="gallium",
            mass_kg=15,
            origin="factory",
            destination="orbit",
            timestamp="2026-06-01T00:00:00"
        ))
        self.assertEqual(ledger.get_cumulative("gallium"), 25)

    def test_ceiling_check(self):
        ledger = MaterialLedger()
        ledger.record(MaterialEntry(
            material="gallium",
            mass_kg=100,
            origin="mine",
            destination="orbit",
            timestamp="2026-01-01T00:00:00"
        ))
        result = ledger.check_against_ceiling(
            material="gallium",
            year=2026,
            global_production_kg=500_000,
            threshold_fraction=0.0001
        )
        # ceiling = 50 kg, consumed = 100 kg → EXCEEDED
        self.assertEqual(result["status"], "EXCEEDED")

    def test_energy_audit(self):
        ledger = MaterialLedger()
        ledger.record(MaterialEntry(
            material="copper",
            mass_kg=1000,
            origin="mine",
            destination="factory",
            energy_cost_kwh=50000,
            co2_cost_kg=25000
        ))
        audit = ledger.energy_audit()
        self.assertEqual(audit["total_energy_kwh"], 50000)
        self.assertEqual(audit["total_co2_kg"], 25000)


class TestConstraintChecker(unittest.TestCase):
    def test_check_produces_report(self):
        checker = ConstraintChecker(log_file="/dev/null")
        result = checker.check_proposal({
            "name": "Test Proposal",
            "launches_per_year": 100,
            "propellant_type": "methane_lox",
            "orbital_mass_kg": 1_000_000,
            "duration_years": 5,
            "deorbit_plan": True,
            "deorbit_timeline_years": 10,
            "active_debris_removal": True,
            "deorbit_bond_funded": True,
            "modules_per_year": 1,
            "recycling_rate": 0.5
        })
        self.assertIsNotNone(result.summary)
        self.assertIsNotNone(result.timestamp)
        self.assertGreater(len(result.constraint_results), 0)

    def test_report_json_export(self):
        checker = ConstraintChecker(log_file="/dev/null")
        result = checker.check_proposal({
            "name": "JSON Test",
            "launches_per_year": 10,
            "propellant_type": "methane_lox",
            "orbital_mass_kg": 100_000,
            "duration_years": 5,
            "deorbit_plan": True,
            "deorbit_timeline_years": 10,
            "active_debris_removal": True,
            "deorbit_bond_funded": True,
            "modules_per_year": 1,
            "recycling_rate": 0.5
        })
        j = result.to_json()
        data = json.loads(j)
        self.assertIn("viable", data)
        self.assertIn("constraints", data)


# Need json import for TestCascadeEngine and TestConstraintChecker
import json


if __name__ == "__main__":
    unittest.main()
