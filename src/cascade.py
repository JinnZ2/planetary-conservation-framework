"""
Coupled feedback loop engine.

Models the cascade interactions between subsystem constraints.
When one constraint degrades, it affects others through defined coupling paths.

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json


@dataclass
class CascadeLink:
    """A coupling between two subsystem constraints."""
    source: str
    target: str
    mechanism: str
    strength: float              # 0.0-1.0 coupling strength
    timescale_years: float
    direction: str = "amplifying"  # "amplifying" or "dampening"

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "mechanism": self.mechanism,
            "strength": self.strength,
            "timescale_years": self.timescale_years,
            "direction": self.direction
        }


# ============================================================
# COUPLING MATRIX
# ============================================================

CASCADE_LINKS = [
    # Thermospheric heating → debris lifetime
    CascadeLink(
        source="thermosphere",
        target="debris",
        mechanism="Soot heating → thermospheric expansion → reduced drag "
                  "→ longer debris lifetimes → higher density",
        strength=0.7,
        timescale_years=1.0,
        direction="amplifying"
    ),
    # Debris density → replacement launches
    CascadeLink(
        source="debris",
        target="launch_cadence",
        mechanism="Debris collisions → satellite loss → replacement launches required",
        strength=0.8,
        timescale_years=0.5,
        direction="amplifying"
    ),
    # Launch cadence → thermospheric heating (closes the loop)
    CascadeLink(
        source="launch_cadence",
        target="thermosphere",
        mechanism="More launches → more soot deposition → more heating",
        strength=0.6,
        timescale_years=0.1,
        direction="amplifying"
    ),
    # Launch cadence → atmosphere
    CascadeLink(
        source="launch_cadence",
        target="atmosphere",
        mechanism="More launches → more BC + H2O + alumina injection",
        strength=0.9,
        timescale_years=0.1,
        direction="amplifying"
    ),
    # Launch cadence → water budget
    CascadeLink(
        source="launch_cadence",
        target="water_budget",
        mechanism="More launches → more H2O at altitude → more H escape",
        strength=0.9,
        timescale_years=0.1,
        direction="amplifying"
    ),
    # Launch cadence → mineral throughput
    CascadeLink(
        source="launch_cadence",
        target="minerals",
        mechanism="More launches + replacement hardware → accelerated mineral consumption",
        strength=0.7,
        timescale_years=1.0,
        direction="amplifying"
    ),
    # Mineral depletion → declining ore grades → energy cost
    CascadeLink(
        source="minerals",
        target="energy_budget",
        mechanism="Declining ore grades → exponentially rising extraction energy per kg",
        strength=0.5,
        timescale_years=5.0,
        direction="amplifying"
    ),
    # Energy competition → grid stress → launch site vulnerability
    CascadeLink(
        source="energy_budget",
        target="launch_sites",
        mechanism="Manufacturing/launch energy competes with grid "
                  "→ rolling blackouts, brownouts",
        strength=0.4,
        timescale_years=2.0,
        direction="amplifying"
    ),
    # Climate stress → launch site physical damage
    CascadeLink(
        source="climate",
        target="launch_sites",
        mechanism="Sea level rise, hurricanes, wildfire "
                  "→ infrastructure damage → schedule disruption",
        strength=0.6,
        timescale_years=5.0,
        direction="amplifying"
    ),
    # Launch site disruption → schedule compression → safety erosion
    CascadeLink(
        source="launch_sites",
        target="safety",
        mechanism="Schedule disruption → pressure to accelerate "
                  "→ safety margin erosion",
        strength=0.7,
        timescale_years=0.5,
        direction="amplifying"
    ),
    # Safety erosion → debris generation
    CascadeLink(
        source="safety",
        target="debris",
        mechanism="Reduced safety margins → higher failure rate → more debris",
        strength=0.8,
        timescale_years=0.1,
        direction="amplifying"
    ),
    # Insurance withdrawal → cost escalation → economic pressure
    CascadeLink(
        source="insurance",
        target="economics",
        mechanism="Insurance contraction → rising costs "
                  "→ economic viability erosion",
        strength=0.9,
        timescale_years=1.0,
        direction="amplifying"
    ),
    # Economic pressure → safety compression
    CascadeLink(
        source="economics",
        target="safety",
        mechanism="Cost pressure → cut corners on debris management, "
                  "testing, redundancy",
        strength=0.6,
        timescale_years=0.5,
        direction="amplifying"
    ),
    # Debris events → insurance withdrawal
    CascadeLink(
        source="debris",
        target="insurance",
        mechanism="Collision events → claims → reinsurance withdrawal "
                  "→ coverage exclusions",
        strength=0.8,
        timescale_years=0.5,
        direction="amplifying"
    ),
]


class CascadeEngine:
    """
    Propagates constraint violations through the coupling matrix.

    Given an initial perturbation (e.g., "launch cadence increases 10x"),
    traces all cascade paths and calculates amplified effects.
    """

    def __init__(self, links: List[CascadeLink] = None):
        self.links = links or CASCADE_LINKS
        self._build_graph()

    def _build_graph(self):
        """Build adjacency list from links."""
        self.graph: Dict[str, List[CascadeLink]] = {}
        for link in self.links:
            if link.source not in self.graph:
                self.graph[link.source] = []
            self.graph[link.source].append(link)

    def trace_cascade(self, origin: str, perturbation: float = 1.0,
                      max_depth: int = 10, min_strength: float = 0.01
                      ) -> List[Dict]:
        """
        Trace cascade effects from an origin subsystem.

        Args:
            origin: starting subsystem name
            perturbation: initial perturbation magnitude (1.0 = 100%)
            max_depth: maximum cascade depth to prevent infinite loops
            min_strength: minimum accumulated strength to continue tracing

        Returns:
            List of cascade paths with accumulated effects
        """
        paths = []
        self._trace_recursive(origin, perturbation, [], set(), paths,
                              max_depth, min_strength)
        return paths

    def _trace_recursive(self, current: str, strength: float,
                         path: List[Dict], visited: set,
                         paths: List[Dict], max_depth: int,
                         min_strength: float):
        if max_depth <= 0 or strength < min_strength:
            return

        if current in self.graph:
            for link in self.graph[current]:
                propagated = strength * link.strength
                step = {
                    "from": link.source,
                    "to": link.target,
                    "mechanism": link.mechanism,
                    "propagated_strength": round(propagated, 4),
                    "timescale_years": link.timescale_years,
                    "direction": link.direction
                }

                new_path = path + [step]

                paths.append({
                    "path": new_path.copy(),
                    "total_strength": round(propagated, 4),
                    "total_timescale": sum(s["timescale_years"] for s in new_path),
                    "is_loop": link.target in visited
                })

                if link.target not in visited:
                    self._trace_recursive(
                        link.target, propagated,
                        new_path, visited | {current},
                        paths, max_depth - 1, min_strength
                    )

    def find_feedback_loops(self) -> List[Dict]:
        """Identify all positive feedback loops in the coupling matrix."""
        loops = []
        for node in self.graph:
            paths = self.trace_cascade(node, max_depth=8)
            for p in paths:
                if p["is_loop"] and p["path"][-1]["to"] == node:
                    loops.append({
                        "origin": node,
                        "path": [s["to"] for s in p["path"]],
                        "total_timescale": p["total_timescale"],
                        "mechanism_chain": [s["mechanism"] for s in p["path"]]
                    })
        return loops

    def print_cascade(self, origin: str, perturbation: float = 1.0):
        """Pretty-print cascade from origin."""
        paths = self.trace_cascade(origin, perturbation)
        print(f"\n{'='*70}")
        print(f"CASCADE FROM: {origin} (perturbation: {perturbation:.0%})")
        print(f"{'='*70}")

        paths.sort(key=lambda p: p["total_strength"], reverse=True)

        for i, p in enumerate(paths[:20]):
            chain = " → ".join(
                [p["path"][0]["from"]] + [s["to"] for s in p["path"]]
            )
            loop_marker = " ⟲ LOOP" if p["is_loop"] else ""
            print(f"\n  [{i+1}] {chain}{loop_marker}")
            print(f"      Strength: {p['total_strength']:.4f} | "
                  f"Timescale: {p['total_timescale']:.1f} yr")
            for step in p["path"]:
                print(f"        → {step['mechanism'][:80]}...")

    def to_json(self) -> str:
        """Export coupling matrix as JSON."""
        return json.dumps({
            "links": [l.to_dict() for l in self.links],
            "subsystems": list(self.graph.keys())
        }, indent=2)
