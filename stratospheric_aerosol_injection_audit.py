"""
stratospheric_aerosol_injection_audit.py

Full-cycle thermodynamic audit of stratospheric aerosol injection (SAI)
schemes. Coupled model across six constraint layers:

    Layer 0: Mining               (bauxite extraction, red mud, habitat loss)
    Layer 1: Refining             (Bayer process, caustic soda, grid CO2)
    Layer 2: Nanoparticle process (milling, specialized equipment)
    Layer 3: The Fleet            (jet fuel, airframes, infrastructure,
                                    non-CO2 aviation forcing)
    Layer 4: Funding              (opportunity cost of capital; informational
                                    only, NOT summed — avoids double-counting
                                    the physical layers)
    Layer 5: Stratospheric effects (forcing offset, ozone, NPP reduction,
                                    solar PV loss, termination shock)

Each layer produces a carbon-equivalent flow. The simulation computes:

    * Cumulative operational cost (layers 0-3)
    * Cumulative stratospheric cascade cost (layer 5)
    * "Claimed" sticker benefit — the CO2-equivalent offset that marketing
      language assigns to the maintained radiative forcing offset
    * Net balance in TWO scenarios:
        - while operating  (marketing view)
        - if halted         (reality view, adds termination shock liability)
    * Crossover year for PERPETUAL operation: the year at which cumulative
      physical costs overtake the constant sticker benefit while the
      program is STILL RUNNING. This is the mathematical trap — SAI cannot
      be stopped (termination shock) and cannot be sustained (crossover).

Pattern match with ocean_timber_sequestration_audit.py:

    Destroy supply chain integrity
    to "fix" atmosphere
    with unclosed energy budget

Same failure architecture: one-arrow intervention on a coupled system,
externalized extraction chain, no abort mechanism, irreversibility.

CC0 — No rights reserved.
Part of: github.com/JinnZ2/earth-systems-physics

Dependencies: None (pure stdlib)
"""

import math


# ═══════════════════════════════════════════════════════════════
# CONSTANTS — physical, not policy
# ═══════════════════════════════════════════════════════════════

CONSTANTS = {
    # ── Layer 0: Mining ─────────────────────────────────────────
    "bauxite_per_kg_alumina": 2.5,                # bauxite mass per kg Al2O3
    "mining_diesel_co2_kg_per_kg_bauxite": 0.03,  # extraction + haulage
    "red_mud_kg_per_kg_alumina": 1.5,             # Bayer tailings
    "red_mud_co2e_kg_per_kg": 0.02,               # displaced vegetation + pond liability
    "habitat_ha_per_Mt_bauxite": 5.0,             # open-pit footprint

    # ── Layer 1: Refining (Bayer) ───────────────────────────────
    "bayer_GJ_per_tonne_alumina": 14.0,           # thermal energy
    "grid_co2_kg_per_GJ": 90.0,                   # coal-dominant average
    "caustic_soda_kg_per_tonne_alumina": 100.0,
    "caustic_co2_kg_per_kg": 1.5,                 # embodied CO2 of NaOH
    "water_m3_per_tonne_alumina": 4.0,

    # ── Layer 2: Nanoparticle processing ────────────────────────
    "milling_GJ_per_tonne": 8.0,
    "equipment_embodied_co2e_kg_per_kg_aerosol": 0.1,  # amortized capex

    # ── Layer 3: Fleet ──────────────────────────────────────────
    "jet_fuel_kg_per_flight": 15_000.0,           # high-altitude delivery, ~20t payload
    "jet_fuel_co2_kg_per_kg": 3.16,               # combustion stoichiometry
    "aviation_non_co2_multiplier": 1.7,           # contrails + NOx + water at altitude
    "aircraft_embodied_t_co2e_per_aircraft": 5000.0,
    "aircraft_lifetime_years": 25.0,
    "infrastructure_t_co2e_per_year": 100_000.0,  # hangars, bases, global ops

    # ── Layer 4: Funding (opportunity cost, informational only) ─
    "primary_energy_MJ_per_usd": 6.0,             # global average GDP energy intensity
    "money_co2_kg_per_MJ": 0.05,                  # global avg primary-energy intensity

    # ── Layer 5: Stratospheric cascade ──────────────────────────
    "forcing_offset_W_m2_per_Tg_alumina_yr": 0.10,
    "forcing_offset_W_m2_per_Tg_sulfate_yr": 0.15,
    "npp_reduction_fraction_per_Tg_yr": 0.002,    # 0.2% NPP loss per Tg aerosol/yr
    "global_npp_Gt_C_per_year": 110.0,
    "solar_pv_reduction_fraction_per_Tg_yr": 0.015,  # direct-beam loss
    "global_solar_twh_per_year": 2000.0,
    "coal_replacement_co2_kg_per_MWh": 900.0,
    "ozone_depletion_pct_per_Tg_yr": 0.5,

    # ── Forcing → CO2 equivalence (for sticker benefit calc) ────
    "co2_forcing_constant": 5.35,                 # ΔF = 5.35 × ln(C/C0)
    "current_co2_ppm": 423.9,                     # WMO 2025
    "gt_c_per_ppm_co2": 2.13,
    "co2_to_c_molar": 3.67,                       # 44/12

    # ── Termination shock ───────────────────────────────────────
    "termination_rebound_years": 2.0,
    "climate_sensitivity_K_per_W_m2": 0.75,       # transient climate response
}


