"""
Planetary Conservation Framework - Atomic Accounting Layer
===========================================================
Treats Earth as a closed mass system with launch flux constraints.
Models element-level depletion timelines under various space
infrastructure scenarios.

Core principle: dM_earth = M_in - M_out (conservation is non-negotiable)

Author: Kavik + Claude
Repository: https://github.com/JinnZ2/planetary-conservation-framework
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

# Natural meteoritic influx to Earth (~tonnes/year)
METEORITIC_INFLUX_TONNES_YR = 40_000

# Thermodynamic minimum energy to LEO (MJ/kg)
THERMO_MIN_LEO_MJ_KG = 32.0

# Current practical energy to LEO (MJ/kg)
PRACTICAL_LEO_MJ_KG = 65.0

# Delta-v Earth surface to LEO (m/s)
DELTA_V_LEO = 9_400


# =============================================================================
# ELEMENT REGISTRY
# =============================================================================

@dataclass
class Element:
    symbol: str
    name: str
    terrestrial_reserves: float  # tonnes
    extraction_rate: float       # tonnes/year
    recycling_rate: float        # tonnes/year
    cascade_threshold: float = 0.15
    space_hardware_weight: float = 0.0

    def years_to_depletion(self, additional_demand: float = 0.0) -> float:
        net_draw = (self.extraction_rate - self.recycling_rate) + additional_demand
        if net_draw <= 0:
            return float('inf')
        usable = self.terrestrial_reserves * (1.0 - self.cascade_threshold)
        return usable / net_draw

    def depletion_trajectory(self, years: int, additional_demand: float = 0.0) -> List[float]:
        net_draw = (self.extraction_rate - self.recycling_rate) + additional_demand
        trajectory = []
        remaining = self.terrestrial_reserves
        for _ in range(years):
            remaining -= net_draw
            remaining = max(0.0, remaining)
            trajectory.append(remaining / self.terrestrial_reserves)
        return trajectory


def build_default_registry() -> Dict[str, Element]:
    return {
        "Cu": Element(
            symbol="Cu", name="Copper",
            terrestrial_reserves=890_000_000,
            extraction_rate=22_000_000,
            recycling_rate=4_000_000,
            cascade_threshold=0.15,
            space_hardware_weight=0.85,
        ),
        "Li": Element(
            symbol="Li", name="Lithium",
            terrestrial_reserves=98_000_000,
            extraction_rate=180_000,
            recycling_rate=18_000,
            cascade_threshold=0.20,
            space_hardware_weight=0.40,
        ),
        "Si": Element(
            symbol="Si", name="Silicon",
            terrestrial_reserves=1_000_000_000_000,
            extraction_rate=8_500_000,
            recycling_rate=1_200_000,
            cascade_threshold=0.05,
            space_hardware_weight=0.95,
        ),
        "Al": Element(
            symbol="Al", name="Aluminum",
            terrestrial_reserves=75_000_000_000,
            extraction_rate=69_000_000,
            recycling_rate=20_000_000,
            cascade_threshold=0.10,
            space_hardware_weight=0.70,
        ),
        "Co": Element(
            symbol="Co", name="Cobalt",
            terrestrial_reserves=8_300_000,
            extraction_rate=190_000,
            recycling_rate=25_000,
            cascade_threshold=0.20,
            space_hardware_weight=0.50,
        ),
        "Nd": Element(
            symbol="Nd", name="Neodymium",
            terrestrial_reserves=8_000_000,
            extraction_rate=35_000,
            recycling_rate=3_500,
            cascade_threshold=0.25,
            space_hardware_weight=0.30,
        ),
        "In": Element(
            symbol="In", name="Indium",
            terrestrial_reserves=18_000,
            extraction_rate=900,
            recycling_rate=400,
            cascade_threshold=0.30,
            space_hardware_weight=0.60,
        ),
        "Ga": Element(
            symbol="Ga", name="Gallium",
            terrestrial_reserves=110_000,
            extraction_rate=500,
            recycling_rate=150,
            cascade_threshold=0.25,
            space_hardware_weight=0.65,
        ),
        "Ta": Element(
            symbol="Ta", name="Tantalum",
            terrestrial_reserves=140_000,
            extraction_rate=1_800,
            recycling_rate=500,
            cascade_threshold=0.20,
            space_hardware_weight=0.55,
        ),
    }


# =============================================================================
# LAUNCH MANIFEST
# =============================================================================

@dataclass
class LaunchPayload:
    name: str
    total_mass_kg: float
    composition: Dict[str, float] = field(default_factory=dict)
    recovery_rate: float = 0.0

    def net_element_loss(self) -> Dict[str, float]:
        loss = {}
        for element, fraction in self.composition.items():
            mass_kg = self.total_mass_kg * fraction
            net = mass_kg * (1.0 - self.recovery_rate)
            loss[element] = net
        return loss


def default_datacenter_payload() -> LaunchPayload:
    return LaunchPayload(
        name="Orbital Data Center Module",
        total_mass_kg=5_000,
        composition={
            "Al": 0.35,
            "Cu": 0.15,
            "Si": 0.05,
            "Co": 0.02,
            "Li": 0.01,
            "In": 0.003,
            "Ga": 0.002,
            "Ta": 0.005,
            "Nd": 0.003,
        },
        recovery_rate=0.0,
    )


# =============================================================================
# SCENARIO ENGINE
# =============================================================================

@dataclass
class Scenario:
    name: str
    payloads: List[LaunchPayload]
    launches_per_year: int
    duration_years: int
    recovery_improvement_rate: float = 0.0
    max_recovery_rate: float = 0.95


class AtomicAccountant:
    def __init__(self, registry: Optional[Dict[str, Element]] = None):
        self.registry = registry or build_default_registry()

    def annual_element_demand(self, scenario: Scenario, year: int = 0) -> Dict[str, float]:
        demand = {}
        for payload in scenario.payloads:
            improved_recovery = min(
                payload.recovery_rate + (scenario.recovery_improvement_rate * year),
                scenario.max_recovery_rate
            )
            for element, fraction in payload.composition.items():
                mass_kg = payload.total_mass_kg * fraction
                net_kg = mass_kg * (1.0 - improved_recovery)
                net_tonnes = (net_kg * scenario.launches_per_year) / 1000.0
                demand[element] = demand.get(element, 0.0) + net_tonnes
        return demand

    def run_depletion_analysis(self, scenario: Scenario) -> Dict[str, dict]:
        results = {}
        bottleneck_years = {}

        for payload in scenario.payloads:
            for element_sym in payload.composition:
                if element_sym not in self.registry:
                    continue
                if element_sym in results:
                    continue

                element = self.registry[element_sym]
                remaining = element.terrestrial_reserves
                trajectory = []
                cascade_year = None
                cascade_level = element.terrestrial_reserves * element.cascade_threshold

                for yr in range(scenario.duration_years):
                    space_demand = self.annual_element_demand(scenario, yr).get(element_sym, 0.0)
                    baseline_draw = element.extraction_rate - element.recycling_rate
                    total_draw = baseline_draw + space_demand
                    remaining -= total_draw
                    remaining = max(0.0, remaining)
                    frac = remaining / element.terrestrial_reserves
                    trajectory.append(frac)
                    if cascade_year is None and remaining <= cascade_level:
                        cascade_year = yr + 1

                year_0_demand = self.annual_element_demand(scenario, 0).get(element_sym, 0.0)
                baseline_demand = element.extraction_rate - element.recycling_rate

                results[element_sym] = {
                    "name": element.name,
                    "years_to_cascade": cascade_year or float('inf'),
                    "trajectory": trajectory,
                    "annual_space_demand_tonnes": year_0_demand,
                    "baseline_demand_tonnes": baseline_demand,
                    "fraction_of_total_demand": (
                        year_0_demand / (baseline_demand + year_0_demand)
                        if (baseline_demand + year_0_demand) > 0 else 0.0
                    ),
                    "reserves_tonnes": element.terrestrial_reserves,
                }
                bottleneck_years[element_sym] = cascade_year or float('inf')

        sorted_elements = sorted(bottleneck_years.items(), key=lambda x: x[1])
        for rank, (sym, _) in enumerate(sorted_elements, 1):
            results[sym]["bottleneck_rank"] = rank

        return results

    def find_sustainable_launch_rate(
        self,
        payload: LaunchPayload,
        target_years: int = 100,
        recovery_rate: float = 0.0,
    ) -> Dict[str, float]:
        ceilings = {}
        for element_sym, fraction in payload.composition.items():
            if element_sym not in self.registry:
                continue
            element = self.registry[element_sym]
            usable = element.terrestrial_reserves * (1.0 - element.cascade_threshold)
            baseline_draw = element.extraction_rate - element.recycling_rate
            baseline_total = baseline_draw * target_years
            remaining_budget = usable - baseline_total
            if remaining_budget <= 0:
                ceilings[element_sym] = 0.0
                continue
            mass_per_launch_kg = payload.total_mass_kg * fraction * (1.0 - recovery_rate)
            mass_per_launch_tonnes = mass_per_launch_kg / 1000.0
            if mass_per_launch_tonnes <= 0:
                ceilings[element_sym] = float('inf')
                continue
            total_launches = remaining_budget / mass_per_launch_tonnes
            ceilings[element_sym] = total_launches / target_years
        return ceilings

    def minimum_recovery_for_sustainability(
        self,
        payload: LaunchPayload,
        launches_per_year: int,
        target_years: int = 100,
    ) -> Dict[str, float]:
        required = {}
        for element_sym, fraction in payload.composition.items():
            if element_sym not in self.registry:
                continue
            element = self.registry[element_sym]
            usable = element.terrestrial_reserves * (1.0 - element.cascade_threshold)
            baseline_draw = element.extraction_rate - element.recycling_rate
            baseline_total = baseline_draw * target_years
            remaining_budget = usable - baseline_total
            if remaining_budget <= 0:
                required[element_sym] = 1.0
                continue
            gross_mass_kg = payload.total_mass_kg * fraction * launches_per_year * target_years
            gross_mass_tonnes = gross_mass_kg / 1000.0
            if gross_mass_tonnes <= remaining_budget:
                required[element_sym] = 0.0
                continue
            r = 1.0 - (remaining_budget / gross_mass_tonnes)
            required[element_sym] = min(r, 1.0)
        return required

    def energy_budget(self, scenario: Scenario) -> dict:
        total_mass_per_year_kg = sum(
            p.total_mass_kg for p in scenario.payloads
        ) * scenario.launches_per_year
        thermo_min_mj = total_mass_per_year_kg * THERMO_MIN_LEO_MJ_KG
        practical_mj = total_mass_per_year_kg * PRACTICAL_LEO_MJ_KG
        thermo_min_twh = thermo_min_mj / 3_600_000_000
        practical_twh = practical_mj / 3_600_000_000
        return {
            "total_mass_per_year_kg": total_mass_per_year_kg,
            "thermodynamic_minimum_twh": thermo_min_twh,
            "practical_estimate_twh": practical_twh,
            "total_over_duration_twh": practical_twh * scenario.duration_years,
        }

    def report(self, scenario: Scenario) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"ATOMIC ACCOUNTING REPORT: {scenario.name}")
        lines.append("=" * 70)
        lines.append("")

        energy = self.energy_budget(scenario)
        lines.append("ENERGY BUDGET")
        lines.append(f"  Annual launch mass:      {energy['total_mass_per_year_kg']:,.0f} kg")
        lines.append(f"  Thermo minimum energy:   {energy['thermodynamic_minimum_twh']:.4f} TWh/yr")
        lines.append(f"  Practical energy:        {energy['practical_estimate_twh']:.4f} TWh/yr")
        lines.append(f"  Total over {scenario.duration_years} years:     {energy['total_over_duration_twh']:.4f} TWh")
        lines.append("")

        results = self.run_depletion_analysis(scenario)

        lines.append("ELEMENT DEPLETION ANALYSIS")
        lines.append(f"  Launches/year: {scenario.launches_per_year}")
        lines.append(f"  Duration: {scenario.duration_years} years")
        lines.append("")
        lines.append(f"  {'Rank':<5} {'Element':<12} {'Cascade Yr':<12} "
                     f"{'Space Draw':<18} {'% of Total':<12}")
        lines.append(f"  {'-'*5} {'-'*12} {'-'*12} {'-'*18} {'-'*12}")

        sorted_results = sorted(results.items(),
                               key=lambda x: x[1]['bottleneck_rank'])

        for sym, data in sorted_results:
            cascade = (f"{data['years_to_cascade']:.0f}"
                      if data['years_to_cascade'] != float('inf')
                      else "inf")
            lines.append(
                f"  {data['bottleneck_rank']:<5} {data['name']:<12} "
                f"{cascade:<12} "
                f"{data['annual_space_demand_tonnes']:>10,.1f} t/yr   "
                f"{data['fraction_of_total_demand']*100:>6.3f}%"
            )

        lines.append("")

        if scenario.payloads:
            payload = scenario.payloads[0]
            ceilings = self.find_sustainable_launch_rate(payload, target_years=100)

            lines.append("SUSTAINABLE LAUNCH CEILINGS (100-year horizon, 0% recovery)")
            bottleneck = min(ceilings.items(), key=lambda x: x[1])
            lines.append(f"  System bottleneck: {self.registry[bottleneck[0]].name} "
                        f"@ {bottleneck[1]:,.0f} launches/yr")
            lines.append("")

            required = self.minimum_recovery_for_sustainability(
                payload, scenario.launches_per_year, target_years=100
            )
            lines.append(f"REQUIRED RECOVERY RATES (for {scenario.launches_per_year} "
                        f"launches/yr over 100 years)")
            for sym, rate in sorted(required.items(), key=lambda x: -x[1]):
                name = self.registry[sym].name if sym in self.registry else sym
                if rate <= 0:
                    lines.append(f"  {name:<12}: no recovery needed")
                elif rate >= 1.0:
                    lines.append(f"  {name:<12}: IMPOSSIBLE at this rate")
                else:
                    lines.append(f"  {name:<12}: {rate*100:.1f}% minimum")

        lines.append("")
        lines.append("=" * 70)
        lines.append("Conservation is non-negotiable. The math doesn't care about marketing.")
        lines.append("=" * 70)

        return "\n".join(lines)


# =============================================================================
# QUICK-RUN SCENARIOS
# =============================================================================

def scenario_current_hype() -> Scenario:
    return Scenario(
        name="Current Hype - No Recovery",
        payloads=[default_datacenter_payload()],
        launches_per_year=200,
        duration_years=50,
        recovery_improvement_rate=0.0,
    )


def scenario_with_recovery() -> Scenario:
    payload = default_datacenter_payload()
    payload.recovery_rate = 0.10
    return Scenario(
        name="With Recovery Infrastructure",
        payloads=[payload],
        launches_per_year=200,
        duration_years=50,
        recovery_improvement_rate=0.02,
    )


def scenario_conservative() -> Scenario:
    payload = default_datacenter_payload()
    payload.recovery_rate = 0.80
    return Scenario(
        name="Conservation-First Design",
        payloads=[payload],
        launches_per_year=50,
        duration_years=100,
        recovery_improvement_rate=0.005,
        max_recovery_rate=0.95,
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    accountant = AtomicAccountant()

    scenarios = [
        scenario_current_hype(),
        scenario_with_recovery(),
        scenario_conservative(),
    ]

    for scenario in scenarios:
        print(accountant.report(scenario))
        print("\n\n")
