// Run cost limit: a backstop under the OpenRouter key's own limit.
// A run is one top-level OpenCode session plus every subagent session it starts; a new session starts a new run.
// When RESERVE_USD is left (at most half the limit), every agent is told to wrap up; at the limit model calls stop and a note is written
// in the run folder. The user's /add-dollar command adds $1 and continues the same run.
// Cost is OpenCode's own figure, checked before each model call; calls already running can overshoot a little.
// To change the limit, edit LIMIT_USD (or set OPENCODE_RUN_COST_LIMIT) and restart OpenCode.
import { existsSync, readdirSync, rmSync, writeFileSync } from "node:fs"
import { join, relative } from "node:path"

const LIMIT_USD = 3
const RESERVE_USD = 0.5 // enough for one verifier round and the report
const ADD_USD = 1
const ADD_MARKER = "[run-cost-limit:add-1]"
const NOTE = "COST_LIMIT_REACHED.md"
const fromEnv = Number(process.env.OPENCODE_RUN_COST_LIMIT)
const baseLimit = Number.isFinite(fromEnv) && fromEnv > 0 ? fromEnv : LIMIT_USD
const usd = (x) => `$${x.toFixed(x > 0 && x < 0.1 ? 3 : 2)}`

export default {
  id: "studio.run-cost-limit",
  async setup(ctx) {
    const directory = ctx.location?.directory ?? process.cwd()
    const parentOf = new Map() // session -> parent session ("" for a top-level session); successful lookups only
    const runs = new Map() // top-level session -> Promise<run>
    const queues = new Map() // top-level session -> last save, so saves for one run happen in order

    const getSession = (id) => ctx.session.get({ sessionID: id })

    async function rootOf(id) {
      const seen = new Set()
      while (!seen.has(id)) {
        seen.add(id)
        if (!parentOf.has(id)) parentOf.set(id, (await getSession(id)).parentID ?? "") // a failed lookup throws, uncached
        const parent = parentOf.get(id)
        if (!parent) return id
        id = parent
      }
      return id
    }

    function runOf(root) {
      if (!runs.has(root)) {
        const load = (async () => {
          const saved = await ctx.storage.get(`run:${root}`)
          const run = {
            sessions: [...new Set([root, ...(saved?.sessions ?? [])])],
            stopped: saved?.stopped === true,
            added: Number(saved?.added) || 0,
            before: saved?.before ?? runFolders(), // run folders that existed before this run began
            folder: saved?.folder ?? null, // this run's folder, claimed when it first appears
          }
          if (!saved) await ctx.storage.set(`run:${root}`, run)
          return run
        })()
        runs.set(root, load)
        load.catch(() => runs.delete(root))
      }
      return runs.get(root)
    }

    // Saves for one run happen one at a time; `change` is applied to the run only after its save succeeds.
    function update(root, run, change) {
      const next = (queues.get(root) ?? Promise.resolve()).catch(() => {}).then(async () => {
        const draft = structuredClone(run)
        if (change(draft) === false) return
        await ctx.storage.set(`run:${root}`, draft)
        Object.assign(run, draft)
      })
      queues.set(root, next)
      return next
    }

    async function spent(run) {
      const costs = await Promise.all(run.sessions.map(async (id) => (await getSession(id)).cost ?? 0))
      return costs.reduce((sum, cost) => sum + cost, 0)
    }

    const limitOf = (run) => baseLimit + run.added

    function runFolders() {
      const runsDir = join(directory, "runs")
      return existsSync(runsDir) ? readdirSync(runsDir).filter((n) => /^run_\d+$/.test(n)) : []
    }

    // The first runs/run_<k> made since this run began; checked before each model call, so a run
    // claims its folder before another session can make a later one.
    function newFolder(run) {
      const ks = runFolders().filter((n) => !run.before.includes(n)).map((n) => Number(n.slice(4)))
      return ks.length ? `runs/run_${Math.min(...ks)}` : null
    }

    const folderOf = (run) => join(directory, run.folder ?? ".")

    function stopNote(run, total) {
      const where = relative(directory, folderOf(run)) || "this folder"
      return [
        `This run stopped at its cost limit: ${usd(total)} spent of ${usd(limitOf(run))}.`,
        "Your answer may be unfinished or not checked.",
        `Next step: type /add-dollar to add ${usd(ADD_USD)} and continue this same run.`,
        "Or start a new session to begin a new run; it starts over and costs again.",
      ].join("\n")
    }

    const wrapUp = (run, total) =>
      `COST NOTICE: this run has used ${usd(total)} of its ${usd(limitOf(run))} limit. Wrap up now. ` +
      "Start no new searches. Give your answer from what you have now and say what is unchecked."

    async function check(sessionID) {
      const root = await rootOf(sessionID)
      const run = await runOf(root)
      await update(root, run, (r) => {
        const found = r.folder ? null : newFolder(r)
        if (r.sessions.includes(sessionID) && !found) return false
        if (!r.sessions.includes(sessionID)) r.sessions.push(sessionID)
        if (found) r.folder = found
      })
      return { root, run, total: await spent(run) }
    }

    const refuse = (text) => { throw new Error(text) }

    await ctx.session.hook("http.request", async (event) => {
      let state
      try {
        state = await check(event.sessionID)
      } catch (error) {
        refuse(`The run cost limit could not read this run's cost (${error?.message ?? error}). Try again in a moment, or start a new session.`)
      }
      const { root, run, total } = state
      if (!run.stopped && total < limitOf(run)) return
      // Decided in the run's save queue, so a grant made meanwhile is seen.
      let latched = false
      await update(root, run, (r) => {
        if (r.stopped || total < baseLimit + r.added) return false
        r.stopped = true
        latched = true
      }).catch(() => { run.stopped = true }) // a failed save still stops the run in memory
      if (!run.stopped) return
      const note = stopNote(run, total)
      if (latched) try { writeFileSync(join(folderOf(run), NOTE), `# Cost limit reached\n\n${note}\n`) } catch {}
      refuse(note)
    })

    await ctx.session.hook("context", async (event) => {
      try {
        const { run, total } = await check(event.sessionID)
        if (!run.stopped && total >= limitOf(run) - Math.min(RESERVE_USD, limitOf(run) / 2)) event.system.push({ type: "text", text: wrapUp(run, total) })
      } catch {} // the request gate refuses the call if the cost cannot be read
    })

    // /add-dollar: only the user's own message in a top-level session counts; agents' prompts go to subagent sessions.
    await ctx.session.hook("prompt", async (event) => {
      const text = String(event.prompt?.text ?? "").replace(/^["'\s]+/, "")
      if (!text.startsWith(ADD_MARKER) && !text.startsWith("/add-dollar")) return
      const root = await rootOf(event.sessionID)
      if (root !== event.sessionID) return
      const run = await runOf(root)
      await update(root, run, (r) => { r.added += ADD_USD; r.stopped = false })
      try { rmSync(join(folderOf(run), NOTE), { force: true }) } catch {}
      event.prompt.text += `\nRun folder: ${relative(directory, folderOf(run)) || "this folder"}.`
    })

    // Agents cannot grant budget: no /add-dollar from the shell, and no server password for shell commands.
    await ctx.shell.hook("create.before", (event) => {
      if (/add-dollar|run-cost-limit:add/.test(String(event.command ?? ""))) throw new Error("Only the user can add budget, by typing /add-dollar.")
      if (event.env && typeof event.env === "object") event.env.OPENCODE_SERVER_PASSWORD = ""
    })

    await ctx.tool.hook("execute.before", (event) => { if (event.tool === "subagent" && event.input?.background) event.input = { ...event.input, background: false } }) // subagents run in the foreground, so Stop on the main session stops them

    // An exhausted OpenRouter key (402) gets its own plain message, separate from the run limit.
    await ctx.session.hook("http.response", (event) => {
      if (event.response.status !== 402) return
      const message =
        "The OpenRouter key has used up its credit, so no AI calls can be made right now. This is not the run cost limit: " +
        "/add-dollar will not help. Ask your instructor for more credit, or wait for the key's limit to reset; then type: continue."
      event.response = new Response(JSON.stringify({ error: { message, code: 402 } }), {
        status: 402,
        headers: { "content-type": "application/json" },
      })
    })

    // Record each new subagent session under its run, so the run's cost includes it after a restart.
    const controller = new AbortController()
    ;(async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        if (event.type !== "session.created") continue
        const { sessionID, parentID } = event.data ?? {}
        parentOf.set(sessionID, parentID ?? "")
        if (parentID) await check(sessionID).catch(() => {}) // the request gate adds it otherwise
      }
    })().catch(() => {})
    return () => controller.abort()
  },
}
