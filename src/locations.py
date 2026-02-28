"""
Launch site vulnerability profiles.

Location-specific constraints incorporating climate risk, infrastructure
fragility, and cascading failure mechanisms.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LaunchSiteProfile:
    """Vulnerability profile for a launch facility."""
    name: str
    location: str
    elevation_m: float
    latitude: float
    longitude: float

    # Climate risks (probability per year, 0.0-1.0)
    hurricane_risk: float = 0.0
    wildfire_risk: float = 0.0
    flooding_risk: float = 0.0
    seismic_risk: float = 0.0
    extreme_heat_risk: float = 0.0

    # Sea level rise vulnerability
    sea_level_rise_mm_per_year: float = 0.0
    years_to_inundation_risk: float = float('inf')

    # Infrastructure
    freshwater_stress: str = "low"
    grid_reliability: str = "high"
    road_access_redundancy: int = 1
    insurance_market_status: str = "stable"

    # Cascade mechanisms
    failure_modes: List[str] = field(default_factory=list)
    coupling_notes: str = ""

    def risk_score(self) -> float:
        """Composite risk score 0-1."""
        climate = max(
            self.hurricane_risk, self.wildfire_risk,
            self.flooding_risk, self.seismic_risk,
            self.extreme_heat_risk
        )
        water_stress = {
            "low": 0, "moderate": 0.25, "high": 0.5, "critical": 0.75
        }
        grid_risk = {
            "high": 0, "moderate": 0.25, "low": 0.5, "critical": 0.75
        }
        insurance_risk = {
            "stable": 0, "contracting": 0.3, "critical": 0.6,
            "unavailable": 0.9
        }
        access_risk = max(0, 1 - self.road_access_redundancy * 0.3)

        return min(1.0, (
            climate * 0.3
            + water_stress.get(self.freshwater_stress, 0.5) * 0.15
            + grid_risk.get(self.grid_reliability, 0.5) * 0.15
            + insurance_risk.get(self.insurance_market_status, 0.5) * 0.25
            + access_risk * 0.15
        ))


# ============================================================
# SITE PROFILES
# ============================================================

BOCA_CHICA = LaunchSiteProfile(
    name="SpaceX Starbase",
    location="Boca Chica, TX",
    elevation_m=2.5,
    latitude=25.997,
    longitude=-97.157,
    hurricane_risk=0.20,
    flooding_risk=0.25,
    extreme_heat_risk=0.15,
    sea_level_rise_mm_per_year=6.0,
    years_to_inundation_risk=30,
    freshwater_stress="high",
    grid_reliability="moderate",
    road_access_redundancy=1,
    insurance_market_status="contracting",
    failure_modes=[
        "Hurricane damage → 2-8 week shutdown",
        "Storm surge → saltwater intrusion → corrosion",
        "Single road access → evacuation/logistics bottleneck",
        "Rio Grande overallocation → freshwater competition",
        "Coastal subsidence from oil/gas extraction",
        "Grid vulnerability to extreme weather events"
    ],
    coupling_notes=(
        "Cameron County semi-arid. Competing water demand with "
        "agriculture and municipal use. Texas coastal insurance "
        "market in active contraction — major insurers pulling back."
    )
)

KENNEDY_SPACE_CENTER = LaunchSiteProfile(
    name="Kennedy Space Center",
    location="Merritt Island, FL",
    elevation_m=4.0,
    latitude=28.524,
    longitude=-80.651,
    hurricane_risk=0.18,
    flooding_risk=0.20,
    extreme_heat_risk=0.10,
    sea_level_rise_mm_per_year=4.0,
    years_to_inundation_risk=35,
    freshwater_stress="moderate",
    grid_reliability="moderate",
    road_access_redundancy=2,
    insurance_market_status="critical",
    failure_modes=[
        "Atlantic hurricane direct path",
        "KSC assessment: significant inundation by 2050-2060",
        "Florida aquifer saltwater intrusion from SLR",
        "Citizens (state insurer) massively overexposed",
        "Private insurers exiting Florida market",
        "Military co-location creates scheduling constraints"
    ],
    coupling_notes=(
        "Florida property insurance in crisis. State-run Citizens "
        "Insurance overexposed. Private market contracting rapidly."
    )
)

VANDENBERG = LaunchSiteProfile(
    name="Vandenberg Space Force Base",
    location="Lompoc, CA",
    elevation_m=112.0,
    latitude=34.742,
    longitude=-120.577,
    wildfire_risk=0.25,
    seismic_risk=0.15,
    extreme_heat_risk=0.10,
    sea_level_rise_mm_per_year=2.0,
    years_to_inundation_risk=200,
    freshwater_stress="high",
    grid_reliability="low",
    road_access_redundancy=2,
    insurance_market_status="contracting",
    failure_modes=[
        "Wildfire → airspace closure → launch window loss",
        "Active fault systems → seismic damage risk",
        "California grid: rolling blackouts, wildfire shutoffs",
        "Drought cycles → water allocation contests",
        "PSPS (Public Safety Power Shutoffs) from utility"
    ],
    coupling_notes=(
        "Primary risk is wildfire, not hurricane. Grid reliability "
        "degraded by wildfire prevention shutoffs. Water allocation "
        "increasingly contested under intensifying drought cycles."
    )
)

KOUROU = LaunchSiteProfile(
    name="Centre Spatial Guyanais",
    location="Kourou, French Guiana",
    elevation_m=15.0,
    latitude=5.236,
    longitude=-52.769,
    flooding_risk=0.15,
    extreme_heat_risk=0.10,
    sea_level_rise_mm_per_year=3.0,
    years_to_inundation_risk=100,
    freshwater_stress="low",
    grid_reliability="moderate",
    road_access_redundancy=1,
    insurance_market_status="stable",
    failure_modes=[
        "Tropical monsoon → flooding risk",
        "Remote location → single-point-of-failure logistics",
        "Regional political instability",
        "Supply chain vulnerability — all components imported"
    ],
    coupling_notes=(
        "Equatorial location provides orbital mechanics advantage. "
        "Geographic isolation creates logistics fragility."
    )
)

ALL_SITES = [BOCA_CHICA, KENNEDY_SPACE_CENTER, VANDENBERG, KOUROU]


def print_site_comparison():
    """Print comparative risk assessment of all launch sites."""
    print(f"\n{'='*70}")
    print(f"LAUNCH SITE VULNERABILITY COMPARISON")
    print(f"{'='*70}")
    for site in sorted(ALL_SITES, key=lambda s: s.risk_score(), reverse=True):
        print(f"\n  {site.name} ({site.location})")
        print(f"    Composite risk score: {site.risk_score():.2f}")
        print(f"    Elevation: {site.elevation_m}m | "
              f"SLR: {site.sea_level_rise_mm_per_year} mm/yr")
        print(f"    Water: {site.freshwater_stress} | "
              f"Grid: {site.grid_reliability} | "
              f"Insurance: {site.insurance_market_status}")
        print(f"    Key failure modes:")
        for fm in site.failure_modes[:3]:
            print(f"      • {fm}")
    print(f"\n{'='*70}\n")
