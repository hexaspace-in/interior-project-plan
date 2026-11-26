"""Turn a stage template into dated stages and tasks."""
import json
from datetime import date, timedelta
from importlib import resources
from typing import Optional


def default_template() -> dict:
    """The 7-stage template for Indian home interiors: brief, concept, design, BOQ, procurement, site, handover."""
    return json.loads(resources.files(__package__).joinpath("default_template.json").read_text(encoding="utf-8"))


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
