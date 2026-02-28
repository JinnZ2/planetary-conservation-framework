"""
Planetary Material Ledger.

Gram-level tracking from mine to orbit to end-of-life.
No hiding in "externalities."

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
Copyright (c) 2026 Kavik
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json


@dataclass
class MaterialEntry:
    """Single entry in the material ledger."""
    material: str
    mass_kg: float
    origin: str              # mine, recycled, stockpile
    destination: str         # factory, launch_site, orbit, deorbit, debris
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    program: str = ""
    lot_id: str = ""
    energy_cost_kwh: float = 0.0
    co2_cost_kg: float = 0.0

    def to_dict(self):
        return self.__dict__


class MaterialLedger:
    """
    Tracks all material flows for space infrastructure programs.

    Every gram from extraction through launch to orbital end-of-life.
    Provides real-time accounting against planetary throughput ceilings.
    """

    def __init__(self):
        self.entries: List[MaterialEntry] = []
        self.annual_totals: Dict[str, Dict[int, float]] = {}

    def record(self, entry: MaterialEntry):
        """Record a material flow."""
        self.entries.append(entry)

        # Update annual totals
        year = int(entry.timestamp[:4]) if entry.timestamp else 2026
        if entry.material not in self.annual_totals:
            self.annual_totals[entry.material] = {}
        if year not in self.annual_totals[entry.material]:
            self.annual_totals[entry.material][year] = 0
        self.annual_totals[entry.material][year] += entry.mass_kg

    def record_batch(self, entries: List[MaterialEntry]):
        """Record multiple material flows at once."""
        for entry in entries:
            self.record(entry)

    def get_annual_consumption(self, material: str, year: int) -> float:
        """Get total consumption of a material in a given year."""
        return self.annual_totals.get(material, {}).get(year, 0)

    def get_cumulative(self, material: str) -> float:
        """Get all-time cumulative consumption of a material."""
        return sum(self.annual_totals.get(material, {}).values())

    def get_all_materials(self) -> List[str]:
        """Get list of all tracked materials."""
        return list(self.annual_totals.keys())

    def check_against_ceiling(self, material: str, year: int,
                              global_production_kg: float,
                              threshold_fraction: float = 0.0001) -> Dict:
        """
        Check annual consumption against planetary ceiling.

        Args:
            material: material name
            year: year to check
            global_production_kg: annual global production
            threshold_fraction: fraction of production as ceiling (default 0.01%)

        Returns:
            Dict with consumption, ceiling, margin, and status
        """
        consumed = self.get_annual_consumption(material, year)
        ceiling = global_production_kg * threshold_fraction
        margin = ceiling - consumed
        margin_pct = (margin / ceiling * 100) if ceiling > 0 else 0

        return {
            "material": material,
            "year": year,
            "consumed_kg": consumed,
            "ceiling_kg": ceiling,
            "margin_kg": margin,
            "margin_pct": round(margin_pct, 2),
            "status": "OK" if margin > 0 else "EXCEEDED",
            "global_production_kg": global_production_kg,
            "threshold_fraction": threshold_fraction
        }

    def check_all_minerals(self, year: int) -> List[Dict]:
        """
        Check all tracked minerals against their ceilings for a given year.

        Uses default global production values from constants.
        """
        from .constants import MINERAL_DATA

        results = []
        for mineral, data in MINERAL_DATA.items():
            result = self.check_against_ceiling(
                material=mineral,
                year=year,
                global_production_kg=data["global_production_kg_per_year"],
                threshold_fraction=data["threshold_fraction"]
            )
            results.append(result)
        return results

    def energy_audit(self) -> Dict:
        """Total energy and CO2 cost of all recorded material flows."""
        total_energy = sum(e.energy_cost_kwh for e in self.entries)
        total_co2 = sum(e.co2_cost_kg for e in self.entries)
        by_material = {}
        for e in self.entries:
            if e.material not in by_material:
                by_material[e.material] = {
                    "energy_kwh": 0, "co2_kg": 0, "mass_kg": 0
                }
            by_material[e.material]["energy_kwh"] += e.energy_cost_kwh
            by_material[e.material]["co2_kg"] += e.co2_cost_kg
            by_material[e.material]["mass_kg"] += e.mass_kg

        return {
            "total_energy_kwh": total_energy,
            "total_co2_kg": total_co2,
            "by_material": by_material,
            "entries_count": len(self.entries)
        }

    def flow_summary(self) -> Dict:
        """Summarize material flows by origin and destination."""
        by_origin = {}
        by_destination = {}
        for e in self.entries:
            if e.origin not in by_origin:
                by_origin[e.origin] = 0
            by_origin[e.origin] += e.mass_kg

            if e.destination not in by_destination:
                by_destination[e.destination] = 0
            by_destination[e.destination] += e.mass_kg

        return {
            "by_origin": by_origin,
            "by_destination": by_destination,
            "total_mass_kg": sum(e.mass_kg for e in self.entries),
            "total_entries": len(self.entries)
        }

    def print_ledger(self, year: int = None):
        """Pretty-print the material ledger."""
        print(f"\n{'='*70}")
        print(f"PLANETARY MATERIAL LEDGER")
        if year:
            print(f"Year: {year}")
        print(f"{'='*70}")

        materials = self.get_all_materials()
        if not materials:
            print("  No entries recorded.")
            print(f"{'='*70}\n")
            return

        for material in sorted(materials):
            cumulative = self.get_cumulative(material)
            print(f"\n  {material}")
            print(f"    Cumulative: {cumulative:,.1f} kg")
            if year:
                annual = self.get_annual_consumption(material, year)
                print(f"    Year {year}: {annual:,.1f} kg")

        audit = self.energy_audit()
        print(f"\n{'─'*70}")
        print(f"  ENERGY AUDIT")
        print(f"    Total energy: {audit['total_energy_kwh']:,.0f} kWh")
        print(f"    Total CO₂: {audit['total_co2_kg']:,.0f} kg")
        print(f"    Entries: {audit['entries_count']}")

        flow = self.flow_summary()
        print(f"\n{'─'*70}")
        print(f"  FLOW SUMMARY")
        print(f"    By origin:")
        for origin, mass in sorted(flow["by_origin"].items(),
                                   key=lambda x: x[1], reverse=True):
            print(f"      {origin}: {mass:,.1f} kg")
        print(f"    By destination:")
        for dest, mass in sorted(flow["by_destination"].items(),
                                 key=lambda x: x[1], reverse=True):
            print(f"      {dest}: {mass:,.1f} kg")

        print(f"\n{'='*70}\n")

    def export_json(self) -> str:
        """Export full ledger as JSON."""
        return json.dumps({
            "entries": [e.to_dict() for e in self.entries],
            "annual_totals": self.annual_totals,
            "energy_audit": self.energy_audit(),
            "flow_summary": self.flow_summary()
        }, indent=2)

    def export_csv(self) -> str:
        """Export ledger entries as CSV string."""
        header = ("timestamp,material,mass_kg,origin,destination,"
                  "program,lot_id,energy_cost_kwh,co2_cost_kg")
        lines = [header]
        for e in self.entries:
            lines.append(
                f"{e.timestamp},{e.material},{e.mass_kg},{e.origin},"
                f"{e.destination},{e.program},{e.lot_id},"
                f"{e.energy_cost_kwh},{e.co2_cost_kg}"
            )
        return "\n".join(lines)
