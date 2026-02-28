"""
Planetary Conservation Framework - Constants & Constraint Thresholds
=====================================================================
Foundation data for the atomic accounting layer.

All ceilings represent conservation-safe limits, NOT geologic maximums
or current production rates. These are the levels below which Earth's
coupled systems maintain functional stability over multi-generational
timescales.

Uncertainty is real. Where values are policy choices rather than
derived physics, they are marked explicitly. Where model spreads
exist, uncertainty placeholders are provided for future probabilistic
propagation.

Schema is versioned. Breaking changes increment major version.

Author: Kavik + Claude
Repository: https://github.com/JinnZ2/planetary-conservation-framework
"""

SCHEMA_VERSION = "1.0.0"

# =============================================================================
# ORBITAL ENVIRONMENT - Regionalized by altitude band
# =============================================================================
#
# Kessler syndrome risk is altitude- and inclination-dependent.
# A single scalar hides critical structure. Each band has its own
# debris density dynamics, collision probability curves, and
# natural decay timescales.
#
# Sources: ESA Space Debris Office, NASA ODPO quarterly reports
# Thresholds: derived from fragmentation cascade models (Liou & Johnson 2006)
# with safety margins applied as policy choices.

ORBITAL = {
    "leo_low": {
        # 200-600 km - high drag, natural decay in months to years
        "altitude_range_km": [200, 600],
        "kessler_threshold_kg": 2_500_000_000,
        "current_tracked_mass_kg": 1_800_000_000,
        "mass_margin_kg": 700_000_000,
        "natural_decay_years_median": 5,
        "collision_probability_per_km3_yr": 1.2e-9,
        "notes": "Atmospheric drag provides natural cleanup. Most ISS-altitude ops.",
        "uncertainty_pct": 25,  # model spread on threshold
    },
    "leo_high": {
        # 600-1000 km - decades to centuries for natural decay
        # THIS IS THE CRITICAL BAND - most mega-constellations target here
        "altitude_range_km": [600, 1000],
        "kessler_threshold_kg": 1_200_000_000,
        "current_tracked_mass_kg": 900_000_000,
        "mass_margin_kg": 300_000_000,
        "natural_decay_years_median": 150,
        "collision_probability_per_km3_yr": 3.8e-9,
        "notes": (
            "Critical band. Starlink, OneWeb, proposed data centers. "
            "Natural decay too slow to self-clean. Active deorbit mandatory."
        ),
        "uncertainty_pct": 35,  # higher uncertainty due to fragmentation unknowns
    },
    "meo": {
        # 1000-35786 km - effectively permanent without active removal
        "altitude_range_km": [1000, 35786],
        "kessler_threshold_kg": 800_000_000,
        "current_tracked_mass_kg": 200_000_000,
        "mass_margin_kg": 600_000_000,
        "natural_decay_years_median": 10_000,
        "collision_probability_per_km3_yr": 0.5e-9,
        "notes": "Navigation constellations (GPS, Galileo). Low density but no cleanup.",
        "uncertainty_pct": 40,
    },
    "gto_geo": {
        # GTO transfer orbits and GEO belt
        "altitude_range_km": [35786, 42164],
        "kessler_threshold_kg": 500_000_000,
        "current_tracked_mass_kg": 150_000_000,
        "mass_margin_kg": 350_000_000,
        "natural_decay_years_median": 1_000_000,  # effectively permanent
        "collision_probability_per_km3_yr": 0.1e-9,
        "notes": "Graveyard orbits exist but compliance is partial. Permanent pollution.",
        "uncertainty_pct": 50,
    },
}


# =============================================================================
# ATMOSPHERIC CONSTRAINTS
# =============================================================================
#
# Launch emissions inject materials at altitudes where residence times
# and radiative/chemical effects differ dramatically from surface emissions.
#
# Black carbon and alumina ceilings are derived from radiative forcing
# and ozone depletion models. Current values are global aggregates.
# TODO: Stratify by fuel type and injection altitude band (polar vs
# equatorial, tropospheric vs mesospheric). Recent literature emphasizes
# disproportionate impact of polar/mesospheric injection.
# See: Ross & Sheaffer 2014, Maloney et al. 2022

