"""
Basic tests for constraint evaluation.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

import unittest
import sys
import os
from copy import deepcopy
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
    MINERALS,
    MINERAL_KEY_ALIASES,
    SPACE_EXPORT_THRESHOLD_FRACTION,
    canonical_mineral_key,
    conservation_ceiling_kg_yr,
    overshoot_ratio,
    production_kg_yr,
    space_export_ceiling_kg_yr,
    CLIMATE_2025,
    co2_ppm,
    co2_pct_of_preindustrial,
    sea_level_rise_mm_yr_total,
    unverified_indicators,
)
from src.locations import ALL_SITES, GLOBAL_SEA_LEVEL_RISE_MM_PER_YEAR
from stratospheric_aerosol_injection_audit import CONSTANTS as SAI_CONSTANTS
from src.constants import MINERAL_DATA
from leverage_analysis import (
    LeverageAnalyzer,
    STANDARD_LEVERS,
    MEADOWS_LEVELS,
)
from transition_pathways import (
    TransitionPlanner,
    TransitionStep,
    Domain,
    Durability,
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

    def test_declared_rare_earth_field_is_honored(self):
        """rare_earth_kg_per_year is a documented proposal field and must bind.

        Regression: the field was documented in the schema but never read, so a
        proposal declaring rare earth demand above the ceiling reported SAFE.
        """
        c = CrustalMaterialThroughput()
        # Ceiling = 350_000_000 * 0.0001 = 35_000 kg/yr
        result = c.evaluate({
            "modules_per_year": 1,
            "recycling_rate": 0.0,
            "rare_earth_kg_per_year": 50_000,
        })
        self.assertEqual(result.status, ConstraintStatus.VIOLATED)
        self.assertAlmostEqual(result.current_value, 50_000)
        self.assertAlmostEqual(result.ceiling_value, 35_000)

    def test_declared_rare_earth_respects_recycling(self):
        c = CrustalMaterialThroughput()
        result = c.evaluate({
            "modules_per_year": 1,
            "recycling_rate": 0.5,
            "rare_earth_kg_per_year": 50_000,
        })
        self.assertAlmostEqual(result.current_value, 25_000)
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)

    def test_material_requirements_overrides_declared_field(self):
        """Most specific declaration wins: material_requirements_kg > shortcut."""
        c = CrustalMaterialThroughput()
        result = c.evaluate({
            "modules_per_year": 1,
            "recycling_rate": 0.0,
            "rare_earth_kg_per_year": 50_000,
            "material_requirements_kg": {"rare_earths": 1_000},
        })
        self.assertNotEqual(result.status, ConstraintStatus.VIOLATED)
        self.assertNotIn("rare_earths", result.notes)

    def test_reports_real_values_not_zero(self):
        """Law 6 previously hardcoded current/ceiling to 0, making reports blank."""
        c = CrustalMaterialThroughput()
        result = c.evaluate({"modules_per_year": 50, "recycling_rate": 0.0})
        self.assertGreater(result.current_value, 0)
        self.assertGreater(result.ceiling_value, 0)
        self.assertIn("kg/year", result.unit)


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


class TestConstantsUnification(unittest.TestCase):
    """planetary_constants.MINERALS is the single source of truth.

    Regression: three modules each kept their own copy of global production and
    silently disagreed on cobalt (190,000,000 vs 220,000,000 kg/yr) for the life
    of the duplication. These tests fail if any copy reappears.
    """

    def test_all_modules_agree_on_production(self):
        for legacy_key in MINERAL_KEY_ALIASES:
            canonical = production_kg_yr(legacy_key)
            with self.subTest(mineral=legacy_key):
                self.assertEqual(
                    MINERAL_DATA[legacy_key]["global_production_kg_per_year"],
                    canonical,
                    "src/constants.py disagrees with planetary_constants",
                )
                self.assertEqual(
                    CrustalMaterialThroughput.GLOBAL_PRODUCTION[legacy_key],
                    canonical,
                    "src/constraints.py disagrees with planetary_constants",
                )

    def test_same_mineral_set_across_modules(self):
        self.assertEqual(
            set(MINERAL_DATA),
            set(CrustalMaterialThroughput.GLOBAL_PRODUCTION),
        )
        self.assertEqual(set(MINERAL_DATA), set(MINERAL_KEY_ALIASES))

    def test_space_export_ceiling_is_derived_not_stored(self):
        for legacy_key in MINERAL_KEY_ALIASES:
            with self.subTest(mineral=legacy_key):
                self.assertAlmostEqual(
                    space_export_ceiling_kg_yr(legacy_key),
                    production_kg_yr(legacy_key) * SPACE_EXPORT_THRESHOLD_FRACTION,
                )
                self.assertAlmostEqual(
                    MINERAL_DATA[legacy_key]["space_export_ceiling_kg_yr"],
                    space_export_ceiling_kg_yr(legacy_key),
                )

    def test_law6_threshold_matches_canonical_fraction(self):
        self.assertEqual(
            CrustalMaterialThroughput.THRESHOLD_FRACTION,
            SPACE_EXPORT_THRESHOLD_FRACTION,
        )

    def test_stored_overshoot_ratio_matches_derived(self):
        """ratio_current_to_ceiling is a cross-check; it must not drift."""
        for mineral, data in MINERALS.items():
            with self.subTest(mineral=mineral):
                self.assertAlmostEqual(
                    data["ratio_current_to_ceiling"],
                    overshoot_ratio(mineral),
                    places=2,
                )

    def test_two_ceilings_are_distinct_quantities(self):
        """The space-export cap and the conservation ceiling are unrelated.

        Conflating them is the confusion this unification exists to end: the
        space cap is a fraction of production, the conservation ceiling is a
        reserve-horizon limit on all use.
        """
        for legacy_key in MINERAL_KEY_ALIASES:
            with self.subTest(mineral=legacy_key):
                self.assertLess(
                    space_export_ceiling_kg_yr(legacy_key),
                    conservation_ceiling_kg_yr(legacy_key),
                )

    def test_alias_resolution(self):
        self.assertEqual(canonical_mineral_key("rare_earths"), "rare_earth_aggregate")
        self.assertEqual(canonical_mineral_key("high_purity_copper"), "copper")
        # Canonical names resolve to themselves.
        self.assertEqual(canonical_mineral_key("tantalum"), "tantalum")
        with self.assertRaises(KeyError):
            canonical_mineral_key("unobtainium")

    def test_cobalt_production_matches_cited_source(self):
        """USGS MCS 2025 reports ~290,000 t world mine production for 2024."""
        cobalt = MINERALS["cobalt"]
        self.assertEqual(cobalt["current_production_kg_yr"], 290_000_000)
        self.assertTrue(cobalt.get("production_verified"))
        self.assertIn("USGS", cobalt.get("production_source", ""))


class TestClimate2025(unittest.TestCase):
    """CLIMATE_2025 is the single source for observed climate indicators.

    Regression guard: CO2 was stored in two places (planetary_constants and
    stratospheric_aerosol_injection_audit) before this block existed. Mineral
    production figures already taught this repo what duplicate constants cost.
    """

    def test_eei_co2_derives_from_climate_block(self):
        self.assertEqual(EARTH_ENERGY_IMBALANCE["co2_ppm"], co2_ppm())
        self.assertEqual(
            EARTH_ENERGY_IMBALANCE["co2_ppm_uncertainty"],
            CLIMATE_2025["greenhouse_gases"]["co2_ppm_uncertainty"])

    def test_sai_audit_co2_matches_canonical(self):
        """The SAI audit keeps a deliberate mirror so it stays dependency-free.

        A mirror is acceptable only while something checks it. This is that
        something — if it fails, update stratospheric_aerosol_injection_audit
        CONSTANTS["current_co2_ppm"] to match CLIMATE_2025.
        """
        self.assertEqual(SAI_CONSTANTS["current_co2_ppm"], co2_ppm())

    def test_co2_percentage_is_derived_not_stored(self):
        gh = CLIMATE_2025["greenhouse_gases"]
        expected = gh["co2_ppm"] / gh["co2_preindustrial_ppm"] * 100.0
        self.assertAlmostEqual(co2_pct_of_preindustrial(), expected)
        self.assertAlmostEqual(
            EARTH_ENERGY_IMBALANCE["co2_pct_of_preindustrial"], expected)

    def test_co2_matches_reported_53_percent_increase(self):
        """BAMS reports 425.6 ppm as a 53% increase over ~278 ppm."""
        increase = co2_pct_of_preindustrial() - 100.0
        self.assertAlmostEqual(increase, 53.0, delta=0.5)

    def test_sea_level_total_is_sum_of_components(self):
        ocean = CLIMATE_2025["ocean"]
        self.assertAlmostEqual(
            sea_level_rise_mm_yr_total(),
            ocean["slr_thermal_expansion_mm_yr_since_2005"]
            + ocean["slr_ice_melt_mm_yr_since_2005"])

    def test_locations_derives_global_slr(self):
        self.assertEqual(GLOBAL_SEA_LEVEL_RISE_MM_PER_YEAR,
                         sea_level_rise_mm_yr_total())

    def test_unverified_indicators_are_reported_not_hidden(self):
        """Figures that could not be confirmed must stay queryable."""
        unverified = unverified_indicators()
        self.assertIn("cryosphere", unverified)
        self.assertIn("tropical_cyclones", unverified)
        self.assertIn("greenhouse_gases.ch4", unverified)
        self.assertIn("greenhouse_gases.n2o", unverified)
        # CO2 and sea level WERE confirmed and must not appear.
        self.assertNotIn("greenhouse_gases.co2", unverified)
        self.assertNotIn("ocean.sea_level", unverified)

    def test_current_state_json_matches_canonical(self):
        """The published data file is a claim too.

        README tells AI systems to load data/current_state.json. No Python
        reads it, so nothing else would catch it drifting from the code.
        """
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "current_state.json")
        with open(path) as f:
            state = json.load(f)

        observed = state["observed_climate_2025"]
        ocean = CLIMATE_2025["ocean"]
        self.assertEqual(observed["co2_ppm"], co2_ppm())
        self.assertEqual(state["earth_energy_imbalance"]["co2_ppm"], co2_ppm())
        self.assertEqual(
            observed["sea_level_mm_above_1993_baseline"],
            ocean["sea_level_mm_above_1993_baseline"])
        self.assertAlmostEqual(
            observed["sea_level_rise_mm_per_yr_since_2005"],
            sea_level_rise_mm_yr_total())
        self.assertAlmostEqual(
            state["earth_energy_imbalance"]["co2_pct_of_preindustrial"],
            co2_pct_of_preindustrial(), places=1)
        self.assertEqual(sorted(observed["unverified"]),
                         sorted(unverified_indicators()))

    def test_every_site_slr_carries_a_source_string(self):
        for site in ALL_SITES:
            with self.subTest(site=site.name):
                self.assertTrue(site.sea_level_rise_source.strip(),
                                "site SLR figure has no attribution")

    def test_site_slr_rates_are_plausible_against_global(self):
        """Local rates vary regionally, but not by an order of magnitude."""
        for site in ALL_SITES:
            with self.subTest(site=site.name):
                self.assertGreater(site.slr_vs_global(), 0.25)
                self.assertLess(site.slr_vs_global(), 4.0)

    def test_elevation_headroom_orders_sites_by_exposure(self):
        boca = next(s for s in ALL_SITES if "Starbase" in s.name)
        vandenberg = next(s for s in ALL_SITES if "Vandenberg" in s.name)
        self.assertLess(boca.elevation_headroom_years(),
                        vandenberg.elevation_headroom_years())


class TestLeverageAnalysis(unittest.TestCase):
    """leverage_analysis ranks modifications by conservation bought per effort."""

    AGGRESSIVE = {
        "name": "Orbital Data Center Phase 1",
        "launches_per_year": 500,
        "payload_mass_kg": 100_000,
        "propellant_type": "methane_lox",
        "orbital_mass_kg": 5_000_000,
        "duration_years": 10,
        "rare_earth_kg_per_year": 50_000,
        "modules_per_year": 1,
        "deorbit_plan": False,
        "recycling_rate": 0.0,
    }

    def setUp(self):
        self.analyzer = LeverageAnalyzer()
        self.levers = {l.name: l for l in STANDARD_LEVERS}

    def test_analysis_does_not_mutate_the_proposal(self):
        """Levers must operate on copies — callers reuse their proposal dicts."""
        original = dict(self.AGGRESSIVE)
        self.analyzer.rank(self.AGGRESSIVE)
        self.assertEqual(self.AGGRESSIVE, original)

    def test_deorbit_commitment_resolves_law_3(self):
        result = self.analyzer.analyze_lever(
            self.AGGRESSIVE, self.levers["commit_deorbit_plan"])
        resolved = [d.law_number for d in result.law_deltas if d.resolved]
        self.assertIn(3, resolved)
        self.assertEqual(result.violations_created, 0)

    def test_partial_orbital_compliance_buys_nothing_on_law_5(self):
        """Law 5 clamps unless deorbit plan AND removal AND bond are all set."""
        bond_only = self.analyzer.analyze_lever(
            self.AGGRESSIVE, self.levers["fund_deorbit_bond"])
        self.assertEqual(bond_only.violations_resolved, 0)

        full = self.analyzer.analyze_lever(
            self.AGGRESSIVE, self.levers["full_orbital_compliance"])
        resolved = [d.law_number for d in full.law_deltas if d.resolved]
        self.assertIn(5, resolved)

    def test_hydrogen_fixes_soot_but_not_the_water_budget(self):
        """The counterintuitive result: hydrogen/LOX is not a water-budget fix.

        Methane at 4.6e6 kg x 0.39 H2O fraction and hydrogen at 2.0e6 kg x 0.9
        produce almost identical H2O per launch. Hydrogen removes black carbon
        entirely, so it resolves Law 7 while leaving Law 1 essentially unmoved.
        """
        result = self.analyzer.analyze_lever(
            self.AGGRESSIVE, self.levers["propellant_to_hydrogen"])
        by_law = {d.law_number: d for d in result.law_deltas}
        self.assertTrue(by_law[7].resolved)
        self.assertFalse(by_law[1].resolved)
        # Law 1 does not merely fail to improve — it gets marginally worse,
        # by ~1.05 percentage points at 500 launches/year.
        self.assertLess(by_law[1].delta, 0)
        self.assertLess(abs(by_law[1].delta), 2.0)

    def test_policy_switch_outranks_parameter_push(self):
        """Meadows' claim, tested rather than asserted."""
        ranked = self.analyzer.rank(self.AGGRESSIVE)
        scores = {r.lever.name: r.leverage_score for r in ranked}
        self.assertGreater(scores["commit_deorbit_plan"],
                           scores["halve_launch_cadence"])

    def test_ranking_is_sorted_descending(self):
        ranked = self.analyzer.rank(self.AGGRESSIVE)
        scores = [r.leverage_score for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_minimum_viable_set_actually_clears_violations(self):
        minimal = self.analyzer.minimum_viable_set(self.AGGRESSIVE)
        self.assertIsNotNone(minimal)
        proposal = deepcopy(self.AGGRESSIVE)
        for lever in minimal:
            lever.apply(proposal)
        violated = [r for r in evaluate_all(proposal)
                    if r.status == ConstraintStatus.VIOLATED]
        self.assertEqual(violated, [])

    def test_every_lever_has_a_known_meadows_rank(self):
        for lever in STANDARD_LEVERS:
            with self.subTest(lever=lever.name):
                self.assertIn(lever.meadows_rank, MEADOWS_LEVELS)


class TestTransitionPathways(unittest.TestCase):
    """transition_pathways models the institutional steps that unlock levers."""

    def setUp(self):
        self.planner = TransitionPlanner()

    def test_pathway_has_no_prerequisite_cycles(self):
        order = self.planner.topological_order()
        self.assertEqual(len(order), len(self.planner.steps))

    def test_topological_order_respects_prerequisites(self):
        seen = set()
        for step in self.planner.topological_order():
            for prereq in step.prerequisites:
                self.assertIn(prereq, seen,
                              f"{step.step_id} ordered before {prereq}")
            seen.add(step.step_id)

    def test_cycle_is_detected(self):
        a = TransitionStep(step_id="a", name="A", domain=Domain.GOVERNANCE,
                           description="", actor="", prerequisites=["b"])
        b = TransitionStep(step_id="b", name="B", domain=Domain.GOVERNANCE,
                           description="", actor="", prerequisites=["a"])
        with self.assertRaises(ValueError):
            TransitionPlanner([a, b])

    def test_unknown_prerequisite_is_rejected(self):
        orphan = TransitionStep(
            step_id="orphan", name="Orphan", domain=Domain.GOVERNANCE,
            description="", actor="", prerequisites=["does_not_exist"])
        with self.assertRaises(ValueError):
            TransitionPlanner([orphan])

    def test_registry_is_the_top_keystone(self):
        """Attribution is impossible without it, so everything routes through."""
        top_step, unlocked = self.planner.keystones()[0]
        self.assertEqual(top_step.step_id, "orbital_registry")
        self.assertGreater(unlocked, 0)

    def test_critical_path_starts_at_a_step_with_no_prerequisites(self):
        chain, total = self.planner.critical_path()
        self.assertEqual(chain[0].prerequisites, [])
        self.assertGreater(total, 0)

    def test_completion_time_exceeds_start_by_duration(self):
        for step in self.planner.steps:
            with self.subTest(step=step.step_id):
                self.assertAlmostEqual(
                    self.planner.completion_time(step.step_id)
                    - self.planner.earliest_start(step.step_id),
                    step.time_years)

    def test_steps_to_unlock_includes_the_provider_and_its_prerequisites(self):
        chain = self.planner.steps_to_unlock("commit_deorbit_plan")
        self.assertIsNotNone(chain)
        ids = [s.step_id for s in chain]
        self.assertIn("orbital_registry", ids)
        # Chain must be self-contained: every prerequisite present.
        for step in chain:
            for prereq in step.prerequisites:
                self.assertIn(prereq, ids)

    def test_unknown_lever_unlocks_nothing(self):
        self.assertIsNone(self.planner.steps_to_unlock("no_such_lever"))

    def test_decaying_foundations_are_load_bearing(self):
        """A DECAYS step with dependents is a maintenance obligation."""
        for step in self.planner.decaying_foundations():
            with self.subTest(step=step.step_id):
                self.assertEqual(step.durability, Durability.DECAYS)
                self.assertGreater(len(self.planner.dependents(step.step_id)), 0)


if __name__ == "__main__":
    unittest.main()
