"""Turn a stage template into dated stages and tasks."""
import json
import re
from datetime import date, timedelta
from importlib import resources
from typing import Optional


def available_templates() -> list:
    """Names of the bundled templates, e.g. ["default", "kitchen"]."""
    return sorted(f.name[:-len("_template.json")] for f in resources.files(__package__).iterdir()
                  if f.name.endswith("_template.json"))


def load_template(name: str) -> dict:
    """Load a bundled template by name, e.g. "default" or "kitchen" (reads <name>_template.json)."""
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name):
        raise ValueError(f"Bad template name {name!r}; use one of {available_templates()}")
    f = resources.files(__package__).joinpath(f"{name}_template.json")
    if not f.is_file():
        raise ValueError(f"No template named {name!r}; use one of {available_templates()}")
    return json.loads(f.read_text(encoding="utf-8"))


def default_template() -> dict:
    """The 7-stage template for Indian home interiors: brief, concept, design, BOQ, procurement, site, handover."""
    return load_template("default")


def _add_days(d: date, n: int, skip_sunday: bool) -> date:
    """Add n calendar days, or n working days (Mon-Sat) when skip_sunday."""
    if not skip_sunday:
        return d + timedelta(days=n)
    out, left = d, n
    while left > 0:
        out += timedelta(days=1)
        if out.weekday() != 6:
            left -= 1
    return out


def plan_project(start: date, template: Optional[dict] = None, skip_sunday: bool = True,
                 people: Optional[dict] = None) -> dict:
    """Return {"start", "end", "stages": [...]} with planned start/end per stage and a due date per task.

    people maps template roles to names, e.g. {"designer": "Asha", "senior": "Ravi"}.
    """
    tpl = template or default_template()
    people = people or {}
    cursor = start
    out = []
    for s in tpl["stages"]:
        s_start = cursor
        s_end = _add_days(s_start, max(s["days"] - 1, 0), skip_sunday)
        tasks = [{**t, "owner": people.get(t["who"], t["who"]), "due": _add_days(s_start, t["day"], skip_sunday).isoformat()}
                 for t in s.get("tasks", [])]
        out.append({**{k: v for k, v in s.items() if k != "tasks"}, "start": s_start.isoformat(), "end": s_end.isoformat(), "tasks": tasks})
        cursor = _add_days(s_end, 1, skip_sunday)
    return {"start": start.isoformat(), "end": out[-1]["end"] if out else start.isoformat(), "stages": out}


def client_approvals(plan: dict) -> list:
    """Stages where the client must approve, with the date it is due."""
    return [{"stage": s["key"], "ask": s.get("client_ask") or s.get("approval_label"), "due": s["end"]}
            for s in plan["stages"] if s.get("client_approval")]