ATMOSPHERIC = {
    "black_carbon": {
        # Soot from kerosene-fueled rockets (RP-1, Jet-A)
        # Injected directly into stratosphere/mesosphere
        "conservation_ceiling_kg_yr": 1_000_000,
        "current_annual_from_launches_kg": 50_000,
        "margin_kg": 950_000,
        "radiative_forcing_per_kg_mw_m2": 0.0001,
        "stratospheric_residence_years": 4,
        "notes": (
            "Stratospheric BC has ~500x the warming effect per kg vs surface BC. "
            "Ceiling based on keeping launch-attributable forcing below 0.01 W/m2."
        ),
        "ceiling_basis": "policy_choice",  # not derived from a single physical law
        "uncertainty_pct": 30,
        # TODO: separate ceilings for polar vs equatorial injection
        "fuel_type_sensitivity": {
            "rp1_kerosene": 1.0,     # baseline
            "methane_lox": 0.15,     # ~85% less BC
            "hydrogen_lox": 0.01,    # near zero BC but water vapor concerns
            "solid_srb": 2.5,        # alumina particles instead - different problem
        },
    },
    "alumina": {
        # Al2O3 particles from solid rocket boosters
        "conservation_ceiling_kg_yr": 2_000_000,
        "current_annual_from_launches_kg": 300_000,
        "margin_kg": 1_700_000,
        "ozone_depletion_sensitivity": "moderate",
        "mesospheric_residence_years": 8,
        "notes": (
            "Alumina particles catalyze ozone destruction and alter mesospheric "
            "chemistry. Ceiling conservative due to incomplete understanding of "
            "heterogeneous chemistry at injection altitudes."
        ),
        "ceiling_basis": "model_derived",
        "uncertainty_pct": 45,  # large model spread
    },
    "water_vapor_mesospheric": {
        # From hydrogen-LOX engines at high altitude
        "conservation_ceiling_kg_yr": 5_000_000,
        "current_annual_from_launches_kg": 200_000,
        "margin_kg": 4_800_000,
        "notes": (
            "Hydrogen engines are 'clean' for BC but inject water vapor "
            "into the mesosphere where it forms noctilucent clouds and "
            "affects OH chemistry. Often overlooked in 'green rocket' marketing."
        ),
        "ceiling_basis": "model_derived",
        "uncertainty_pct": 50,
    },
}


# =============================================================================
# HYDROGEN ESCAPE - Law 1 (Water Budget)
# =============================================================================
#
# Earth loses hydrogen to space via Jeans escape and non-thermal
# processes. This is a one-way door - lost hydrogen is gone forever.
# Over geologic time this drives planetary oxidation (Catling & Zahnle 2020).
#
# The anthropogenic cap (1%) is a POLICY CHOICE, not a derived physical
# constant. It represents the precautionary principle applied to an
# irreversible process. Critics will ask "why 1% and not 0.1% or 10%?"
# Answer: because we're choosing the threshold below which we're confident
# the signal is lost in natural variability. This is conservative by design.
#
# Source: Catling & Zahnle 2020 (long-term oxidizing trends)
# Source: WACCM model results for launch plume hydrogen dissociation

HYDROGEN_ESCAPE = {
    "natural_rate_kg_yr": 95_000,
    "natural_rate_uncertainty_pct": 20,
    "anthropogenic_cap_fraction": 0.01,  # POLICY CHOICE - see notes above
    "anthropogenic_cap_kg_yr": 950,
    "current_anthropogenic_contribution_kg_yr": 50,  # rough estimate
    "margin_kg_yr": 900,
    "cap_basis": (
        "Precautionary policy choice. Set at 1% of natural rate to remain "
        "within natural variability envelope. Irreversible process demands "
        "conservative threshold. Adjustable with better data."
    ),
    "notes": (
        "This is a directional risk indicator for long-term planetary "
        "habitability, not an engineering limit for individual missions. "
        "Relevant at civilization-scale launch cadences sustained over decades."
    ),
}


