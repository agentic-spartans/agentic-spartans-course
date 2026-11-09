# Simple team

Two agents. The writer finds web pages and writes a short brief with a link after each claim. The checker opens every link and marks each one DEAD, BLOCKED, WRONG or OK. You talk to the writer; the writer calls the checker.

## Run it

1. In OpenCode, open this folder (AgentTeams › clip02 › clip02_01_simple-team), not AgentTeams.
2. Check it works: ask "Hi! What agents are on this team?" The writer names itself and the checker.
3. Type `/do` and a topic, for example `/do today's 5 biggest news stories: for each, some detail, the date, and the link to the article`. Use public topics only.
4. If the checker flags something, the writer asks whether to fix it. Answer, then read `runs/run_<k>/brief.md`.

## What is in the folder

The files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux.

- `opencode.json`: the model and what the agents may do.
- `.opencode/agents/writer.md` and `checker.md`: one file per agent. The writer is `mode: primary`, the agent you talk to; the checker is `mode: subagent`, a helper only the writer starts, and it cannot edit anything.
- `.opencode/commands/do.md`: the saved prompt behind `/do`. Your topic goes where it says `$ARGUMENTS`; step 4 is where the writer stops to ask you.
- `AGENTS.md`: rules every agent reads (plain sentences, work only inside this folder, how to delete).
- `.opencode/plugins/run-cost-limit.js`: stops a run at $3; type `/add-dollar` to add $1 and continue. Helper agents start in the foreground, so Stop stops them too (unless you press Ctrl+B).
- `.opencode/plugins/delete-guard.js`: refuses deletes and moves outside this folder until you type `yes, delete <full path>`.

These rules prevent accidents; they do not lock the agents in. Keep files you care about out of AgentTeams.
