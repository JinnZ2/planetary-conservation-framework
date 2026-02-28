
---

### `src/constants.py`

```python
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
    value=3.0,            # kg/s
    unit="kg/s",
    source="Catling & Zahnle 2009, updated estimates",
    measured_date=date(2024, 1, 1),
    uncertainty_pct=30.0,
    notes="Natural thermal + non-thermal escape. ~9.5e7 kg/year"
)

HYDROGEN_ESCAPE_ANNUAL_KG = 9.5e7  # ~3 kg/s * 365.25 * 86400

# Mesospheric mass
MESOSPHERIC_MASS_KG = MeasuredValue(
    value=5e15,           # kg (order of magnitude)
    unit="kg",
    source="NRLMSISE-00 atmospheric model",
    measured_date=date(2023, 1, 1),
    uncertainty_pct=20.0,
    notes="Mesosphere ~50-85 km altitude"
)

# Earth moment of inertia
EARTH_MOMENT_OF_INERTIA = MeasuredValue(
    value=8.04e37,        # kg⋅m²
    unit="kg⋅m²",
    source="IERS Conventions 2010",
    measured_date=date(2010, 1, 1),
    uncertainty_pct=0.001,
    notes="Polar moment of inertia"
)

# Current orbital mass (all objects)
CURRENT_ORBITAL_MASS_KG = MeasuredValue(
    value=1e7,            # ~10,000 metric tons
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
    value=1.75e6,         # ~1500-2000 metric tons
    unit="kg",
    source="Bryce Tech State of the Satellite Industry 2025",
    measured_date=date(2025, 1, 1),
    uncertainty_pct=10.0
)

# Starship parameters
STARSHIP_PAYLOAD_TO_LEO_KG = 150_000       # fully reusable config
STARSHIP_PROPELLANT_PER_LAUNCH_KG = 4_600_000  # methane + LOX total stack
STARSHIP_CO2_PER_LAUNCH_KG = 2_500_000     # approximate CO2 from methane combustion
STARSHIP_H2O_PER_LAUNCH_KG = 1_800_000     # water vapor produced

# Propellant composition ratios (methane/LOX)
METHANE_LOX_RATIO = 3.6                    # oxidizer to fuel ratio
METHANE_CO2_FACTOR = 2.75                  # kg CO2 per kg CH4
METHANE_H2O_FACTOR = 2.25                  # kg H2O per kg CH4

# ============================================================
# SPACE DATA CENTER MODULE PARAMETERS
# ============================================================

@dataclass
class DataCenterModule:
    """Mass budget for a single space data center module (~
