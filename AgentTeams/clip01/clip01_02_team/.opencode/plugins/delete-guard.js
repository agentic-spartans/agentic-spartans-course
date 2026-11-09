// Delete guard: a shell or patch call that deletes or moves files outside the team folder is refused until the
// user types "yes, delete <path>" in the chat; the yes covers one call. Inside the team folder and the temp folders nothing changes.
import { existsSync, realpathSync } from "node:fs"
import { homedir, tmpdir } from "node:os"
import { dirname, resolve, sep } from "node:path"
const DELETE = /^(rm|rmdir|unlink|shred|srm|trash|mv|remove-item|ri|del|erase|rd|move|move-item|mi)$/i
const PREFIX = /^(sudo|doas|command|builtin|exec|nohup|time|nice|env|xargs)$/i
const SHELLS = /^(bash|sh|zsh|dash|cmd|pwsh|powershell)(\.exe)?$/i
const TTL_MS = 30 * 60 * 1000 // how long a typed "yes, delete" stays valid
function real(p) { // realpath of the nearest existing ancestor, so links and not-yet-existing names resolve
  let q = p
  while (!existsSync(q) && dirname(q) !== q) q = dirname(q)
  try { return realpathSync(q) + p.slice(q.length) } catch { return p }
}
const within = (p, root) => p === root || p.startsWith(root.endsWith(sep) ? root : root + sep)
const absolute = (cwd, p) => real(resolve(cwd, p.replace(/^~(?=$|[\\/])/, homedir())))
function parts(command) { // split at shell operators outside quotes, so a quoted "a & b.pdf" stays one word
  const out = []; let cur = "", q = ""
  for (let i = 0; i < command.length; i++) {
    const c = command[i], two = command.slice(i, i + 2)
    if (c === "\\" && q !== "'") { cur += two; i++; continue } // an escaped character is never an operator: find's \( \) \;
    if (q === '"' && (two === "$(" || c === "`")) { out.push(cur); cur = ""; q = ""; if (two === "$(") i++; continue } // a substitution runs even inside double quotes; read its body unquoted
    if (q) { cur += c; if (c === q) q = ""; continue }
    if (c === '"' || c === "'") { q = c; cur += c; continue }
    if (two === "&&" || two === "||" || two === "$(") { out.push(cur); cur = ""; i++; continue }
    if (";|&\n()`".includes(c)) { out.push(cur); cur = ""; continue }
    cur += c
  }
  return [...out, cur]
}
const words = (s) => (s.match(/"[^"]*"|'[^']*'|\S+/g) ?? []).map((w) => w.replace(/^(["'])([\s\S]*)\1$/, "$2"))
function targets(command, cwd, out = []) { // { path } per delete or move argument; { raw } when it cannot be resolved
  for (const part of parts(command)) {
    let w = words(part.trim())
    while (w.length && (PREFIX.test(w[0]) || /^\w+=/.test(w[0]))) w = w.slice(1)
    const verb = (w[0] ?? "").replace(/^.*[\\/]/, "")
    if (/^(cd|pushd|chdir|set-location|sl)$/i.test(verb) && w[1]) cwd = absolute(cwd, w[1])
    if (SHELLS.test(verb)) { const i = w.findIndex((a) => /^([-/]c|-command)$/i.test(a)); if (i > 0) targets(w.slice(i + 1).join(" "), cwd, out) }
    const base = (x) => (x ?? "").replace(/^.*[\\/]/, "")
    const find = verb === "find" && w.some((a, i) => a === "-delete" || (/^-exec(dir)?$/.test(a) && DELETE.test(base(w[i + 1]))))
    if (!DELETE.test(verb) && !find) continue
    let args = w.slice(1)
    if (find) { // search roots: after find's own options (-H -L -P -E -X -d -s -x -O3, -D x, -f root), before the first expression
      const roots = []
      let i = 1
      for (; i < w.length; i++) {
        if (/^-([HLPEXdsx]|O\d*)$/.test(w[i])) continue
        if (w[i] === "-D") { i++; continue }
        if (w[i] === "-f") { roots.push(w[++i] ?? "."); continue }
        break
      }
      while (i < w.length && !/^(-|\\?\(|!)/.test(w[i])) roots.push(w[i++])
      args = roots.length ? roots : ["."]
      w.forEach((a, j) => { // operands of -exec rm/mv are targets too; {} stands for what find found under the roots
        if (!/^-exec(dir)?$/.test(a) || !DELETE.test(base(w[j + 1]))) return
        for (let k = j + 2; k < w.length && !/^(;|\\;|\+)$/.test(w[k]); k++) if (!w[k].includes("{}")) args.push(w[k])
      })
    }
    for (const a of args.filter((a) => !a.startsWith("-") && !(process.platform === "win32" && /^\/\w$/.test(a))))
      out.push(/[$%]/.test(a) ? { raw: a } : { path: absolute(cwd, a.replace(/[\\/]?[^\\/]*[*?[].*$/, "") || ".") })
  }
  return out
}
export default {
  id: "studio.delete-guard",
  async setup(ctx) {
    const team = real(ctx.location?.directory ?? process.cwd())
    const temp = [real(tmpdir()), real("/tmp")] // files inside temp folders pass; the folders themselves do not
    const approved = new Map() // path -> expiry; set only by the user, used by one call
    const grant = (text) => { for (const m of String(text).matchAll(/^["'\s]*yes,?\s+delete\s+(.+?)["'\s]*$/gim))
      approved.set(absolute(team, m[1].replace(/^(["'`])(.*)\1$/, "$2")), Date.now() + TTL_MS) }
    await ctx.session.hook("prompt", async (event) => { // agents' prompts go to subagent sessions, so only top-level ones count
      if (!(await ctx.session.get({ sessionID: event.sessionID })).parentID) grant(event.prompt?.text ?? "")
    })
    await ctx.tool.hook("execute.after", (event) => { // the user's typed answer to the writer's question box
      if (event.tool === "question" && event.status === "completed") grant((event.result.metadata?.answers ?? []).flat().join("\n"))
    })
    await ctx.tool.hook("execute.before", (event) => {
      const input = event.input ?? {}
      const found = event.tool === "shell" ? targets(String(input.command ?? ""), absolute(team, String(input.workdir ?? ".")))
        : event.tool === "patch" ? [...String(input.patchText ?? "").matchAll(/^\*\*\* (?:Delete File|Move to): (.+)$/gm)].map((m) => ({ path: absolute(team, m[1].trim()) }))
        : []
      const pass = (p) => within(p, team) || temp.some((t) => p !== t && within(p, t))
      const granted = (p) => [...approved].find(([a, t]) => t > Date.now() && within(p, a))?.[0]
      const bad = [...new Set(found.filter((t) => t.raw || !(pass(t.path) || granted(t.path))).map((t) => t.raw ?? t.path))]
      if (!bad.length) for (const t of found) if (!pass(t.path)) approved.delete(granted(t.path))
      if (bad.length) throw new Error(`Refused: this deletes or moves files outside the team folder: ${bad.join(", ")}. ` +
        "Do not try another way (no script, no other command). If the user did not ask for this, work inside the team folder and move " +
        "unwanted files to runs/<run>/trash/. If they did: the checker reports this to the writer and stops; the writer tells the user " +
        "in plain words what it wants to delete and why, asks them to type exactly \"yes, delete <full path>\", and retries only after that. " +
        "Write paths out in full; a variable such as $HOME or %USERPROFILE% cannot be checked.")
    })
  },
}
