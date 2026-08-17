"""
Transition Pathways — the active steps from the current regime to a conserving one
==================================================================================

`leverage_analysis.py` produces an uncomfortable result: the single most
effective modification available to a space programme is to commit to a deorbit
plan. It resolves a conservation law outright, and it consumes no physical
resource. It is, in the language of that module, a policy switch with an effort
weight of 1.

So why has it not happened?

Because "free" is a statement about thermodynamics, not about institutions. A
commitment that costs nothing in joules can still be unreachable, because
nothing in the surrounding governance or financial system requires it, verifies
it, prices it, or penalizes its absence. The lever exists; the mechanism to pull
it does not.

This module models that mechanism. It holds the governance, financial, and
verification steps that stand between the current regime and one where the
cheap levers are actually taken — with their prerequisites, their incumbent
resistance, and their durability.

WHAT IT COMPUTES
----------------

- **Keystone steps** — the ones that unlock the most downstream. These are where
  effort compounds; everything else is either a prerequisite for them or waits
  on them.
- **The critical path** — the longest unavoidable chain of prerequisites, which
  sets the floor on transition time regardless of budget.
- **Stall points** — high-resistance steps with no alternative route. A single
  contested step that everything routes through is where transitions die.
- **Durability** — whether a step ratchets (stays done), sticks (erodes slowly),
  or decays (reverts without continuous energy). A pathway whose foundation
  decays is not a transition, it is a treadmill.
- **Unlocked levers** — which `leverage_analysis` modifications each step makes
  available, so the institutional work can be priced against the conservation
  it actually buys.

WHAT IT DOES NOT DO
-------------------

It does not predict whether a transition will happen, or how long a specific
jurisdiction will take. The `time_years` and `incumbent_resistance` figures are
stated judgments, not measurements — flagged the same way `EFFORT_WEIGHTS` and
`ceiling_basis: "policy_choice"` are flagged elsewhere in this framework. The
*structure* — what depends on what — is the durable content here. The numbers
are there to be argued with.

Related modules:
  power_dynamics.py                   — why incumbents resist (GOVERNANCE_CONSTRAINTS)
  constraint_accountability_engine.py — reversion energy of accumulated comfort choices
  consequence_velocity.py             — whether the transition outpaces the damage
  buffer_sensor_corruption.py         — why verification steps are load-bearing

stdlib only. No dependencies.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


# =============================================================================
# CLASSIFICATION
# =============================================================================

class Domain(Enum):
    GOVERNANCE = "governance"
    FINANCIAL = "financial"
    VERIFICATION = "verification"
    INDUSTRIAL = "industrial"


class Durability(Enum):
    """What happens to this step if attention moves elsewhere."""
    RATCHET = "ratchet"   # stays done; reversal requires deliberate effort
    STICKY = "sticky"     # erodes slowly; survives inattention for years
    DECAYS = "decays"     # reverts without continuous maintenance energy


# Ordinal, policy choice — not measured. See module docstring.
RESISTANCE_BASIS = "policy_choice"


@dataclass
class TransitionStep:
    """One active step from the current regime toward a conserving one."""
    step_id: str
    name: str
    domain: Domain
    description: str
    actor: str
    prerequisites: List[str] = field(default_factory=list)
    time_years: float = 1.0
    incumbent_resistance: float = 0.5   # [0,1]; who loses, and how hard they fight
    durability: Durability = Durability.STICKY
    unlocks_levers: List[str] = field(default_factory=list)
    notes: str = ""


# =============================================================================
# THE PATHWAY
# =============================================================================
#
# Ordering here is by dependency, not by importance. Read the prerequisites,
# not the sequence in the list.

TRANSITION_STEPS: List[TransitionStep] = [

    # ---- Verification: nothing downstream can be enforced without it --------
    TransitionStep(
        step_id="orbital_registry",
        name="Public orbital object registry",
        domain=Domain.VERIFICATION,
        description="Every object in orbit carries a public record: mass, "
                    "operator, orbit, and declared end-of-life plan.",
        actor="International registry body / national licensing authorities",
        prerequisites=[],
        time_years=3.0,
        incumbent_resistance=0.35,
        durability=Durability.RATCHET,
        notes="Foundational. Attribution is impossible without it, and every "
              "financial instrument downstream needs attribution to price "
              "anything. Low resistance because it threatens no one directly — "
              "which is exactly why it is the place to start.",
    ),
    TransitionStep(
        step_id="independent_tracking",
        name="Independent tracking and verification capability",
        domain=Domain.VERIFICATION,
        description="Measurement capability sufficient to verify deorbit and "
                    "debris claims without relying on the operator's own report.",
        actor="Independent technical body",
        prerequisites=["orbital_registry"],
        time_years=4.0,
        incumbent_resistance=0.45,
        durability=Durability.DECAYS,
        notes="DECAYS: sensor networks degrade without sustained funding, and "
              "a degraded sensor reports comfortable numbers rather than no "
              "numbers. See buffer_sensor_corruption.py — an unfunded verifier "
              "is worse than an absent one, because it still produces output.",
    ),
    TransitionStep(
        step_id="public_margin_disclosure",
        name="Mandatory public margin disclosure",
        domain=Domain.GOVERNANCE,
        description="Constraint margins for every licensed programme are "
                    "published on the same schedule as financial reporting.",
        actor="Licensing authority",
        prerequisites=["orbital_registry"],
        time_years=2.0,
        incumbent_resistance=0.55,
        durability=Durability.STICKY,
        unlocks_levers=["commit_deorbit_plan"],
        notes="Meadows rank 6 — information flow. Cheap, and it changes "
              "behaviour without changing a single physical parameter, because "
              "a published margin is a margin someone can be asked about.",
    ),

    # ---- Governance: the rules that make the cheap levers mandatory ---------
    TransitionStep(
        step_id="liability_attribution",
        name="Legal attribution of debris liability",
        domain=Domain.GOVERNANCE,
        description="Damage caused by a fragment is attributable to the "
                    "operator that placed the parent object in orbit.",
        actor="Treaty body / national legislatures",
        prerequisites=["orbital_registry"],
        time_years=6.0,
        incumbent_resistance=0.80,
        durability=Durability.RATCHET,
        notes="The hinge of the whole pathway. Until damage has an owner, "
              "every downstream financial instrument is unpriceable. Highest "
              "resistance outside the audit body because it converts an "
              "externality into a balance-sheet item.",
    ),
    TransitionStep(
        step_id="licence_requires_check",
        name="Launch licence conditioned on constraint check",
        domain=Domain.GOVERNANCE,
        description="No launch licence issues without a passing constraint "
                    "evaluation, published with the licence.",
        actor="National licensing authority",
        prerequisites=["orbital_registry", "public_margin_disclosure"],
        time_years=4.0,
        incumbent_resistance=0.70,
        durability=Durability.STICKY,
        unlocks_levers=["commit_deorbit_plan", "full_orbital_compliance"],
        notes="Meadows rank 5 — rules. This is the step that converts the "
              "framework from advisory to binding.",
    ),
    TransitionStep(
        step_id="sunset_all_exceptions",
        name="Mandatory sunset clauses on exceptions",
        domain=Domain.GOVERNANCE,
        description="Every constraint exception carries an expiry date, a "
                    "public justification, and a margin recalculation.",
        actor="Licensing authority",
        prerequisites=["licence_requires_check"],
        time_years=2.0,
        incumbent_resistance=0.60,
        durability=Durability.STICKY,
        notes="Without this, the exception process becomes the regime. "
              "power_dynamics.GOVERNANCE_CONSTRAINTS lists the same "
              "requirement for constraint exceptions.",
    ),
    TransitionStep(
        step_id="independent_audit_body",
        name="Independent constraint audit body",
        domain=Domain.GOVERNANCE,
        description="Standing body with tenure limits, mandatory rotation, "
                    "and at least three external feedback channels.",
        actor="Treaty body",
        prerequisites=["licence_requires_check", "independent_tracking"],
        time_years=5.0,
        incumbent_resistance=0.85,
        durability=Durability.DECAYS,
        notes="DECAYS: capture is the default end state of any standing body "
              "without rotation. power_dynamics.py treats sustained power as a "
              "neurotoxic exposure requiring dose limits — the rotation rules "
              "ARE the maintenance energy this step needs.",
    ),

    # ---- Financial: pricing what the rules now attribute --------------------
    TransitionStep(
        step_id="deorbit_bond_escrow",
        name="Deorbit bond held in escrow",
        domain=Domain.FINANCIAL,
        description="Bond posted before launch, sized to end-of-life cost, "
                    "released only on independently verified disposal.",
        actor="Licensing authority + financial custodian",
        prerequisites=["liability_attribution", "independent_tracking"],
        time_years=3.0,
        incumbent_resistance=0.65,
        durability=Durability.RATCHET,
        unlocks_levers=["fund_deorbit_bond", "full_orbital_compliance"],
        notes="Converts a future public cost into a present private one. "
              "Requires verification to release against, which is why "
              "independent_tracking is a prerequisite and not a nicety.",
    ),
    TransitionStep(
        step_id="third_party_insurance",
        name="Mandatory third-party liability insurance",
        domain=Domain.FINANCIAL,
        description="Coverage required for collision and re-entry damage, "
                    "priced on the operator's own constraint margins.",
        actor="Regulator + insurance market",
        prerequisites=["liability_attribution"],
        time_years=3.0,
        incumbent_resistance=0.50,
        durability=Durability.STICKY,
        notes="Once premiums price margin, the insurer becomes a second "
              "enforcement channel that does not depend on regulatory will. "
              "The framework already treats insurance withdrawal as a binding "
              "constraint in its own right.",
    ),
    TransitionStep(
        step_id="reinsurance_backstop",
        name="Public reinsurance backstop",
        domain=Domain.FINANCIAL,
        description="Public backstop for tail risk, conditioned on compliance, "
                    "so the market prices risk instead of exiting it.",
        actor="Treasury / multilateral fund",
        prerequisites=["third_party_insurance"],
        time_years=4.0,
        incumbent_resistance=0.55,
        durability=Durability.DECAYS,
        notes="DECAYS: a backstop is a budget line, and budget lines are "
              "renegotiated. Guards against the failure mode where insurers "
              "withdraw entirely and the activity proceeds uninsured.",
    ),
    TransitionStep(
        step_id="material_passport",
        name="Material passport for orbital hardware",
        domain=Domain.INDUSTRIAL,
        description="Per-component record of critical mineral content, "
                    "origin, and recycled fraction.",
        actor="Manufacturers + standards body",
        prerequisites=["orbital_registry"],
        time_years=4.0,
        incumbent_resistance=0.60,
        durability=Durability.RATCHET,
        notes="Law 6 is unenforceable without it — you cannot cap a draw you "
              "cannot measure. Supply-chain opacity is the binding obstacle, "
              "not metallurgy.",
    ),
    TransitionStep(
        step_id="virgin_material_levy",
        name="Levy on virgin critical minerals, rebated for recycled content",
        domain=Domain.FINANCIAL,
        description="Price differential between virgin and recycled feedstock, "
                    "set to make closed-loop supply the cheaper option.",
        actor="Treasury",
        prerequisites=["material_passport"],
        time_years=3.0,
        incumbent_resistance=0.75,
        durability=Durability.STICKY,
        unlocks_levers=["recycling_50pct", "recycling_95pct", "halve_rare_earth_draw"],
        notes="Meadows rank 12 as a parameter — but it operates on rank 10, "
              "the structure of a material flow, because it changes which "
              "direction the cheapest path runs.",
    ),
    TransitionStep(
        step_id="producer_responsibility",
        name="Extended producer responsibility for orbital hardware",
        domain=Domain.FINANCIAL,
        description="Manufacturers retain end-of-life obligation for what they "
                    "build, not merely the operators who fly it.",
        actor="Legislatures",
        prerequisites=["material_passport", "liability_attribution"],
        time_years=5.0,
        incumbent_resistance=0.80,
        durability=Durability.RATCHET,
        unlocks_levers=["recycling_50pct", "active_debris_removal"],
        notes="Moves the design incentive upstream. Recyclability becomes a "
              "manufacturing requirement rather than an operator problem.",
    ),

    # ---- Industrial: capability that the financial steps create demand for --
    TransitionStep(
        step_id="adr_service_market",
        name="Active debris removal service market",
        domain=Domain.INDUSTRIAL,
        description="Commercial removal services purchasable at known price.",
        actor="Commercial providers",
        prerequisites=["deorbit_bond_escrow"],
        time_years=6.0,
        incumbent_resistance=0.25,
        durability=Durability.STICKY,
        unlocks_levers=["active_debris_removal", "full_orbital_compliance"],
        notes="Lowest resistance in the pathway — this one creates a market "
              "rather than constraining one. It cannot lead, though: without "
              "the bond there is no funded demand to sell into.",
    ),
]


# =============================================================================
# ANALYSIS
# =============================================================================

class TransitionPlanner:
    """Dependency analysis over a set of transition steps."""

    def __init__(self, steps: Optional[List[TransitionStep]] = None):
        self.steps = steps if steps is not None else list(TRANSITION_STEPS)
        self.by_id: Dict[str, TransitionStep] = {s.step_id: s for s in self.steps}
        self._validate()

    def _validate(self):
        for s in self.steps:
            for p in s.prerequisites:
                if p not in self.by_id:
                    raise ValueError(
                        f"Step {s.step_id!r} requires unknown step {p!r}"
                    )
        self.topological_order()  # raises on cycle

    def topological_order(self) -> List[TransitionStep]:
        """Dependency order. Raises ValueError on a prerequisite cycle."""
        visited: Dict[str, int] = {}
        order: List[TransitionStep] = []

        def visit(sid: str, stack: List[str]):
            state = visited.get(sid, 0)
            if state == 1:
                cycle = " → ".join(stack + [sid])
                raise ValueError(f"Prerequisite cycle: {cycle}")
            if state == 2:
                return
            visited[sid] = 1
            for p in self.by_id[sid].prerequisites:
                visit(p, stack + [sid])
            visited[sid] = 2
            order.append(self.by_id[sid])

        for s in self.steps:
            visit(s.step_id, [])
        return order

    def dependents(self, step_id: str) -> Set[str]:
        """Every step that transitively requires this one."""
        out: Set[str] = set()
        frontier = [step_id]
        while frontier:
            current = frontier.pop()
            for s in self.steps:
                if current in s.prerequisites and s.step_id not in out:
                    out.add(s.step_id)
                    frontier.append(s.step_id)
        return out

    def prerequisites_of(self, step_id: str) -> Set[str]:
        """Every step this one transitively requires."""
        out: Set[str] = set()
        frontier = list(self.by_id[step_id].prerequisites)
        while frontier:
            current = frontier.pop()
            if current in out:
                continue
            out.add(current)
            frontier.extend(self.by_id[current].prerequisites)
        return out

    def keystones(self) -> List[tuple]:
        """Steps ranked by how much they unlock downstream."""
        scored = [(s, len(self.dependents(s.step_id))) for s in self.steps]
        scored.sort(key=lambda t: (-t[1], t[0].time_years))
        return scored

    def earliest_start(self, step_id: str) -> float:
        """Years until this step can begin, assuming unlimited parallelism."""
        prereqs = self.by_id[step_id].prerequisites
        if not prereqs:
            return 0.0
        return max(
            self.earliest_start(p) + self.by_id[p].time_years for p in prereqs
        )

    def completion_time(self, step_id: str) -> float:
        return self.earliest_start(step_id) + self.by_id[step_id].time_years

    def critical_path(self) -> tuple:
        """The longest unavoidable chain. Returns (steps, total_years)."""
        terminal = max(self.steps, key=lambda s: self.completion_time(s.step_id))

        chain: List[TransitionStep] = []
        current: Optional[TransitionStep] = terminal
        while current is not None:
            chain.append(current)
            if not current.prerequisites:
                break
            current = max(
                (self.by_id[p] for p in current.prerequisites),
                key=lambda s: self.completion_time(s.step_id),
            )
        chain.reverse()
        return chain, self.completion_time(terminal.step_id)

    def stall_points(self, resistance_threshold: float = 0.6) -> List[tuple]:
        """High-resistance steps that a lot of the pathway routes through.

        A contested step with many dependents and no alternative route is where
        a transition stalls — not because it is hard, but because stopping it
        stops everything behind it.
        """
        risky = []
        for s in self.steps:
            if s.incumbent_resistance < resistance_threshold:
                continue
            blocked = len(self.dependents(s.step_id))
            if blocked == 0:
                continue
            risky.append((s, blocked, s.incumbent_resistance * blocked))
        risky.sort(key=lambda t: -t[2])
        return risky

    def decaying_foundations(self) -> List[TransitionStep]:
        """DECAYS steps that other steps depend on.

        A pathway resting on a step that reverts without maintenance is not a
        transition — it is a treadmill, and it will be reported as complete
        right up until it isn't.
        """
        return [
            s for s in self.steps
            if s.durability == Durability.DECAYS and self.dependents(s.step_id)
        ]

    def steps_to_unlock(self, lever_name: str) -> Optional[List[TransitionStep]]:
        """The cheapest-by-time chain that makes a leverage lever available."""
        providers = [s for s in self.steps if lever_name in s.unlocks_levers]
        if not providers:
            return None
        best = min(providers, key=lambda s: self.completion_time(s.step_id))
        needed = self.prerequisites_of(best.step_id) | {best.step_id}
        chain = [s for s in self.topological_order() if s.step_id in needed]
        return chain


# =============================================================================
# REPORTING
# =============================================================================

def print_transition_report(planner: Optional[TransitionPlanner] = None):
    planner = planner or TransitionPlanner()

    print("=" * 78)
    print("TRANSITION PATHWAYS — current regime → conserving regime")
    print("=" * 78)
    print(f"\n  {len(planner.steps)} steps. Resistance and duration are stated")
    print(f"  judgments (basis: {RESISTANCE_BASIS}), not measurements.")
    print("  The dependency structure is the durable content.\n")

    print("  DEPENDENCY ORDER")
    print("  " + "-" * 74)
    print(f"  {'step':<26} {'domain':<14} {'start':>6} {'done':>6} "
          f"{'resist':>7} {'durability':>10}")
    print("  " + "-" * 74)
    for s in planner.topological_order():
        print(f"  {s.step_id:<26} {s.domain.value:<14} "
              f"{planner.earliest_start(s.step_id):>5.0f}y "
              f"{planner.completion_time(s.step_id):>5.0f}y "
              f"{s.incumbent_resistance:>7.2f} {s.durability.value:>10}")

    print("\n  KEYSTONE STEPS — what unlocks the most")
    print("  " + "-" * 74)
    for s, unlocked in planner.keystones()[:5]:
        if unlocked == 0:
            continue
        print(f"  {s.step_id:<26} unlocks {unlocked:>2} downstream step(s), "
              f"resistance {s.incumbent_resistance:.2f}")
    print("\n    The first entry is where effort compounds. Everything else is")
    print("    either a prerequisite for it or waiting behind it.")

    chain, total = planner.critical_path()
    print(f"\n  CRITICAL PATH — {total:.0f} years, {len(chain)} steps")
    print("  " + "-" * 74)
    print("    " + "\n      → ".join(s.step_id for s in chain))
    print(f"\n    This is the floor on transition time with unlimited budget and")
    print(f"    no political friction. Adding money does not shorten it; only")
    print(f"    removing a prerequisite does.")

    print("\n  STALL POINTS — contested steps that everything routes through")
    print("  " + "-" * 74)
    for s, blocked, score in planner.stall_points()[:4]:
        print(f"  {s.step_id:<26} resistance {s.incumbent_resistance:.2f} × "
              f"{blocked} blocked = {score:.1f}")
        print(f"    {s.actor}")
    print("\n    Stopping one of these stops everything behind it. These are")
    print("    where a transition dies quietly, reported as 'under review'.")

    decaying = planner.decaying_foundations()
    print("\n  DECAYING FOUNDATIONS — steps others depend on that revert")
    print("  " + "-" * 74)
    for s in decaying:
        print(f"  {s.step_id:<26} {len(planner.dependents(s.step_id))} "
              f"step(s) depend on this")
    if not decaying:
        print("  (none)")
    print("\n    These need continuous maintenance energy. A pathway resting on")
    print("    them will be reported complete long after it has stopped working.")

    print("\n  WHAT UNLOCKS THE CHEAPEST CONSERVATION LEVERS")
    print("  " + "-" * 74)
    for lever in ("commit_deorbit_plan", "fund_deorbit_bond",
                  "active_debris_removal", "recycling_50pct"):
        chain = planner.steps_to_unlock(lever)
        if not chain:
            print(f"  {lever:<24} — no step in this pathway unlocks it")
            continue
        years = max(planner.completion_time(s.step_id) for s in chain)
        print(f"  {lever:<24} {len(chain)} step(s), {years:.0f}y: "
              f"{' → '.join(s.step_id for s in chain)}")

    print("\n    leverage_analysis.py rates commit_deorbit_plan as the single")
    print("    most effective modification available, at effort weight 1. The")
    print("    line above is what it actually costs to make that lever")
    print("    reachable. 'Free' was a claim about joules, not institutions.")
    print("=" * 78)


def _demo():
    print_transition_report()


if __name__ == "__main__":
    _demo()
