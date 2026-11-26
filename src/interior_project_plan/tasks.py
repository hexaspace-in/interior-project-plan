"""Repeating tasks and task dependencies.

Repeat rule (a dict): {"freq": "daily"|"weekly"|"monthly"|"every_n", "days": [0..6] (weekly, 0=Mon),
"month_day": 1-31 or 0 for the last working day (monthly), "every": N (every_n), "mode": "schedule"|"completion",
"skip_sunday": True, "until": "YYYY-MM-DD" (optional)}. Working days are Mon-Sat, as common in India.
Dependencies are finish-to-start: a task cannot start until the tasks it waits for are done; loops are refused.
"""
import calendar
from datetime import date, timedelta
from typing import Optional


class RuleError(ValueError):
    pass


class DependencyError(ValueError):
    pass


def _d(s: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def check_rule(r: dict):
    if r["freq"] == "weekly" and (not r.get("days") or any(d < 0 or d > 6 for d in r.get("days"))):
        raise RuleError("Pick the days of the week")
    if r["freq"] == "every_n" and r.get("every", 1) < 2:
        raise RuleError("Every N days needs 2 or more days (or use Daily)")
    if r.get("until") and not _d(r.get("until")):
        raise RuleError("Bad end date")


def describe(r: dict) -> str:
    f = r.get("freq")
    if f == "daily":
        txt = "Every working day (Mon–Sat)" if r.get("skip_sunday", True) else "Every day"
    elif f == "weekly":
        txt = "Every " + ", ".join(WEEKDAYS[d] for d in sorted(r.get("days") or []))
    elif f == "monthly":
        md = r.get("month_day") or 0
        txt = "Every month on the last working day" if not md else f"Every month on the {md}{'th' if 10 <= md % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(md % 10, 'th')}"
    else:
        txt = f"Every {r.get('every')} days"
    if r.get("mode") == "completion":
        txt += " after the last one is done"
    if r.get("until"):
        txt += f", until {_d(r['until']).strftime('%d %b %Y')}"
    return txt


def _last_working(y: int, m: int) -> date:
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() == 6:
        d -= timedelta(days=1)
    return d


def next_due(r: dict, after: date) -> Optional[date]:
    """The first date strictly after `after` that matches the rule (None when past `until`)."""
    f = r["freq"]
    if f == "daily":
        d = after + timedelta(days=1)
        while r.get("skip_sunday", True) and d.weekday() == 6:
            d += timedelta(days=1)
    elif f == "weekly":
        d = after + timedelta(days=1)
        while d.weekday() not in (r.get("days") or [0]):
            d += timedelta(days=1)
    elif f == "monthly":
        y, m, md = after.year, after.month, r.get("month_day") or 0
        d = None
        for _ in range(3):
            cand = _last_working(y, m) if not md else date(y, m, min(md, calendar.monthrange(y, m)[1]))
            if md and cand.weekday() == 6 and r.get("skip_sunday", True):
                cand -= timedelta(days=1)                      # a Sunday date moves to the Saturday before
            if cand > after:
                d = cand
                break
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    else:
        d = after + timedelta(days=r.get("every") or 1)
        if r.get("skip_sunday", True) and d.weekday() == 6:
            d += timedelta(days=1)
    if d and r.get("until") and _d(r["until"]) and d > _d(r["until"]):
        return None
    return d


def lead_days(r: dict) -> int:
    """How many days before its due date a scheduled repeat is created."""
    return {"daily": 0, "weekly": 2, "monthly": 7}.get(r["freq"], min(7, max(0, (r.get("every") or 1) - 1)))


def first_due(r: dict, start: date) -> date:
    """The first due date on or after `start` that matches the rule."""
    if r["freq"] == "every_n":
        return start
    return next_due(r, start - timedelta(days=1)) or start


def check_deps(tid: str, deps: list, graph: dict):
    """graph = {task id: [ids it waits for]} for the whole list. Refuses self, unknown ids and loops."""
    if tid in deps:
        raise DependencyError("A task cannot wait for itself")
    unknown = [d for d in deps if d not in graph]
    if unknown:
        raise DependencyError("Pick tasks from the same list")
    g = dict(graph)
    g[tid] = list(deps)
    seen, stack = set(), list(deps)
    while stack:
        x = stack.pop()
        if x == tid:
            raise DependencyError("That would make a loop: these tasks would wait for each other forever")
        if x in seen:
            continue
        seen.add(x)
        stack.extend(g.get(x) or [])


def blockers(t: dict, by_id: dict) -> list:
    """Open tasks this one waits for."""
    out = []
    for d in t.get("depends_on") or []:
        p = by_id.get(d)
        if p and p.get("status") not in ("done", "cancelled"):
            out.append({"id": p["id"], "title": p["title"], "no": p.get("no"), "due": p.get("due"), "status": p.get("status")})
    return out


def check_can_start(new_status: str, blocked: list):
    if new_status in ("doing", "review", "done") and blocked:
        raise DependencyError("Waiting for: " + ", ".join(b["title"] for b in blocked[:3]) + ". It can start once that is done.")
