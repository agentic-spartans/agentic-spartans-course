---
# Copy this file into .opencode/agents/ as <agent-name>.md, fill it in, and add a step for it in .opencode/commands/do.md.
description: "One line on what your agent does."
mode: subagent
# edit: the one file this agent may write.
permission:
  edit:
    "*": deny
    "runs/*/logs/<your-file>": allow
  task: deny
color: "#06B6D4"
---

[Who this agent is and what it delivers.]

[Its file: a new `## Round <n>` in `logs/<your-file>` each time it runs.]

[Its limits.]
