# Legacy — the precedence record

**Nothing in this folder is dead. It is superseded, which is not the same thing.**

A claim that was tested and failed is more useful than a claim that was never
tested. A design note whose every item has landed is the reason the current code
looks the way it does. Both are precedent. Deleting them would leave the repo
looking like it had always been right, which is a lie about how it got here.

## The rule

1. When a file is superseded, it moves here — it is **not** deleted and **not**
   rewritten in place.
2. Its entry goes in the ledger below: what it claimed, what replaced it, and
   what the evidence was.
3. When a *claim inside a living file* is falsified, the file is corrected in
   place and the **original wording is quoted in the ledger**, so the correction
   is auditable rather than silent.
4. Precedence carries. A superseded file still governs anything downstream that
   was decided while it was current. If you are re-litigating a decision made
   under an old file, read the old file first.

See [`../METHOD.md`](../METHOD.md) for the loop this folder is the output of.

---

## Ledger

### 1. `Possible-addons.md` — review notes, fully discharged

**Status:** superseded — every item implemented.
**Moved:** 2026-08-14. **Superseded by:** `src/planetary_constants.py`.

A critique of the first constants layer. Each item was acted on; the file is
kept because it is the stated *reason* for the shape of `planetary_constants.py`,
and nothing in that module explains its own motivation.

| Claim in the notes | Where it landed | Verified |
|---|---|---|
| `rare_earth_ceiling_kg_yr` at 35,000 vs 350,000,000 production "will confuse everyone" — rename to communicate intent | `conservation_ceiling_kg_yr` throughout, with an explicit `NAMING CONVENTION` comment at `planetary_constants.py:226` | ✅ |
| One scalar for LEO debris density is "practically meaningless" — split into altitude bands | `ORBITAL` regionalized into `leo_low`, `leo_high`, `meo`, `gto_geo`, each with its own threshold and margin | ✅ |
| Framework gives pass/fail; real world needs distributions. Even `uncertainty_pct: null` placeholders signal honesty | `uncertainty_pct` carried on constraint entries throughout | ✅ |
| Add `schema_version` — "non-negotiable for anything that's going to evolve" | `SCHEMA_VERSION = "1.0.0"` | ✅ |
| Law 4 (geodynamo) should be a "directional risk indicator" so it can be neither weaponized nor dismissed | `GEODYNAMO` documented as a directional risk indicator, not a hard limit | ✅ |
| The 1% hydrogen escape cap is a policy choice, not derived physics — say so | `HYDROGEN_ESCAPE` framed as policy-choice caps; `ceiling_basis: "policy_choice"` distinguishes these from `model_derived` and `derived_from_reserves_and_recycling` | ✅ |
| Black carbon not stratified by injection altitude — flag as a known simplification with a TODO | `# TODO: separate ceilings for polar vs equatorial injection` at `planetary_constants.py:118` | ✅ |

**Caveat that survives the move:** `src/constants.py` was *not* migrated to the
new naming. It still uses `annual_ceiling_kg` and is still the live source for
`MaterialLedger` (`src/materials.py:113`). The two modules use the same 35,000
figure for different quantities — `constants.py` means the space-export cap,
`planetary_constants.py` means the global conservation ceiling (35,000,000).
The rename was never finished. This is an open item, not a closed one.

---

### 2. README quick-start output — falsified by execution

**Status:** claim corrected in place in `README.md` on 2026-08-14. Original
wording preserved here.

The README published a worked example with its expected output. Nobody had run
it. When run against the code as committed, four of the six stated facts were
wrong.

**The original claim:**

```
result.print_report()
# CONSTRAINT VIOLATIONS DETECTED: 5 of 7
# Law 1 (Water Budget): VIOLATED — propellant combustion 47x ceiling
# Law 2 (Atmosphere): VIOLATED — black carbon 12x threshold by year 4
# Law 5 (Debris): VIOLATED — no deorbit plan, Kessler margin exceeded year 7
# Law 6 (Materials): VIOLATED — rare earth consumption 14x threshold
# Law 7 (Thermosphere): VIOLATED — feedback loop activated by year 6
```

**What running it actually produced (before any fix):**

| README claim | Observed | Verdict |
|---|---|---|
| "5 of 7" violations | 4 of 6 — only six laws are evaluated; Law 4 is derived and has no class | ✗ wrong on both numbers |
| Law 1 VIOLATED, "47x ceiling" | VIOLATED, but 2.99e6 / 9.50e5 = **3.1x** | ✗ magnitude wrong |
| Law 2 VIOLATED, "black carbon 12x threshold" | **SAFE, 97.5% margin.** 500 methane launches × 50 kg = 25,000 kg vs a 1,000,000 kg ceiling — 40x *under*, not 12x over | ✗ inverted |
| Law 3 — not mentioned | **VIOLATED** — no deorbit plan | ✗ omitted |
| Law 5 VIOLATED, no deorbit plan | VIOLATED | ✓ |
| Law 6 VIOLATED, "rare earth 14x threshold" | **SAFE, 78.6% margin** despite the proposal declaring 50,000 kg/yr | ✗ — and this one was a code bug, see below |
| Law 7 VIOLATED, feedback loop | VIOLATED | ✓ |

**Search for unknowns — why did Law 6 disagree?**

The README was closer to right than the code was. `rare_earth_kg_per_year` is
documented as a proposal field in three places (`README.md`,
`CLAUDE.md`, and the `check_proposal()` docstring at `src/checker.py:141`) but
`CrustalMaterialThroughput.evaluate()` never read it. It read only
`modules_per_year`, `recycling_rate`, and `material_requirements_kg`. A proposal
declaring 50,000 kg/yr of rare earths — above the 35,000 kg/yr ceiling — was
scored as though it had declared nothing, and reported SAFE.

