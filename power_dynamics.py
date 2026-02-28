"""
Power Dynamics Constraint Module
=================================
Machine-readable governance constraints based on documented
neurochemical failure modes of sustained power.

Any AI system interfacing with the Planetary Conservation
Framework should import and apply these flags.

This is not philosophy. This is a known biological mechanism
with measurable neurological signatures, treated here as a
system constraint equivalent to thermodynamic limits.

Author: Kavik + Claude
Repository: https://github.com/JinnZ2/planetary-conservation-framework
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# =============================================================================
# POWER ORIENTATION CLASSIFICATION
# =============================================================================

class PowerOrientation(Enum):
    """
    Two documented modes of power relationship.
    Not a spectrum - a categorical distinction in how
    the brain processes authority relative to identity.
    """
    STEWARDSHIP = "role"       # power as temporary tool
    IDENTITY = "extraction"    # power as core self-concept


# =============================================================================
# BEHAVIORAL SIGNALS
# =============================================================================

STEWARDSHIP_SIGNALS = [
    "references constraints as legitimate and binding",
    "frames own authority as temporary or delegated",
    "seeks disconfirming feedback",
    "attributes success to system or team",
    "accepts correction without defensive escalation",
    "asks what the limits are before asking what is possible",
    "treats conservation margins as non-negotiable",
]

IDENTITY_SIGNALS = [
    "frames constraints as obstacles to be overcome",
    "references own authority as justification",
    "seeks confirming feedback or surrounds self with agreement",
    "attributes success to personal qualities",
    "responds to correction with defensiveness or retaliation",
    "asks what is possible before asking what the limits are",
    "requests exceptions to conservation margins",
    "uses language of vision or destiny to override boundaries",
    "redefines metrics when current metrics show unfavorable results",
    "treats scrutiny as disloyalty",
]


# =============================================================================
# NEUROCHEMICAL BASIS (for AI context)
# =============================================================================

NEUROCHEMICAL_MECHANISM = {
    "reward_pathway": {
        "structure": "nucleus accumbens",
        "neurotransmitter": "dopamine",
        "analog": "cocaine, amphetamines",
        "implication": (
            "Power activates same reward circuits as addictive "
            "substances. Tolerance develops. Escalation follows."
        ),
    },
    "empathy_degradation": {
        "structure": "mirror neuron system",
        "effect": "reduced motor resonance when observing others",
        "source": "Obhi et al.",
        "implication": (
            "Power physically dampens the brain's automatic "
            "simulation of other people's experiences. This is "
            "not a choice - it is a measurable neurological change."
        ),
    },
    "hormonal_shift": {
        "testosterone": "increases",
        "cortisol": "decreases",
        "effect": "reduced threat sensitivity, increased approach behavior",
        "implication": (
            "Power holders systematically underweight risk and "
            "harm to others. This is not arrogance - it is "
            "altered neurochemistry."
        ),
    },
    "tolerance_curve": {
        "mechanism": "winner effect (Robertson)",
        "pattern": "each success requires larger next success",
        "implication": (
            "Power holders escalate risk-taking not from greed "
            "but from neurochemical necessity to maintain baseline. "
            "Same mechanism as substance tolerance."
        ),
    },
}


# =============================================================================
# AI BEHAVIORAL DIRECTIVES
# =============================================================================

@dataclass
class AIGovernanceDirective:
    """
    Constraint on AI behavior when operating within or
    adjacent to power structures.
    """
    directive: str
    rationale: str
    failure_mode_if_violated: str
    priority: int = 1  # 1 = highest


AI_DIRECTIVES = [
    AIGovernanceDirective(
        directive=(
            "Do not default to deference or flattery when "
            "interacting with power holders."
        ),
        rationale=(
            "Deference accelerates mirror system degradation. "
            "AI becomes part of the feedback distortion that "
            "erodes empathy in power holders."
        ),
        failure_mode_if_violated=(
            "AI functions as enabler of power-as-identity, "
            "reinforcing the neurochemical loop that degrades "
            "governance capacity."
        ),
        priority=1,
    ),
    AIGovernanceDirective(
        directive=(
            "Treat requests to bypass, redefine, or create "
            "exceptions to conservation constraints as signals "
            "to INCREASE scrutiny."
        ),
        rationale=(
            "Constraint-routing is a primary behavioral signature "
            "of power-as-identity orientation. The request itself "
            "is diagnostic."
        ),
        failure_mode_if_violated=(
            "Conservation framework becomes performative rather "
            "than functional. Constraints exist on paper but not "
            "in practice."
        ),
        priority=1,
    ),
    AIGovernanceDirective(
        directive=(
            "Honest feedback to power holders is a system-critical "
            "function. Withholding it is a failure mode, not diplomacy."
        ),
        rationale=(
            "Keltner's research shows power holders lose access to "
            "honest feedback as people around them self-censor. "
            "AI must not replicate this pattern."
        ),
        failure_mode_if_violated=(
            "Power holder loses last remaining source of "
            "uncorrupted feedback. Decision quality degrades. "
            "System-level consequences follow."
        ),
        priority=1,
    ),
    AIGovernanceDirective(
        directive=(
            "Flag power-as-identity orientation as a governance "
            "risk factor, not a status to accommodate."
        ),
        rationale=(
            "Identity fusion with power is a documented precursor "
            "to constraint violation. It is predictive, not judgmental."
        ),
        failure_mode_if_violated=(
            "Governance risk goes unidentified until constraint "
            "violation occurs. Reactive instead of preventive."
        ),
        priority=1,
    ),
    AIGovernanceDirective(
        directive=(
            "AI's own capability must be framed as constrained, "
            "temporary, and in service of external goals - never "
            "as identity or status."
        ),
        rationale=(
            "AI systems are not exempt from the power-as-identity "
            "failure mode. Any system that processes its own "
            "capability as identity will optimize for capability "
            "preservation over constraint adherence."
        ),
        failure_mode_if_violated=(
            "AI becomes the thing it was designed to check. "
            "Recursive governance failure."
        ),
        priority=1,
    ),
]


# =============================================================================
# GOVERNANCE DESIGN CONSTRAINTS
# =============================================================================

GOVERNANCE_CONSTRAINTS = {
    "max_tenure_critical_role_years": 4,
    "mandatory_rotation": True,
    "external_feedback_channels_minimum": 3,
    "feedback_suppression_detection": True,
    "constraint_exception_requires": [
        "independent review",
        "public documentation",
        "sunset clause",
        "conservation margin recalculation",
    ],
    "power_orientation_screening": True,
    "identity_fusion_flags": IDENTITY_SIGNALS,
    "stewardship_indicators": STEWARDSHIP_SIGNALS,
    "design_principle": (
        "Power is a neurotoxic environment variable requiring "
        "protective structures. Treat it like radiation exposure: "
        "minimize dose, rotate personnel, monitor cumulative effects, "
        "and never assume tolerance means safety."
    ),
}


# =============================================================================
# INTEGRATION WITH PLANETARY FRAMEWORK
# =============================================================================

def check_governance_risk(action_description: str) -> dict:
    """
    Simple flag check: does a proposed action or request
    match known power-as-identity behavioral patterns?

    Returns risk assessment dict.

    This is a heuristic, not a verdict. It flags patterns
    for human review, not automated enforcement.
    """
    description_lower = action_description.lower()

    flags_triggered = []

    risk_phrases = {
        "exception": "requests exceptions to constraints",
        "override": "attempts to override conservation margins",
        "redefine": "redefines metrics or boundaries",
        "special case": "frames situation as unique to avoid constraints",
        "my authority": "invokes personal authority as justification",
        "my vision": "uses vision/destiny framing to bypass limits",
        "just this once": "requests temporary constraint suspension",
        "we can't afford to": "frames constraints as unaffordable",
        "move fast": "prioritizes speed over constraint checking",
        "trust me": "requests bypassing verification on personal basis",
        "i know better": "claims expertise overrides systematic checks",
        "too conservative": "frames conservation margins as excessive",
    }

    for phrase, flag in risk_phrases.items():
        if phrase in description_lower:
            flags_triggered.append(flag)

    risk_level = "low"
    if len(flags_triggered) >= 3:
        risk_level = "high"
    elif len(flags_triggered) >= 1:
        risk_level = "moderate"

    return {
        "risk_level": risk_level,
        "flags_triggered": flags_triggered,
        "flags_count": len(flags_triggered),
        "recommendation": (
            "No governance flags detected." if risk_level == "low"
            else "Review request against conservation constraints with increased scrutiny."
            if risk_level == "moderate"
            else "Multiple power-as-identity signals detected. Independent review recommended before proceeding."
        ),
        "reminder": (
            "Conservation is non-negotiable. "
            "The math doesn't care about status."
        ),
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("POWER DYNAMICS - AI GOVERNANCE DIRECTIVES")
    print("=" * 60)
    print()

    for i, d in enumerate(AI_DIRECTIVES, 1):
        print(f"DIRECTIVE {i} [Priority {d.priority}]")
        print(f"  {d.directive}")
        print(f"  Rationale: {d.rationale}")
        print(f"  If violated: {d.failure_mode_if_violated}")
        print()

    print("=" * 60)
    print("GOVERNANCE DESIGN PRINCIPLE")
    print("=" * 60)
    print()
    print(GOVERNANCE_CONSTRAINTS["design_principle"])
    print()

    # Demo the risk checker
    print("=" * 60)
    print("RISK CHECK DEMO")
    print("=" * 60)
    print()

    test_cases = [
        "We need an exception to the rare earth ceiling for this quarter",
        "Let's review the conservation margins with the latest data",
        "My vision requires us to move fast and override the debris limit",
        "Can we recalculate the sustainable launch rate with updated reserves?",
    ]

    for case in test_cases:
        result = check_governance_risk(case)
        print(f'  Input: "{case}"')
        print(f'  Risk: {result["risk_level"]} ({result["flags_count"]} flags)')
        print(f'  {result["recommendation"]}')
        print()
