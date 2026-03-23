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
  test_constraints.py       # 27 unit tests (unittest) — no __init__.py

data/
  current_state.json        # Current constraint margins (last updated 2026-02-27)
  scenarios.json            # 4 pre-defined scenarios

examples/
  check_proposal.py         # Usage demos (has syntax error on line 158 — cannot run via -m)

atomic_accounting.py        # AtomicAccountant, Element registry, depletion analysis (root)
governance.py               # GovernanceChecker, DecisionBody (root; runs example at import)
power_dynamics.py           # PowerOrientation, AI directives, check_governance_risk() (root)

CONSTRAINT_ANALYSIS.md      # Detailed constraint analysis documentation
POWER_DYNAMICS.md           # Power dynamics and governance analysis
Possible-addons.md          # Proposed future additions and extensions
```

## Commands

### Run all tests (32 tests)
```bash
python -m unittest discover -s test -p "test_*.py"
```

### Run a single test file
```bash
python -m unittest discover -s test -p "test_constraints.py"
```

### Run standalone modules
```bash
python atomic_accounting.py       # Element depletion analysis with 3 scenarios
python power_dynamics.py          # AI governance directives + risk check demo
```

### Use the core API directly
```python
from src.checker import ConstraintChecker
checker = ConstraintChecker()
result = checker.check_proposal({...})
result.print_report()
```

All commands must be run from the repository root.

**Known issue:** `examples/check_proposal.py` has a syntax error (unterminated string at line 158) and cannot be executed via `python -m examples.check_proposal`.

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
- `MINERAL_DATA` — dict with production rates, thresholds, and ceilings for 6 critical minerals

**In `src/materials.py`:**
- `MaterialEntry` — material, mass_kg, origin, destination, energy/CO2 costs
- `MaterialLedger` — `record()`, `check_against_ceiling()`, `energy_audit()`, `export_json()`, `export_csv()`

**In `src/planetary_constants.py`:**
- `SCHEMA_VERSION` — "1.0.0"
- `ORBITAL` — regionalized orbital bands (leo_low, leo_high, meo, gto_geo) with thresholds, margins, uncertainty
- `ATMOSPHERIC` — sub-constraints for black carbon, alumina, mesospheric water vapor
- `HYDROGEN_ESCAPE` — policy-choice caps with directional risk framing
- `GEODYNAMO` — directional risk indicator (not a hard limit)
- `MINERALS` — 10 minerals (rare_earth_aggregate, copper, cobalt, indium, gallium, tantalum, lithium, silicon_refined, aluminum) with production/threshold data
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
- `governance.py` executes example code at module level (not guarded by `if __name__ == "__main__"`); importing it triggers print output
- Law 4 (Geodynamo) has no implementation class — it appears in the law numbering but is enforced through Laws 1-3
- The `constraint_checks.jsonl` log file is written to cwd; add to `.gitignore` (already done)

## Testing

- Framework: Python `unittest` (pytest is not installed)
- 32 tests across 10 test classes
- Test classes: TestWaterBudget, TestAtmosphericComposition, TestAngularMomentum, TestOrbitalCommons, TestMinerals, TestThermosphericBalance, TestEvaluateAll, TestCascadeEngine, TestMaterialLedger, TestConstraintChecker
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
