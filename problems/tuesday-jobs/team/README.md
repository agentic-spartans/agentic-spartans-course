# Tuesday jobs team

Picks a future by what an ordinary Tuesday in a job is like. You talk to the orchestrator; it gives each agent its task, one job each, and reports back to you.

```
planner → you → diary writers → moment scorers → verifier → you → report writer
```

The planner writes the plan and its checks, and you approve both. Then you rate the moments, several diary writers write a Tuesday diary for each job, several moment scorers score how clearly each moment shows in each diary without seeing the job names, and the verifier checks the work against the approved checks. You pick your favorite diary, and the orchestrator tells you which job it is. The report writer then writes your report.

## Run it

1. In OpenCode, open this team folder, not AgentTeams.
2. Start a new chat for each run. Type `/do Read task.md.`
3. Read the plan and its checks, and approve them or ask for changes.
4. Rate the moments, then pick your favorite diary.
5. Each run gets its own folder, `runs/run_1/`, `runs/run_2/` and so on: the result in `deliverable/`, each agent's notes in `logs/`, and your report as `report.docx`. Open the report in Word, fill in your judgment and notes, and hand it in.

Run small first: in `task.md`, change the 10 moments and 50 jobs to 5 and 25.

## What is in the folder

The files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux.

- `task.md`: the task and its three checks. Edit it to change what a run does.
- `opencode.json`: the model and what the agents may do. Agents may read and write anything in this folder; anything outside it asks first.
- `.opencode/agents/`: one short file per agent. `orchestrator.md` is empty on purpose: its instructions live in `/do`.
- `.opencode/commands/do.md`: the saved prompt behind `/do`, the run order and the plan pause.
- `AGENTS.md`: rules every agent reads.
- `.opencode/plugins/run-cost-limit.js`: limits each chat and its agents to about $3. Calls already running can go over. Type `/add-dollar` in that chat to add $1 and continue. Helper agents start in the foreground, so Stop stops them too (unless you press Ctrl+B).
- `.opencode/plugins/report-docx.js` and `.opencode/vendor/`: turn `report.md` into `report.docx` inside OpenCode, so you install nothing.
- `.opencode/agent_template.md` and `tools/render_page.py`: from the starter team; this team does not use them.

These rules prevent accidents; they do not lock the agents in. Keep files you care about out of AgentTeams.
