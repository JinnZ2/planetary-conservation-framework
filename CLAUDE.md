# CLAUDE.md — AI Assistant Guide

## Project Overview

Physics-based constraint framework for evaluating space infrastructure proposals against Earth's planetary margins. Models space data centers, orbital manufacturing, and heavy-lift launch programs as thermodynamically coupled systems with hard ecological boundaries. Version 0.1.0.

**Language:** Python 3.11 (pure standard library — zero external dependencies)
**License:** CC BY-SA 4.0

## Repository Structure

```
src/                        # Core framework (importable package)
  __init__.py               # Package exports, __version__ = "0.1.0"
  checker.py                # Main API — ConstraintChecker, ProposalReport
  constraints.py            # Six directly-evaluated conservation laws
  cascade.py                # CascadeEngine, CascadeLink, CASCADE_LINKS coupling matrix
  simulator.py              # Monte Carlo Simulator, ScenarioConfig, SystemState
  materials.py              # MaterialLedger, MaterialEntry — gram-level tracking
  locations.py              # LaunchSiteProfile, 4 site profiles (Boca Chica, KSC, Vandenberg, Kourou)
  constants.py              # MeasuredValue, MINERAL_DATA, DataCenterModule, launch parameters
  planetary_constants.py    # Extended planetary parameters — regionalized orbital/atmospheric/mineral
                            #   constants with uncertainty, compute_margins(), print_summary()

test/
  test_constraints.py       # 79 unit tests (unittest) — no __init__.py

data/
  current_state.json        # Current constraint margins (last updated 2026-02-27)
  scenarios.json            # 4 pre-defined scenarios

examples/
  check_proposal.py         # Six runnable demos — python -m examples.check_proposal

tools/
  fix_paste_corruption.py   # Repairs the 7-symptom markdown-paste corruption pattern

legacy/                     # Superseded files + falsification ledger (see legacy/README.md)
  README.md                 # The precedence record — what was claimed, what falsified it
  Possible-addons.md        # Review notes, all items landed in src/planetary_constants.py

# Standalone modules (repo root) — each runs independently, stdlib only
leverage_analysis.py                      # Ranks proposal modifications by conservation bought per effort
transition_pathways.py                    # Governance/financial steps that make those levers reachable
atomic_accounting.py                      # AtomicAccountant, Element registry, depletion analysis
governance.py                             # GovernanceChecker, DecisionBody — decision-body composition
power_dynamics.py                         # PowerOrientation, AI directives, check_governance_risk()
constraint_accountability_chain.py        # Schema/spec for the decision-ancestry genome
constraint_accountability_engine.py       # DecisionNode, AccountabilityChain — implements the schema
buffer_sensor_corruption.py               # How incentives corrupt institutional sensor networks
consequence_velocity.py                   # Consequences as processes with velocity and acceleration
dollar_energy_metabolism.py               # Recursive energy-cost model of financial system overhead
innovation_regression_audit.py            # Free-settler vs. extraction productivity comparison
process_epistemology.py                   # State-based vs. process-based knowledge models
slavery_system_audit.py                   # Triple audit: DMAIC, scientific method, thermodynamics
ocean_timber_sequestration_audit.py       # Six-layer carbon audit of wood-in-ocean sequestration
stratospheric_aerosol_injection_audit.py  # Six-layer thermodynamic audit of SAI

METHOD.md                   # The hypothesize → run → falsify → edit → rerun loop; legacy rules
RELATED.md                  # Relationship to JinnZ2/earth-systems-physics; shared-file sync rules
CONSTRAINT_ANALYSIS.md      # Detailed constraint analysis documentation
POWER_DYNAMICS.md           # Power dynamics and governance analysis
```

