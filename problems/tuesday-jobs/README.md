# Pick a future by its Tuesday

Contributor: Spartan Agentic AI Studio, Michigan State University
Cartoon: An open diary on a desk seen from above, with a garden trowel, a wrench, a stick of chalk and a cup of coffee around it.
Run time: about 50 minutes per run
Run cost: about $0.71 per run
Model: GPT-6 Luna, high reasoning effort

## The problem

A job title makes you think about how respected the job is and who does it. What you actually live with is an ordinary working day, such as a Tuesday. This agent team lets you pick a job by diaries of its Tuesdays, built from moments such as dealing with something unexpected, before you see any job title.

![The eight boxes are the steps under "What the agent team does", in order. The orange box is the verifier's check.](sketch.png)

## What we want to find out

- What matters most to you in an ordinary workday?
- Which diary would you pick if you could not see the job title?
- What job is behind the diary you picked?

## What the agent team does

![The work moves from the planner to the diary writers, the moment scorers and the verifier. You approve the plan, rate the moments and pick a diary; a failed check goes back to the orchestrator.](team.png)

The orchestrator is the agent you talk to, and it gives every other agent one task. At the end you learn the job behind your diary and get a report.

- Step 1: The planner, an AI helper, writes the plan: the steps for this run and the checks its result must pass. It lists 10 moments: small parts of a workday, such as handling something unexpected. It also picks 50 different jobs so that each moment fits some of them. Each job gets a secret label, such as J13, so its name stays hidden from you.
- Step 2: You read the plan and approve it, or ask for changes. Then you look at the moments, not the jobs, and rate how much you like each one from 1 to 5. A 1 means you would rather not have it, and a 5 means you like it a lot.
- Step 3: Several diary writers, also AI helpers, work at once, each on a share of the jobs. Each invents a diary of an ordinary Tuesday in that job, about 150 words, never using a word of the job's name.
- Step 4: Several moment scorers work at once, each on a share of the diaries, and never see the job names. They find how relevant each of your 10 moments is in the diary, from 0 if it never happens to 5 if it clearly happens. This mark is about the diary, not about how much you like the moment. For each mark they copy the line from the diary that shows it.
- Step 5: The verifier checks the work of the diary writers and moment scorers against the three points under "What a good answer looks like". Work that fails goes back to be redone before you see any diary.
- Step 6: The team ranks the diaries by how well their moments match your ratings, as the next section explains. You read the best ones, shown only by their labels, and pick the Tuesday you like best.
- Step 7: Only now does the orchestrator tell you the job behind your diary. That is the job whose Tuesday you liked best, chosen before you knew what it was.
- Step 8: The report writer writes your report as a Word file: the task, the checks, the results and how the team worked. You add your own judgment.

## How the diaries are ranked and what it leaves out

- The team picks the rule and shows it with the best diaries. In our run, a diary's score was the average of its marks, where each moment counts as many times as your rating.
- A moment you rated 5 counts five times, and one you rated 2 counts twice. Pay, schooling and the place of the job do not count.
- AI invents every diary, so a diary shows what a Tuesday in that job could be like, not a real person's day.
- The three checks test the rules of this exercise, such as hidden job names and exact quotes. They do not test whether a diary is true to the job.

## What you need to run it

Nothing beyond OpenCode and the downloaded folder. A run stops when it has spent $3. To start small, as our tester did, change the 10 moments and 50 jobs in the task file to 5 and 25.

## What a good answer looks like

- No job name reaches you or the moment scorers before you pick.
- Every scored moment comes with a line copied word for word from its diary.
- Most moments show up in the diaries.

## What the team found

Our tester asked for a smaller run first: 5 moments and 25 jobs instead of 10 and 50. The run time and cost at the bottom of this page come from this smaller run.

- The moments were checking the schedule and messages first thing, talking a question through with a coworker, a stretch of focused work, handling something unexpected, and wrapping up the day. Our tester rated them 3, 2, 5, 4 and 4, so focused work mattered most.
- Our tester picked diary J13 by its label. Earlier, while looking into a failed check, our tester had asked to see the diary lines that held job titles. J13's marks were 5, 4, 5, 5 and 5, which gives 4.89 out of 5 when each mark counts as many times as that moment's rating. It ranked fourth of 25, and three diaries tied for first with 5 on every moment. All 25 scored between 3.9 and 5, because moments that nearly every job has cannot tell jobs apart.
- J13 was a journalist. For the first moment the scorers gave it a 5 and quoted "Tuesday morning began with the newsroom calendar, overnight messages, and a call to my editor about the neighborhood meeting."
- Every moment showed up in the diaries, so the third point was met. The first point was not: an early scoring round saw a diary that still held its job title. The verifier caught it, and the team threw that round away and had five new scorers redo it.
- The second point was not met either. The verifier found one copied line that did not match its diary word for word, and the team fixed it. Our tester chose not to have the verifier check again, so the team's last verdict stayed FAIL. Read our pick as a demonstration of how the team works, not as a checked result.
