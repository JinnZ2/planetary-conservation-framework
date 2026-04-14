# Related Work

This repo is a sibling of
[JinnZ2/earth-systems-physics](https://github.com/JinnZ2/earth-systems-physics),
not a parent or child of it. Several standalone audit files exist in both
repos and are kept in sync; a few files are specific to one repo or the
other. This document records the relationship so future edits don't
accidentally diverge.

## What the two repos are

**`planetary-conservation-framework`** (this repo) is a physics-based
constraint framework for evaluating space infrastructure proposals against
Earth's planetary margins. It models space data centers, orbital
manufacturing, and heavy-lift launch programs as thermodynamically coupled
systems with hard ecological boundaries. Version 0.1.0. Pure standard
library — zero external dependencies.

The framework code lives in `src/` (checker, constraints, cascade,
simulator, materials, locations, constants, planetary_constants) with tests
in `test/`. Standalone audits live at the repo root.

**`earth-systems-physics`** is a coupled differential equation framework
mapping Earth physics as constraint layers 0-6 (electromagnetics,
magnetosphere, ionosphere, atmosphere, hydrosphere, lithosphere,
biosphere), plus a 0b magnomechanical sub-layer, a cascade engine, an
assumption validator, and a collection of magnomechanical modules
(banded_crystal_computer, cavity_optomagnonics, magnon_polaron_hybridization,
etc.). It accepts numpy as a dependency.

The shared audit files are a set of system-diagnostic modules that apply
equally to both frameworks and live at the root of each repo.

## Shared files (kept in sync)

These seven files appear in both repos and are intended to stay
semantically equivalent. They are social / institutional / financial
diagnostics rather than physics code, which is why they naturally live in
both the Earth-systems framework and the conservation framework.

| File | Role |
|---|---|
| `buffer_sensor_corruption.py` | Models how incentive structures corrupt sensor networks — institutional sensors that optimize for comfort over accuracy |
| `consequence_velocity.py` | Treats consequences as processes with velocity, acceleration, coupling, and buffer capacity rather than fixed future costs |
| `dollar_energy_metabolism.py` | Recursive two-parameter energy-cost model for financial system overhead (leverage, margin, taxation, narrative, political) |
| `innovation_regression_audit.py` | Compares free-settler vs. extraction productivity; proves slavery is a regression from prior labor systems, not an innovation |
| `ocean_timber_sequestration_audit.py` | Full-cycle carbon audit of wood-in-ocean sequestration schemes across six coupled layers (harvest, transport, benthic, chemistry, gas, thermohaline) |
| `process_epistemology.py` | State-based vs. process-based knowledge models (English "the soil is fertile" vs. Ojibwe "the soil is fertiling") |
| `slavery_system_audit.py` | Triple audit of chattel slavery via Six Sigma DMAIC, scientific method, and thermodynamic analysis — all three reject the labor-system hypothesis |

### Intentional divergences from canonical

Three of the shared files diverge from the `earth-systems-physics` canonical
versions in small, deliberate ways to satisfy this repo's pure-stdlib rule
(CLAUDE.md: "Python 3.11 — pure standard library, zero external
dependencies"):

- **`buffer_sensor_corruption.py`** — drops `import numpy as np`, adds a
  local `_mean(xs)` helper, swaps `np.mean(...)` to `_mean(...)` in two
  sites.
- **`consequence_velocity.py`** — drops the unused `import numpy as np`
  line. No other changes.
- **`process_epistemology.py`** — swaps `import numpy as np` to
  `import random`, `np.random.seed(42)` to `random.seed(42)`, and
  `np.random.normal(0, 0.01)` to `random.gauss(0, 0.01)`.

**`dollar_energy_metabolism.py`** diverges from canonical in a different
direction: it carries documentation and variable-name improvements that
were made here during audit and have not yet been ported back to
`earth-systems-physics`. Specifically:

- The module docstring describes the actual two-parameter model
  (`subtotal / (1 - r_recursive)`, layer sum + recursive tail) instead of
  the earlier one-parameter simplification (`E_base / (1 - r_effective)`)
  that didn't match what the code computes.
- The `funding_years_low/high` local variables were renamed to
  `funding_frac_low/high` — they're fractions, not years.
- Comment said "six overhead layers" when there are five.
- `find_breakeven_r()` docstring clarifies the `subtotal=13.7` default
  comes from the typical-climate scenario mid-layer sum.
- The `layer_positions` field comment includes `'none'` as a valid option
  (used by the `direct_action` scenario).

These are improvements worth porting back upstream the next time the
canonical version is edited; the sync direction is `planetary-conservation-framework → earth-systems-physics`
for this file.

## Cloned from earth-systems-physics

These two files were cloned from `earth-systems-physics` as a matched
pair. They are also kept in sync going forward, with one known naming
asymmetry:

| File | Role |
|---|---|
| `constraint_accountability_chain.py` | Schema / meta-model. Pure dict templates (`DECISION_NODE`, `ACCOUNTABILITY_CHAIN`) documenting the "DNA-like ancestry of decisions where comfort was chosen over direct sensing." No executable code, no imports. |
| `constraint_accountability_engine.py` | Working engine. `DecisionNode` + `AccountabilityChain` classes implementing the schema — comfort propagation, override-failure detection, reversion-cost calculation, cascade-risk sigmoid, institutional-blindness phenotype, epigenetic event modifiers. Pure stdlib (`hashlib`, `time`, `math`). Ships with a manufacturing-floor safety demo under `if __name__ == "__main__":`. |

### Why these are here

They are the decision-level analog of this repo's sensor-level
`buffer_sensor_corruption.py`. Both files share the same core axis —
`direct_sense` vs `comfort_protect` — and the same vocabulary for how
ground signal gets distorted (`attenuation`, `delay`, `reframe`,
`delegate_down`, `normalize`, `silence`). `buffer_sensor_corruption`
models the phenomenon at individual sensors; these two files model it at
the governance / decision-chain level, tracing a specific decision's
ancestry back to the originating comfort choice.

They sit naturally next to `governance.py` and `power_dynamics.py`,
adding an analytical dimension those files don't cover: genealogical
propagation of a specific decision through layers, and the non-linear
`cascade_risk` + `time_to_failure` phenotype that drops out of the
accumulated signal distortion.

### Filename asymmetry vs upstream

The canonical file in `earth-systems-physics` is named
`constraint_availability_enginr.py` — the filename has two separate
errors (`availability` should be `accountability`, `enginr` should be
`engine`). However, line 1 of the file itself is the comment
`# constraint_accountability_engine.py`, which is the internally-correct
name. When the file was cloned here, the filename was corrected to match
its own self-naming, which is why this repo uses
`constraint_accountability_engine.py`.

Upstream sync strategy: when next touching the file over there, rename
`constraint_availability_enginr.py` → `constraint_accountability_engine.py`
to match this repo and the file's own header comment. Direction for this
sync asymmetry: `planetary-conservation-framework → earth-systems-physics`
(filename only; contents are identical).

## Files specific to this repo (no earth-systems-physics counterpart)

These exist here but not in `earth-systems-physics`:

- `stratospheric_aerosol_injection_audit.py` — the SAI counterpart to
  `ocean_timber_sequestration_audit.py`, with the same six-layer structure
  and the same "solution is made of the problem" pattern match. Written
  from scratch in this repo.
- `atomic_accounting.py` — element depletion analysis
- `governance.py` — governance checker with decision-body modelling
- `power_dynamics.py` — AI directives and power orientation modelling
- `src/` — the whole constraint framework (checker, constraints,
  cascade, simulator, materials, locations, constants, planetary_constants),
  including the WMO State of the Global Climate 2025 Earth Energy
  Imbalance integration
- `test/test_constraints.py` — 49 unit tests (unittest)
- `data/current_state.json`, `data/scenarios.json`
- `examples/check_proposal.py`
- `tools/fix_paste_corruption.py` — maintenance tool

## Files specific to earth-systems-physics (not cloned here)

These exist in the parent framework but not here, and are not planned
for cloning either because they would pull in numpy / the layer framework
or because they lie outside this repo's scope:

- **Physics layer modules (8 files):** `layer_0_electromagnetics`,
  `layer_0b_magnomechanical`, `layer_1_magnetosphere`, `layer_2_ionosphere`,
  `layer_3_atmosphere`, `layer_4_hydrosphere`, `layer_5_lithosphere`,
  `layer_6_biosphere` — all numpy-dependent physics
- **Physical cascade engine:** `cascade_engine.py` — 1078 lines, imports
  numpy and all seven layer modules. This repo has its own `src/cascade.py`
  which is the space-operations coupling engine (thermosphere → debris →
  launch cadence). The two cascades are conceptually parallel but model
  different physical layers and are maintained separately.
- **Magnomechanical modules (11 files):** `banded_crystal_computer`,
  `cavity_optomagnonics`, `cold_climate_crystal`, `confined_magnon_polaron`,
  `crystal_device_gradient`, `device_scaling`, `earth_magnomechanical`,
  `electrostatic_transducer`, `magnon_polaron_hybridization`,
  `magnonic_sublayer`, `multi_channel_coupling` — hardware/device physics,
  out of scope for this framework
- **Other:** `energy_audit.py`, `chattel_slavery_triple_audit.py` (a
  variant of `slavery_system_audit.py`), `test_smoke.py`

Most of these are numpy-dependent or hardware-simulation-oriented and
would not fit cleanly into this repo's pure-stdlib / constraint-framework
scope.

## Keeping them in sync

When editing any of the seven shared files:

1. Make the change here first (or over there — either direction works).
2. After committing, check the canonical version in the other repo for
   drift. The quickest check is:
   ```bash
   curl -sSfL https://raw.githubusercontent.com/JinnZ2/earth-systems-physics/main/FILENAME -o /tmp/esp.py
   diff -u /tmp/esp.py FILENAME
   ```
3. For the three stdlib-swap files, the diff will always show the numpy
   lines — that's expected. Any OTHER differences are drift and should be
   reconciled.
4. For `dollar_energy_metabolism.py`, the local version carries the
   improvements listed above. Any new drift beyond those known deltas is
   worth investigating.

If the paste-corruption pattern hits again when syncing, `tools/fix_paste_corruption.py`
handles all seven corruption symptoms documented in its module docstring.
