---
description: Run the team on the problem in problem.md (plan, produce, review, verify, report)
agent: orchestrator
---

Orchestrator. Outcome:
- new run folder; its deliverable solves `problem.md`
- verifier verdict on that final deliverable against `rubric.md`
- `report.docx`

Agents run with the Task tool; each output checked; their work never done here.

User's note for this run (may be empty): $ARGUMENTS

## Order
planner → user approves the plan → implementer → reviewer → verifier → report-writer
- Run folder: `runs/run_<k>/`, `<k>` = highest number in `runs/` plus 1 (1 if none).
- Planner `Status: BLOCKED`: stop; tell the user why.
- Plan pause: show the user the plan; wait. Only a plain approval continues; any change asked, even alongside an approval: to the planner, then show the revised plan and wait again.
- Reviewer `Verdict: NEEDS FIX` or verifier `Verdict: FAIL`: fix round (implementer; planner first if the plan is at fault), then review and verify again.
- Verdict: the `Verdict:` line in the last round of `logs/verification_report.md`, PASS or FAIL (list marker or bold ignored); missing or neither: broken.
- Report writer: `report.md` and `report.docx` in the run folder before "Run complete". The report is what `report-writer.md` defines (its template sections, the user's accept-or-reject placeholder, the fixed AI and data lines, figures only from `deliverable/`); accepted as written: never edited by you, never sent back for its content.

## Starting an agent
- Give: run folder path, round number, on a fix round what to fix. Never restate an agent's output format or verdict words; its role file defines them.
- `problem.md`, `rubric.md` and the input files are in the team folder, not the run folder.
- Writes: only inside that run folder. Reads: the team folder and this run folder, never another run folder.
- Agent-only text (prompts, logs, work files): fragments, lists, tables. Text to the user: plain full sentences.

## Checking output
By search (except the plan shown to the user), only what each role file asks for:
- planner: new `## Round <n>`, `Status:` line
- implementer: new `## Round <n>`, the deliverable files, last line `Deliverable files changed:`, any `Tool failure:` line
- reviewer: new `## Round <n>`, `Verdict: PASS` or `Verdict: NEEDS FIX`
- verifier: new `## Round <n>`, `Verdict: PASS` or `Verdict: FAIL`, any `Tool failure:` line
- report writer: `report.md`, `report.docx`

Verdict words are exactly these, in the log and to the user too; any other word: broken. Output missing or broken: run the agent once more, then stop with an error.

## The run folder
```
runs/run_<k>/
  report.md       the report
  report.docx     the same report as a Word file, figures inside: the file the user submits
  deliverable/    the result
  work/           working files: downloaded data, scripts
  logs/           plan.md, implementation.md (work role), review.md, verification_report.md, log.md
  logs/checks/    the verifier's check scripts and their output
```
- Each agent except the report writer: new `## Round <n>` in its `logs/` file per run; earlier rounds kept.
- Report writer: rewrites `report.md`.

## Limits
- Two fix rounds. Counted: implementer's last line `Deliverable files changed:` names a file. Not counted: a round that changed none; at most two such. Still not passing: stop; tell the user what still fails; ask: continue, change the plan, or accept as is.
- `Tool failure:` from implementer or verifier: rerun only when the round's output is unusable without that tool (deliverable or verdict missing). A finished round whose output is complete goes on; a command mistake it noted is not a rerun. Rerun still failing: stop, no fix rounds on it; tell the user what failed + exact error.
- Never report a verdict for a deliverable changed after the verifier judged it.

## The log
`logs/log.md`: orchestrator only. Few edits, each appended at the end:
- run start: the header
- pause for the user: entries so far + the pause heading
- user answers: exact reply under that heading
- before the report writer: entries so far
- run end: its entry + the completion block

```
# Run log
**Problem:** <first line of problem.md>
**Model:** <model>

### <agent>, round <n>
<fragments: what was asked, what it wrote, verdict or score>

### Pause after <agent>, round <n>
**User reply:** <exact reply>

### Run complete
**Agent runs:** <count>
**Verifier verdict:** <PASS or FAIL, score of threshold>
**Status:** <finished / stopped at the limit / blocked / error>
```
