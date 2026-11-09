# Make your own skill

One agent, the orchestrator, and no skills yet. You make the first one.

## Run it

1. In OpenCode, open this folder (AgentTeams › clip06 › clip06_02_make-skill), not AgentTeams.
2. Do a task once with the orchestrator, for example "Tell me about a peace lily. Look it up and answer in three lines. Is it good for pets? What is the requirement for light and for water? And give me a link."
3. Say "Save this to a project level skill and name it Plant Info." It writes a new folder in `.opencode/skills/` with a SKILL.md inside. Read it.
4. Test it: start a new session and ask "Tell me about snake plants." without naming the skill. The chat shows the skill being loaded.

## What is in the folder

The files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux.

- `opencode.json`: the model and what the agent may do. It can search and read the web and read this folder; it can write only inside `.opencode/skills/`, and it cannot run commands.
- `.opencode/agents/orchestrator.md`: the agent you talk to.
- `.opencode/skills/`: empty until you make a skill.
- `.opencode/plugins/run-cost-limit.js`: stops a run at $3; type `/add-dollar` to add $1 and continue.
