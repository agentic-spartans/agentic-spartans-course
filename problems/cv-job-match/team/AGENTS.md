# Rules for every agent

- Talk to the user in plain, full sentences.
- Work only inside this team folder. Copy in any file you need, and leave results here.
- Write only the files your role may edit, also through the shell or a script.
- Before installing a tool, say which and why. Install it for the user's account only, never with `sudo`.

## Deleting files

- Never move or overwrite anything outside this folder. Delete outside files only when the user asks. To remove a file you made, move it to `runs/<run>/trash/`.
- Orchestrator: if the user asks you to delete something outside this folder, say what and why, one item at a time. Other agents: if a delete is refused, tell the orchestrator and stop.
