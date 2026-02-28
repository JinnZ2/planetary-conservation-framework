from dataclasses import dataclass
from enum import Enum

class Role(Enum):
    LEADER = "leader"
    WISE = "wise"

@dataclass
class DecisionBody:
    leaders: int            # number of people with executive authority
    wise_people: int        # number of independent stewards/elders
    tie_breaker_available: bool  # whether a 3rd wise person can be invoked

@dataclass
class GovernanceAssessment:
    passes_minimum: bool
    issues: list
    recommendations: list

class GovernanceChecker:
    def assess_decision_body(self, body: DecisionBody) -> GovernanceAssessment:
        issues = []
        recommendations = []

        # Minimum pattern from your culture:
        # - at least 2 leaders
        # - at least 2 wise people
        # - optional 3rd wise person for stalemates
        passes = True

        if body.leaders < 2:
            passes = False
            issues.append("Only one leader detected. Single-point-of-failure for authority.")
            recommendations.append(
                "Introduce at least one co-leader or co-equal authority to prevent solo capture."
            )

        if body.wise_people < 2:
            passes = False
            issues.append("Fewer than two wise stewards. No internal check on ‘wisdom’ layer.")
            recommendations.append(
                "Establish at least two independent stewards/elders who do not hold executive power."
            )

        if body.wise_people >= 2 and not body.tie_breaker_available:
            issues.append("No explicit tie-break mechanism among wise stewards.")
            recommendations.append(
                "Define a third, temporary wise role or rotating external arbiter for stalemates."
            )

        # Strong pattern: leaders != wise people
        # (avoid same individuals holding both roles)
        # This assumes you’ll check that in a richer model with identities.

        return GovernanceAssessment(
            passes_minimum=passes,
            issues=issues,
            recommendations=recommendations
        )

# Example usage:
body = DecisionBody(leaders=1, wise_people=2, tie_breaker_available=False)
checker = GovernanceChecker()
assessment = checker.assess_decision_body(body)

print("GOVERNANCE MINIMUM PATTERN MET:", assessment.passes_minimum)
for issue in assessment.issues:
    print("ISSUE:", issue)
for rec in assessment.recommendations:
    print("RECOMMENDATION:", rec)
