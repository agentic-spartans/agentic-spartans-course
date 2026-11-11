# Starter team

The team to copy for your own project. You talk to the orchestrator; it gives each agent its task, one job each, and reports back to you.

```
planner → you → implementer → reviewer → verifier → report-writer
                    ↑              │ NEEDS FIX  │ FAIL
                    └──────────────┴────────────┘
```

The planner plans the work and the checks the result must pass, and you approve both. The implementer makes the result, the reviewer lists fixes, the verifier checks the result against the approved checks, and the report writer writes your report. A NEEDS FIX or a FAIL sends the work back for a fix.

## Make it yours

1. Copy this folder, paste the copy next to the original, in `clip08`, and give the copy your project's name.
2. The agents are in `.opencode/agents/`. Files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux. Keeping every agent is fine. If you delete one, also take its step out of `.opencode/commands/do.md`, which lists each agent's step, or ask the team to make both changes. Add an agent only when a job needs a different one: copy an agent file and rename it (or copy `.opencode/agent_template.md`), and add its step to `do.md`.
3. Write your project's details (what to make, how many, what you decide) in a task file in the folder, such as `my_task.md`.

## Run it

1. In OpenCode, open your team folder, not AgentTeams.
2. Start a new chat for each run. Type `/do Read my_task.md.` (or the full task after `/do`).
3. Read the plan and its checks, and approve them or ask for changes.
4. Each run gets its own folder, `runs/run_1/`, `runs/run_2/` and so on: the result in `deliverable/`, each agent's notes in `logs/`, and your report as `report.docx`. Open the report in Word, fill in your judgment and notes, then hand in your whole team folder as the Final project folder says.

## What is in the folder

- `opencode.json`: the model and what the agents may do. Agents may read and write anything in this folder; anything outside it asks first.
- `.opencode/agents/`: one short file per agent: what it does, and its job in one line. `orchestrator.md` is empty on purpose: its instructions live in `/do`.
- `.opencode/commands/do.md`: the saved prompt behind `/do`, the run order and the plan pause.
- `.opencode/agent_template.md`: copy it into `.opencode/agents/` to add an agent.
- `AGENTS.md`: rules every agent reads (plain sentences, work only inside this folder, how to delete).
- `.opencode/plugins/run-cost-limit.js`: limits each chat and its agents to about $3. Calls already running can go over. Type `/add-dollar` in that chat to add $1 and continue. Helper agents start in the foreground, so Stop stops them too (unless you press Ctrl+B).
- `.opencode/plugins/report-docx.js` and `.opencode/vendor/`: turn `report.md` into `report.docx` inside OpenCode, so you install nothing.
- `tools/render_page.py`: lets the team look at a web page it made, the way a reader would. It needs Python and Playwright, so it matters only when your result is a web page.

These rules prevent accidents; they do not lock the agents in. Put your project's files inside your copy, and keep a backup copy of them elsewhere.
