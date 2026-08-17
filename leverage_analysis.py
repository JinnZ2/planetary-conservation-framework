"""
Leverage Analysis — which small modifications buy the most conservation
=======================================================================

The framework as built answers one question: "does this proposal violate the
conservation laws?" It answers it well and it answers it with a number. But a
checker that only ever says *no* leaves the most useful question unasked:

    Of all the changes available, which smallest one buys the most margin?

This module answers that. It takes a proposal, applies each candidate
modification independently, re-runs the six conservation laws, and ranks the
modifications by margin gained per unit of effort spent.

WHY THE RANKING IS THE POINT
----------------------------

Donella Meadows' observation about leverage points is that people intuitively
reach for the weakest ones. Parameters — subsidy levels, launch counts, quotas —
are the most obvious place to push and the least effective. Rules, information
flows, and goals sit far higher on the leverage ladder and are pushed far less
often, because pushing them requires a decision rather than a budget.

This module tests that claim inside this framework rather than asserting it.
Each lever carries a Meadows rank alongside its measured effect, so the two can
be read against each other. See the demo output: the levers that resolve the
most violations are not the ones that consume the most resources.

EFFORT WEIGHTS ARE A POLICY CHOICE
----------------------------------

"Margin per unit effort" requires a cost model, and there isn't a physical one —
the cost of flipping a regulation is not measured in joules. The weights in
`EFFORT_WEIGHTS` are ordinal judgments, flagged as such in the same way
`planetary_constants.py` flags `ceiling_basis: "policy_choice"`. Change them and
the ranking changes. They are arguable, and they are meant to be argued with;
what is not arguable is the measured margin delta, which comes from the same
constraint code the checker uses.

stdlib only. No dependencies.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import sys
import os
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.constraints import evaluate_all, ConstraintStatus


# =============================================================================
# EFFORT MODEL — ordinal, policy choice, not derived
# =============================================================================

class EffortClass(Enum):
    """What kind of thing has to happen for this modification to occur."""
    POLICY_SWITCH = "policy_switch"   # a decision; consumes no physical resource
    OPERATIONAL = "operational"       # run existing hardware differently
    CAPITAL = "capital"               # build or buy something new
    TECHNOLOGY = "technology"         # requires capability not yet at scale


# Ordinal effort weights. NOT derived from physics or cost data — these are
# stated judgments about relative difficulty, held here so they can be
# challenged in one place instead of being buried in a ranking function.
#
# basis: policy_choice
EFFORT_WEIGHTS = {
    EffortClass.POLICY_SWITCH: 1.0,
    EffortClass.OPERATIONAL: 3.0,
    EffortClass.CAPITAL: 10.0,
    EffortClass.TECHNOLOGY: 30.0,
}

EFFORT_WEIGHT_BASIS = "policy_choice"


# =============================================================================
# MEADOWS LEVERAGE LADDER
# =============================================================================
#
# Meadows' canonical numbering runs 12 (weakest) to 1 (strongest). It is kept
# in her original direction here rather than inverted, so the numbers mean what
# they mean in the literature. Lower rank = higher leverage.

MEADOWS_LEVELS = {
    12: "Constants, parameters, numbers (subsidies, taxes, standards)",
    11: "Size of buffers and other stabilizing stocks",
    10: "Structure of material stocks and flows",
    9: "Length of delays relative to rate of system change",
    8: "Strength of negative feedback loops",
    7: "Gain around driving positive feedback loops",
    6: "Structure of information flows (who does/doesn't have access)",
    5: "Rules of the system (incentives, punishments, constraints)",
    4: "Power to add, change, evolve or self-organize system structure",
    3: "Goals of the system",
    2: "Mindset or paradigm out of which the system arises",
    1: "Power to transcend paradigms",
}


# =============================================================================
# LEVERS
# =============================================================================

@dataclass
class Lever:
    """A single candidate modification to a proposal.

    `apply` receives a deep copy of the proposal and mutates it in place.
    """
    name: str
    description: str
    effort: EffortClass
    meadows_rank: int
    apply: Callable[[dict], None]
    reversible: bool = True
    notes: str = ""

    @property
    def effort_weight(self) -> float:
        return EFFORT_WEIGHTS[self.effort]

    @property
    def meadows_label(self) -> str:
        return MEADOWS_LEVELS[self.meadows_rank]


def _set(field_name: str, value):
    def _apply(p: dict):
        p[field_name] = value
    return _apply


def _scale(field_name: str, factor: float, default=0):
    def _apply(p: dict):
        p[field_name] = p.get(field_name, default) * factor
    return _apply


def _switch_propellant(new_type: str):
    """Switch propellant type, dropping any explicit per-launch mass override.

    Switching propellant means switching vehicle, so the per-launch propellant
    mass moves to the new type's default rather than carrying the old vehicle's
    figure across. Callers who want to hold mass fixed should set
    `propellant_per_launch_kg` again after applying.
    """
    def _apply(p: dict):
        p["propellant_type"] = new_type
        p.pop("propellant_per_launch_kg", None)
    return _apply


def _apply_all(*appliers):
    def _apply(p: dict):
        for a in appliers:
            a(p)
    return _apply


# The standard lever set. Each entry is a modification a real programme could
# actually make; nothing here is hypothetical technology except where the
# effort class says TECHNOLOGY.
STANDARD_LEVERS: List[Lever] = [
    Lever(
        name="commit_deorbit_plan",
        description="Adopt a mandatory deorbit/recovery plan",
        effort=EffortClass.POLICY_SWITCH,
        meadows_rank=5,
        apply=_set("deorbit_plan", True),
        notes="Laws 3 and 5 both gate on this flag. No physical resource "
              "is consumed by the commitment itself.",
    ),
    Lever(
        name="fund_deorbit_bond",
        description="Fund a deorbit bond held in escrow",
        effort=EffortClass.POLICY_SWITCH,
        meadows_rank=5,
        apply=_set("deorbit_bond_funded", True),
        notes="Financial instrument. Moves the cost of end-of-life from the "
              "commons to the operator's balance sheet.",
    ),
    Lever(
        name="active_debris_removal",
        description="Operate active debris removal for net reduction",
        effort=EffortClass.CAPITAL,
        meadows_rank=10,
        apply=_set("active_debris_removal", True),
        notes="Requires hardware. Changes the direction of a material flow.",
    ),
    Lever(
        name="full_orbital_compliance",
        description="All three orbital commitments together "
                    "(deorbit plan + bond + active removal)",
        effort=EffortClass.CAPITAL,
        meadows_rank=5,
        apply=_apply_all(
            _set("deorbit_plan", True),
            _set("deorbit_bond_funded", True),
            _set("active_debris_removal", True),
        ),
        notes="Law 5 clamps to zero margin unless ALL THREE are present. "
              "Partial compliance buys nothing on that law.",
    ),
    Lever(
        name="recycling_50pct",
        description="Reach 50% in-orbit/returned material recycling",
        effort=EffortClass.OPERATIONAL,
        meadows_rank=10,
        apply=_set("recycling_rate", 0.5),
    ),
    Lever(
        name="recycling_95pct",
        description="Reach 95% closed-loop material recycling",
        effort=EffortClass.TECHNOLOGY,
        meadows_rank=10,
        apply=_set("recycling_rate", 0.95),
        notes="Not demonstrated at scale for orbital hardware.",
    ),
    Lever(
        name="propellant_to_hydrogen",
        description="Switch propellant to hydrogen/LOX",
        effort=EffortClass.TECHNOLOGY,
        meadows_rank=10,
        apply=_switch_propellant("hydrogen_lox"),
        notes="Eliminates black carbon entirely. Does NOT help the water "
              "budget — see demo output.",
    ),
    Lever(
        name="propellant_to_electric",
        description="Switch to electric/electromagnetic launch",
        effort=EffortClass.TECHNOLOGY,
        meadows_rank=10,
        apply=_switch_propellant("electric"),
        notes="No combustion products at all. Not available for heavy lift.",
    ),
    Lever(
        name="halve_launch_cadence",
        description="Halve launches per year",
        effort=EffortClass.OPERATIONAL,
        meadows_rank=12,
        apply=_scale("launches_per_year", 0.5),
        notes="The classic parameter push — most obvious, least leveraged.",
    ),
    Lever(
        name="halve_orbital_mass",
        description="Halve total mass placed in orbit",
        effort=EffortClass.OPERATIONAL,
        meadows_rank=12,
        apply=_scale("orbital_mass_kg", 0.5),
    ),
    Lever(
        name="halve_rare_earth_draw",
        description="Halve declared rare earth demand",
        effort=EffortClass.OPERATIONAL,
        meadows_rank=12,
        apply=_scale("rare_earth_kg_per_year", 0.5),
    ),
    Lever(
        name="halve_module_rate",
        description="Halve modules deployed per year",
        effort=EffortClass.OPERATIONAL,
        meadows_rank=12,
        apply=_scale("modules_per_year", 0.5, default=1),
    ),
]


# =============================================================================
# ANALYSIS
# =============================================================================

@dataclass
class LawDelta:
    law_number: int
    name: str
    margin_before: float
    margin_after: float
    status_before: ConstraintStatus
    status_after: ConstraintStatus

    @property
    def delta(self) -> float:
        return self.margin_after - self.margin_before

    @property
    def resolved(self) -> bool:
        return (self.status_before == ConstraintStatus.VIOLATED
                and self.status_after != ConstraintStatus.VIOLATED)

    @property
    def broken(self) -> bool:
        return (self.status_before != ConstraintStatus.VIOLATED
                and self.status_after == ConstraintStatus.VIOLATED)


@dataclass
class LeverageResult:
    lever: Lever
    law_deltas: List[LawDelta]
    violations_before: int
    violations_after: int
    binding_margin_before: float
    binding_margin_after: float

    @property
    def violations_resolved(self) -> int:
        return sum(1 for d in self.law_deltas if d.resolved)

    @property
    def violations_created(self) -> int:
        return sum(1 for d in self.law_deltas if d.broken)

    @property
    def binding_margin_gain(self) -> float:
        return self.binding_margin_after - self.binding_margin_before

    @property
    def laws_improved(self) -> List[int]:
        return [d.law_number for d in self.law_deltas if d.delta > 1e-9]

    @property
    def leverage_score(self) -> float:
        """Conservation bought per unit of effort spent.

        A resolved violation is worth far more than margin on a law that was
        already passing — the laws are constraints, not a score to maximize.
        Weighted accordingly, then divided by the (policy-choice) effort weight.
        """
        net_resolved = self.violations_resolved - self.violations_created
        # Binding-margin gain is capped so a single enormous percentage swing
        # (Law 7 runs to -1900%) cannot dominate the ranking, and is weighted
        # far below an actual resolution: the laws are pass/fail constraints,
        # not a score to maximize. Moving -1900% to -900% is not progress
        # toward compliance, it is a smaller violation.
        capped_gain = max(-100.0, min(100.0, self.binding_margin_gain))
        raw = (net_resolved * 1000.0) + capped_gain
        return raw / self.lever.effort_weight


class LeverageAnalyzer:
    """Rank candidate modifications to a proposal by conservation bought."""

    def __init__(self, levers: Optional[List[Lever]] = None):
        self.levers = levers if levers is not None else list(STANDARD_LEVERS)

    @staticmethod
    def _evaluate(proposal: dict):
        return evaluate_all(proposal)

    @staticmethod
    def _violations(results) -> int:
        return sum(1 for r in results if r.status == ConstraintStatus.VIOLATED)

    @staticmethod
    def _binding_margin(results) -> float:
        return min(r.margin_remaining_pct for r in results)

    def analyze_lever(self, proposal: dict, lever: Lever) -> LeverageResult:
        base = self._evaluate(proposal)

        modified = deepcopy(proposal)
        lever.apply(modified)
        after = self._evaluate(modified)

        by_law = {r.law_number: r for r in after}
        deltas = [
            LawDelta(
                law_number=b.law_number,
                name=b.name,
                margin_before=b.margin_remaining_pct,
                margin_after=by_law[b.law_number].margin_remaining_pct,
                status_before=b.status,
                status_after=by_law[b.law_number].status,
            )
            for b in base
        ]

        return LeverageResult(
            lever=lever,
            law_deltas=deltas,
            violations_before=self._violations(base),
            violations_after=self._violations(after),
            binding_margin_before=self._binding_margin(base),
            binding_margin_after=self._binding_margin(after),
        )

    def rank(self, proposal: dict) -> List[LeverageResult]:
        """All levers, ranked by leverage score, best first."""
        results = [self.analyze_lever(proposal, l) for l in self.levers]
        results.sort(key=lambda r: r.leverage_score, reverse=True)
        return results

    def minimum_viable_set(
        self, proposal: dict, max_size: int = 4
    ) -> Optional[List[Lever]]:
        """Smallest combination of levers that clears every violation.

        Exhaustive over combinations up to `max_size`, cheapest-effort first
        within each size. Returns None if no combination that small suffices —
        which is itself a finding, not a failure.
        """
        from itertools import combinations

        # Every lever is a candidate, including composite ones: adopting a
        # bundle of commitments is a single decision, and excluding it here
        # made reachable proposals look unreachable.
        candidates = list(self.levers)

        for size in range(1, max_size + 1):
            best: Optional[List[Lever]] = None
            best_effort = float("inf")
            for combo in combinations(candidates, size):
                modified = deepcopy(proposal)
                for lever in combo:
                    lever.apply(modified)
                if self._violations(self._evaluate(modified)) == 0:
                    effort = sum(l.effort_weight for l in combo)
                    if effort < best_effort:
                        best_effort = effort
                        best = list(combo)
            if best:
                return best
        return None


# =============================================================================
# REPORTING
# =============================================================================

def print_leverage_report(proposal: dict, analyzer: Optional[LeverageAnalyzer] = None):
    analyzer = analyzer or LeverageAnalyzer()
    base = evaluate_all(proposal)
    violations = [r for r in base if r.status == ConstraintStatus.VIOLATED]

    print("=" * 78)
    print(f"LEVERAGE ANALYSIS: {proposal.get('name', 'Unnamed Proposal')}")
    print("=" * 78)
    print(f"\n  Baseline: {len(violations)} of {len(base)} laws violated")
    print(f"  Binding margin: {min(r.margin_remaining_pct for r in base):.1f}%")
    print(f"\n  Effort weights are a policy choice (basis: {EFFORT_WEIGHT_BASIS}).")
    print("  Meadows rank: 12 = weakest leverage, 1 = strongest.\n")

    results = analyzer.rank(proposal)

    print(f"  {'modification':<28} {'effort':<14} {'Mdw':>4} "
          f"{'fixed':>6} {'broke':>6} {'score':>8}")
    print("  " + "-" * 74)
    for r in results:
        print(f"  {r.lever.name:<28} {r.lever.effort.value:<14} "
              f"{r.lever.meadows_rank:>4} {r.violations_resolved:>6} "
              f"{r.violations_created:>6} {r.leverage_score:>8.1f}")

    print("\n  " + "-" * 74)
    print("  TOP MODIFICATIONS IN DETAIL\n")
    for r in results[:3]:
        if r.violations_resolved == 0 and r.binding_margin_gain <= 0:
            continue
        print(f"  ▸ {r.lever.name} — {r.lever.description}")
        print(f"      effort: {r.lever.effort.value} "
              f"(weight {r.lever.effort_weight:.0f})")
        print(f"      Meadows {r.lever.meadows_rank}: {r.lever.meadows_label}")
        print(f"      violations {r.violations_before} → {r.violations_after}")
        for d in r.law_deltas:
            if abs(d.delta) > 1e-9:
                flag = "  <- RESOLVED" if d.resolved else ("  <- BROKE" if d.broken else "")
                print(f"        Law {d.law_number}: {d.margin_before:>9.1f}% → "
                      f"{d.margin_after:>9.1f}%{flag}")
        if r.lever.notes:
            print(f"      note: {r.lever.notes}")
        print()

    minimal = analyzer.minimum_viable_set(proposal)
    print("  " + "-" * 74)
    if minimal:
        total_effort = sum(l.effort_weight for l in minimal)
        print(f"  MINIMUM VIABLE SET — {len(minimal)} modification(s), "
              f"total effort {total_effort:.0f}:")
        for l in minimal:
            print(f"    • {l.name} ({l.effort.value}, Meadows {l.meadows_rank})")
        print("\n  This clears every violation. Nothing smaller does.")
    else:
        print("  NO COMBINATION of up to 4 modifications clears every violation.")
        print("  The proposal is not reachable by small changes — it needs to be")
        print("  smaller, not merely better managed.")
    print("=" * 78)

    return results


# =============================================================================
# DEMO
# =============================================================================

def _demo():
    # The README's worked example: 500 launches/yr, no deorbit plan, no recycling.
    aggressive = {
        "name": "Orbital Data Center Phase 1",
        "launches_per_year": 500,
        "payload_mass_kg": 100_000,
        "propellant_type": "methane_lox",
        "orbital_mass_kg": 5_000_000,
        "duration_years": 10,
        "rare_earth_kg_per_year": 50_000,
        "modules_per_year": 1,
        "deorbit_plan": False,
        "recycling_rate": 0.0,
    }
    print_leverage_report(aggressive)

    print("\n\n")

    # A smaller programme, to show the ranking is proposal-dependent.
    modest = {
        "name": "Modest Research Constellation",
        "launches_per_year": 40,
        "payload_mass_kg": 20_000,
        "propellant_type": "kerosene_lox",
        "orbital_mass_kg": 400_000,
        "duration_years": 10,
        "modules_per_year": 1,
        "deorbit_plan": False,
        "recycling_rate": 0.0,
    }
    print_leverage_report(modest)


if __name__ == "__main__":
    _demo()
