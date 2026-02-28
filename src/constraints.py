"""
The Seven Conservation Laws — constraint classes for planetary boundary enforcement.

Each constraint tracks: current margin, consumption rate, time to binding,
and cascade coupling to other constraints.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import json


class ConstraintStatus(Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ConstraintResult:
    """Result of evaluating a single constraint."""
    law_number: int
    name: str
    status: ConstraintStatus
    margin_remaining_pct: float
    time_to_binding_years: Optional[float]
    current_value: float
    ceiling_value: float
    unit: str
    mechanism: str
    cascade_triggers: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "law_number": self.law_number,
            "name": self.name,
            "status": self.status.value,
            "margin_remaining_pct": round(self.margin_remaining_pct, 2),
            "time_to_binding_years": self.time_to_binding_years,
            "current_value": self.current_value,
            "ceiling_value": self.ceiling_value,
            "unit": self.unit,
            "mechanism": self.mechanism,
            "cascade_triggers": self.cascade_triggers,
            "data_sources": self.data_sources,
            "notes": self.notes,
            "timestamp": self.timestamp
        }

    def __repr__(self):
        return (f"Law {self.law_number} ({self.name}): {self.status.value} "
                f"— {self.margin_remaining_pct:.1f}% margin, "
                f"binding in {self.time_to_binding_years} years")


def _status_from_margin(margin_pct: float) -> ConstraintStatus:
    if margin_pct > 50:
        return ConstraintStatus.SAFE
    elif margin_pct > 20:
        return ConstraintStatus.CAUTION
    elif margin_pct > 5:
        return ConstraintStatus.WARNING
    elif margin_pct > 0:
        return ConstraintStatus.CRITICAL
    else:
        return ConstraintStatus.VIOLATED


# ============================================================
# CONSERVATION LAW 1: PLANETARY WATER BUDGET
# ============================================================

class PlanetaryWaterBudget:
    """
    Conservation Law 1: Planetary Water Budget

    Anthropogenic addition to hydrogen escape rate must not exceed 1%
    of natural baseline. Caps propellant combustion producing H2O at
    altitudes where UV dissociation occurs.
    """
    LAW_NUMBER = 1
    NAME = "Planetary Water Budget"

    NATURAL_ESCAPE_KG_PER_YEAR = 9.5e7
    MAX_ANTHROPOGENIC_ADDITION_KG = 9.5e5

    def evaluate(self, proposal: dict) -> ConstraintResult:
        """
        Evaluate a proposal against the water budget constraint.

        proposal must contain:
            - launches_per_year: int
            - propellant_type: str ("methane_lox", "hydrogen_lox", "solid",
                                    "electric", "electromagnetic")
            - propellant_per_launch_kg: float (optional, has defaults)
        """
        launches = proposal.get("launches_per_year", 0)
        prop_type = proposal.get("propellant_type", "methane_lox")

        if prop_type == "methane_lox":
            h2o_per_launch = proposal.get("propellant_per_launch_kg", 4_600_000) * 0.39
        elif prop_type == "hydrogen_lox":
            h2o_per_launch = proposal.get("propellant_per_launch_kg", 2_000_000) * 0.9
        elif prop_type == "solid":
            h2o_per_launch = proposal.get("propellant_per_launch_kg", 500_000) * 0.15
        elif prop_type in ("electric", "electromagnetic"):
            h2o_per_launch = 0
        else:
            h2o_per_launch = proposal.get("propellant_per_launch_kg", 4_600_000) * 0.39

        total_h2o = launches * h2o_per_launch
        dissociation_fraction = 0.03
        h_produced = total_h2o * dissociation_fraction * (2 / 18)

        margin = self.MAX_ANTHROPOGENIC_ADDITION_KG - h_produced
        margin_pct = (margin / self.MAX_ANTHROPOGENIC_ADDITION_KG) * 100

        if h_produced > 0:
            ttb = margin / h_produced if margin > 0 else 0
        else:
            ttb = None

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(margin_pct),
            margin_remaining_pct=margin_pct,
            time_to_binding_years=round(ttb, 1) if ttb is not None else None,
            current_value=h_produced,
            ceiling_value=self.MAX_ANTHROPOGENIC_ADDITION_KG,
            unit="kg H/year",
            mechanism="H2O from propellant combustion → UV dissociation at altitude → H escape",
            cascade_triggers=["OH radical budget disruption", "atmospheric self-cleaning capacity"],
            data_sources=["Catling & Zahnle 2009", "Ross & Sheaffer 2014"],
            notes=f"Propellant type: {prop_type}, {launches} launches/year"
        )


# ============================================================
# CONSERVATION LAW 2: ATMOSPHERIC COMPOSITION INTEGRITY
# ============================================================

class AtmosphericComposition:
    """
    Conservation Law 2: Atmospheric Composition Integrity

    Limits on mesospheric injection, black carbon above tropopause,
    and alumina particles to prevent ozone depletion and radiative forcing.
    """
    LAW_NUMBER = 2
    NAME = "Atmospheric Composition Integrity"

    MESOSPHERIC_CEILING_KG = 5e11
    BC_CEILING_KG = 1_000_000
    ALUMINA_CEILING_KG = 100_000

    BC_PER_METHANE_LAUNCH_KG = 50
    BC_PER_KEROSENE_LAUNCH_KG = 150
    ALUMINA_PER_SOLID_LAUNCH_KG = 300

    def evaluate(self, proposal: dict) -> ConstraintResult:
        launches = proposal.get("launches_per_year", 0)
        prop_type = proposal.get("propellant_type", "methane_lox")

        if prop_type == "methane_lox":
            bc_annual = launches * self.BC_PER_METHANE_LAUNCH_KG
            alumina_annual = 0
        elif prop_type == "kerosene_lox":
            bc_annual = launches * self.BC_PER_KEROSENE_LAUNCH_KG
            alumina_annual = 0
        elif prop_type == "solid":
            bc_annual = launches * self.BC_PER_KEROSENE_LAUNCH_KG * 0.5
            alumina_annual = launches * self.ALUMINA_PER_SOLID_LAUNCH_KG
        else:
            bc_annual = 0
            alumina_annual = 0

        bc_margin_pct = ((self.BC_CEILING_KG - bc_annual) / self.BC_CEILING_KG) * 100
        alumina_margin_pct = ((self.ALUMINA_CEILING_KG - alumina_annual) /
                              self.ALUMINA_CEILING_KG) * 100 if alumina_annual > 0 else 100

        tightest_margin = min(bc_margin_pct, alumina_margin_pct)
        tightest_name = "black carbon" if bc_margin_pct <= alumina_margin_pct else "alumina"

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(tightest_margin),
            margin_remaining_pct=tightest_margin,
            time_to_binding_years=None,
            current_value=bc_annual if tightest_name == "black carbon" else alumina_annual,
            ceiling_value=self.BC_CEILING_KG if tightest_name == "black carbon" else self.ALUMINA_CEILING_KG,
            unit="kg/year",
            mechanism=f"Tightest sub-constraint: {tightest_name}. "
                      f"BC: {bc_annual:.0f}/{self.BC_CEILING_KG:.0f} kg/yr, "
                      f"Alumina: {alumina_annual:.0f}/{self.ALUMINA_CEILING_KG:.0f} kg/yr",
            cascade_triggers=["ozone depletion", "radiative forcing", "mesospheric chemistry"],
            data_sources=["Ross & Sheaffer 2014", "Maloney et al. 2022"],
        )


# ============================================================
# CONSERVATION LAW 3: ANGULAR MOMENTUM BUDGET
# ============================================================

class AngularMomentumBudget:
    """
    Conservation Law 3: Angular Momentum Budget

    Monotonic change in Earth's moment of inertia must not exceed
    10^-14 of total per century. Requires deorbit/recovery within 25 years.
    """
    LAW_NUMBER = 3
    NAME = "Angular Momentum Budget"

    EARTH_I = 8.04e37
    MAX_DELTA_I_FRACTION_PER_CENTURY = 1e-14
    MAX_CUMULATIVE_ORBITAL_MASS_KG = 1e11
    DEORBIT_REQUIREMENT_YEARS = 25

    def evaluate(self, proposal: dict) -> ConstraintResult:
        orbital_mass = proposal.get("orbital_mass_kg", 0)
        duration = proposal.get("duration_years", 10)
        has_deorbit = proposal.get("deorbit_plan", False)
        deorbit_timeline = proposal.get("deorbit_timeline_years", 999)

        current_orbital = 1e7

        cumulative = current_orbital + orbital_mass
        margin = self.MAX_CUMULATIVE_ORBITAL_MASS_KG - cumulative
        margin_pct = (margin / self.MAX_CUMULATIVE_ORBITAL_MASS_KG) * 100

        notes = []
        if not has_deorbit:
            notes.append("NO DEORBIT PLAN — violates mandatory recovery requirement")
            margin_pct = min(margin_pct, 0)
        elif deorbit_timeline > self.DEORBIT_REQUIREMENT_YEARS:
            notes.append(f"Deorbit timeline {deorbit_timeline}yr exceeds "
                         f"{self.DEORBIT_REQUIREMENT_YEARS}yr requirement")

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(margin_pct),
            margin_remaining_pct=margin_pct,
            time_to_binding_years=None,
            current_value=cumulative,
            ceiling_value=self.MAX_CUMULATIVE_ORBITAL_MASS_KG,
            unit="kg cumulative in orbit",
            mechanism="Mass export without return changes Earth I. "
                      "Mandatory deorbit/recovery within 25 years.",
            cascade_triggers=["orbital debris density", "replacement cycle mass"],
            data_sources=["IERS Conventions 2010", "Framework derivation"],
            notes="; ".join(notes) if notes else "Deorbit plan present"
        )


# ============================================================
# CONSERVATION LAW 5: ORBITAL SPACE AS COMMONS
# ============================================================

class OrbitalCommons:
    """
    Conservation Law 5: Orbital Space as Commons

    Debris density must stay below 50% of Kessler threshold per altitude band.
    All infrastructure must demonstrate net debris reduction over lifetime.
    """
    LAW_NUMBER = 5
    NAME = "Orbital Space as Commons"

    KESSLER_MARGIN_FRACTION = 0.50
    DEBRIS_GENERATION_RATE = 0.001

    def evaluate(self, proposal: dict) -> ConstraintResult:
        orbital_mass = proposal.get("orbital_mass_kg", 0)
        duration = proposal.get("duration_years", 10)
        has_deorbit = proposal.get("deorbit_plan", False)
        active_removal = proposal.get("active_debris_removal", False)
        deorbit_bond = proposal.get("deorbit_bond_funded", False)

        debris_generated = orbital_mass * self.DEBRIS_GENERATION_RATE * duration
        current_debris_mass = 1e7 * 0.1

        kessler_threshold = 5e6
        projected_debris = current_debris_mass + debris_generated

        margin = (kessler_threshold * self.KESSLER_MARGIN_FRACTION) - projected_debris
        margin_pct = (margin / (kessler_threshold * self.KESSLER_MARGIN_FRACTION)) * 100

        violations = []
        if not has_deorbit:
            violations.append("No deorbit plan")
        if not active_removal:
            violations.append("No active debris removal — net debris reduction required")
        if not deorbit_bond:
            violations.append("No funded deorbit bond")

        if violations:
            margin_pct = min(margin_pct, 0)

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(margin_pct),
            margin_remaining_pct=margin_pct,
            time_to_binding_years=None,
            current_value=projected_debris,
            ceiling_value=kessler_threshold * self.KESSLER_MARGIN_FRACTION,
            unit="kg debris mass (LEO)",
            mechanism="Debris accumulation toward Kessler threshold. "
                      "Thermospheric contraction reduces drag → longer debris lifetimes.",
            cascade_triggers=["Kessler cascade", "satellite loss", "GPS/comm degradation",
                              "insurance market withdrawal"],
            data_sources=["NASA ODPO", "ESA MASTER model"],
            notes="; ".join(violations) if violations else "Compliance requirements met"
        )


# ============================================================
# CONSERVATION LAW 6: CRUSTAL MATERIAL THROUGHPUT
# ============================================================

class CrustalMaterialThroughput:
    """
    Conservation Law 6: Crustal Material Throughput

    Annual export must not exceed 0.01% of global production per critical material.
    Programs exceeding threshold must demonstrate in-orbit recycling.
    """
    LAW_NUMBER = 6
    NAME = "Crustal Material Throughput"

    THRESHOLD_FRACTION = 0.0001

    DEFAULT_MATERIAL_PER_MODULE = {
        "rare_earths": (5_000, 10_000),
        "high_purity_copper": (15_000, 30_000),
        "lithium": (2_000, 5_000),
        "cobalt": (1_000, 3_000),
        "gallium": (5, 15),
        "indium": (2, 8),
    }

    GLOBAL_PRODUCTION = {
        "rare_earths": 350_000_000,
        "high_purity_copper": 22_000_000_000,
        "lithium": 180_000_000,
        "cobalt": 220_000_000,
        "gallium": 500_000,
        "indium": 900_000,
    }

    def evaluate(self, proposal: dict) -> ConstraintResult:
        modules_per_year = proposal.get("modules_per_year", 1)
        recycling_rate = proposal.get("recycling_rate", 0.0)
        custom_materials = proposal.get("material_requirements_kg", {})

        violations = []
        tightest_margin_pct = 100.0
        tightest_mineral = "none"

        for mineral, production in self.GLOBAL_PRODUCTION.items():
            ceiling = production * self.THRESHOLD_FRACTION

            if mineral in custom_materials:
                annual_demand = custom_materials[mineral] * (1 - recycling_rate)
            else:
                default_range = self.DEFAULT_MATERIAL_PER_MODULE.get(mineral, (0, 0))
                per_module = (default_range[0] + default_range[1]) / 2
                annual_demand = per_module * modules_per_year * (1 - recycling_rate)

            if ceiling > 0:
                margin_pct = ((ceiling - annual_demand) / ceiling) * 100
            else:
                margin_pct = 0

            if margin_pct < tightest_margin_pct:
                tightest_margin_pct = margin_pct
                tightest_mineral = mineral

            if margin_pct <= 0:
                violations.append(
                    f"{mineral}: {annual_demand:.0f} kg/yr exceeds "
                    f"ceiling {ceiling:.0f} kg/yr ({abs(margin_pct):.0f}% over)"
                )

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(tightest_margin_pct),
            margin_remaining_pct=tightest_margin_pct,
            time_to_binding_years=None,
            current_value=0,
            ceiling_value=0,
            unit="multiple minerals",
            mechanism=f"Tightest mineral: {tightest_mineral}. "
                      f"Recycling rate: {recycling_rate*100:.0f}%",
            cascade_triggers=["supply chain disruption", "price escalation",
                              "competition with terrestrial green transition"],
            data_sources=["USGS Mineral Commodity Summaries 2025"],
            notes="; ".join(violations) if violations else
                  f"Within thresholds at {modules_per_year} modules/yr"
        )


# ============================================================
# CONSERVATION LAW 7: THERMOSPHERIC ENERGY BALANCE
# ============================================================

class ThermosphericBalance:
    """
    Conservation Law 7: Thermospheric Energy Balance

    Soot heating must not reverse thermospheric contraction trend.
    Positive feedback: heating → expansion → drag → shorter lifetimes →
    more replacement launches → more heating.
    """
    LAW_NUMBER = 7
    NAME = "Thermospheric Energy Balance"

    CONTRACTION_RATE_KM_PER_DECADE = -2.0
    SOOT_HEATING_COEFFICIENT = 1e-6
    REVERSAL_THRESHOLD_W_PER_M2 = 0.005

    def evaluate(self, proposal: dict) -> ConstraintResult:
        launches = proposal.get("launches_per_year", 0)
        prop_type = proposal.get("propellant_type", "methane_lox")

        if prop_type == "methane_lox":
            bc_per_launch = 50
        elif prop_type == "kerosene_lox":
            bc_per_launch = 150
        else:
            bc_per_launch = 0

        bc_annual = launches * bc_per_launch
        heating = bc_annual * self.SOOT_HEATING_COEFFICIENT

        margin = self.REVERSAL_THRESHOLD_W_PER_M2 - heating
        margin_pct = ((margin / self.REVERSAL_THRESHOLD_W_PER_M2) * 100
                      if self.REVERSAL_THRESHOLD_W_PER_M2 > 0 else 0)

        feedback_factor = 1.0
        if heating > 0 and self.REVERSAL_THRESHOLD_W_PER_M2 > 0:
            gain = heating / self.REVERSAL_THRESHOLD_W_PER_M2
            if gain < 1:
                feedback_factor = 1 / (1 - gain)
            else:
                feedback_factor = float('inf')

        return ConstraintResult(
            law_number=self.LAW_NUMBER,
            name=self.NAME,
            status=_status_from_margin(margin_pct),
            margin_remaining_pct=margin_pct,
            time_to_binding_years=None,
            current_value=heating,
            ceiling_value=self.REVERSAL_THRESHOLD_W_PER_M2,
            unit="W/m² thermospheric heating",
            mechanism=f"BC deposition: {bc_annual} kg/yr → {heating:.6f} W/m² heating. "
                      f"Feedback amplification factor: {feedback_factor:.2f}x. "
                      f"Positive feedback loop: heating → drag → replacement → more heating.",
            cascade_triggers=["orbital lifetime reduction", "replacement cascade",
                              "debris acceleration", "launch cadence pressure"],
            data_sources=["Ross & Sheaffer 2014", "Emmert 2015"],
            notes="Fastest feedback loop — operates on annual timescales"
        )


# ============================================================
# AGGREGATE EVALUATION
# ============================================================

ALL_CONSTRAINTS = [
    PlanetaryWaterBudget(),
    AtmosphericComposition(),
    AngularMomentumBudget(),
    # Law 4 (Geodynamo) is derived — enforced through Laws 1-3
    OrbitalCommons(),
    CrustalMaterialThroughput(),
    ThermosphericBalance(),
]


def evaluate_all(proposal: dict) -> List[ConstraintResult]:
    """Evaluate a proposal against all conservation laws."""
    return [c.evaluate(proposal) for c in ALL_CONSTRAINTS]