# =============================================================================
# GEODYNAMO - Law 4 (DIRECTIONAL RISK INDICATOR)
# =============================================================================
#
# EXPLICIT FRAMING: This is a directional risk indicator, NOT a hard
# engineering limit. It should not be weaponized as either FUD or false
# reassurance. The geodynamo operates on timescales and energy scales
# far beyond current launch activity. However, the principle of tracking
# mass redistribution effects on rotational dynamics is sound and becomes
# relevant at scales proposed by some long-term space infrastructure visions.

GEODYNAMO = {
    "indicator_type": "directional_risk",
    "earth_angular_momentum_kg_m2_s": 7.07e33,
    "max_safe_annual_mass_redistribution_kg": 1e12,
    "current_annual_launch_mass_kg": 1.5e7,
    "orders_of_magnitude_margin": 5,
    "notes": (
        "DIRECTIONAL RISK INDICATOR ONLY. Current launch activity is ~5 orders "
        "of magnitude below any conceivable effect on Earth's rotation or "
        "geodynamo. Included for completeness and to set a framework for "
        "evaluating far-future scenarios (asteroid mining return mass, "
        "lunar material transport). Not relevant for near-term policy."
    ),
    "confidence": "low_relevance_high_margin",
}


# =============================================================================
# MINERAL RESOURCES - Conservation-safe ceilings
# =============================================================================
#
# NAMING CONVENTION: All ceilings use `_conservation_ceiling_` to
# distinguish from geological reserves or current production rates.
# These represent the annual draw rate compatible with multi-generational
# resource availability including terrestrial demand growth.
#
# These are NOT "how much exists" - they are "how much can be drawn
# annually while maintaining system-level resource security for 100+ years."
#
# Values derived from: USGS reserves data, recycling rates, demand
# growth projections, and cascade failure analysis from atomic_accounting.py

