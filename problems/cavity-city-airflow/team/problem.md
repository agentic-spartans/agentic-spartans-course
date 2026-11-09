# Problem: wind-driven airflow in a city street canyon, from a general two-dimensional incompressible flow solver (mechanical engineering, fluid mechanics)

## Application
Wind blowing over the rooftops drives a recirculating vortex in the street between two buildings (a street canyon). The simplest model of it is the lid-driven cavity: the street and the two building walls form the cavity, and the wind above the roofs is the moving lid. This task builds a general solver, proves it correct on two cases with known answers, and shows the velocity field in a street 20 m wide between buildings 20 m tall.

The model is laminar and two-dimensional. A real street canyon at city wind speeds is turbulent (Reynolds number around 10^7); the laminar solution at Re = 100 shows the flow pattern (one vortex filling a canyon whose height equals its width), not the turbulent speeds. The deliverable states this.

## Task
1. Write a general two-dimensional incompressible laminar flow solver in Python, as the Model and Method sections prescribe. It reads one case file (format below) and runs that case; boundary conditions on each of the four sides come only from the case file.
2. Run the channel case and compare with the exact fully developed profile.
3. Run the cavity case and compare the centerline velocities with Ghia et al. (1982), supplied in `ghia1982_re100.csv`.
4. Show the cavity field as the street canyon and answer the questions under Street canyon.
5. Deliver the files listed under Deliverable. Runs have no internet.

## Model
Dimensionless incompressible Navier-Stokes equations, isothermal, continuity and x and y momentum only:
- du/dt + d(uu)/dx + d(uv)/dy = -dp/dx + (1/Re)(d2u/dx2 + d2u/dy2)
- dv/dt + d(uv)/dx + d(vv)/dy = -dp/dy + (1/Re)(d2v/dx2 + d2v/dy2)
- du/dx + dv/dy = 0

Lengths are scaled by a reference length L and velocities by a reference speed U (channel: the channel height and the inflow centerline speed; cavity: the cavity width and the lid speed), so Re = U L / nu. No temperature equation, no turbulence model.

## Method (prescribed)
1. Staggered (marker-and-cell) grid on a rectangle [0, Lx] x [0, Ly] with nx x ny uniform cells: pressure at cell centers, u on the vertical cell faces (nx+1 by ny values), v on the horizontal cell faces (nx by ny+1 values).
2. Fractional-step (Chorin projection) method, three steps per time step: (1) predict intermediate velocities from the convective and viscous terms without pressure, explicit in time; (2) solve the pressure Poisson equation whose right-hand side is the divergence of the intermediate velocity divided by the time step; (3) correct the velocities with the pressure gradient. Not SIMPLE, SIMPLER or PISO.
3. Second-order central differences for the convective and viscous terms.
4. Pressure Poisson equation solved iteratively: Gauss-Seidel, SOR (red-black ordering allowed) or conjugate gradient. Homogeneous Neumann conditions for pressure on every side (the normal velocity on every boundary is set before the solve and is not changed by the correction); the pressure level is fixed by any one constraint (for example zero mean).
5. Boundary conditions, per side, from the case file:
   - `wall` with a tangential `speed` (0 for a fixed wall, the lid speed for the moving lid; positive along +x on the bottom and top sides, along +y on the left and right sides): normal velocity zero.
   - `inflow` with a normal-velocity `profile`, a Python expression in `s`, the coordinate along that side (y on the left and right sides, x on the bottom and top), entering the domain; tangential velocity zero.
   - `outflow`: zero normal gradient of both velocity components, with one uniform correction of the outflow normal velocity so that the total outflow equals the total inflow at every step.
   - The tangential velocity at a wall or inflow side is imposed through a ghost value half a cell outside the boundary chosen so that the scheme is exact for a quadratic profile: ghost = (8 w - 6 q1 + q2)/3, where w is the boundary value and q1, q2 the first and second interior values next to that side. (The common reflection ghost = 2 w - q1 has a second-order error, so the channel cannot then meet its limit.)
