---
description: Write a short brief with real sources on the topic you add.
agent: writer
---
Topic and the user's note: $ARGUMENTS
1. Make the run folder `runs/run_<k>` (k = highest number in `runs/` plus 1, or 1). Log each step in `runs/run_<k>/logs/log.md`.
2. Write the brief in `runs/run_<k>/brief.md`.
3. Have the checker check every link, once.
4. If the checker flagged anything, show the user and ask whether to fix it, unless their note already says.
5. Fix once. Do not check again.
6. Tell the user what changed and where the brief is, and stop.
