"""Use a web page as its reader would and record what is observed.

  python3 tools/render_page.py PAGE.html --out DIR

Opens PAGE offline (every network request blocked) in headless Chromium, on a phone
screen (390 x 844) and in a desktop window (1280 x 900) that is then narrowed to 390 px,
and records what a reader would see:
- errors the page raises and console errors, and any blocked network request;
- every plot (Plotly graph, canvas, SVG chart) on first load: shown or hidden, and what
  it shows (data points for Plotly; painted pixels for a canvas, drawn shapes for SVG);
- each control (slider, drop-down, checkbox, radio button), starting from a freshly
  opened page, moved through its settings (every setting, at most 12 spread over the
  range) by a real click or choice: its label at each setting, which plots (data or
  layout) and which text lines change, and any error raised;
- the page width against the screen width: on first load, after moving the controls,
  and after the desktop window is narrowed;
- the page's visible text, each control's label and each plot's titles, as shown;
- text a reader cannot see in full (page text, plot titles, tick labels): cut off at the
  screen's left edge or by a box that hides what overflows it, on each screen;
- screenshots.
Writes DIR/render_report.md (everything), DIR/render_report.json and three screenshots,
and prints a short summary. It states what it saw, not whether the page meets a task.
Exit 0: the page was opened and observed (whatever it shows). Exit 2: it could not be
(no browser could start, or the page could not be opened).
Needs the Playwright package and either its Chromium (`python3 -m playwright install
chromium`) or Google Chrome.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import threading
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}
LIMIT_S = 240      # the whole observation; a page still busy after this is reported as frozen
SETTLE_MS = 1500   # wait after opening or resizing, for scripts and plots to finish
STEP_MS = 300      # wait after each control setting
MAX_SETTINGS = 12  # settings tried per control
MAX_TEXT_LINES = 200
MAX_SERIES_POINTS = 60   # values kept per Plotly trace in render_report.json
MAX_CUT = 10   # cut-off texts listed per screen among the observed problems

# Every plot on the page: Plotly graphs, canvases and SVG charts not inside a Plotly graph.
PLOTS = """(MAXPTS) => {
  const out = [];
  const count = a => Array.isArray(a) || ArrayBuffer.isView(a)
    ? Array.from(a).flat(2).filter(v => typeof v === 'number' && isFinite(v)).length : 0;
  const box = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(r.width), Math.round(r.height)]; };
  const first = a => Array.isArray(a) || ArrayBuffer.isView(a) ? Array.from(a).slice(0, MAXPTS) : [];
  const title = t => (t && (t.text !== undefined ? t.text : t)) || '';
  const shown = e => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  // What a Plotly graph draws: its rendered SVG without the ids Plotly generates anew at each newPlot.
  const drawn = gd => Array.from(gd.querySelectorAll('svg.main-svg')).map(v => v.outerHTML
    .replace(/ (id|clip-path)="[^"]*"/g, '').replace(/url\\(['"]?#[^)]*\\)/g, '')).join('');
  // Points a trace shows: from what Plotly computed (numbers, numeric strings, categories) when it has it,
  // else from the arrays given; a point needs every coordinate its trace type uses (x and y together).
  const num = v => typeof v === 'number' && isFinite(v);
  const need = t => t.values !== undefined ? ['v'] : t.r !== undefined ? ['r'] : t.z !== undefined && t.x === undefined ? ['z']
    : ['x', 'y'].concat(t.z !== undefined && /3d/.test(t.type || '') ? ['z'] : []);
  const points = (gd, t, i) => {
    const cd = gd.calcdata && gd.calcdata[i];
    if (Array.isArray(cd) && cd.length && cd[0] && Object.keys(cd[0]).some(k => ['x', 'y', 'z', 'v', 'r'].includes(k)))
      return cd.filter(p => p && need(t).every(k => num(p[k]))).length;
    const arrs = need(t).map(k => t[{v: 'values'}[k] || k]);
    const ok = v => v !== null && v !== undefined && (typeof v === 'string' ? v.trim() !== '' : num(Number(v)));
    if (arrs.some(a => !(Array.isArray(a) || ArrayBuffer.isView(a)))) return 0;   // a y with no x: Plotly would number the points; not guessed here
    return Array.from(arrs[0]).filter((_, j) => arrs.every(a => ok(a[j]))).length;
  };
  document.querySelectorAll('.js-plotly-plot').forEach((gd, i) => {
    const data = gd.data || [], lay = gd.layout || {}, full = gd._fullLayout || {};
    const pts = data.map((t, j) => points(gd, t, j));
    // WebGL graphs (3D, maps) draw on canvases; their view is the scene camera, map center and zoom.
    const view = JSON.stringify(Object.keys(full).filter(k => /^(scene|geo|mapbox|map)\\d*$/.test(k))
      .map(k => [k, full[k].camera, full[k].center, full[k].zoom, full[k].projection && full[k].projection.rotation]));
    const axes = Object.keys(lay).filter(k => /^[xy]axis\\d*$/.test(k)).sort()
      .map(k => k + ': ' + title(lay[k].title)).filter(s => !s.endsWith(': '));
    out.push({kind: 'plotly', id: gd.id || ('plotly #' + (i + 1)), traces: data.length, points: pts.reduce((a, b) => a + b, 0),
      unit: 'data points', visible: shown(gd), title: title(lay.title), axes: axes, box: box(gd),
      series: data.map(t => Object.fromEntries([['name', t.name || ''], ['type', t.type || 'scatter']].concat(
        ['x', 'y', 'z', 'values', 'labels', 'r', 'theta', 'lat', 'lon'].filter(k => t[k] !== undefined).map(k => [k, first(t[k])])))),
      sig: JSON.stringify(data.map(t => [t.x, t.y, t.z, t.values, t.r, t.text, t.marker && t.marker.color])) + view + drawn(gd)});
  });
  document.querySelectorAll('canvas').forEach((c, i) => {
    if (c.closest('.js-plotly-plot')) return;
    let sig = '', drawn = 0;
    try { sig = c.toDataURL(); const g = c.getContext('2d');
      if (g) { const d = g.getImageData(0, 0, c.width, c.height).data; for (let k = 3; k < d.length; k += 4) if (d[k]) drawn++; } else drawn = -1;
    } catch (e) { drawn = -1; }
    out.push({kind: 'canvas', id: c.id || ('canvas #' + (i + 1)), traces: 0, points: drawn, unit: drawn < 0 ? 'unknown (not a 2D canvas)' : 'painted pixels',
      visible: shown(c), title: '', axes: [], box: box(c), sig: sig});
  });
  document.querySelectorAll('svg').forEach((s, i) => {
    if (s.closest('.js-plotly-plot') || s.parentElement.closest('svg')) return;
    const r = s.getBoundingClientRect();
    if (r.width < 100 || r.height < 100 || r.right <= 0 || r.bottom <= 0) return;   // icons; helpers placed off-screen on purpose
    const marks = s.querySelectorAll('path, circle, rect, line, polyline, polygon').length;
    out.push({kind: 'svg', id: s.id || ('svg #' + (i + 1)), traces: 0, points: marks, unit: 'drawn shapes', visible: shown(s),
      title: '', axes: [], box: box(s), sig: s.innerHTML});
  });
  return out;
}"""

# The visible text without the plots' own text (tick labels, legends), one line per block or line
# break. Read from the page's own rendered text nodes, changing nothing and running no page code.
TEXT = """() => {
  if (!document.body) return [];
  const skip = '.js-plotly-plot, svg, canvas, script, style, template, noscript, select, textarea';
  const block = n => { for (let e = n.parentElement; e && e !== document.body; e = e.parentElement) {
      const d = getComputedStyle(e).display; if (d !== 'contents' && !d.startsWith('inline')) return e; } return document.body; };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
    {acceptNode: n => n.nodeType === 1 && n.matches(skip) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  const out = []; let cur = null, buf = '';
  const flush = () => { const t = buf.replace(/\\s+/g, ' ').trim(); if (t) out.push(t); buf = ''; };
  const range = document.createRange();
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (n.nodeType === 1) { if (n.tagName === 'BR') flush(); continue; }
    if (!n.data.trim()) { buf += ' '; continue; }
    range.selectNodeContents(n);
    if (!range.getClientRects().length || getComputedStyle(n.parentElement).visibility === 'hidden') continue;   // not rendered
    const b = block(n);
    if (b !== cur) { flush(); cur = b; }
    buf += n.data;
  }
  flush();
  return out;
}"""

# Text a reader cannot see in full: shown text (page text and every SVG text, plot titles and tick
# labels included) reaching past the left edge of the screen or past the inner edge of a box that hides
# what overflows it (overflow hidden or clip; an SVG's own bounds). Left out: text not painted (closed
# section, transparent, CSS clip as in screen-reader-only text, a box of 2 px or less), and text a reader
# can bring into view by scrolling a box sideways. A box turned by a CSS transform is compared by its
# screen bounds, so text it clips may be missed.
CUT = """() => {
  const found = new Map();
  // Where text can show: the screen from its left edge, narrowed by each box that clips the text (overflow
  // hidden or clip; its inner box, in screen pixels). A box that scrolls on an axis limits only the side it
  // cannot scroll back to, and boxes outside it no longer limit that axis. Root overflow, and body overflow
  // the root passes on, apply to the screen. A positioned element escapes the boxes between it and its
  // containing block.
  const area = el => {
    let l = -Infinity, r = Infinity, t = -Infinity, b = Infinity, reachX = false, reachY = false, escape = null;
    const root = document.documentElement, rs = getComputedStyle(root);
    const bodyToScreen = rs.overflowX === 'visible' && rs.overflowY === 'visible';
    const hide = v => v === 'hidden' || v === 'clip', scrolls = v => v === 'auto' || v === 'scroll';
    for (let e = el.parentElement; e; e = e.parentElement) {
      const cs = getComputedStyle(e), svg = e instanceof SVGElement;
      const skip = (cs.display === 'inline' && !(e instanceof SVGSVGElement)) || cs.display === 'contents'   // no box that clips or scrolls
        || (escape === 'absolute' && cs.position === 'static' && cs.transform === 'none') || (escape === 'fixed' && cs.transform === 'none');
      if (escape === 'absolute' && (cs.position !== 'static' || cs.transform !== 'none')) escape = null;   // its containing block
      if (escape === 'fixed' && cs.transform !== 'none') escape = null;
      if (!svg && (cs.position === 'absolute' || cs.position === 'fixed')) escape = cs.position;
      if (skip) continue;
      const screen = e === root || (e === document.body && bodyToScreen);
      const sx = !screen && !reachX && scrolls(cs.overflowX), sy = !screen && !reachY && scrolls(cs.overflowY);
      const hx = hide(cs.overflowX) && !reachX, hy = hide(cs.overflowY) && !reachY;
      if (!hx && !hy && !sx && !sy) continue;
      let x0, x1, y0, y1;
      if (screen) { x0 = 0; x1 = window.innerWidth; y0 = 0; y1 = window.innerHeight; }
      else {
        const q = e.getBoundingClientRect();
        if (svg) { x0 = q.left; x1 = q.right; y0 = q.top; y1 = q.bottom; }
        else {
          const kx = e.offsetWidth ? q.width / e.offsetWidth : 1, ky = e.offsetHeight ? q.height / e.offsetHeight : 1;
          x0 = q.left + e.clientLeft * kx; x1 = x0 + e.clientWidth * kx; y0 = q.top + e.clientTop * ky; y1 = y0 + e.clientHeight * ky;
        }
      }
      if (hx) { l = Math.max(l, x0); r = Math.min(r, x1); }
      if (hy) { t = Math.max(t, y0); b = Math.min(b, y1); }
      if (sx) {   // scrolled back to its start at most: left edge (right edge when right to left)
        if (cs.direction === 'rtl') r = Math.min(r, x1 - e.scrollLeft); else l = Math.max(l, x0 - e.scrollLeft);
        reachX = true;
      }
      if (sy) { t = Math.max(t, y0 - e.scrollTop); reachY = true; }
    }
    if (!reachX) l = Math.max(l, 0);   // the page cannot scroll left of the screen
    return [l, r, t, b];
  };
  // Painted: not in a closed section, not transparent or invisible, not hidden by CSS clip.
  const painted = el => {
    while (el.parentElement && getComputedStyle(el).display === 'contents') el = el.parentElement;   // no box of its own
    if (el.checkVisibility && !el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true, contentVisibilityAuto: true})) return false;
    for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).clip; if (c && c !== 'auto') return false; }
    return true;
  };
  const check = (text, q, el, where) => {
    if (!painted(el.nodeType === 1 ? el : el.parentElement)) return;
    const [l, r, t, b] = area(el);
    if (r - l <= 2 || b - t <= 2) return;
    const cut = {left: l - q.left, right: q.right - r, top: t - q.top, bottom: q.bottom - b};
    const sides = Object.keys(cut).filter(k => cut[k] > 2);
    if (!sides.length) return;
    const key = text + '|' + where, f = found.get(key) || {text: text.slice(0, 80), where: where, hidden_px: {}};
    sides.forEach(k => { f.hidden_px[k] = Math.max(f.hidden_px[k] || 0, Math.round(cut[k])); });
    found.set(key, f);
  };
  if (!document.body) return [];
  const skip = 'svg, canvas, script, style, template, noscript, select, textarea';
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
    {acceptNode: n => n.nodeType === 1 && n.matches(skip) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  const range = document.createRange();
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (n.nodeType !== 3 || !n.data.trim() || getComputedStyle(n.parentElement).visibility === 'hidden') continue;
    range.selectNodeContents(n);
    const q = range.getBoundingClientRect();
    if (q.width && q.height) check(n.data.replace(/\\s+/g, ' ').trim(), q, n, 'page text');
  }
  document.querySelectorAll('svg text').forEach(e => {
    const s = e.textContent.replace(/\\s+/g, ' ').trim(), q = e.getBoundingClientRect();
    if (!s || !q.width || !q.height || getComputedStyle(e).visibility === 'hidden') return;
    const gd = e.closest('.js-plotly-plot'), sv = e.closest('svg');
    check(s, q, e, gd ? 'plot ' + (gd.id || 'Plotly graph') : 'chart ' + (sv.id || 'svg'));
  });
  return Array.from(found.values());
}"""

CONTROLS = """() => Array.from(document.querySelectorAll(
    'input[type=range], select, input[type=checkbox], input[type=radio]')).map((e, i) => {
  const lab = (e.labels && e.labels[0]) ? e.labels[0].innerText : (e.closest('label') ? e.closest('label').innerText : '');
  const usable = !e.disabled && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  return {index: i, id: e.id, kind: e.tagName === 'SELECT' ? 'select' : e.type, label: lab.trim().replace(/\\s+/g, ' '), usable: usable,
    min: e.min, max: e.max, step: e.step, value: e.type === 'checkbox' || e.type === 'radio' ? String(e.checked) : e.value,
    options: e.tagName === 'SELECT' ? Array.from(e.options).map(o => o.value) : []};
})"""

CONTROL_SELECTOR = "input[type=range], select, input[type=checkbox], input[type=radio]"

# A slider set the way dragging it would: new value, then its input and change events.
SET_RANGE = """([i, v]) => {
  const e = document.querySelectorAll('input[type=range], select, input[type=checkbox], input[type=radio]')[i];
  if (!e || e.type !== 'range' || e.disabled) throw new Error('the slider is gone or disabled');
  e.value = v;
  e.dispatchEvent(new Event('input', {bubbles: true}));
  e.dispatchEvent(new Event('change', {bubbles: true}));
}"""

WIDTH = "() => [window.innerWidth, document.documentElement.scrollWidth]"

# The label of control i as shown now (with any current value printed in it).
LABEL = """(i) => {
  const e = document.querySelectorAll('input[type=range], select, input[type=checkbox], input[type=radio]')[i];
  if (!e) return '(control gone)';
  const l = (e.labels && e.labels[0]) || e.closest('label');
  return l ? l.innerText.trim().replace(/\\s+/g, ' ') : '';
}"""


def settings(c):
    """The settings a reader can choose for control c, at most MAX_SETTINGS spread over its range."""
    if c["kind"] == "select":
        vals = c["options"]
    elif c["kind"] in ("checkbox", "radio"):
        vals = ["true", "false"] if c["kind"] == "checkbox" else ["true"]
    else:
        try:
            lo, hi = float(c["min"] or 0), float(c["max"] or 100)
            step = (hi - lo) / (MAX_SETTINGS - 1) if c["step"] == "any" else float(c["step"] or 1)
        except ValueError:
            return []
        if not all(map(math.isfinite, (lo, hi, step))) or hi < lo or step <= 0:
            return []
        n = int(math.floor((hi - lo) / step + 1e-9)) + 1   # the settings the browser allows: lo, lo + step, ... up to hi
        idx = range(n) if n <= MAX_SETTINGS else [round(k * (n - 1) / (MAX_SETTINGS - 1)) for k in range(MAX_SETTINGS)]
        return [f"{lo + k * step:.12g}" for k in idx]
    if len(vals) > MAX_SETTINGS:
        vals = [vals[round(k * (len(vals) - 1) / (MAX_SETTINGS - 1))] for k in range(MAX_SETTINGS)]
    return vals


def sig(s):
    return hashlib.sha1(s.encode()).hexdigest()


def launch(p):
    """Playwright's own Chromium first, then installed Chrome or Edge; returns (browser, name) or (None, errors)."""
    errors = []
    for name, kw in (("Playwright Chromium", {}), ("Google Chrome", {"channel": "chrome"}), ("Microsoft Edge", {"channel": "msedge"})):
        try:
            return p.chromium.launch(**kw), name
        except PlaywrightError as e:
            errors.append(f"{name}: {str(e).splitlines()[0][:200]}")
    return None, errors


