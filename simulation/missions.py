"""Validated, declarative mission rubrics over *simulated* lab state.

Definitions are bundled data, never Python expressions or arbitrary external paths in the API.
Only registered criterion IDs can execute. A mission cannot extend the program's powers.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core import Lab

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
CRITERIA = frozenset({"cable_present", "successful_ping_evidence", "security_and_sticky_mac_learned", "saved_configuration"})
ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
API_KEY = re.compile(r"mission_[a-z0-9_]+\Z")
REQUIRED = frozenset({"schema_version", "id", "api_key", "name", "fidelity", "difficulty", "prerequisites",
                      "objectives", "initial_topology", "starting_problem", "available_equipment", "authorized_targets",
                      "tasks", "hints", "rubric", "required_evidence", "success", "failure", "recovery", "report"})
EQUIPMENT = frozenset({"pc-a", "pc-b", "sw1", "copper-repair-cable", "simulated-switch-cli"})


class MissionDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class Mission:
    id: str
    api_key: str
    name: str
    prerequisites: tuple[str, ...]
    rubric: dict[str, int]
    success: tuple[str, ...]
    objectives: tuple[str, ...]
    hints: tuple[str, ...]
    authorized_targets: tuple[str, ...]
    difficulty: str
    tasks: tuple[str, ...]
    available_equipment: tuple[str, ...]
    required_evidence: tuple[str, ...]
    starting_problem: str
    failure: str
    recovery: str
    report: str

    def describe(self) -> dict:
        return {"id": self.id, "api_key": self.api_key, "name": self.name, "difficulty": self.difficulty,
                "objectives": list(self.objectives), "tasks": list(self.tasks), "hints": list(self.hints),
                "prerequisites": list(self.prerequisites), "authorized_targets": list(self.authorized_targets),
                "available_equipment": list(self.available_equipment), "required_evidence": list(self.required_evidence),
                "starting_problem": self.starting_problem, "failure": self.failure, "recovery": self.recovery,
                "report": self.report, "max_score": sum(self.rubric.values()), "fidelity": "SIMULATED"}


def _strings(value, field: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(isinstance(v, str) and v.strip() for v in value):
        raise MissionDefinitionError(f"{field} must be a list of non-empty strings")
    return tuple(value)


def _unique_fields(pairs: list[tuple[str, object]]) -> dict:
    data = {}
    for key, value in pairs:
        if key in data:
            raise MissionDefinitionError(f"Duplicate JSON field: {key}")
        data[key] = value
    return data


def load_missions(directory: Path = SCENARIOS) -> tuple[Mission, ...]:
    missions = []
    for file in sorted(directory.glob("mission_*.json")):
        try:
            doc = json.loads(file.read_text(encoding="utf-8"), object_pairs_hook=_unique_fields)
            if not isinstance(doc, dict) or type(doc.get("schema_version")) is not int or doc["schema_version"] != 1:
                raise MissionDefinitionError("Unsupported scenario schema version")
            if set(doc) != REQUIRED:
                raise MissionDefinitionError(f"Scenario fields mismatch: missing={sorted(REQUIRED - set(doc))}, unknown={sorted(set(doc) - REQUIRED)}")
            mid, api = doc["id"], doc["api_key"]
            if not isinstance(mid, str) or not ID.fullmatch(mid) or not isinstance(api, str) or not API_KEY.fullmatch(api):
                raise MissionDefinitionError("Invalid mission ID or API key")
            if doc.get("fidelity") != "SIMULATED" or doc.get("initial_topology") != "builtin-school-lab-v1":
                raise MissionDefinitionError("Unsupported fidelity or topology")
            rubric = doc["rubric"]
            if (not isinstance(rubric, dict) or not rubric or not set(rubric) <= CRITERIA or
                    any(type(weight) is not int or weight < 1 or weight > 10 for weight in rubric.values())):
                raise MissionDefinitionError("Rubric requires known criteria with integer weights 1..10")
            expression = doc["success"]
            if not isinstance(expression, str):
                raise MissionDefinitionError("Success must be an AND expression over rubric criterion IDs")
            terms = tuple(expression.split(" AND "))
            if len(set(terms)) != len(terms) or set(terms) != set(rubric):
                raise MissionDefinitionError("Success may only AND each listed rubric criterion once")
            prereqs = doc["prerequisites"]
            if not isinstance(prereqs, list) or not all(isinstance(p, str) and ID.fullmatch(p) for p in prereqs):
                raise MissionDefinitionError("Invalid prerequisites")
            targets = _strings(doc["authorized_targets"], "authorized_targets")
            if not set(targets) <= {"pc-a:eth0", "pc-b:eth0", "sw1:fa0/1", "sw1:fa0/3"} or len(set(targets)) != len(targets):
                raise MissionDefinitionError("Unknown or duplicate authorized target")
            for field in ("name", "starting_problem", "failure", "recovery", "report"):
                if not isinstance(doc[field], str) or not doc[field].strip():
                    raise MissionDefinitionError(f"{field} requires a non-empty string")
            if doc["difficulty"] not in ("beginner", "intermediate", "advanced"):
                raise MissionDefinitionError("Unsupported difficulty")
            equipment = _strings(doc["available_equipment"], "available_equipment")
            if not set(equipment) <= EQUIPMENT:
                raise MissionDefinitionError("Unknown equipment")
            missions.append(Mission(mid, api, doc["name"], tuple(prereqs), dict(rubric), terms,
                                    _strings(doc["objectives"], "objectives"), _strings(doc["hints"], "hints", True), targets,
                                    doc["difficulty"], _strings(doc["tasks"], "tasks"), equipment,
                                    _strings(doc["required_evidence"], "required_evidence"), doc["starting_problem"],
                                    doc["failure"], doc["recovery"], doc["report"]))
        except (KeyError, TypeError, ValueError, UnicodeError) as exc:
            raise MissionDefinitionError(f"Invalid scenario {file.name}: {exc}") from exc
    if not missions:
        raise MissionDefinitionError("No mission definitions found")
    ids = {m.id for m in missions}
    if len(ids) != len(missions) or len({m.api_key for m in missions}) != len(missions):
        raise MissionDefinitionError("Duplicate mission ID or API key")
    for mission in missions:
        if mission.id in mission.prerequisites or not set(mission.prerequisites) <= ids:
            raise MissionDefinitionError(f"Invalid prerequisites for {mission.id}")
    # Detect dependency cycles and sort in prerequisite order.
    visited: set[str] = set()
    active: set[str] = set()
    ordered: list[Mission] = []
    by_id = {m.id: m for m in missions}

    def visit(mid: str) -> None:
        if mid in active:
            raise MissionDefinitionError("Mission prerequisite cycle")
        if mid in visited:
            return
        active.add(mid)
        for prereq in by_id[mid].prerequisites:
            visit(prereq)
        active.remove(mid)
        visited.add(mid)
        ordered.append(by_id[mid])

    for mission in missions:
        visit(mission.id)
    return tuple(ordered)


# Fail early at import on invalid bundled scenario content, not while a player is mid-mission.
MISSIONS = load_missions()


def assess(lab: Lab) -> dict:
    """Evaluate observed state, not entered command strings or synthetic score claims."""
    cable = bool(lab.link_of("pc-b:eth0"))
    port = lab.ports["sw1:fa0/3"]
    mac = lab.ports["pc-b:eth0"].mac
    ping = (lab.last_ping and lab.last_ping_source == "pc-b:eth0" and
            lab.last_ping_target == "pc-a:eth0" and cable)
    sticky = port.security and port.sticky and mac in port.learned and not port.violated
    config = lab.saved_config
    current = {"vlan": port.vlan, "enabled": port.enabled, "security": port.security,
               "sticky": port.sticky, "maximum": port.maximum, "violation": port.violation}
    saved = bool(config and mac in config.get("sticky_macs", []) and
                 config.get("interfaces", {}).get("sw1:fa0/3") == current)
    criteria = {"cable_present": cable, "successful_ping_evidence": ping,
                "security_and_sticky_mac_learned": sticky, "saved_configuration": saved}
    report: dict[str, dict] = {}
    completed: dict[str, bool] = {}
    for mission in MISSIONS:
        prerequisite_met = all(completed[p] for p in mission.prerequisites)
        results = {key: bool(criteria[key]) for key in mission.rubric}
        success = prerequisite_met and all(results[key] for key in mission.success)
        completed[mission.id] = success
        report[mission.api_key] = {"id": mission.id, "complete": success, "prerequisites_met": prerequisite_met,
                                   "criteria": results, "score": sum(weight for key, weight in mission.rubric.items() if results[key]),
                                   "max_score": sum(mission.rubric.values()), "cable": cable, "ping_evidence": ping,
                                   "port_security": port.security, "sticky_mac_learned": sticky, "saved": saved}
    return report
