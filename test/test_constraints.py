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
from src.planetary_constants import (
    EARTH_ENERGY_IMBALANCE,
    eei_to_total_power_w,
    eei_to_annual_heat_zj,
    eei_from_ohc_trend,
    partition_excess_energy,
    accumulated_heat_zj,
    forcing_as_eei_fraction,
    compute_margins,
)


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


    def test_kerosene_lox_handled(self):
        c = PlanetaryWaterBudget()
        result = c.evaluate({
            "launches_per_year": 50,
            "propellant_type": "kerosene_lox",
            "propellant_per_launch_kg": 4_600_000
        })
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)
        self.assertGreater(result.current_value, 0)

    def test_hydrogen_lox_produces_more_h2o(self):
        c = PlanetaryWaterBudget()
        methane = c.evaluate({
            "launches_per_year": 100,
            "propellant_type": "methane_lox",
            "propellant_per_launch_kg": 2_000_000
        })
        hydrogen = c.evaluate({
            "launches_per_year": 100,
            "propellant_type": "hydrogen_lox",
            "propellant_per_launch_kg": 2_000_000
        })
        # H2/LOX produces more H2O per kg propellant than methane/LOX
        self.assertGreater(hydrogen.current_value, methane.current_value)


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

    def test_hydrogen_lox_safe(self):
        c = AtmosphericComposition()
        result = c.evaluate({
            "launches_per_year": 10000,
            "propellant_type": "hydrogen_lox"
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

    def test_steady_state_heating_model(self):
        """Heating should reflect steady-state BC (annual × residence time)."""
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 100,
            "propellant_type": "methane_lox"
        })
        # 100 launches × 50 kg BC × 4 yr residence × 1e-6 = 0.02 W/m²
        expected_heating = 100 * 50 * 4.0 * 1e-6
        self.assertAlmostEqual(result.current_value, expected_heating, places=6)

    def test_solid_produces_soot(self):
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 100,
            "propellant_type": "solid"
        })
        self.assertGreater(result.current_value, 0)


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