MINERALS = {
    "rare_earth_aggregate": {
        # Nd, Dy, Pr, etc. combined
        "conservation_ceiling_kg_yr": 35_000_000,
        "current_production_kg_yr": 350_000_000,
        "ratio_current_to_ceiling": 10.0,
        "notes": (
            "Current production ALREADY exceeds conservation ceiling by 10x. "
            "This is a pre-existing crisis that space demand exacerbates. "
            "Ceiling represents rate compatible with 100-year reserve horizon "
            "at current recycling rates (~10% for rare earths)."
        ),
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 30,
        "recycling_rate_current_pct": 10,
        "recycling_rate_needed_for_sustainability_pct": 65,
    },
    "copper": {
        "conservation_ceiling_kg_yr": 12_000_000_000,
        "current_production_kg_yr": 22_000_000_000,
        "ratio_current_to_ceiling": 1.83,
        "notes": "Exceeding ceiling. Recycling improvements critical.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 20,
        "recycling_rate_current_pct": 18,
        "recycling_rate_needed_for_sustainability_pct": 50,
    },
    "cobalt": {
        "conservation_ceiling_kg_yr": 100_000_000,
        "current_production_kg_yr": 190_000_000,
        "ratio_current_to_ceiling": 1.9,
        "notes": "Battery demand driving overshoot. DRC concentration risk.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 25,
        "recycling_rate_current_pct": 13,
        "recycling_rate_needed_for_sustainability_pct": 55,
    },
    "indium": {
        "conservation_ceiling_kg_yr": 400_000,
        "current_production_kg_yr": 900_000,
        "ratio_current_to_ceiling": 2.25,
        "notes": (
            "Critical bottleneck. Used in displays, solar cells, semiconductors. "
            "Extremely limited reserves. Space hardware demand would accelerate "
            "an already critical depletion timeline."
        ),
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 35,
        "recycling_rate_current_pct": 44,
        "recycling_rate_needed_for_sustainability_pct": 80,
    },
    "gallium": {
        "conservation_ceiling_kg_yr": 250_000,
        "current_production_kg_yr": 500_000,
        "ratio_current_to_ceiling": 2.0,
        "notes": "Semiconductor-critical. China controls ~80% of production.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 30,
        "recycling_rate_current_pct": 30,
        "recycling_rate_needed_for_sustainability_pct": 70,
    },
    "tantalum": {
        "conservation_ceiling_kg_yr": 900_000,
        "current_production_kg_yr": 1_800_000,
        "ratio_current_to_ceiling": 2.0,
        "notes": "Capacitor-critical. Conflict mineral sourcing concerns.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 25,
        "recycling_rate_current_pct": 28,
        "recycling_rate_needed_for_sustainability_pct": 60,
    },
    "lithium": {
        "conservation_ceiling_kg_yr": 100_000_000,
        "current_production_kg_yr": 180_000_000,
        "ratio_current_to_ceiling": 1.8,
        "notes": "Battery boom driving overshoot. Brine vs hard-rock extraction.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 25,
        "recycling_rate_current_pct": 10,
        "recycling_rate_needed_for_sustainability_pct": 55,
    },
    "silicon_refined": {
        # Metallurgical and semiconductor grade, not crustal abundance
        "conservation_ceiling_kg_yr": 8_000_000_000,
        "current_production_kg_yr": 8_500_000_000,
        "ratio_current_to_ceiling": 1.06,
        "notes": "Near ceiling but abundant feedstock. Energy cost is the real limit.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 15,
        "recycling_rate_current_pct": 14,
        "recycling_rate_needed_for_sustainability_pct": 25,
    },
    "aluminum": {
        "conservation_ceiling_kg_yr": 50_000_000_000,
        "current_production_kg_yr": 69_000_000_000,
        "ratio_current_to_ceiling": 1.38,
        "notes": "Abundant ore but energy-intensive. Recycling well-established.",
        "ceiling_basis": "derived_from_reserves_and_recycling",
        "uncertainty_pct": 15,
        "recycling_rate_current_pct": 29,
        "recycling_rate_needed_for_sustainability_pct": 45,
    },
}


# =============================================================================
# LAUNCH INFRASTRUCTURE - Socio-technical constraints
# =============================================================================

LAUNCH = {
    "max_realistic_cadence_20yr": 2_000,
    "cadence_basis": "expert_judgment",  # explicitly flagged
    "cadence_notes": (
        "Based on pad throughput analysis, manufacturing bottlenecks, "
        "range scheduling, and regulatory constraints. NOT a pure data "
        "extrapolation. BryceTech historical data informs but does not "
        "determine this figure. Assumes continued exponential growth in "
        "launch capability which is itself uncertain."
    ),
    "current_annual_launches": 250,  # approximate 2024-2025
    "historical_peak_annual": 200,   # approximate, pre-Starship era
    "pad_throughput_constraint": (
        "Even with rapid-reuse vehicles, pad turnaround, weather windows, "
        "range safety, and airspace coordination create hard scheduling limits. "
        "Multiple pads help but introduce logistics complexity."
    ),
}


# =============================================================================
# ENERGY CONSTANTS
# =============================================================================

ENERGY = {
    "thermo_min_leo_mj_kg": 32.0,
    "practical_leo_mj_kg": 65.0,
    "delta_v_leo_m_s": 9_400,
    "meteoritic_influx_tonnes_yr": 40_000,
    "global_electricity_twh_yr": 29_000,  # approximate 2024
    "notes": (
        "Thermodynamic minimum is the absolute floor - no engine achieves it. "
        "Practical estimate includes gravity losses, drag, and engine efficiency. "
        "Real-world is typically 2-3x thermodynamic minimum."
    ),
}


# =============================================================================
# PRECOMPUTED MARGINS FOR CONSTRAINT CHECKER
# =============================================================================
#
# These enable simple "proposal_increment + current > ceiling" checks
# without recomputing from raw data each time.