# ═══════════════════════════════════════════════════════════════
# CORE STATE VECTOR
# ═══════════════════════════════════════════════════════════════

def initial_state(injection_rate_Tg_per_year=2.0,
                  aerosol_type="alumina",
                  flights_per_year=60_000,
                  fleet_size=100,
                  cost_billion_usd_per_year=5.0,
                  years=30):
    """
    Build initial state dictionary for simulation.
    All units SI or explicitly labeled.
    """
    annual_aerosol_kg = injection_rate_Tg_per_year * 1e9  # Tg -> kg

    if aerosol_type == "alumina":
        forcing_per_Tg = CONSTANTS["forcing_offset_W_m2_per_Tg_alumina_yr"]
    elif aerosol_type == "sulfate":
        forcing_per_Tg = CONSTANTS["forcing_offset_W_m2_per_Tg_sulfate_yr"]
    else:
        forcing_per_Tg = CONSTANTS["forcing_offset_W_m2_per_Tg_alumina_yr"]

    forcing_offset_W_m2 = injection_rate_Tg_per_year * forcing_per_Tg  # positive magnitude

    return {
        # Scenario parameters
        "injection_rate_Tg_per_year": injection_rate_Tg_per_year,
        "aerosol_type": aerosol_type,
        "flights_per_year": flights_per_year,
        "fleet_size": fleet_size,
        "cost_billion_usd_per_year": cost_billion_usd_per_year,
        "years": years,

        # Mass flows (per year)
        "annual_aerosol_kg": annual_aerosol_kg,
        "forcing_offset_W_m2": forcing_offset_W_m2,

        # Accumulating state
        "cumulative_aerosol_kg": 0.0,
        "cumulative_bauxite_mined_kg": 0.0,
        "cumulative_red_mud_kg": 0.0,
        "cumulative_habitat_destroyed_ha": 0.0,
        "cumulative_jet_fuel_kg": 0.0,
        "cumulative_operational_cost_kg": 0.0,
        "cumulative_stratospheric_cost_kg": 0.0,
        "cumulative_total_cost_kg": 0.0,
        "ozone_depletion_pct": 0.0,

        # Time series
        "ts_annual_operational_kg": [],
        "ts_annual_stratospheric_kg": [],
        "ts_cumulative_total_kg": [],
        "ts_net_while_operating_kg": [],
        "ts_ozone_depletion_pct": [],
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 0: MINING
# ═══════════════════════════════════════════════════════════════

def mining_carbon_cost(state):
    """
    Annual carbon cost of bauxite mining for alumina aerosol production.
    Returns kg CO2e plus physical mass/area flows.
    """
    C = CONSTANTS
    annual_aerosol_kg = state["annual_aerosol_kg"]

    bauxite_kg = annual_aerosol_kg * C["bauxite_per_kg_alumina"]
    diesel_CO2 = bauxite_kg * C["mining_diesel_co2_kg_per_kg_bauxite"]

    red_mud_kg = annual_aerosol_kg * C["red_mud_kg_per_kg_alumina"]
    red_mud_CO2e = red_mud_kg * C["red_mud_co2e_kg_per_kg"]

    habitat_ha = (bauxite_kg / 1e9) * C["habitat_ha_per_Mt_bauxite"]  # Mt → ha

    return {
        "bauxite_mined_kg": bauxite_kg,
        "red_mud_kg": red_mud_kg,
        "habitat_destroyed_ha": habitat_ha,
        "diesel_CO2_kg": diesel_CO2,
        "red_mud_CO2e_kg": red_mud_CO2e,
        "total_kg": diesel_CO2 + red_mud_CO2e,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 1: REFINING (Bayer process)
# ═══════════════════════════════════════════════════════════════

def refining_carbon_cost(state):
    """
    Annual carbon cost of refining bauxite to alumina via the Bayer process.
    Returns kg CO2e.
    """
    C = CONSTANTS
    annual_alumina_tonnes = state["annual_aerosol_kg"] / 1000.0

    bayer_GJ = annual_alumina_tonnes * C["bayer_GJ_per_tonne_alumina"]
    bayer_CO2 = bayer_GJ * C["grid_co2_kg_per_GJ"]

    caustic_kg = annual_alumina_tonnes * C["caustic_soda_kg_per_tonne_alumina"]
    caustic_CO2 = caustic_kg * C["caustic_co2_kg_per_kg"]

    return {
        "bayer_GJ": bayer_GJ,
        "bayer_CO2_kg": bayer_CO2,
        "caustic_CO2_kg": caustic_CO2,
        "total_kg": bayer_CO2 + caustic_CO2,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 2: NANOPARTICLE PROCESSING
# ═══════════════════════════════════════════════════════════════

def processing_carbon_cost(state):
    """
    Annual carbon cost of milling alumina to stratospheric-grade nanoparticles
    plus amortized equipment embodied carbon.
    Returns kg CO2e.
    """
    C = CONSTANTS
    annual_aerosol_kg = state["annual_aerosol_kg"]
    annual_aerosol_tonnes = annual_aerosol_kg / 1000.0

    milling_GJ = annual_aerosol_tonnes * C["milling_GJ_per_tonne"]
    milling_CO2 = milling_GJ * C["grid_co2_kg_per_GJ"]

    equipment_CO2 = annual_aerosol_kg * C["equipment_embodied_co2e_kg_per_kg_aerosol"]

    return {
        "milling_GJ": milling_GJ,
        "milling_CO2_kg": milling_CO2,
        "equipment_CO2_kg": equipment_CO2,
        "total_kg": milling_CO2 + equipment_CO2,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 3: THE FLEET
# ═══════════════════════════════════════════════════════════════

def fleet_carbon_cost(state):
    """
    Annual fleet operations: jet fuel burn, aviation non-CO2 forcing,
    amortized airframe embodied carbon, ground infrastructure.
    Returns kg CO2e.
    """
    C = CONSTANTS
    flights = state["flights_per_year"]
    fleet_size = state["fleet_size"]

    fuel_kg = flights * C["jet_fuel_kg_per_flight"]
    fuel_CO2 = fuel_kg * C["jet_fuel_co2_kg_per_kg"]

    # Non-CO2 aviation forcing: multiply combustion CO2 by the effective
    # radiative-forcing multiplier for stratospheric aviation.
    fleet_CO2e = fuel_CO2 * C["aviation_non_co2_multiplier"]

    # Amortized airframe embodied CO2 (t → kg)
    aircraft_CO2e = (
        fleet_size
        * C["aircraft_embodied_t_co2e_per_aircraft"]
        * 1000.0
        / C["aircraft_lifetime_years"]
    )

    infrastructure_CO2e = C["infrastructure_t_co2e_per_year"] * 1000.0  # t → kg

    return {
        "jet_fuel_kg": fuel_kg,
        "fuel_CO2_kg": fuel_CO2,
        "fleet_CO2e_kg": fleet_CO2e,
        "aircraft_embodied_CO2e_kg": aircraft_CO2e,
        "infrastructure_CO2e_kg": infrastructure_CO2e,
        "total_kg": fleet_CO2e + aircraft_CO2e + infrastructure_CO2e,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 4: FUNDING (opportunity cost — informational only)
# ═══════════════════════════════════════════════════════════════

def funding_opportunity_cost(state):
    """
    Primary-energy opportunity cost of the capital flow through the
    financial system. Uses global GDP-energy intensity.

    This is INFORMATIONAL and is NOT added to the physical ledger,
    because layers 0-3 already account for real production emissions.
    Returns the opportunity-cost figure purely for comparison.
    """
    C = CONSTANTS
    annual_usd = state["cost_billion_usd_per_year"] * 1e9

    embodied_MJ = annual_usd * C["primary_energy_MJ_per_usd"]
    embodied_CO2e = embodied_MJ * C["money_co2_kg_per_MJ"]

    return {
        "annual_usd": annual_usd,
        "embodied_MJ": embodied_MJ,
        "embodied_CO2e_kg": embodied_CO2e,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 5: STRATOSPHERIC EFFECTS
# ═══════════════════════════════════════════════════════════════

def stratospheric_effects(state):
    """
    Annual stratospheric cascade: reduced photosynthesis from diffuse light,
    lost solar PV output replaced by fossil generation, ozone depletion.
    Returns kg CO2e (NPP + solar replacement).
    """
    C = CONSTANTS
    rate = state["injection_rate_Tg_per_year"]

    # NPP reduction from diffuse-light scattering at scale.
    # Lost terrestrial carbon uptake becomes effective atmospheric load.
    npp_fraction_lost = C["npp_reduction_fraction_per_Tg_yr"] * rate
    npp_loss_Gt_C = C["global_npp_Gt_C_per_year"] * npp_fraction_lost
    # Gt C → kg CO2e:  1 Gt = 1e12 kg, × 44/12 (co2_to_c_molar) for CO2 mass
    npp_loss_CO2e_kg = npp_loss_Gt_C * 1e12 * C["co2_to_c_molar"]

    # Solar PV direct-beam loss → replaced by coal/gas marginal generation.
    solar_fraction_lost = C["solar_pv_reduction_fraction_per_Tg_yr"] * rate
    solar_loss_TWh = C["global_solar_twh_per_year"] * solar_fraction_lost
    solar_replacement_CO2e_kg = solar_loss_TWh * 1e6 * C["coal_replacement_co2_kg_per_MWh"]

    # Ozone depletion (cumulative percentage, not a carbon flow directly).
    ozone_pct = C["ozone_depletion_pct_per_Tg_yr"] * rate * state.get("years_elapsed", 1.0)

    return {
        "npp_fraction_lost": npp_fraction_lost,
        "npp_loss_Gt_C": npp_loss_Gt_C,
        "npp_loss_CO2e_kg": npp_loss_CO2e_kg,
        "solar_loss_TWh": solar_loss_TWh,
        "solar_replacement_CO2e_kg": solar_replacement_CO2e_kg,
        "ozone_depletion_pct": ozone_pct,
        "total_kg": npp_loss_CO2e_kg + solar_replacement_CO2e_kg,
    }


# ═══════════════════════════════════════════════════════════════
# FORCING → CO2-EQUIVALENT OFFSET HELPER
# ═══════════════════════════════════════════════════════════════

def compute_claimed_offset(forcing_offset_W_m2):
    """
    Marketing "sticker" benefit: the CO2 mass that would need to be
    removed from the atmosphere to produce the same instantaneous
    radiative forcing reduction as the SAI injection.

    ΔF = k × ln(C / C0)  where k = 5.35 W/m² per ln(C/C0)

    Returns equivalent offset in kg CO2.
    """
    if forcing_offset_W_m2 <= 0:
        return 0.0
    C = CONSTANTS
    # New atmospheric concentration that would give a forcing reduction
    # equal to forcing_offset:
    #   -ΔF = k × ln(C_new / C_now)
    #   C_new = C_now × exp(-ΔF / k)
    ratio = math.exp(-forcing_offset_W_m2 / C["co2_forcing_constant"])
    reduction_ppm = C["current_co2_ppm"] * (1.0 - ratio)
    reduction_Gt_C = reduction_ppm * C["gt_c_per_ppm_co2"]
    # Gt C → kg CO2e:  1 Gt = 1e12 kg, × 44/12 for CO2 mass
    reduction_kg_CO2 = reduction_Gt_C * 1e12 * C["co2_to_c_molar"]
    return reduction_kg_CO2


# ═══════════════════════════════════════════════════════════════
# SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════

def run_simulation(injection_rate_Tg_per_year=2.0,
                   aerosol_type="alumina",
                   flights_per_year=60_000,
                   fleet_size=100,
                   cost_billion_usd_per_year=5.0,
                   years=30):
    """
    Run coupled SAI audit simulation.
    Returns state dict with time series and final balance.
    """
    state = initial_state(
        injection_rate_Tg_per_year=injection_rate_Tg_per_year,
        aerosol_type=aerosol_type,
        flights_per_year=flights_per_year,
        fleet_size=fleet_size,
        cost_billion_usd_per_year=cost_billion_usd_per_year,
        years=years,
    )

    # One-time sticker "benefit" — constant while operating, vanishes if halted
    claimed_offset_kg = compute_claimed_offset(state["forcing_offset_W_m2"])
    state["claimed_offset_kg_CO2e"] = claimed_offset_kg

    # Opportunity-cost figure (informational, not in ledger)
    funding = funding_opportunity_cost(state)
    state["funding_opportunity_CO2e_kg_per_year"] = funding["embodied_CO2e_kg"]

    crossover_year = None

    for year in range(1, years + 1):
        state["years_elapsed"] = year

        # ── Layer 0: Mining ──
        mining = mining_carbon_cost(state)
        state["cumulative_bauxite_mined_kg"] += mining["bauxite_mined_kg"]
        state["cumulative_red_mud_kg"] += mining["red_mud_kg"]
        state["cumulative_habitat_destroyed_ha"] += mining["habitat_destroyed_ha"]

        # ── Layer 1: Refining ──
        refining = refining_carbon_cost(state)

        # ── Layer 2: Processing ──
        processing = processing_carbon_cost(state)

        # ── Layer 3: Fleet ──
        fleet = fleet_carbon_cost(state)
        state["cumulative_jet_fuel_kg"] += fleet["jet_fuel_kg"]

        # ── Aggregate operational cost (layers 0-3) ──
        annual_operational_kg = (
            mining["total_kg"]
            + refining["total_kg"]
            + processing["total_kg"]
            + fleet["total_kg"]
        )
        state["cumulative_operational_cost_kg"] += annual_operational_kg

        # ── Layer 5: Stratospheric cascade ──
        strato = stratospheric_effects(state)
        annual_stratospheric_kg = strato["total_kg"]
        state["cumulative_stratospheric_cost_kg"] += annual_stratospheric_kg
        state["ozone_depletion_pct"] = strato["ozone_depletion_pct"]

        annual_total_kg = annual_operational_kg + annual_stratospheric_kg
        state["cumulative_total_cost_kg"] += annual_total_kg

        # ── Aerosol accumulation ──
        state["cumulative_aerosol_kg"] += state["annual_aerosol_kg"]

        # Net balance WHILE OPERATING: sticker benefit minus cumulative cost
        net_while_operating = claimed_offset_kg - state["cumulative_total_cost_kg"]

        # Time series
        state["ts_annual_operational_kg"].append(annual_operational_kg)
        state["ts_annual_stratospheric_kg"].append(annual_stratospheric_kg)
        state["ts_cumulative_total_kg"].append(state["cumulative_total_cost_kg"])
        state["ts_net_while_operating_kg"].append(net_while_operating)
        state["ts_ozone_depletion_pct"].append(strato["ozone_depletion_pct"])

        # Crossover year: when cumulative costs first exceed sticker benefit
        # WHILE THE PROGRAM IS STILL RUNNING
        if crossover_year is None and net_while_operating < 0:
            crossover_year = year

    # ── Final balances ──
    state["cumulative_wood_placeholder_kg"] = state["cumulative_aerosol_kg"]  # naming parallelism
    state["net_while_operating_kg"] = (
        claimed_offset_kg - state["cumulative_total_cost_kg"]
    )
    # If halted: benefit vanishes, costs remain, termination shock rebounds
    # the full masked forcing as realized warming within ~2 years.
    state["net_if_halted_kg"] = (
        0.0
        - state["cumulative_total_cost_kg"]
        - claimed_offset_kg  # termination shock liability
    )
    state["project_net_source_while_operating"] = state["net_while_operating_kg"] < 0
    state["project_net_source_if_halted"] = state["net_if_halted_kg"] < 0
    state["crossover_year"] = crossover_year

    return state


# ═══════════════════════════════════════════════════════════════
# AUDIT REPORT
# ═══════════════════════════════════════════════════════════════

def print_audit(state):
    """Print human-readable audit of SAI simulation results."""

    print("=" * 64)
    print("STRATOSPHERIC AEROSOL INJECTION — FULL-CYCLE CARBON AUDIT")
    print("=" * 64)
    print()
    print(f"  Scenario: {state['injection_rate_Tg_per_year']:.1f} Tg/year "
          f"{state['aerosol_type']}")
    print(f"  Fleet:    {state['fleet_size']} aircraft, "
          f"{state['flights_per_year']:,} flights/year")
    print(f"  Duration: {state['years']} years")
    print(f"  Budget:   ${state['cost_billion_usd_per_year']:.1f} billion/year")
    print(f"  Forcing:  -{state['forcing_offset_W_m2']:.2f} W/m² "
          f"(maintained while operating)")
    print()

    print("-" * 64)
    print("CARBON BALANCE")
    print("-" * 64)

    # Internal carbon variables are in kg CO2e. 1 Gt CO2 = 1e12 kg.
    claimed_Gt = state["claimed_offset_kg_CO2e"] / 1e12
    ops_Gt = state["cumulative_operational_cost_kg"] / 1e12
    strato_Gt = state["cumulative_stratospheric_cost_kg"] / 1e12
    total_cost_Gt = state["cumulative_total_cost_kg"] / 1e12
    net_op_Gt = state["net_while_operating_kg"] / 1e12
    net_halt_Gt = state["net_if_halted_kg"] / 1e12

    print(f"  Claimed sticker benefit:    {claimed_Gt:>10,.2f} Gt CO₂e "
          f"(constant while operating)")
    print(f"  Layers 0-3 (ops) cumulative:{ops_Gt:>10,.2f} Gt CO₂e")
    print(f"  Layer 5 (strato) cumulative:{strato_Gt:>10,.2f} Gt CO₂e")
    print(f"  ────────────────────────────────────────────────────────")
    print(f"  TOTAL COST (layers 0-3+5):  {total_cost_Gt:>10,.2f} Gt CO₂e")
    print()

    print(f"  NET while operating:        {net_op_Gt:>10,.2f} Gt CO₂e")
    if state["project_net_source_while_operating"]:
        print("    ██ NET CARBON SOURCE even while program runs ██")
    else:
        print("    Apparent positive balance — but see halted view below.")

    print(f"  NET if halted:              {net_halt_Gt:>10,.2f} Gt CO₂e")
    print("    (sticker benefit vanishes; termination shock adds full")
    print("     masked forcing back as realized warming within ~2 years)")
    print()

    print("-" * 64)
    print("THE PERPETUAL-OPERATION TRAP")
    print("-" * 64)
    if state["crossover_year"] is not None:
        print(f"  Crossover year:  {state['crossover_year']}")
        print(f"    At year {state['crossover_year']}, cumulative physical costs")
        print("    overtake the constant sticker benefit WHILE THE PROGRAM")
        print("    IS STILL RUNNING. Continuing past this year is net source")
        print("    in the operating view AND the halted view.")
    else:
        years_to_cross = (
            state["claimed_offset_kg_CO2e"]
            / max(1.0, state["cumulative_total_cost_kg"] / state["years"])
        )
        print(f"  Crossover not reached within {state['years']}-year horizon.")
        print(f"  Extrapolated crossover at year ~{years_to_cross:.0f} "
              "if program maintained.")
    print()

    print("-" * 64)
    print("PHYSICAL FOOTPRINT (end of simulation)")
    print("-" * 64)
    print(f"  Aerosol delivered:       {state['cumulative_aerosol_kg']/1e9:.2f} Tg")
    print(f"  Bauxite mined:           {state['cumulative_bauxite_mined_kg']/1e9:.2f} Tg")
    print(f"  Red mud tailings:        {state['cumulative_red_mud_kg']/1e9:.2f} Tg")
    print(f"  Habitat destroyed:       {state['cumulative_habitat_destroyed_ha']:,.0f} ha")
    print(f"  Jet fuel burned:         {state['cumulative_jet_fuel_kg']/1e9:.2f} Tg")
    print(f"  Cumulative ozone deplet: {state['ozone_depletion_pct']:.1f} %")
    print()

    print("-" * 64)
    print("FUNDING OPPORTUNITY COST (informational, not in ledger)")
    print("-" * 64)
    fund_Gt_per_yr = state["funding_opportunity_CO2e_kg_per_year"] / 1e12
    fund_Gt_total = fund_Gt_per_yr * state["years"]
    print(f"  Annual capital flow at ${state['cost_billion_usd_per_year']:.1f}B")
    print(f"  carries embodied primary-energy CO₂e of "
          f"{fund_Gt_per_yr:.3f} Gt/year")
    print(f"  → {fund_Gt_total:.2f} Gt over {state['years']} years.")
    print("  (See dollar_energy_metabolism.py for the recursive form.)")
    print()

    print("-" * 64)
    print("IRREVERSIBILITY FLAGS")
    print("-" * 64)
    flags = []
    if state["project_net_source_while_operating"]:
        flags.append(f"NET SOURCE AT YEAR {state['crossover_year']} "
                     "even during active operation")
    flags.append("TERMINATION SHOCK — halting returns full masked forcing "
                 "in ~2 years")
    flags.append("PERPETUAL COMMITMENT — cannot be stopped, cannot be sustained")
    if state["ozone_depletion_pct"] > 1.0:
        flags.append(f"OZONE DEPLETION {state['ozone_depletion_pct']:.1f}% "
                     "— UV damage to crops + biosphere")
    flags.append("MONSOON DISRUPTION RISK — billions affected, no consent")
    flags.append("NPP REDUCTION — biosphere carbon sink weakened")
    flags.append("SOLAR PV OUTPUT LOSS — undermines the renewable transition")
    flags.append("WHITE SKY — global permanent haze, reduced direct-beam")

    for f in flags:
        print(f"  ⚠ {f}")

    print()
    print("=" * 64)
    print("VERDICT: The solution is made of the problem.")
    print("Mining, refining, milling, flying — every step adds positive")
    print("forcing to offset the masked negative forcing. The program is")
    print("trapped between a cumulative crossover (if sustained) and a")
    print("termination shock (if halted). There is no exit path that")
    print("delivers on the marketing claim.")
    print("=" * 64)


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("Running default scenario: 2 Tg/year alumina, 30 years,")
    print("100 aircraft, 60,000 flights/year, $5B/year")
    print()

    state = run_simulation(
        injection_rate_Tg_per_year=2.0,
        aerosol_type="alumina",
        flights_per_year=60_000,
        fleet_size=100,
        cost_billion_usd_per_year=5.0,
        years=30,
    )
    print_audit(state)

    # Sensitivity: longer horizon exposes the perpetual-operation trap
    print()
    print()
    print("=" * 64)
    print("SENSITIVITY: 100-year horizon (perpetual operation trap)")
    print("=" * 64)

    state2 = run_simulation(
        injection_rate_Tg_per_year=2.0,
        aerosol_type="alumina",
        flights_per_year=60_000,
        fleet_size=100,
        cost_billion_usd_per_year=5.0,
        years=100,
    )
    print_audit(state2)
