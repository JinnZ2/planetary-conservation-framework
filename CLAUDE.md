# CLAUDE.md — AI Assistant Guide

## Project Overview

Physics-based constraint framework for evaluating space infrastructure proposals against Earth's planetary margins. Models space data centers, orbital manufacturing, and heavy-lift launch programs as thermodynamically coupled systems with hard ecological boundaries.

**Language:** Python 3.11 (pure standard library — zero external dependencies)
**License:** CC BY-SA 4.0

## Repository Structure

```
src/                        # Core framework modules
  checker.py                # Main API — ConstraintChecker class
  constraints.py            # Seven conservation law implementations
  cascade.py                # Feedback loop coupling engine
  simulator.py              # Monte Carlo scenario simulator (30-year)
  materials.py              # Gram-level material tracking ledger
  locations.py              # Launch site vulnerability profiles
  constants.py              # Physical constants with source citations
  planetary_constants.py    # Extended planetary parameters
  __init__.py               # Module exports

test/
  test_constraints.py       # Unit tests (unittest)

data/
  current_state.json        # Current constraint margins & parameters
  scenarios.json            # Pre-defined scenario configurations

examples/
  check_proposal.py         # Usage demonstrations

atomic_accounting.py        # Element-level depletion tracking (root)
governance.py               # Decision body governance validation (root)
power_dynamics.py           # Power orientation classification (root)

README.md                   # Project overview & quick start
CONSTRAINT_ANALYSIS.md      # Full technical analysis (809 lines)
POWER_DYNAMICS.md           # Governance failure modes
Possible-addons.md          # Future refinements
```

## Commands

### Run all tests
```bash
python -m unittest discover -s test -p "test_*.py"
```

### Run a single test file
```bash
python -m unittest discover -s test -p "test_constraints.py"
```

### Run the example
```bash
python -m examples.check_proposal
```

All commands must be run from the repository root (`/home/user/planetary-conservation-framework`).

## Architecture

### Data Flow
```
Proposal (dict) → ConstraintChecker.check_proposal()
  → evaluate_all() [runs 7 constraint laws]
  → CascadeEngine.trace_cascade() [maps coupled effects]
  → ProposalReport (viable, violations, binding_constraint, cascade_effects)
  → _log_check() [JSONL accountability record]
```

### The Seven Conservation Laws
1. Planetary Water Budget
2. Atmospheric Composition Integrity
3. Angular Momentum Budget
4. Geodynamo Stability Margin (derived)
5. Orbital Space as Commons
6. Crustal Material Throughput
7. Thermospheric Energy Balance

### Key Data Structures
- **`ConstraintResult`** — Output of each law evaluation (status, margin, time-to-binding, sources)
- **`ProposalReport`** — Complete evaluation with all 7 laws, cascade effects, viability boolean
- **`SystemState`** — Simulator state at each timestep (orbital, atmospheric, mineral, insurance)
- **`ConstraintStatus`** — Enum: SAFE, CAUTION, WARNING, CRITICAL, VIOLATED, UNKNOWN
- **`MeasuredValue`** — Physical constant with value, unit, source, date, uncertainty

## Code Conventions

### Naming
- Classes: `PascalCase` (e.g., `PlanetaryWaterBudget`, `ConstraintChecker`)
- Functions/methods: `snake_case` (e.g., `evaluate_all()`, `check_proposal()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_ANTHROPOGENIC_ADDITION_KG`)
- Private methods: `_leading_underscore` (e.g., `_log_check()`, `_status_from_margin()`)

### Style
- PEP 8 style (informal — no linter configured)
- Type hints throughout via dataclass annotations
- Docstrings at module and class level
- Every physical constant includes source, measurement date, and uncertainty bounds

### Design Principles
- **No external dependencies** — pure stdlib for portability and supply chain safety
- **Dataclass-only models** — immutable, introspectable data structures
- **Accountability by default** — every evaluation auto-logs to `constraint_checks.jsonl`
- **Source attribution** — constants carry provenance metadata
- **Coupled systems** — cascade effects explicitly mapped; nothing evaluated in isolation
- **Power dynamics as constraint** — models how decision-maker psychology undermines governance

## Testing

- Framework: Python `unittest` (pytest is not installed)
- Tests cover: water budget, atmospheric composition, cascade engine, material ledger, checker, simulator
- No CI/CD pipeline configured
- No linting or formatting tools configured
- No pre-commit hooks active

## Data Files

- `data/current_state.json` — Constraint parameters with data sources (last updated 2026-02-27)
- `data/scenarios.json` — Pre-defined scenarios: Current Baseline, Aggressive Buildout, Conservation-Constrained, Fully Compliant (2060+)