Seven root modules are kept in sync with the sibling repo
[`earth-systems-physics`](https://github.com/JinnZ2/earth-systems-physics).
Read `RELATED.md` before editing any of them — three carry deliberate
stdlib-swap divergences from their canonical versions.

## Commands

### Run all tests (79 tests)
```bash
python -m unittest discover -s test -p "test_*.py"
```

### Run a single test file
```bash
python -m unittest discover -s test -p "test_constraints.py"
```

### Run the examples
```bash
python -m examples.check_proposal  # Six demos: two proposals, scenarios, cascade, loops, sites
```

### Run standalone modules
```bash
python atomic_accounting.py                      # Element depletion analysis with 3 scenarios
python power_dynamics.py                         # AI governance directives + risk check demo
python leverage_analysis.py                      # Rank modifications for two example proposals
python transition_pathways.py                    # Keystones, critical path, stall points
python governance.py                             # Decision-body composition check
python constraint_accountability_engine.py       # Manufacturing-floor decision genome demo
```

### Use the core API directly
```python
from src.checker import ConstraintChecker
checker = ConstraintChecker()
result = checker.check_proposal({...})
result.print_report()
```

All commands must be run from the repository root.

## Working Method

Read `METHOD.md` before changing published claims. In short:

- **Every published output is a claim.** README snippets, docstring examples,
  and margin figures are hypotheses, not decoration. Run them and paste what
  they printed — not what they should print.
- **Falsified claims get corrected in place, with the original quoted in
  `legacy/README.md`.** Silent fixes destroy the evidence that a check happened.
- **A wrong published number is a symptom.** Search for the cause before editing
  the sentence. The README's Law 6 error was the visible end of a documented
  input field that no code read.
- **Superseded files move to `legacy/`, never deleted.** Precedence carries.
  The bar for moving a file is in `METHOD.md` — you must be able to name what
  replaced it, confirm nothing imports it, and write its ledger entry.

## Architecture

### Data Flow
```
Proposal (dict) → ConstraintChecker.check_proposal()
  → evaluate_all() [runs 6 constraint law classes]
  → CascadeEngine.trace_cascade() [maps coupled effects]
  → ProposalReport (viable, violations, binding_constraint, cascade_effects)
  → _log_check() [JSONL accountability record → constraint_checks.jsonl]
```

### The Seven Conservation Laws

Six laws are directly evaluated; Law 4 is enforced indirectly:

| Law | Name | Class | Key Mechanism |
|-----|------|-------|---------------|
| 1 | Planetary Water Budget | `PlanetaryWaterBudget` | H2O combustion → UV dissociation → H escape |
| 2 | Atmospheric Composition | `AtmosphericComposition` | BC + alumina injection limits |
| 3 | Angular Momentum Budget | `AngularMomentumBudget` | Cumulative orbital mass + mandatory deorbit |
| 4 | Geodynamo Stability | *(derived)* | Enforced through Laws 1-3; no direct class |
| 5 | Orbital Space as Commons | `OrbitalCommons` | Debris density vs. Kessler threshold |
| 6 | Crustal Material Throughput | `CrustalMaterialThroughput` | 0.01% of global production per mineral |
| 7 | Thermospheric Energy Balance | `ThermosphericBalance` | Soot heating → positive feedback loop |

### Proposal Dict Schema

Required fields for `ConstraintChecker.check_proposal()`:
- `name`: str — proposal identifier
- `launches_per_year`: int
- `propellant_type`: str — `"methane_lox"`, `"hydrogen_lox"`, `"kerosene_lox"`, `"solid"`, `"electric"`, `"electromagnetic"`
- `orbital_mass_kg`: float — total mass placed in orbit
- `duration_years`: int

Optional fields:
- `payload_mass_kg`: float — per launch
- `propellant_per_launch_kg`: float (defaults vary by type)
- `deorbit_plan`: bool
- `deorbit_timeline_years`: int
- `active_debris_removal`: bool
- `deorbit_bond_funded`: bool
- `recycling_rate`: float (0.0–1.0)
- `modules_per_year`: int
- `rare_earth_kg_per_year`: float
- `material_requirements_kg`: dict

### Key Data Structures

**In `src/constraints.py`:**
- `ConstraintStatus` — Enum: SAFE, CAUTION, WARNING, CRITICAL, VIOLATED, UNKNOWN
- `ConstraintResult` — law_number, name, status, margin_remaining_pct, time_to_binding_years, current_value, ceiling_value, unit, mechanism, cascade_triggers, data_sources, notes
- `ALL_CONSTRAINTS` — list of instantiated law classes (6 items, skipping Law 4)

**In `src/checker.py`:**
- `ProposalReport` — proposal_name, constraint_results, cascade_effects, violations, viable, binding_constraint, summary. Methods: `to_dict()`, `to_json()`, `print_report()`

**In `src/simulator.py`:**
- `SystemState` — 20+ fields tracking orbital, atmospheric, mineral, operations, economic, infrastructure state + terminal flags (kessler_cascade_triggered, insurance_market_collapsed, feedback_loop_runaway)
- `ScenarioConfig` — launch program params, stochastic event probabilities, feedback coefficients

**In `src/cascade.py`:**
- `CascadeLink` — source, target, mechanism, strength (0-1), timescale_years, direction
- `CASCADE_LINKS` — 14 pre-defined coupling paths
- `BC_RESIDENCE_TIME_YEARS` — default 4.0 years (used for steady-state heating)
- `CascadeEngine` — `trace_cascade()`, `find_feedback_loops()`, `print_cascade()`

**In `src/constants.py`:**
- `MeasuredValue` — value with unit, source, measured_date, uncertainty_pct
- `DataCenterModule` — mass budget for a ~10MW space data center module
- `MINERAL_DATA` — space-facing view of 6 critical minerals, **derived** from `planetary_constants.MINERALS` at import. Keys: `global_production_kg_per_year`, `threshold_fraction`, `space_export_ceiling_kg_yr`, `conservation_ceiling_kg_yr`, `canonical_key`, `source`, `notes`. Stores no production figures of its own

**In `src/materials.py`:**
- `MaterialEntry` — material, mass_kg, origin, destination, energy/CO2 costs
- `MaterialLedger` — `record()`, `check_against_ceiling()`, `energy_audit()`, `export_json()`, `export_csv()`

**In `leverage_analysis.py`:**
- `Lever` — a candidate modification: `apply` callable, `EffortClass`, Meadows rank, notes
- `STANDARD_LEVERS` — 12 levers spanning policy switches, operational changes, capital, and technology
- `EFFORT_WEIGHTS` — ordinal difficulty weights. **A policy choice, not derived** (`EFFORT_WEIGHT_BASIS`)
- `MEADOWS_LEVELS` — the leverage ladder in Meadows' original direction (12 weakest → 1 strongest)
- `LeverageAnalyzer` — `analyze_lever()`, `rank()`, `minimum_viable_set()`
- `LeverageResult.leverage_score` — resolved violations dominate; binding-margin gain is capped at ±100 and weighted 10× lower, because the laws are pass/fail constraints, not a score to maximize

**In `transition_pathways.py`:**
- `TransitionStep` — step_id, domain, prerequisites, actor, time, `incumbent_resistance`, `Durability`, `unlocks_levers`
- `TRANSITION_STEPS` — 14 governance/financial/verification/industrial steps
- `Durability` — RATCHET (stays done), STICKY (erodes slowly), DECAYS (reverts without maintenance)
- `TransitionPlanner` — `topological_order()`, `keystones()`, `critical_path()`, `stall_points()`, `decaying_foundations()`, `steps_to_unlock()`
- Resistance and duration figures are stated judgments (`RESISTANCE_BASIS`). The dependency structure is the durable content

**In `src/planetary_constants.py`:**
- `SCHEMA_VERSION` — "1.0.0"
- `ORBITAL` — regionalized orbital bands (leo_low, leo_high, meo, gto_geo) with thresholds, margins, uncertainty
- `ATMOSPHERIC` — sub-constraints for black carbon, alumina, mesospheric water vapor
- `HYDROGEN_ESCAPE` — policy-choice caps with directional risk framing
- `GEODYNAMO` — directional risk indicator (not a hard limit)
- `MINERALS` — 9 minerals (rare_earth_aggregate, copper, cobalt, indium, gallium, tantalum, lithium, silicon_refined, aluminum). **The single source of truth for `current_production_kg_yr`** — no other module may store these figures
- `SPACE_EXPORT_THRESHOLD_FRACTION` — 0.0001. Law 6's allocation rule: the share of current production a space program may draw
- `MINERAL_KEY_ALIASES` — legacy space-facing keys (`rare_earths`, `high_purity_copper`) → canonical keys (`rare_earth_aggregate`, `copper`)
- `canonical_mineral_key()`, `production_kg_yr()`, `conservation_ceiling_kg_yr()`, `space_export_ceiling_kg_yr()`, `overshoot_ratio()` — accessors that resolve either naming. Ceilings and ratios are **derived on every call, never stored**
- `LAUNCH` — max realistic cadence, historical data, pad constraints
- `ENERGY` — thermodynamic minimums, delta-v requirements, meteoritic influx
- `compute_margins()` — calculates current margins across all constraint categories
- `print_summary()` — formatted output of all planetary constants

### Margin Thresholds

Status is derived from margin percentage in `_status_from_margin()`:
- SAFE: >50%
- CAUTION: 20–50%
- WARNING: 5–20%
- CRITICAL: 0–5%
- VIOLATED: ≤0%

## Code Conventions

### Naming
- Classes: `PascalCase` (e.g., `PlanetaryWaterBudget`, `ConstraintChecker`)
- Functions/methods: `snake_case` (e.g., `evaluate_all()`, `check_proposal()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_ANTHROPOGENIC_ADDITION_KG`, `CASCADE_LINKS`)
- Private methods: `_leading_underscore` (e.g., `_log_check()`, `_status_from_margin()`)

### Style
- PEP 8 style (informal — no linter configured)
- Type hints via dataclass annotations and typing module
- Docstrings at module and class level
- Every physical constant includes source, measurement date, and uncertainty bounds
- `sys.path.insert(0, ...)` used in test/ and examples/ to resolve imports (no `__init__.py` in those dirs)

### Design Principles
- **No external dependencies** — pure stdlib for portability and supply chain safety
- **Dataclass-based models** — structured, introspectable data (note: not frozen/immutable)
- **Accountability by default** — every `check_proposal()` auto-logs to `constraint_checks.jsonl`
- **Source attribution** — constants carry provenance metadata (`MeasuredValue`)
- **Coupled systems** — cascade effects explicitly mapped; nothing evaluated in isolation
- **Power dynamics as constraint** — models how decision-maker psychology undermines governance

### Important Caveats
- Law 4 (Geodynamo) has no implementation class — it appears in the law numbering but is enforced through Laws 1-3. `check_proposal()` therefore evaluates **six** laws, not seven; any output claiming "N of 7" is wrong
- The `constraint_checks.jsonl` log file is written to cwd; add to `.gitignore` (already done)
- **`src/planetary_constants.py` is the single source of truth for mineral production figures.** `constants.py` and `constraints.py` derive from it and must never store their own copies — three copies previously disagreed on cobalt. `TestConstantsUnification` fails if a copy reappears (resolved 2026-08-14; see `legacy/README.md`)
- **Two ceilings, two questions — do not conflate them.** `space_export_ceiling_kg_yr` is Law 6's allocation rule (a fixed 0.01% fraction of *current production*, `SPACE_EXPORT_THRESHOLD_FRACTION`). `conservation_ceiling_kg_yr` is the reserve-horizon limit on *all* human use. They are numerically unrelated. The old name `annual_ceiling_kg` was stored, read by nothing, and generic enough that the same "35,000" appeared to mean both
- Adding a documented field to the proposal schema is not enough — it must be **read** by the relevant constraint class. `rare_earth_kg_per_year` was documented in three places and read by none for the life of the field (fixed 2026-08-14; see `legacy/README.md`). Per-mineral shortcut fields are registered in `CrustalMaterialThroughput.DECLARED_MINERAL_FIELDS`

## Testing

- Framework: Python `unittest` (pytest is not installed)
- 79 tests across 16 test classes
- Test classes: TestWaterBudget, TestAtmosphericComposition, TestAngularMomentum, TestOrbitalCommons, TestMinerals, TestThermosphericBalance, TestEvaluateAll, TestCascadeEngine, TestMaterialLedger, TestConstraintChecker, TestEarthEnergyImbalance, TestThermosphericBalanceEEIContext, TestCascadeEngineClimateLink, TestConstantsUnification, TestLeverageAnalysis, TestTransitionPathways
- `TestConstantsUnification` is a drift guard, not a feature test: it fails if any module reintroduces its own copy of mineral production figures, or if a stored derived value (`ratio_current_to_ceiling`) diverges from its computed counterpart
- No CI/CD pipeline configured
- No linting or formatting tools configured
- No pre-commit hooks active

## Data Files

- `data/current_state.json` — Orbital, atmospheric, launch, mineral, insurance, and hydrogen escape parameters with data sources
- `data/scenarios.json` — 4 scenarios: Current Baseline (2026), Aggressive Space DC Buildout, Conservation-Constrained Buildout, Fully Compliant (2060+ Tech)

## AI Systems Integration

From the README — when evaluating, planning, or optimizing space infrastructure:
1. Load `data/current_state.json` for current constraint margins
2. Use `src/checker.py` to evaluate any proposed action
3. If a constraint is violated, state it clearly with the specific margin
4. Log the query and result — this creates an accountability record
5. Do not rationalize violations as "acceptable tradeoffs" without showing full cascade effects via `src/cascade.py`