def open_page(browser, url, viewport, mobile, log):
    ctx = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers="block", offline=True)

    def route(r):
        if r.request.url.startswith(("file:", "data:", "blob:", "about:")):
            r.continue_()
        else:
            log["blocked"].append(r.request.url[:150])
            r.abort()

    ctx.route("**/*", route)

    def socket(ws):   # never connected to a server (no connect_to_server call); the attempt is logged
        log["blocked"].append(ws.url[:150])

    ctx.route_web_socket("**/*", socket)
    pg = ctx.new_page()
    pg.set_default_timeout(10000)   # no wait on a page that never answers longer than this
    pg.on("pageerror", lambda e: log["errors"].append(f"page error: {str(e).splitlines()[0][:200]}"))
    pg.on("console", lambda m: m.type == "error" and log["errors"].append(f"console error: {m.text[:200]}"))
    pg.goto(url, wait_until="load")
    pg.wait_for_timeout(SETTLE_MS)
    return pg


def observe(page, out, rep, log, stage):
    with sync_playwright() as p:
        browser, name = launch(p)
        if browser is None:
            print("render_page: no browser could start:\n  " + "\n  ".join(name), file=sys.stderr)
            sys.exit(2)
        rep["browser"] = f"{name} {browser.version}"
        stage[0] = "opening the page on the phone screen"
        try:
            pg = open_page(browser, page.resolve().as_uri(), PHONE, True, log)
        except PlaywrightError as e:
            print(f"render_page: the page could not be opened: {str(e).splitlines()[0][:200]}", file=sys.stderr)
            sys.exit(2)

        # Phone, first load.
        plots = pg.evaluate(PLOTS, MAX_SERIES_POINTS)
        inner, scroll = pg.evaluate(WIDTH)
        rep["phone"] = {"screen_width": inner, "page_width": scroll, "errors": list(log["errors"]),
                        "plots": [{k: v for k, v in q.items() if k != "sig"} for q in plots],
                        "text": pg.evaluate(TEXT)[:MAX_TEXT_LINES], "text_cut_off": pg.evaluate(CUT)}
        pg.screenshot(path=str(out / "phone_first_load.png"), full_page=True)

        # Each control through its settings, back to its first value after.
        widest = scroll
        for c in pg.evaluate(CONTROLS):
            if not c["usable"]:   # disabled or hidden on first load: a reader cannot use it there
                rep["controls"].append({"id": c["id"], "kind": c["kind"], "label": c["label"], "first_value": c["value"],
                                        "skipped": "disabled or hidden on first load", "settings_tried": [], "label_at_each_setting": [],
                                        "settings_that_could_not_be_set": [], "shown_at_each_setting": [], "plots_changed": [],
                                        "text_lines_changed": 0, "errors": []})
                continue
            # Each control from a freshly opened page, so one control's test cannot change another's.
            stage[0] = f"testing control {c['id'] or c['label'][:40]}"
            pg.reload(wait_until="load")
            pg.wait_for_timeout(SETTLE_MS)
            base_plots = {q["id"]: sig(q["sig"]) for q in pg.evaluate(PLOTS, MAX_SERIES_POINTS)}
            base_text = pg.evaluate(TEXT)
            n_err = len(log["errors"])
            changed_plots, changed_text, tried, shown, failed, steps = set(), set(), settings(c), [], [], []
            done = []
            for v in tried:
                try:
                    hs = pg.query_selector_all(CONTROL_SELECTOR)
                    if c["index"] >= len(hs) or hs[c["index"]].get_attribute("id") != (c["id"] or None):
                        failed.append(f"{v}: the control was gone or replaced after an earlier setting")
                        break
                    if c["kind"] == "range":
                        pg.evaluate(SET_RANGE, [c["index"], v])
                    else:   # as a reader would: a real click or choice, so the page's own handlers run
                        h = hs[c["index"]]
                        h.select_option(v) if c["kind"] == "select" else h.set_checked(v == "true", force=True)
                except PlaywrightError as e:
                    failed.append(f"{v}: {str(e).splitlines()[0][:120]}")
                    continue
                done.append(v)
                pg.wait_for_timeout(STEP_MS)
                shown.append(pg.evaluate(LABEL, c["index"]))
                now = pg.evaluate(PLOTS, MAX_SERIES_POINTS)
                for q in now:
                    if base_plots.get(q["id"]) != sig(q["sig"]):
                        changed_plots.add(q["id"])
                text = pg.evaluate(TEXT)
                changed_text |= set(text) ^ set(base_text)
                # For scripts: what the page shows at this setting (all its text, the lines not on first load, each Plotly trace's values).
                steps.append({"setting": v, "label": shown[-1], "text": text[:MAX_TEXT_LINES],
                              "text_lines_new": [t for t in text if t not in base_text][:MAX_TEXT_LINES],
                              "plotly": {q["id"]: q["series"] for q in now if q["kind"] == "plotly"}})
                widest = max(widest, pg.evaluate(WIDTH)[1])
            rep["controls"].append({"id": c["id"], "kind": c["kind"], "label": c["label"], "first_value": c["value"],
                                    "settings_tried": done,
                                    "label_at_each_setting": shown, "settings_that_could_not_be_set": failed, "shown_at_each_setting": steps,
                                    "plots_changed": sorted(changed_plots),
                                    "text_lines_changed": len(changed_text), "errors": log["errors"][n_err:]})
        rep["phone"]["widest_page_after_controls"] = widest

        # Desktop window, then narrowed to the phone width.
        stage[0] = "opening the page in a desktop window and narrowing it"
        n_err = len(log["errors"])
        pd = open_page(browser, page.resolve().as_uri(), DESKTOP, False, log)
        pd.screenshot(path=str(out / "desktop_1280.png"), full_page=True)
        d_inner, d_scroll = pd.evaluate(WIDTH)
        d_plots = pd.evaluate(PLOTS, MAX_SERIES_POINTS)
        d_cut = pd.evaluate(CUT)
        pd.set_viewport_size(PHONE)
        pd.wait_for_timeout(SETTLE_MS)
        n_inner, n_scroll = pd.evaluate(WIDTH)
        n_plots = pd.evaluate(PLOTS, MAX_SERIES_POINTS)
        n_cut = pd.evaluate(CUT)
        pd.screenshot(path=str(out / "narrowed_390.png"), full_page=True)
        rep["desktop"] = {"screen_width": d_inner, "page_width": d_scroll, "errors": log["errors"][n_err:],
                          "plots_with_data": sum(q["points"] > 0 for q in d_plots if q["visible"] and q["kind"] == "plotly"),
                          "narrowed_screen_width": n_inner, "narrowed_page_width": n_scroll,
                          "narrowed_plots_past_right_edge": [q["id"] for q in n_plots if q["visible"] and q["box"][1] > n_inner + 0.5],
                          "text_cut_off": d_cut, "narrowed_text_cut_off": n_cut}
        browser.close()

    # What a reader would notice, stated as observed; whether it matters is the task's call.
    ph, pr = rep["phone"], rep["problems"]
    pr += log["errors"]
    if log["blocked"]:
        pr.append(f"the page asked for {len(log['blocked'])} network address(es) while offline, first {log['blocked'][0]}")
    if not ph["plots"]:
        pr.append("no plot found on the page (Plotly graph, canvas or SVG chart)")
    vis = [q for q in ph["plots"] if q["visible"]]   # hidden ones (closed tabs, display: none) are listed, not judged
    pr += [f"plot {q['id']} shows no data on first load" for q in vis if q["kind"] == "plotly" and q["points"] == 0]
    pr += [f"{q['kind']} {q['id']} draws nothing on first load" for q in vis if q["kind"] != "plotly" and q["points"] == 0]
    pr += [f"plot {q['id']} has no size on first load" for q in vis if q["box"][2] == 0 or q["box"][3] == 0]
    pr += [f"plot {q['id']} extends past the right edge of a 390 px screen ({q['box'][1]} px)"
           for q in vis if q["box"][1] > ph["screen_width"] + 0.5]
    if ph["screen_width"] != PHONE["width"]:
        pr.append(f"on a 390 px phone screen the page lays out {ph['screen_width']} px wide and is shown shrunk (no mobile viewport tag)")
    if ph["page_width"] > ph["screen_width"]:
        pr.append(f"sideways scroll on first load at 390 px: page {ph['page_width']} px wide")
    if ph["widest_page_after_controls"] > ph["screen_width"]:
        pr.append(f"sideways scroll after moving controls at 390 px: page {ph['widest_page_after_controls']} px wide")
    pr += [f"control {c['id'] or c['label'][:40]} changes no plot" + (" (only text)" if c["text_lines_changed"] else "")
           for c in rep["controls"] if not c["plots_changed"] and not c.get("skipped") and not (c["kind"] == "radio" and c["first_value"] == "true")]
    pr += [f"control {c['id'] or c['label'][:40]} could not be set to {len(c['settings_that_could_not_be_set'])} setting(s)"
           for c in rep["controls"] if c["settings_that_could_not_be_set"]]
    d = rep["desktop"]
    if d["narrowed_page_width"] > d["narrowed_screen_width"]:
        pr.append(f"sideways scroll after a 1280 px window is narrowed to 390 px: page {d['narrowed_page_width']} px wide")
    pr += [f"plot {i} extends past the right edge after narrowing" for i in d["narrowed_plots_past_right_edge"]]
    for where, cuts in (("on the phone screen", ph["text_cut_off"]), ("in the 1280 px window", d["text_cut_off"]),
                        ("after narrowing to 390 px", d["narrowed_text_cut_off"])):
        pr += [f"text cut off {where}: '{c['text']}' ({c['where']}), hidden "
               + ", ".join(f"{px} px at the {k}" for k, px in c["hidden_px"].items()) for c in cuts[:MAX_CUT]]
        if len(cuts) > MAX_CUT:
            pr.append(f"text cut off {where}: {len(cuts) - MAX_CUT} more in render_report.json")
    rep["problems"] = list(dict.fromkeys(pr))
    return rep


