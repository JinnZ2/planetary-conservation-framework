"""
Decision-point constraint checker.

Takes a proposed action and returns which constraints it violates,
by how much, on what timeline, and what cascade effects follow.

Logs every query for accountability.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json

from .constraints import (
    evaluate_all, ConstraintResult, ConstraintStatus,
    ALL_CONSTRAINTS
)
from .cascade import CascadeEngine


@dataclass
class ProposalReport:
    """Complete evaluation report for a proposed action."""
    proposal_name: str
    proposal_params: dict
    timestamp: str
    constraint_results: List[ConstraintResult]
    cascade_effects: List[Dict]
    violations: List[ConstraintResult]
    viable: bool
    binding_constraint: Optional[str]
    summary: str

    def to_dict(self) -> dict:
        return {
            "proposal_name": self.proposal_name,
            "proposal_params": self.proposal_params,
            "timestamp": self.timestamp,
            "viable": self.viable,
            "binding_constraint": self.binding_constraint,
            "summary": self.summary,
            "violations_count": len(self.violations),
            "constraints": [r.to_dict() for r in self.constraint_results],
            "cascade_effects_count": len(self.cascade_effects)
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def print_report(self):
        print(f"\n{'='*70}")
        print(f"PLANETARY CONSERVATION FRAMEWORK — CONSTRAINT CHECK")
        print(f"{'='*70}")
        print(f"Proposal: {self.proposal_name}")
        print(f"Timestamp: {self.timestamp}")
        print(f"{'='*70}")

        if self.viable:
            print(f"\n  ✓ VIABLE — All constraints satisfied")
        else:
            print(f"\n  ✗ CONSTRAINT VIOLATIONS DETECTED: "
                  f"{len(self.violations)} of {len(self.constraint_results)}")

        print(f"\n{'─'*70}")
        for r in self.constraint_results:
            status_sym = {
                ConstraintStatus.SAFE: "✓",
                ConstraintStatus.CAUTION: "⚠",
                ConstraintStatus.WARNING: "▲",
                ConstraintStatus.CRITICAL: "▼",
                ConstraintStatus.VIOLATED: "✗",
                ConstraintStatus.UNKNOWN: "?"
            }
            sym = status_sym.get(r.status, "?")
            print(f"\n  {sym} Law {r.law_number} ({r.name}): {r.status.value}")
            print(f"    Margin: {r.margin_remaining_pct:.1f}%")
            print(f"    Value: {r.current_value:.2e} / {r.ceiling_value:.2e} {r.unit}")
            if r.time_to_binding_years:
                print(f"    Time to binding: {r.time_to_binding_years:.1f} years")
            print(f"    Mechanism: {r.mechanism[:100]}")
            if r.notes:
                print(f"    Notes: {r.notes}")
            if r.cascade_triggers:
                print(f"    Cascade triggers: {', '.join(r.cascade_triggers)}")

        if self.cascade_effects:
            print(f"\n{'─'*70}")
            print(f"  ACTIVE CASCADE PATHS: {len(self.cascade_effects)}")
            for i, ce in enumerate(self.cascade_effects[:10]):
                chain = " → ".join(
                    [ce["path"][0]["from"]] + [s["to"] for s in ce["path"]]
                )
                print(f"    [{i+1}] {chain} "
                      f"(strength: {ce['total_strength']:.3f}, "
                      f"timescale: {ce['total_timescale']:.1f}yr)")

        print(f"\n{'='*70}")
        print(f"SUMMARY: {self.summary}")
        print(f"{'='*70}\n")


class ConstraintChecker:
    """
    Main interface for evaluating proposals against planetary constraints.

    Usage:
        checker = ConstraintChecker()
        result = checker.check_proposal({...})
        result.print_report()
    """

    def __init__(self, log_file: str = "constraint_checks.jsonl"):
        self.cascade_engine = CascadeEngine()
        self.log_file = log_file

    def check_proposal(self, proposal: dict) -> ProposalReport:
        """
        Evaluate a proposal against all conservation laws.

        Required proposal fields:
            name: str — proposal identifier
            launches_per_year: int
            propellant_type: str — "methane_lox", "hydrogen_lox", "kerosene_lox",
                                   "solid", "electric", "electromagnetic"
            orbital_mass_kg: float — total mass to be placed in orbit
            duration_years: int

        Optional fields:
            payload_mass_kg: float — per launch
            propellant_per_launch_kg: float
            deorbit_plan: bool
            deorbit_timeline_years: int
            active_debris_removal: bool
            deorbit_bond_funded: bool
            recycling_rate: float (0.0-1.0)
            modules_per_year: int
            rare_earth_kg_per_year: float
            material_requirements_kg: dict
        """
        timestamp = datetime.utcnow().isoformat()
        name = proposal.get("name", "Unnamed Proposal")

        # Evaluate all constraints
        results = evaluate_all(proposal)

        # Identify violations
        violations = [r for r in results
                      if r.status in (ConstraintStatus.VIOLATED,
                                      ConstraintStatus.CRITICAL)]

        viable = len([r for r in results
                      if r.status == ConstraintStatus.VIOLATED]) == 0

        # Find binding constraint (lowest margin)
        binding = min(results, key=lambda r: r.margin_remaining_pct)

        # Trace cascade effects from violated subsystems
        cascade_effects = []
        subsystem_map = {
            1: "water_budget",
            2: "atmosphere",
            3: "angular_momentum",
            5: "debris",
            6: "minerals",
            7: "thermosphere"
        }
        for v in violations:
            subsystem = subsystem_map.get(v.law_number)
            if subsystem:
                effects = self.cascade_engine.trace_cascade(subsystem)
                cascade_effects.extend(effects)

        # Sort cascade by strength
        cascade_effects.sort(key=lambda x: x["total_strength"], reverse=True)

        # Generate summary
        if viable:
            summary = (
                f"Proposal '{name}' satisfies all planetary conservation "
                f"constraints. Binding constraint: Law {binding.law_number} "
                f"({binding.name}) at {binding.margin_remaining_pct:.1f}% margin."
            )
        else:
            violation_laws = [f"Law {v.law_number}" for v in violations]
            summary = (
                f"Proposal '{name}' VIOLATES {len(violations)} conservation "
                f"law(s): {', '.join(violation_laws)}. Binding constraint: "
                f"Law {binding.law_number} ({binding.name}) at "
                f"{binding.margin_remaining_pct:.1f}% margin. "
                f"{len(cascade_effects)} cascade paths activated."
            )

        report = ProposalReport(
            proposal_name=name,
            proposal_params=proposal,
            timestamp=timestamp,
            constraint_results=results,
            cascade_effects=cascade_effects[:50],
            violations=violations,
            viable=viable,
            binding_constraint=f"Law {binding.law_number} ({binding.name})",
            summary=summary
        )

        # Log the check
        self._log_check(report)

        return report

    def _log_check(self, report: ProposalReport):
        """Append check to log file for accountability."""
        try:
            with open(self.log_file, "a") as f:
                log_entry = {
                    "timestamp": report.timestamp,
                    "proposal": report.proposal_name,
                    "viable": report.viable,
                    "violations": len(report.violations),
                    "binding_constraint": report.binding_constraint,
                    "params": report.proposal_params
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # logging failure should not break evaluation
