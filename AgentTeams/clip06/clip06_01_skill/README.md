# Skill demo

One agent, the orchestrator, and one skill, `plant-card`. Ask how to care for a plant, without saying "plant card": the orchestrator looks it up on the web and answers with a plant card, because the skill's description fits the question.

## Run it

1. In OpenCode, open this folder (AgentTeams › clip06 › clip06_01_skill), not AgentTeams.
2. Ask, for example, "Tell me about snake plants." The chat shows the skill being loaded, then a three-line plant card.

## What is in the folder

The files that start with a dot are hidden: show them with Command + Shift + period on Mac, View › Show › Hidden items on Windows, or Ctrl + H on Linux.

- `opencode.json`: the model and what the agent may do. It can search and read the web and read this folder; it cannot change files or run commands.
- `.opencode/agents/orchestrator.md`: the agent you talk to.
- `.opencode/skills/plant-card/SKILL.md`: the skill. The agent sees only its name and description, and loads the rest when a question fits the description.
- `.opencode/plugins/run-cost-limit.js`: stops a run at $3; type `/add-dollar` to add $1 and continue.