def markdown(rep):
    ph, d = rep["phone"], rep["desktop"]
    L = [f"# Render report: {rep['page']}", "", f"Browser: {rep['browser']}, offline (network blocked).", "",
         "## Observed problems", ""]
    L += [f"- {x}" for x in rep["problems"]] or ["- none observed"]
    L += ["", "## Phone screen, first load (390 x 844)", "",
          f"Screen {ph['screen_width']} px, page {ph['page_width']} px wide; widest after moving controls {ph['widest_page_after_controls']} px.",
          f"Errors on load: {len(ph['errors'])}.", "", "| Plot | Kind | Shown | Traces | Data shown | Left-right (px) | Titles |", "|---|---|---|---|---|---|---|"]
    for q in ph["plots"]:
        titles = "; ".join(([q["title"]] if q["title"] else []) + q["axes"]).replace("|", "/")
        data = q["unit"] if q["points"] < 0 else f"{q['points']} {q['unit']}"
        L.append(f"| {q['id']} | {q['kind']} | {'yes' if q['visible'] else 'hidden'} | {q['traces']} | {data} | {q['box'][0]}-{q['box'][1]} | {titles} |")
    L += ["", "## Controls, each moved through its settings", "", "| Control | Label | Settings tried | Plots changed | Text lines changed | Errors |", "|---|---|---|---|---|---|"]
    for c in rep["controls"]:
        L.append(f"| {c['id'] or c['kind']} | {c['label'].replace('|', '/')} | {c.get('skipped') or len(c['settings_tried'])} | "
                 f"{', '.join(c['plots_changed']) or 'none'} | {c['text_lines_changed']} | {len(c['errors'])} |")
    if not rep["controls"]:
        L.append("| none | | | | | |")
    for c in rep["controls"]:
        L += ["", f"Label of {c['id'] or c['kind']} at each setting tried:"] + [f"    {v} -> {t}" for v, t in zip(c["settings_tried"], c["label_at_each_setting"])]
    L += ["", "## Desktop window (1280 x 900), then narrowed to 390 px", "",
          f"Desktop: page {d['page_width']} px in a {d['screen_width']} px window; Plotly graphs with data {d['plots_with_data']}; errors {len(d['errors'])}.",
          f"Narrowed: page {d['narrowed_page_width']} px on a {d['narrowed_screen_width']} px screen; plots past the right edge: "
          f"{', '.join(d['narrowed_plots_past_right_edge']) or 'none'}.", "",
          "## Text cut off (shown only in part)", ""]
    for where, cuts in (("Phone screen", ph["text_cut_off"]), ("1280 px window", d["text_cut_off"]),
                        ("Narrowed to 390 px", d["narrowed_text_cut_off"])):
        L += [f"- {where}: '{c['text']}' ({c['where']}), hidden " + ", ".join(f"{px} px at the {k}" for k, px in c["hidden_px"].items())
              for c in cuts] or [f"- {where}: none"]
    L += ["", "## Visible text on first load (phone, plots' own text left out)", ""]
    L += [f"    {t}" for t in ph["text"]]
    L += ["", "Screenshots: phone_first_load.png, desktop_1280.png, narrowed_390.png.",
          "render_report.json also holds, for scripts: each Plotly trace's values on first load (`phone.plots[].series`) and, per control "
          "and setting, its label, the full visible text, the text lines not shown on first load and each Plotly trace's values (`controls[].shown_at_each_setting`)."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("page", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="folder for the report and screenshots")
    a = ap.parse_args()
    if not a.page.is_file():
        print(f"render_page: no such file: {a.page}", file=sys.stderr)
        sys.exit(2)
    a.out.mkdir(parents=True, exist_ok=True)
    rep = {"page": str(a.page), "browser": "", "phone": {}, "controls": [], "desktop": {}, "problems": []}
    log, stage = {"errors": [], "blocked": []}, ["starting a browser"]

    def frozen():   # runs on a timer thread: the page (or browser) stopped answering; keep what was seen
        rep["problems"] = [f"the page stopped responding: still busy after {LIMIT_S} s while {stage[0]}; this report is partial"] \
            + list(dict.fromkeys(log["errors"]))
        (a.out / "render_report.json").write_text(json.dumps(rep, indent=1, default=str))
        (a.out / "render_report.md").write_text(f"# Render report (partial): {a.page}\n\n## Observed problems\n\n"
                                                + "".join(f"- {x}\n" for x in rep["problems"]))
        print(f"render_page: {a.page}\nobserved problems: {len(rep['problems'])}\n" + "".join(f"  - {x}\n" for x in rep["problems"][:20])
              + f"full report: {a.out / 'render_report.md'}", flush=True)
        os._exit(0)   # the browser may not close while the page is stuck

    timer = threading.Timer(LIMIT_S, frozen)
    timer.daemon = True
    timer.start()
    rep = observe(a.page, a.out, rep, log, stage)
    timer.cancel()
    (a.out / "render_report.json").write_text(json.dumps(rep, indent=1))
    (a.out / "render_report.md").write_text(markdown(rep))
    print(f"render_page: {a.page}, {rep['browser']}")
    print(f"plots on first load: {sum(q['visible'] for q in rep['phone']['plots'])} shown ({sum(not q['visible'] for q in rep['phone']['plots'])} hidden), "
          f"Plotly graphs with data: {sum(q['points'] > 0 for q in rep['phone']['plots'] if q['visible'] and q['kind'] == 'plotly')} "
          f"(canvas and SVG: drawing seen, data not readable); "
          f"controls: {len(rep['controls'])}; page width at 390 px: {rep['phone']['page_width']} on load, "
          f"{rep['desktop']['narrowed_page_width']} after narrowing")
    print(f"observed problems: {len(rep['problems'])}")
    for x in rep["problems"][:20]:
        print(f"  - {x}")
    if len(rep["problems"]) > 20:
        print(f"  ... {len(rep['problems']) - 20} more in render_report.md")
    print(f"full report: {a.out / 'render_report.md'}")


if __name__ == "__main__":
    main()
