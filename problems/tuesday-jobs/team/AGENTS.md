# Rules for every agent

- Talk to the user in plain, full sentences.
- Work only inside this team folder. Copy in any file you need, and leave results here.
- To see a web page you made as a reader would, run `python3 tools/render_page.py <page> --out <folder>`.
- Before installing a tool, say which and why. Install it for the user's account only, never with `sudo`.

## Deleting files

- Never move or overwrite anything outside this folder. Delete outside files only with the approval below. To remove a file you made, move it to `runs/<run>/trash/`.
- Orchestrator: if the user asks you to delete something outside this folder, say what and why, one item at a time, and ask them to type `yes, delete` followed by its full path. Other agents: if a delete is refused, tell the orchestrator and stop.
