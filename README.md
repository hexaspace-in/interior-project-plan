# interior-project-plan

Plan home-interior projects from a stage template, and run repeating and dependent tasks. Built for Indian practice: Mon–Sat working days, client sign-offs at each key stage.

- **Default template:** 7 stages and 30 tasks, taken from real turnkey projects. The stages are brief and measurement, concept, design development, BOQ approval, procurement and production, site execution, and handover. Each task has an owner role and a day offset. Five stages need the client's sign-off.
- **`plan_project(start)`** turns the template into dated stages and task due dates. It skips Sundays by default.
- **Repeat rules:** daily (Mon–Sat), weekly on chosen days, monthly on a date or the last working day, or every N days. Repeats run on a fixed schedule or after the last one is done, with an optional end date. `describe()` gives a plain-English summary of a rule.
- **Dependencies:** "can't start until X is done", with loop detection.

Templates are plain JSON, so you can edit them or bring your own (office fit-out, retail, villa).

## Install

```bash
pip install interior-project-plan
```

## Example

```python
from datetime import date
from interior_project_plan import plan_project, client_approvals, next_due, describe

plan = plan_project(date(2026, 12, 1), people={"designer": "Asha", "senior": "Ravi"})
plan["end"]                 # planned handover date
client_approvals(plan)      # [{'stage': 'brief', 'ask': 'Sign off the brief', 'due': '2026-12-05'}, ...]

rule = {"freq": "weekly", "days": [0, 3]}          # every Mon and Thu
describe(rule)                                      # 'Every Mon, Thu'
next_due(rule, date(2026, 12, 1))                   # date(2026, 12, 3)
```

## Contribute

New templates (modular kitchen only, office fit-out, renovation) are very welcome. Add a JSON file next to `default_template.json` with a test. See issues labelled `good first issue`.

## Licence

MIT. Maintained by [Hexaspace](https://hexaspace.in).
