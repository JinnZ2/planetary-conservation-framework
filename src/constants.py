"""
Physical constants and current baseline values for planetary constraints.
All values include sources and measurement dates.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class MeasuredValue:
    """A value with source, date, and uncertainty."""
    value: float
    unit: str
    source: str
    measured_date: date
    uncertainty_pct: float = 0.0
    notes: str = ""

    def __repr__(self):
        return f"{self.value} {self.unit} (±{self.uncertainty_pct}%, {self.source}, {self.measured_date})"


# ============================================================
# EARTH SYSTEM BASELINES
# ============================================================

# Hydrogen escape rate
HYDROGEN_ESCAPE_RATE = MeasuredValue(
    value=3.0,
    unit="kg/s",
    source="Catling & Zahnle 2009, updated estimates",
    measured_date=date(2024, 1, 1),
    uncertainty_pct=30.0,
    notes="Natural thermal + non-thermal escape. ~9.5e7 kg/year"
)

HYDROGEN_ESCAPE_ANNUAL_KG = 9.5e7  # ~3 kg/s * 365.25 * 86400

# Mesospheric mass
MESOSPHERIC_MASS_KG = MeasuredValue(
    value=5e15,
    unit="kg",
    source="NRLMSISE-00 atmospheric model",
    measured_date=date(2023, 1, 1),
    uncertainty_pct=20.0,
    notes="Mesosphere ~50-85 km altitude"
)

# Earth moment of inertia
EARTH_MOMENT_OF_INERTIA = MeasuredValue(
    value=8.04e37,
    unit="kg⋅m²",
    source="IERS Conventions 2010",
    measured_date=date(2010, 1, 1),
    uncertainty_pct=0.001,
    notes="Polar moment of inertia"
)

# Current orbital mass (all objects)
CURRENT_ORBITAL_MASS_KG = MeasuredValue(
    value=1e7,
    unit="kg",
    source="ESA Space Debris Office estimates",
    measured_date=date(2025, 6, 1),
    uncertainty_pct=15.0,
    notes="Includes active satellites, debris, upper stages"
)

# ============================================================
# LAUNCH SYSTEM PARAMETERS
# ============================================================

# Global annual launch mass to orbit
CURRENT_ANNUAL_LAUNCH_MASS_KG = MeasuredValue(
    value=1.75e6,
    unit="kg",
    source="Bryce Tech State of the Satellite Industry 2025",
    measured_date=date(2025, 1, 1),
    uncertainty_pct=10.0
)

# Starship parameters
STARSHIP_PAYLOAD_TO_LEO_KG = 150_000
STARSHIP_PROPELLANT_PER_LAUNCH_KG = 4_600_000
STARSHIP_CO2_PER_LAUNCH_KG = 2_500_000
STARSHIP_H2O_PER_LAUNCH_KG = 1_800_000

# Propellant composition ratios (methane/LOX)
METHANE_LOX_RATIO = 3.6
METHANE_CO2_FACTOR = 2.75
METHANE_H2O_FACTOR = 2.25

# ============================================================
# SPACE DATA CENTER MODULE PARAMETERS
# ============================================================

@dataclass
class DataCenterModule:
    """Mass budget for a single space data center module (~10MW equivalent)."""
    compute_hardware_kg: tuple = (50_000, 80_000)
    solar_arrays_kg: tuple = (80_000, 120_000)
    thermal_radiators_kg: tuple = (60_000, 100_000)
    radiation_shielding_kg: tuple = (200_000, 500_000)
    structure_kg: tuple = (50_000, 80_000)
    power_management_kg: tuple = (30_000, 50_000)
    communications_kg: tuple = (5_000, 10_000)
    spares_consumables_kg: tuple = (50_000, 80_000)

    @property
    def total_range_kg(self) -> tuple:
        low = sum(v[0] for v in [
            self.compute_hardware_kg, self.solar_arrays_kg,
            self.thermal_radiators_kg, self.radiation_shielding_kg,
            self.structure_kg, self.power_management_kg,
            self.communications_kg, self.spares_consumables_kg
        ])
        high = sum(v[1] for v in [
            self.compute_hardware_kg, self.solar_arrays_kg,
            self.thermal_radiators_kg, self.radiation_shielding_kg,
            self.structure_kg, self.power_management_kg,
            self.communications_kg, self.spares_consumables_kg
        ])
        return (low, high)

    @property
    def total_midpoint_kg(self) -> float:
        r = self.total_range_kg
        return (r[0] + r[1]) / 2


STANDARD_MODULE = DataCenterModule()

# ============================================================
# MINERAL RESERVES AND PRODUCTION
# ============================================================

MINERAL_DATA = {
    "rare_earths": {
        "global_production_kg_per_year": 350_000_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 35_000,
        "source": "USGS Mineral Commodity Summaries 2025",
        "notes": "Includes all REE. China dominates production ~60%"
    },
    "high_purity_copper": {
        "global_production_kg_per_year": 22_000_000_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 2_200_000,
        "source": "USGS 2025",
        "notes": "Declining ore grades globally. Energy cost per kg rising"
    },
    "lithium": {
        "global_production_kg_per_year": 180_000_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 18_000,
        "source": "USGS 2025",
        "notes": "Battery demand competing. Brine vs hard rock extraction"
    },
    "cobalt": {
        "global_production_kg_per_year": 220_000_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 22_000,
        "source": "USGS 2025",
        "notes": "DRC dominance, ethical sourcing constraints"
    },
    "gallium": {
        "global_production_kg_per_year": 500_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 50,
        "source": "USGS 2025",
        "notes": "Critical for semiconductors. China controls ~98% production"
    },
    "indium": {
        "global_production_kg_per_year": 900_000,
        "threshold_fraction": 0.0001,
        "annual_ceiling_kg": 90,
        "source": "USGS 2025",
        "notes": "Solar panel demand competing"
    }
}

# ============================================================
# ATMOSPHERIC THRESHOLDS
# ============================================================

BC_ANNUAL_CEILING_KG = 1_000_000
BC_PER_STARSHIP_LAUNCH_KG = 50

ALUMINA_ANNUAL_CEILING_KG = 100_000
ALUMINA_PER_SRB_LAUNCH_KG = 300

MESOSPHERIC_INJECTION_CEILING_KG = 5e11

# ============================================================
# ORBITAL DEBRIS PARAMETERS
# ============================================================

KESSLER_THRESHOLD_DENSITY = MeasuredValue(
    value=0.0,
    unit="objects/km³",
    source="NASA ODPO models",
    measured_date=date(2025, 1, 1),
    uncertainty_pct=25.0,
    notes="Threshold varies by altitude band. LEO most critical."
)

DEBRIS_CRITICAL_BANDS = {
    "LEO_low": (200, 600),
    "LEO_mid": (600, 1000),
    "LEO_high": (1000, 2000),
    "MEO": (2000, 35786),
    "GEO": (35786, 36786)
}

TRACKED_OBJECTS_COUNT = MeasuredValue(
    value=40_000,
    unit="objects",
    source="US Space Surveillance Network",
    measured_date=date(2025, 6, 1),
    uncertainty_pct=5.0,
    notes="Objects >10cm. Estimated 1M+ objects >1cm"
)

# ============================================================
# INSURANCE MARKET INDICATORS
# ============================================================

INSURANCE_DATA = {
    "cyber_incident_surge_pct": 118,
    "reinsurance_participation_drop_pct": 60,
    "coverage_exclusion_expansion_pct": 30,
    "source": "Swiss Re / Munich Re space insurance reports 2025",
    "notes": "Market contraction indicates risk beyond profitable underwriting"
}

# ============================================================
# REPLACEMENT CYCLE PARAMETERS
# ============================================================

RADIATION_HARDWARE_LIFETIME_YEARS = (3, 5)
REPLACEMENT_MASS_PER_CYCLE_KG = (150_000_000, 450_000_000)