Law 6 also hardcoded `current_value=0, ceiling_value=0`, so its report line read
`0.00e+00 / 0.00e+00` while every other law printed real numbers. The blank
output is why the disagreement went unnoticed.

**Fixed** in `src/constraints.py`: `DECLARED_MINERAL_FIELDS` maps the documented
shortcut field to its mineral, with precedence `material_requirements_kg` >
shortcut field > module-derived default; recycling still applies; real demand
and ceiling values are now reported. Four regression tests added
(`test/test_constraints.py`, `TestMinerals`).

**Rerun after the fix:** 5 of 6 violations. Law 6 VIOLATED at −42.9%
(50,000 / 35,000 kg/yr). The README now states this measured output.

**What this cost:** the framework's headline example under-reported violations
for as long as the field has been documented. A constraint checker that silently
ignores a declared input is worse than one that rejects it — this is exactly the
failure mode `buffer_sensor_corruption.py` models, occurring inside the
instrument itself.

**Standing lesson:** every published output in this repo is a claim. Run it.

---

### 3. Three copies of the mineral production figures — one disagreed

**Status:** resolved 2026-08-14. `annual_ceiling_kg` retired; cobalt production
corrected against the cited source.

This is the open item entry 1 left behind: the naming rename from
`Possible-addons.md` was never finished, and `src/constants.py` and
`src/planetary_constants.py` were "not unified."

**What was actually wrong — worse than the naming.** Three modules each kept
their own copy of global mineral production:

| | `constants.py` | `constraints.py` | `planetary_constants.py` |
|---|---|---|---|
| rare earths | 350,000,000 | 350,000,000 | 350,000,000 |
| copper | 22,000,000,000 | 22,000,000,000 | 22,000,000,000 |
| lithium | 180,000,000 | 180,000,000 | 180,000,000 |
| **cobalt** | **220,000,000** | **220,000,000** | **190,000,000** |
| gallium | 500,000 | 500,000 | 500,000 |
| indium | 900,000 | 900,000 | 900,000 |

Cobalt disagreed by 16%, in a framework whose entire premise is auditable
numbers. Nothing detected it because nothing compared them.

**Searching for unknowns — which figure was right?**

Neither. Both cite USGS. USGS Mineral Commodity Summaries 2025 (published
January 2025) reports world cobalt mine production for 2024 at approximately
**290,000 metric tons = 290,000,000 kg** — a record high, with Congo (Kinshasa)
at ~76% of production and Indonesia ~10%. The repo's two values were 24% and 34%
low respectively. The disagreement was the visible symptom; both branches being
stale was the actual finding.

Corrected to 290,000,000 kg/yr, carrying `production_source`, `production_year`,
and `production_verified` fields. Consequence: cobalt's Law 6 space-export
ceiling rises from 22,000 to 29,000 kg/yr. Rare earths remain the binding
mineral in every scenario checked, so no published output changed. The direct
USGS PDF was unreachable from this environment (egress blocked); the figure rests
on two independent secondary retrievals of MCS 2025 and should be re-checked
against the primary document when reachable.

**The naming defect.** `annual_ceiling_kg` was:
- **stored**, though it is exactly `production × threshold_fraction`
- **read by nothing** — `materials.py` recomputes from production and fraction
- **named so generically** that the same "35,000" appeared to mean both the
  space-export cap and the global conservation ceiling (35,000,000)

Retired in favour of `space_export_ceiling_kg_yr`, derived on every access.

**The two ceilings, now documented at the top of `MINERALS`:**

| | question it answers | derived from |
|---|---|---|
| `conservation_ceiling_kg_yr` | how much may humanity draw per year, all uses, on a 100+ year reserve horizon? | reserves + recycling rates |
| `space_export_ceiling_kg_yr` | how much of that may a space program take? | `SPACE_EXPORT_THRESHOLD_FRACTION` × current production |

They are numerically unrelated and answer different questions. Conflating them
was the confusion `Possible-addons.md` predicted three years of naming ago.

**Fix.** `planetary_constants.MINERALS` is now the single source of truth.
`constants.MINERAL_DATA` and `CrustalMaterialThroughput.GLOBAL_PRODUCTION` are
built from it via `MINERAL_KEY_ALIASES`; neither stores a production figure.
Accessors (`production_kg_yr`, `space_export_ceiling_kg_yr`, `overshoot_ratio`,
`conservation_ceiling_kg_yr`, `canonical_mineral_key`) resolve either naming
scheme. `compute_margins()` derives `overshoot_factor` rather than reading the
stored ratio.

**Rerun / verification.** 61 tests pass (was 53). `TestConstantsUnification`
was confirmed to work by reintroducing the old cobalt value — it fails, naming
cobalt. That negative test is the point: the guard is only worth having if it
demonstrably fires.

**What this cost:** nothing yet, and that is the uncomfortable part. Cobalt was
never the binding mineral, so a 16% internal contradiction sat in a published
constraint framework without consequence — and therefore without detection. The
next duplicated constant might bind.

**Standing lesson:** a derived value that is stored will eventually disagree
with its own derivation. Derive it, or test that it matches.

**Still open:** the remaining eight `MINERALS` production figures have not been
re-verified against primary sources. Only cobalt carries
`production_verified: True`. The rest should be checked and stamped the same
way — the audit that found cobalt did not clear the others.
