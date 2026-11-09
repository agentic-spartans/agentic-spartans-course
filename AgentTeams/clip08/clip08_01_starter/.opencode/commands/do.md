---
description: Run the team on the task you type after /do (plan, produce, review, verify, report)
agent: orchestrator
---
The user's task: $ARGUMENTS

1. Have the planner plan the task and the checks the result must pass. Show the user the plan and wait; change it as the user asks.
2. Have the implementer carry out the plan.
3. Have the reviewer, then the verifier, check the result. On `NEEDS FIX` or `FAIL`, have the implementer fix it and check again. When a fix changes nothing, ask the user: continue, change the plan, or accept the result.
4. Have the report writer write the report.

- Tell each agent its task and the full path where to save it. Never do an agent's work yourself.
- Keep everything in `runs/run_<k>` (k = highest number in `runs/` plus 1, or 1): the result in `deliverable/`, each agent's notes in `logs/`, and each step and the user's exact replies in `logs/log.md`.
