# Wind in a city street

Contributor: Spartan Agentic AI Studio, Michigan State University
Cartoon: Two city buildings seen from the side, with wind blowing over their roofs and a large swirl of air turning between them in the street below.
Run time: about 85 minutes per run
Run cost: about $0.38 per run
Model: GPT-6 Luna, high reasoning effort

## The problem

City planners want to know how air moves in a street between two tall buildings, because the air carries fumes and heat. We picture the street from the side as a square of air, 20 meters on each side, a box whose moving lid is the wind (engineers say lid-driven cavity). The agent team writes a program that computes how fast the air moves everywhere in that square.

![Wind U blows over the roofs and turns a swirl of air, or vortex, in the street, with its center at the star. W is the street width and H the building height, both 20 meters, and the dashed line at 0.1 H is 2 meters up.](sketch.png)

## What we want to find out

- Where is the center of the swirl, in meters from the left building and above the ground?
- How fast does the air move sideways 2 meters above the street, as a share of the roof wind speed?
- Does the program reproduce two known answers, for air pushed between two flat plates (channel flow) and for the box with a moving lid?

## What the agent team does

![You talk to the orchestrator, and you approve the plan from the planner before the implementer starts. The reviewer and verifier send problems back to the implementer, and the report writer sends you the report.](team.png)

The implementer, the agent that writes code, writes the program and runs it on the street and both known cases. The reviewer reads the code, and the verifier runs it again to test the answers. You get the program, its tables and pictures, a short summary with the commands that rebuild them, and a Word report from the report writer.

## What the calculation leaves out

- The program treats the air as calm and slow, so the swirl settles into one steady pattern.
- Engineers rate this with the Reynolds number: low means smooth, or laminar, and high means gusty, or turbulent. Ours is 100, and real city wind is near 10 million.
- So our results show the shape of the swirl, not the real speeds in a street.

## What you need to run it

A run stops when it has spent $3.

## What a good answer looks like

- When the verifier runs the program again, it matches both known answers. Between the plates it matches the exact answer to twelve decimal places. In the lid box, its speeds stay within 5 percent of the lid speed from the values Ghia, Ghia and Shin published in 1982. No grid square may gain or lose air: its divergence stays below one ten-billionth. The speeds must stop changing: the residual, their largest rate of change, stays below one trillionth between the plates and one millionth in the lid box for 200 steps. A program that gets two known answers right is more likely to be right about the street, whose answer nobody knows.
- The program follows the method we set and solves new boxes without changes to its code. It cuts the box into small squares, with pressure at each center and air speeds on the edges (a staggered grid). Each time step moves the air, then corrects the pressure so no air piles up in a square (Chorin's projection method).
- Every question is answered by a picture or table that the program made, with labeled axes. The verifier computes the swirl center and the speed at 2 meters on its own and gets the same values.
- The team's summary lists what to type to rebuild every result and names where the 1982 values come from. It says that real streets are turbulent and that AI did the work.

## What the team found

The pictures and numbers come from our sample run. The verifier passed it, and our own later check confirmed every answer below. That check also found two small flaws that change none of them. In a test box whose open sides all have speeds you set, with no free exit, the program slightly changes those speeds. One row of the team's summary also loses its number.

- The swirl center sits 12.5 meters from the left building and 15 meters above the ground (the lowest point of the stream function, a measure of the air's path). That is high in the street and a little toward the right building, the way the wind blows.
- At 2 meters up, the fastest sideways air moves at 6.35 percent of the roof wind speed. It flows against the roof wind, from right to left, because the bottom of the swirl turns the other way.
- Both known answers matched. Between the plates, the program matched the exact answer to thirteen decimal places. In the lid box, its largest gap from the 1982 values was 0.87 percent of the lid speed, well inside the 5 percent limit.

![Color shows air speed as a share of the roof wind, white lines trace the air's path, and the dot marks the fastest air on the line 2 meters up. Redrawn from the sample's saved data for phone reading.](sample_1.png)

![The program's sideways speed up the middle of the lid box, the line, matches the 1982 values, the dots, from the floor at 0 to the lid at 1. Redrawn from the sample's saved data for phone reading.](sample_2.png)