class TestEarthEnergyImbalance(unittest.TestCase):
    """
    Tests for the WMO State of the Global Climate 2025 energy-imbalance
    equations and constants.
    """

    def test_partition_fractions_sum_to_one(self):
        total = sum(EARTH_ENERGY_IMBALANCE["partition_fraction"].values())
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_eei_to_total_power_w(self):
        # 1 W/m² across Earth's surface = ~5.10e14 W
        power = eei_to_total_power_w(1.0)
        self.assertAlmostEqual(power, 5.10e14, places=0)

    def test_eei_to_annual_heat_zj_scales_linearly(self):
        one = eei_to_annual_heat_zj(1.0)
        two = eei_to_annual_heat_zj(2.0)
        self.assertAlmostEqual(two, 2.0 * one, places=6)

    def test_eei_annual_heat_matches_expected_magnitude(self):
        # 1 W/m² × 5.10e14 m² × 3.156e7 s ≈ 1.61e22 J ≈ 16.1 ZJ/yr
        heat_zj = eei_to_annual_heat_zj(1.0)
        self.assertAlmostEqual(heat_zj, 16.1, delta=0.2)

    def test_eei_from_ohc_trend_roundtrip(self):
        # Forward: EEI → annual heat → ocean share → implied EEI
        eei_in = 1.30
        total_heat_zj = eei_to_annual_heat_zj(eei_in)
        ocean_heat_zj = total_heat_zj * 0.91
        eei_out = eei_from_ohc_trend(ocean_heat_zj,
                                     ocean_partition_fraction=0.91)
        self.assertAlmostEqual(eei_in, eei_out, places=6)

    def test_wmo_11_zj_per_yr_headline(self):
        # WMO 2025: ~11 ZJ/yr additional uptake between 2005 and 2025.
        # Dividing by the ocean share should imply an EEI increment
        # consistent with the published ~0.5-0.9 W/m² range.
        implied_eei = eei_from_ohc_trend(11.0)
        self.assertGreater(implied_eei, 0.5)
        self.assertLess(implied_eei, 0.9)

    def test_partition_excess_energy_preserves_total(self):
        eei = 1.30
        allocated = partition_excess_energy(eei)
        self.assertAlmostEqual(sum(allocated.values()), eei, places=6)
        # Ocean must dominate per WMO 2025.
        self.assertGreater(allocated["ocean"],
                           allocated["land"]
                           + allocated["ice"]
                           + allocated["atmosphere"])

    def test_accumulated_heat_zj_linear(self):
        eei = 1.30
        one_year = accumulated_heat_zj(eei, 1)
        ten_years = accumulated_heat_zj(eei, 10)
        self.assertAlmostEqual(ten_years, 10 * one_year, places=6)

    def test_forcing_as_eei_fraction(self):
        # A 0.013 W/m² launch forcing against 1.30 W/m² EEI = 1%
        frac = forcing_as_eei_fraction(0.013, baseline_eei_w_m2=1.30)
        self.assertAlmostEqual(frac, 0.01, places=6)

    def test_forcing_fraction_defaults_to_wmo_mean(self):
        # Without explicit baseline, should use 2020-2025 WMO mean (1.30).
        frac_default = forcing_as_eei_fraction(1.30)
        self.assertAlmostEqual(frac_default, 1.0, places=6)

    def test_co2_and_temperature_sanity(self):
        self.assertGreater(EARTH_ENERGY_IMBALANCE["co2_ppm"], 420)
        self.assertAlmostEqual(
            EARTH_ENERGY_IMBALANCE["temperature_anomaly_c_2025"], 1.43, places=2
        )

    def test_compute_margins_includes_eei(self):
        margins = compute_margins()
        self.assertIn("earth_energy_imbalance", margins)
        eei_m = margins["earth_energy_imbalance"]
        self.assertIn("current_eei_w_m2", eei_m)
        self.assertIn("partition_w_m2", eei_m)
        self.assertIn("annual_heat_zj", eei_m)
        # Current EEI should exceed the historical baseline.
        self.assertGreater(eei_m["current_eei_w_m2"],
                           eei_m["historical_eei_w_m2"])


class TestThermosphericBalanceEEIContext(unittest.TestCase):
    """ThermosphericBalance should reference the WMO 2025 EEI baseline."""

    def test_background_eei_constant_present(self):
        self.assertTrue(hasattr(ThermosphericBalance, "BACKGROUND_EEI_W_PER_M2"))
        self.assertAlmostEqual(
            ThermosphericBalance.BACKGROUND_EEI_W_PER_M2, 1.30, places=2
        )

    def test_mechanism_reports_eei_context(self):
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 100,
            "propellant_type": "methane_lox"
        })
        self.assertIn("WMO", result.mechanism)
        self.assertIn("EEI", result.mechanism)

    def test_wmo_source_cited(self):
        c = ThermosphericBalance()
        result = c.evaluate({
            "launches_per_year": 10,
            "propellant_type": "methane_lox"
        })
        self.assertTrue(
            any("WMO" in src for src in result.data_sources),
            f"Expected WMO in data_sources, got {result.data_sources}"
        )


class TestCascadeEngineClimateLink(unittest.TestCase):
    """The climate → debris coupling (WMO EEI context) should be present."""

    def test_climate_to_debris_link_exists(self):
        engine = CascadeEngine()
        paths = engine.trace_cascade("climate", max_depth=4)
        targets = {step["to"] for p in paths for step in p["path"]}
        self.assertIn("debris", targets)

    def test_climate_to_thermosphere_link_exists(self):
        engine = CascadeEngine()
        paths = engine.trace_cascade("climate", max_depth=4)
        targets = {step["to"] for p in paths for step in p["path"]}
        self.assertIn("thermosphere", targets)


if __name__ == "__main__":
    unittest.main()
