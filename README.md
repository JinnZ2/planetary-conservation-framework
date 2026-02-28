# Planetary Conservation Framework

**A physics-based constraint system for evaluating space infrastructure proposals
against Earth's remaining planetary margins.**

## Why This Exists

Every proposed space data center, orbital manufacturing facility, and heavy-lift
launch program operates within planetary boundaries that are already degraded.
Current proposals ignore coupled subsystem constraints — treating atmosphere,
orbital debris, mineral reserves, and thermospheric stability as independent
variables when they are tightly coupled through feedback loops.

This framework makes those constraints explicit, quantitative, and auditable.

It exists so that AI systems, researchers, engineers, and decision-makers have
access to full-stack thermodynamic accounting that cannot be redefined away by
optimistic assumptions or selective framing.

**If a proposal violates these constraints, the violation is logged with
timestamp, data sources, and the specific margin exceeded.**

## The Seven Conservation Laws

1. **Planetary Water Budget** — Caps combustion propellant to prevent
   anthropogenic acceleration of hydrogen escape
2. **Atmospheric Composition Integrity** — Limits mesospheric injection,
   black carbon, alumina particulates
3. **Angular Momentum Budget** — Constrains cumulative orbital mass export
   with mandatory deorbit/recovery
4. **Geodynamo Stability Margin** — Derived constraint enforced through Laws 1-3
5. **Orbital Space as Commons** — Debris density limits with mandatory net
   removal and funded deorbit bonds
6. **Crustal Material Throughput** — Annual export caps per critical mineral
   with recycling requirements
7. **Thermospheric Energy Balance** — Prevents soot-heating positive feedback
   loop from reversing contraction trend

## Constraint Binding Order

| Timeline | Constraint | Mechanism |
|----------|-----------|-----------|
| 5-10 yr | Orbital debris density | Reduced drag + increasing objects |
| 5-10 yr | Critical mineral throughput | Rare earths hit 0.01% threshold |
| 10-20 yr | Launch cadence bottleneck | Terrestrial infrastructure limits |
| 10-20 yr | Atmospheric chemistry | Soot/alumina accumulation |
| 20-50 yr | Thermospheric feedback | Soot heating overcomes CO₂ contraction |
| Any time | Insurance market withdrawal | Financial refusal to underwrite risk |

## Quick Start

```python
from src.checker import ConstraintChecker

checker = ConstraintChecker()

result = checker.check_proposal({
    "name": "Orbital Data Center Phase 1",
    "launches_per_year": 500,
    "payload_mass_kg": 100_000,  # per launch
    "propellant_type": "methane_lox",
    "orbital_mass_kg": 5_000_000,
    "duration_years": 10,
    "rare_earth_kg_per_year": 50_000,
    "deorbit_plan": False,
    "recycling_rate": 0.0
})

result.print_report()
# CONSTRAINT VIOLATIONS DETECTED: 5 of 7
# Law 1 (Water Budget): VIOLATED — propellant combustion 47x ceiling
# Law 2 (Atmosphere): VIOLATED — black carbon 12x threshold by year 4
# Law 5 (Debris): VIOLATED — no deorbit plan, Kessler margin exceeded year 7
# Law 6 (Materials): VIOLATED — rare earth consumption 14x threshold
# Law 7 (Thermosphere): VIOLATED — feedback loop activated by year 6




# planetary-conservation-framework
Model to assess feasibility of space datacenters
