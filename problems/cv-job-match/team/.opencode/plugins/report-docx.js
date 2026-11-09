// Word report without pandoc: adds the tool make_report_docx, which turns a run's report.md into report.docx
// inside OpenCode itself (its own JavaScript runtime and the vendored docx library), so the user installs nothing.
// Handles what report-writer.md asks for: headings, paragraphs with bold, italic, code and links, $math$ as plain
// text with sub- and superscripts, numbered and bulleted lists, pipe tables with a "Table:" caption, figures
// ![caption](path) from the run folder (PNG or JPEG), and code blocks. Tables and figures are numbered in order.
import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs"
import { isAbsolute, join, relative, resolve, sep } from "node:path"
import {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, HeadingLevel, ImageRun, LevelFormat, Packer,
  Paragraph, Table, TableCell, TableRow, TextRun, WidthType,
} from "../vendor/docx.mjs"

const MAX_WIDTH_PX = 576 // 6 inches at 96 pixels per inch
const FONT = "Calibri"
const schema = (json) => ({ "~standard": { version: 1, vendor: "studio", validate: (value) => ({ value }),
  jsonSchema: { input: () => json, output: () => json } } })

function imageSize(buf) { // width and height from a PNG or JPEG header
  if (buf.readUInt32BE(0) === 0x89504e47) return { type: "png", w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }
  if (buf[0] === 0xff && buf[1] === 0xd8) {
    for (let i = 2; i < buf.length - 9;) {
      if (buf[i] !== 0xff) { i++; continue }
      const marker = buf[i + 1], len = buf.readUInt16BE(i + 2)
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker))
        return { type: "jpg", w: buf.readUInt16BE(i + 7), h: buf.readUInt16BE(i + 5) }
      i += 2 + len
    }
  }
  return null
}

function mathRuns(tex, style) { // LaTeX between dollar signs, shown as plain text with sub- and superscripts
  const text = tex.replace(/\\(min|max|log|ln|exp|sin|cos|tan)\b/g, "$1").replace(/\\(left|right|,|;|!)/g, "")
    .replace(/\\(?:cdot|times)/g, "×").replace(/\\leq?/g, "≤").replace(/\\geq?/g, "≥").replace(/\\neq/g, "≠")
    .replace(/\\approx/g, "≈").replace(/\\pm/g, "±").replace(/\\infty/g, "∞").replace(/\\(?:frac)\{([^}]*)\}\{([^}]*)\}/g, "($1)/($2)")
    .replace(/\\([a-zA-Z]+)/g, (m, name) => GREEK[name] ?? name)
  const runs = []
  for (const m of text.matchAll(/([_^])(\{[^}]*\}|.)|([^_^]+)/g)) {
    if (m[3]) runs.push(new TextRun({ ...style, text: m[3], italics: true }))
    else runs.push(new TextRun({ ...style, text: m[2].replace(/^\{|\}$/g, ""), italics: true, subScript: m[1] === "_", superScript: m[1] === "^" }))
  }
  return runs
}
const GREEK = { alpha: "α", beta: "β", gamma: "γ", delta: "δ", Delta: "Δ", epsilon: "ε", theta: "θ", lambda: "λ", mu: "μ",
  nu: "ν", pi: "π", rho: "ρ", sigma: "σ", Sigma: "Σ", tau: "τ", phi: "φ", omega: "ω", Omega: "Ω" }

function inline(text, style = {}) { // **bold**, *italic*, `code`, [text](url), $math$
  const out = []
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\$([^$]+)\$/g
  let last = 0
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push(new TextRun({ ...style, text: text.slice(last, m.index) }))
    if (m[1] !== undefined) out.push(...inline(m[1], { ...style, bold: true }))
    else if (m[2] !== undefined) out.push(...inline(m[2], { ...style, italics: true }))
    else if (m[3] !== undefined) out.push(new TextRun({ ...style, text: m[3], font: "Consolas" }))
    else if (m[4] !== undefined) out.push(new ExternalHyperlink({ link: m[5], children: [new TextRun({ ...style, text: m[4], style: "Hyperlink" })] }))
    else out.push(...mathRuns(m[6], style))
    last = m.index + m[0].length
  }
  if (last < text.length) out.push(new TextRun({ ...style, text: text.slice(last) }))
  return out
}

const cells = (line) => line.trim().replace(/^\|/, "").replace(/(?<!\\)\|$/, "").split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, "|"))
const rule = { style: BorderStyle.SINGLE, size: 4, color: "999999" }
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }

function table(rows) { // header row bold; a thin line under every row, none at the sides
  const cols = rows[0].length
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: rule, bottom: rule, left: none, right: none, insideHorizontal: rule, insideVertical: none },
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: Array.from({ length: cols }, (_, j) => new TableCell({
        children: [new Paragraph({ children: inline(r[j] ?? "", i === 0 ? { bold: true } : {}) })],
      })),
    })),
  })
}