6. Time step from the stability limits of the explicit scheme (viscous, including the stronger diagonal the quadratic ghost gives next to a wall, and convective); the code prints the time step and the rule it used.
7. Steady state. The residual of time step n is R_n = max over all u and v unknowns of |q^(n+1) - q^n| / dt (dimensionless). The run is steady when R_n falls below the case's `steady_tol` and stays below it for 200 further consecutive steps; it then stops.

## Case file format (JSON)
Keys: `name` (output prefix), `Lx`, `Ly`, `nx`, `ny`, `Re`, `steady_tol`, and `bc` with keys `left`, `right`, `bottom`, `top`, each an object `{"type": "wall", "speed": <number>}`, `{"type": "inflow", "profile": "<expression in s>"}` or `{"type": "outflow"}`. Example: `{"name": "channel", "Lx": 4.0, "Ly": 1.0, "nx": 80, "ny": 20, "Re": 100, "steady_tol": 1e-12, "bc": {"left": {"type": "inflow", "profile": "4*s*(1-s)"}, "right": {"type": "outflow"}, "bottom": {"type": "wall", "speed": 0}, "top": {"type": "wall", "speed": 0}}}`. Any physically admissible combination of the three side types must run the same way, with no change to the code: positive `Lx`, `Ly`, `Re` and `steady_tol`, integer `nx` and `ny` of at least 4, and, when no side is `outflow`, inflow profiles whose total flux is zero. The solver refuses any other case with a clear message (for example net inflow with no outflow side, for which no divergence-free field exists) rather than running it.

## Cases
| Case file | Domain Lx x Ly | Cells nx x ny | Re | Boundary conditions | steady_tol |
|---|---|---|---|---|---|
| `cases/channel.json` | 4 x 1 | 80 x 20 | 100 | left inflow `4*s*(1-s)`; right outflow; bottom and top fixed walls | 1e-12 |
| `cases/cavity.json` | 1 x 1 | 40 x 40 | 100 | top wall speed 1 (the lid, moving in +x); left, right, bottom fixed walls | 1e-6 |

Both start from rest (u = v = 0 in the interior).

## Known answers and how to compare
- Channel: the exact fully developed profile between two walls with speeds u_b (bottom) and u_t (top) that carries the flow rate of the inflow profile (its integral over the side) is u(y) = u_b + (u_t - u_b) y / H + G y (H - y), with G fixed by that flow rate; v = 0. Derive G and evaluate the exact profile at the u nodes. The task's inflow profile is itself this fully developed profile, so the steady solution equals it everywhere: compare at every u node of the domain and report the outlet column separately.
- Cavity: `ghia1982_re100.csv` holds Ghia, Ghia and Shin (1982), J. Comput. Phys. 48, 387-411, Tables I and II at Re = 100: columns `y,u_ghia` (u/U_lid on the vertical centerline x = 0.5) and `x,v_ghia` (v/U_lid on the horizontal centerline y = 0.5), 17 points each, including the wall values. With even nx and ny the u faces lie on x = 0.5 and the v faces on y = 0.5; take the solver's values at the Ghia coordinates by linear interpolation along that line, including the wall values (0 at fixed walls, 1 at the lid).
- Error norms over the points compared: L2 = sqrt((1/N) sum (q_i - q_ref,i)^2) and Linf = max |q_i - q_ref,i|.

## Acceptance limits
- Channel: |u - u_exact| <= 1e-12 at every u node and |v| <= 1e-12 at every v node.
- Both cases: maximum cell divergence |(u_e - u_w)/dx + (v_n - v_s)/dy| <= 1e-10 at steady state.
- Cavity: |solver - Ghia| <= 0.05 at each of the 17 points on each centerline.
- Both cases: the residual history shows R_n below the Cases table's `steady_tol` for the last 200 steps.

## Street canyon
Draw the cavity field as a street 20 m wide between buildings 20 m tall, wind over the roofs blowing in +x: streamlines or vectors over the speed (as a fraction of the rooftop wind speed), axes in metres, the vortex center marked. Answer, with numbers computed from the field:
1. Where is the center of the vortex (x and y, as fractions of the street width and in metres)? Use the minimum of the stream function psi (psi = 0 on the walls, u = dpsi/dy) over the cell corners.
2. How fast does the air move near street level compared with the rooftop wind: the largest |u| on the line y = 0.1 L, as a fraction of the lid speed?

