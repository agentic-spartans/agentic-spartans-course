# Full team

An orchestrator and five roles, one job each. You talk to the orchestrator; it calls each role in turn and reports back to you.

```
planner → you → implementer → reviewer → verifier → report-writer
                    ↑              │ NEEDS FIX  │ FAIL
                    └──────────────┴────────────┘
```

The planner plans the work and the checks the result must pass, and you approve both. The implementer makes the result, the reviewer lists fixes, the verifier checks the result against the approved checks, and the report writer writes your report. A NEEDS FIX or a FAIL sends the work back for a fix round.

## Run it

1. In OpenCode, open this folder (AgentTeams › clip03 › clip03_01_full-team), not AgentTeams.
2. Start a new chat for each task. Type `/do` followed by the full task.
3. Read the plan and its checks, and approve them or ask for changes.
4. Each run gets its own folder, `runs/run_1/`, `runs/run_2/` and so on: the result in `deliverable/`, the verifier's check in `logs/verification_report.md`, and your report as `report.docx`. Open the report in Word, fill in your judgment and notes, and hand it in.

## What is in the folder

The files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux.

- `opencode.json`: the model and what the agents may do.
- `.opencode/agents/`: one file per agent. `orchestrator.md` is empty on purpose: OpenCode needs an agent to start from, and its instructions live in `/do`.
- `.opencode/commands/do.md`: the saved prompt behind `/do`, the run order and the plan pause.
- `.opencode/agent_template.md`: copy it into `.opencode/agents/` to add an agent, and add a step for it in `do.md`.
- `AGENTS.md`: rules every agent reads (plain sentences, work only inside this folder, how to delete).
- `.opencode/plugins/run-cost-limit.js`: limits each chat and its agents to about $3. Calls already running can go over. Type `/add-dollar` in that chat to add $1 and continue. Helper agents start in the foreground, so Stop stops them too (unless you press Ctrl+B).
- `.opencode/plugins/delete-guard.js`: refuses deletes and moves outside this folder until you type `yes, delete <full path>`.
- `.opencode/plugins/report-docx.js` and `.opencode/vendor/`: turn `report.md` into `report.docx` inside OpenCode, so you install nothing.
- `tools/render_page.py`: lets the team look at a web page it made, the way a reader would. It needs Python and Playwright, so it matters only when your result is a web page.

These rules prevent accidents; they do not lock the agents in. Keep files you care about out of AgentTeams.
