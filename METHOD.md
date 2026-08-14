# Method

How claims enter, change, and leave this repo.

This is a constraint framework. Its only value is that its numbers are checkable
and its history is honest. A framework that quietly edits its own past to look
consistent has the same defect it exists to detect — see
`buffer_sensor_corruption.py`, which models institutions whose sensors optimize
for comfort over accuracy. The rules below exist so this repo cannot become that.

## The loop

```
    hypothesize ──▶ run ──▶ compare
         ▲                     │
         │                     ├── matches ──▶ record that it was checked, and when
         │                     │
         │                     └── falsified ─▶ edit the claim
         │                                          │
         │                                          ▼
         └────── rerun ◀── search for unknowns ◀────┘
```

**1. Hypothesize.** State the claim so it can fail. "Rare earth demand exceeds
the ceiling" is a hypothesis. "This is concerning" is not. Every published
number, every example output, every margin in `data/current_state.json` is a
hypothesis in this sense.

**2. Run.** Execute it. Not "reason about whether it would pass" — run it and
capture the output.

**3. Compare.** Against the claim as written, not against a charitable
reinterpretation of what the claim probably meant.

**4. If falsified, edit the claim.** Correct the file in place, and quote the
original wording in `legacy/README.md`. The correction must be auditable. A
silent fix destroys the only evidence that the check happened.

**5. Search for unknowns.** A falsified claim is a signal, not a typo. Ask why
the gap existed and how long it survived. The README's Law 6 error was not a bad
sentence — it was a documented input field that no code ever read. The wrong
sentence was the visible end of a real defect. Fix the defect, not the sentence.

**6. Rerun.** Confirm the corrected claim against the corrected code. Record the
measured output, not the expected one.

## Precedence

**Superseded is not deleted.** When a file stops being current it moves to
`legacy/` with a ledger entry, and it keeps its authority over decisions made
while it was current. If you are reopening a question that was settled under an
older file, read that file first — it usually contains the reasoning that the
replacement omits.

`legacy/Possible-addons.md` is the worked example: every item in it landed in
`src/planetary_constants.py`, and nothing in that module explains why it is
shaped the way it is. The superseded file is the only surviving rationale.

## What counts as legacy

Move a file to `legacy/` when **all** of these hold:

- Something else now does its job, and you can name that thing.
- Nothing imports it. (`grep -rn "import <name>" --include=*.py .`)
- You can write its ledger entry — claim, replacement, evidence. If you cannot
  state what falsified or superseded it, you have not established that it did.

Do **not** move a file just because it is small, old, unpolished, or
unreferenced by the docs. Unique working capability is not legacy. `governance.py`
was assessed against these criteria on 2026-08-14 and **stayed**: its
decision-body model (2 leaders / 2 wise / tie-breaker) has no counterpart in
`power_dynamics.py`, which covers tenure, rotation, feedback channels, and
power-orientation screening but never body composition. It was under-integrated,
not superseded — so it was fixed (its module-level demo now sits behind an
`if __name__ == "__main__":` guard) rather than retired.

Files shared with
[`earth-systems-physics`](https://github.com/JinnZ2/earth-systems-physics) —
listed in `RELATED.md` — are not moved unilaterally, because moving one here
creates drift there. Reconcile across both repos first.

## Standing checks

Before publishing any output in a README, docstring, or example:

```bash
python -m unittest discover -s test -p "test_*.py"   # 53 tests
python -m examples.check_proposal                     # all six demos
```

Run the snippet you are about to publish, and paste what it printed. Do not
paste what it should print.
