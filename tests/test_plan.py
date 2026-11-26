from datetime import date

import pytest

from interior_project_plan import (DependencyError, RuleError, check_can_start, check_deps, check_rule,
                                   client_approvals, default_template, describe, next_due, plan_project)


def test_template():
    t = default_template()
    assert [s["key"] for s in t["stages"]] == ["brief", "concept", "design", "boq", "procurement", "site", "handover"]


def test_plan_dates_skip_sunday():
    p = plan_project(date(2026, 12, 1), people={"designer": "Asha"})   # Tue
    brief = p["stages"][0]
    assert brief["start"] == "2026-12-01" and brief["end"] == "2026-12-05"   # 5 working days Tue-Sat
    assert p["stages"][1]["start"] == "2026-12-07"                           # Sunday skipped
    assert brief["tasks"][0]["owner"] == "Asha"
    assert len(client_approvals(p)) == 5


def test_plan_calendar_days():
    p = plan_project(date(2026, 12, 1), skip_sunday=False)
    assert p["stages"][0]["end"] == "2026-12-05" and p["stages"][1]["start"] == "2026-12-06"


def test_repeat_rules():
    assert next_due({"freq": "daily"}, date(2026, 12, 5)) == date(2026, 12, 7)          # Sat -> Mon
    assert next_due({"freq": "weekly", "days": [0, 3]}, date(2026, 12, 1)) == date(2026, 12, 3)
    assert next_due({"freq": "monthly", "month_day": 0}, date(2026, 12, 1)) == date(2026, 12, 31)
    assert next_due({"freq": "every_n", "every": 7, "until": "2026-12-05"}, date(2026, 12, 1)) is None
    assert describe({"freq": "monthly", "month_day": 2}) == "Every month on the 2nd"
    with pytest.raises(RuleError):
        check_rule({"freq": "weekly", "days": []})


def test_dependencies():
    graph = {"a": [], "b": ["a"], "c": ["b"]}
    check_deps("a", [], graph)
    with pytest.raises(DependencyError):
        check_deps("a", ["c"], graph)          # loop a -> c -> b -> a
    with pytest.raises(DependencyError):
        check_can_start("doing", [{"title": "Measure site"}])