function convert(markdown, folder) {
  const lines = markdown.replace(/\r\n?/g, "\n").split("\n")
  const body = []
  let tables = 0, figures = 0, listId = 0
  const caption = (label, n, text) => new Paragraph({ children: [new TextRun({ text: `${label} ${n}. `, bold: true }), ...inline(text)], spacing: { after: 200 } })
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (!line.trim()) continue
    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    if (heading) {
      const level = [HeadingLevel.TITLE, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3][heading[1].length - 1]
      body.push(new Paragraph({ heading: level, children: inline(heading[2]) }))
      continue
    }
    if (/^```/.test(line)) {
      for (i++; i < lines.length && !/^```/.test(lines[i]); i++)
        body.push(new Paragraph({ children: [new TextRun({ text: lines[i], font: "Consolas", size: 18 })], spacing: { after: 0 } }))
      continue
    }
    const image = line.match(/^!\[([^\]]*)\]\((?:<([^>]+)>|([^)\s]+))\)\s*$/)
    if (!image && /^!\[/.test(line)) throw new Error(`Figure line not understood (write ![caption](deliverable/file.png)): ${line.trim()}`)
    if (image) {
      const path = image[2] ?? image[3]
      const file = resolve(folder, path)
      const root = realpathSync(folder)
      if (!existsSync(file) || !(realpathSync(file) + sep).startsWith(root + sep)) throw new Error(`Figure not found inside the run folder: ${path}`)
      const data = readFileSync(file)
      const size = imageSize(data)
      if (!size) throw new Error(`Figure is not a PNG or JPEG: ${path}`)
      const scale = Math.min(1, MAX_WIDTH_PX / size.w)
      body.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true,
        children: [new ImageRun({ type: size.type, data, transformation: { width: Math.round(size.w * scale), height: Math.round(size.h * scale) } })] }))
      body.push(caption("Figure", ++figures, image[1]))
      continue
    }
    if (/^\s*\|/.test(line)) {
      const rows = []
      const header = i
      for (; i < lines.length && /^\s*\|/.test(lines[i]); i++) {
        const row = cells(lines[i])
        if (i === header + 1 && row.every((c) => /^:?-+:?$/.test(c))) continue // the delimiter row, only right under the header
        if (rows.length && row.length !== rows[0].length) throw new Error(`Table row has ${row.length} cells, the header has ${rows[0].length}: ${lines[i].trim()}`)
        rows.push(row)
      }
      let j = i
      while (j < lines.length && !lines[j].trim()) j++
      const cap = lines[j]?.match(/^Table:\s*(.*)$/)
      if (cap) { body.push(caption("Table", ++tables, cap[1])); i = j } else i--
      body.push(table(rows))
      body.push(new Paragraph({ children: [] }))
      continue
    }
    const tableCap = line.match(/^Table:\s*(.*)$/) // a caption written above its table
    if (tableCap) { body.push(caption("Table", ++tables, tableCap[1])); continue }
    const item = line.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/)
    if (item) {
      const numbered = /\d/.test(item[2])
      const ref = numbered ? `numbers${++listId}` : "bullets"
      let last = null
      for (; i < lines.length; i++) {
        const m = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/)
        if (m && /\d/.test(m[2]) === numbered) {
          last = { level: Math.min(2, Math.floor(m[1].length / 2)), text: m[3] }
          body.push(last)
          continue
        }
        if (!m && last && /^\s+\S/.test(lines[i])) { last.text += " " + lines[i].trim(); continue } // an indented continuation line
        let k = i
        while (k < lines.length && !lines[k].trim()) k++
        const next = lines[k]?.match(/^(\s*)([-*+]|\d+[.)])\s+/)
        if (k > i && next && /\d/.test(next[2]) === numbered) { i = k - 1; continue } // blank lines inside one list
        i--
        break
      }
      for (let k = body.length - 1; k >= 0 && !(body[k] instanceof Paragraph || body[k] instanceof Table); k--)
        body[k] = new Paragraph({ numbering: { reference: ref, level: body[k].level }, children: inline(body[k].text) })
      continue
    }
    const para = [line.trim()]
    while (i + 1 < lines.length && lines[i + 1].trim() && !/^(#|```|!\[|\s*\||\s*([-*+]|\d+[.)])\s|Table:)/.test(lines[i + 1])) para.push(lines[++i].trim())
    body.push(new Paragraph({ children: inline(para.join(" ")), spacing: { after: 160 } }))
  }
  const level = (format, text, n) => ({ level: n, format, text, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360 * (n + 1), hanging: 260 } } } })
  return new Document({
    styles: { default: { document: { run: { font: FONT, size: 22 } } } },
    numbering: { config: [
      { reference: "bullets", levels: [0, 1, 2].map((n) => level(LevelFormat.BULLET, "•", n)) },
      ...Array.from({ length: listId }, (_, k) => ({ reference: `numbers${k + 1}`, levels: [0, 1, 2].map((n) => level(LevelFormat.DECIMAL, `%${n + 1}.`, n)) })),
    ] },
    sections: [{ children: body }],
  })
}

export default {
  id: "studio.report-docx",
  async setup(ctx) {
    const team = ctx.location?.directory ?? process.cwd()
    await ctx.tool.transform((t) => t.add({
      name: "make_report_docx",
      description: "Turns a run's report.md into report.docx in the same folder, figures inside. Give the run folder, e.g. runs/run_3.",
      options: { codemode: false },
      input: schema({ type: "object", properties: { run_folder: { type: "string", description: "The run folder, e.g. runs/run_3" } }, required: ["run_folder"], additionalProperties: false }),
      output: schema({ type: "string" }),
      execute: async ({ run_folder }) => {
        const folder = resolve(team, run_folder)
        const rel = existsSync(folder) ? relative(realpathSync(team), realpathSync(folder)) : ".."
        if (!rel || isAbsolute(rel) || rel === ".." || rel.startsWith(".." + sep)) throw new Error("The run folder must be an existing folder inside the team folder.")
        const source = join(folder, "report.md")
        if (!existsSync(source)) throw new Error(`No report.md in ${run_folder}.`)
        const doc = convert(readFileSync(source, "utf8"), folder)
        writeFileSync(join(folder, "report.docx"), await Packer.toBuffer(doc))
        return { output: `Wrote ${join(run_folder, "report.docx")}.` }
      },
    }))
  },
}