def compute_margins() -> dict:
    """
    Compute current margins for all constraint categories.
    Returns nested dict matching the structure above with
    margin values and margin_fraction (how much headroom remains).
    """
    margins = {
        "orbital": {},
        "atmospheric": {},
        "minerals": {},
        "hydrogen_escape": {},
    }

    # Orbital margins by band
    for band_name, band_data in ORBITAL.items():
        margins["orbital"][band_name] = {
            "margin_kg": band_data["mass_margin_kg"],
            "margin_fraction": (
                band_data["mass_margin_kg"] / band_data["kessler_threshold_kg"]
            ),
            "uncertainty_pct": band_data["uncertainty_pct"],
        }

    # Atmospheric margins
    for pollutant, data in ATMOSPHERIC.items():
        margins["atmospheric"][pollutant] = {
            "margin_kg": data["margin_kg"],
            "margin_fraction": (
                data["margin_kg"] / data["conservation_ceiling_kg_yr"]
            ),
            "uncertainty_pct": data["uncertainty_pct"],
        }

    # Mineral margins
    for mineral, data in MINERALS.items():
        overshoot = data["current_production_kg_yr"] - data["conservation_ceiling_kg_yr"]
        margins["minerals"][mineral] = {
            "margin_kg_yr": -overshoot,  # negative means already over ceiling
            "margin_fraction": (
                -overshoot / data["conservation_ceiling_kg_yr"]
            ),
            "already_exceeding": overshoot > 0,
            "overshoot_factor": data["ratio_current_to_ceiling"],
            "uncertainty_pct": data["uncertainty_pct"],
        }

    # Hydrogen escape margin
    margins["hydrogen_escape"] = {
        "margin_kg_yr": HYDROGEN_ESCAPE["margin_kg_yr"],
        "margin_fraction": (
            HYDROGEN_ESCAPE["margin_kg_yr"] / HYDROGEN_ESCAPE["anthropogenic_cap_kg_yr"]
        ),
        "cap_basis": HYDROGEN_ESCAPE["cap_basis"],
    }

    return margins


# =============================================================================
# SUMMARY - What the numbers say at a glance
# =============================================================================

def print_summary():
    """Quick status check across all constraint categories."""
    margins = compute_margins()

    print("=" * 70)
    print(f"PLANETARY CONSERVATION FRAMEWORK - STATUS SUMMARY")
    print(f"Schema version: {SCHEMA_VERSION}")
    print("=" * 70)

    print("\nORBITAL BANDS:")
    for band, data in margins["orbital"].items():
        status = "OK" if data["margin_fraction"] > 0.2 else "CAUTION" if data["margin_fraction"] > 0.05 else "CRITICAL"
        print(f"  {band:<12}: {data['margin_fraction']*100:>5.1f}% margin remaining  [{status}]  (+-{data['uncertainty_pct']}%)")

    print("\nATMOSPHERIC:")
    for pollutant, data in margins["atmospheric"].items():
        status = "OK" if data["margin_fraction"] > 0.5 else "CAUTION" if data["margin_fraction"] > 0.1 else "CRITICAL"
        print(f"  {pollutant:<30}: {data['margin_fraction']*100:>5.1f}% margin  [{status}]")

    print("\nMINERALS (conservation ceiling vs current production):")
    for mineral, data in margins["minerals"].items():
        if data["already_exceeding"]:
            print(f"  {mineral:<22}: EXCEEDING ceiling by {data['overshoot_factor']:.1f}x  [CRITICAL]")
        else:
            print(f"  {mineral:<22}: {abs(data['margin_fraction'])*100:>5.1f}% margin  [OK]")

    print("\nHYDROGEN ESCAPE:")
    he = margins["hydrogen_escape"]
    print(f"  Margin: {he['margin_kg_yr']:,.0f} kg/yr ({he['margin_fraction']*100:.1f}% of cap)")
    print(f"  Basis: {he['cap_basis'][:70]}...")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_summary()