## Deliverable (files in `runs/<run>/deliverable/`)
1. `solver.py`: `python3 solver.py <case.json> --out <dir>` runs one case and writes into `<dir>`: `<name>_fields.npz` (arrays `u` (nx+1, ny), `v` (nx, ny+1), `p` (nx, ny), and the case parameters), `<name>_residuals.csv` (columns `step,time,residual`, one row per time step), `<name>_run.json` (time step, steps, final residual, steps below `steady_tol` at the end, maximum divergence). Nothing in the code is specific to one case: no case names, no boundary types or values outside the case file.
2. `cases/channel.json`, `cases/cavity.json`: the two case files of the Cases table.
3. `postprocess.py`: `python3 postprocess.py --out <dir> --ghia ghia1982_re100.csv` reads the solver outputs in `<dir>` and writes there every table and figure below.
4. `channel_profile.csv`: `y,u_numerical,u_exact,error` at the outlet u column.
5. `cavity_centerlines.csv`: `line,coordinate,ghia,solver,difference`, 17 rows for `u_vertical` and 17 for `v_horizontal`.
6. `norms.csv`: `case,quantity,points,L2,Linf` for: channel u at the outlet, channel u at all nodes, cavity u on the vertical centerline, cavity v on the horizontal centerline.
7. `run_summary.csv`: per case: `case,nx,ny,Re,dt,steps,final_residual,steady_tol,steps_below_tol,max_divergence`.
8. `canyon_summary.csv`: `quantity,value,units` for the two Street canyon answers (vortex center in fractions and in metres; street-level speed fraction).
9. Figures (PNG, labeled axes with units or "dimensionless"): `fig_channel_validation.png` (numerical outlet u(y) over the exact profile), `fig_cavity_u_vertical.png` (u/U_lid against y, solver line and Ghia points), `fig_cavity_v_horizontal.png` (v/U_lid against x, same), `fig_residuals.png` (R_n against time, log scale, both cases, with each `steady_tol`), `fig_street_canyon.png`.
10. The fields, residual and run files of both cases in the deliverable folder itself (run with `--out` set to it).
11. `summary.md`, as short as it can be while answering every question: the commands that reproduce every file from the deliverable folder; a results table (the norms, the divergence and residual figures against the limits, the canyon answers); one line per assumption; the laminar-versus-turbulent limitation; data source and license of `ghia1982_re100.csv`; and a disclosure block: the exact line `Produced by AI (<model>)` once, with the model named, then the data used, each marked public or synthetic.

## Code
Python 3 with numpy, scipy and matplotlib (install any that are missing). Each case of the Cases table runs in under 5 minutes on a laptop; vectorized numpy, no Python loops over cells in the time loop. Every number in every output file is computed at run time from the case files and `ghia1982_re100.csv`.

## Data
`ghia1982_re100.csv`: values of the published tables of Ghia, Ghia and Shin (1982), numeric reference data cited with the paper. No other data.

## Scope of this team
The family of problems: two-dimensional incompressible laminar flow on a rectangle, solved with the method above (staggered grid, Chorin projection, explicit central differences, iterative pressure solver, quadratic-exact wall ghosts), in Python, each case running in a few minutes on a laptop.
- Varies: Reynolds number in the laminar range (Ghia et al. tabulate Re = 100, 400, 1000 and higher); domain size and aspect ratio (street height to width); grid size; any combination of fixed walls, moving walls, inflow and outflow on the four sides; street dimensions in the canyon view; the validation cases and their reference data, supplied with each task.
- Fixed: two dimensions, laminar, isothermal, the method, the deliverable structure (case files, solver, postprocessing, tables, figures, short summary), validation by velocity only.
- Not in scope: turbulence models, three dimensions, heat or pollutant transport.
- Example inside the scope that differs from this task: a deep street canyon twice as tall as it is wide (Lx = 1, Ly = 2) at Re = 100, with a channel whose flow enters through the bottom side and leaves through the top as its exact-solution check.
