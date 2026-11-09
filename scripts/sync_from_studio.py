#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# dependencies = ["pymupdf"]
# ///
"""Refresh this repository from the Studio sources: the demo teams (AgentTeams/), the problems approved for GitHub in the
catalog (problems/, each team as a folder, no zip files) and the slide PDFs (slides/). Run: scripts/sync_from_studio.py DEMOS_DIR PROBLEMS_DIR SLIDES_PDF_DIR
DEMOS_DIR is the AgentTeams source, PROBLEMS_DIR the problem bank, SLIDES_PDF_DIR holds videoNN_*.pdf files exported
without speaker notes."""
import gzip
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
# Problems approved for GitHub: the Studio catalog (problem-bank/catalog.json) lists "github" in a public version's
# approved_destinations. Nothing else is copied.


def approved_problems(bank):
    catalog = json.loads((bank.parent / "catalog.json").read_text(encoding="utf-8"))
    return {
        Path(e["source"]).name: e["id"]
        for e in catalog["examples"]
        if any(v["audience"] == "public" and "github" in v["approved_destinations"] for v in e["versions"])
    }


SKIP_NAMES = {".DS_Store", ".stfolder", ".stignore"}
REFUSE_DIRS = {"runs", "node_modules"}
# Private absolute paths and OpenRouter keys must never reach the public repository.
FORBIDDEN = re.compile(rb"sk-or-v1-|file:///|[A-Za-z]:[\\/]+Users[\\/]|/Users/[A-Za-z]|/home/[a-z]")


def check(name, data):
    """Refuse forbidden content, looking inside zip members and gzip files."""
    if name.endswith((".zip", ".docx")):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for m in z.namelist():
                if any(part in REFUSE_DIRS for part in m.split("/")) or m.rsplit("/", 1)[-1].startswith(".env"):
                    sys.exit(f"refusing {name}: member {m} is run output or a secret file")
                check(f"{name}:{m}", z.read(m))
        return
    if name.endswith(".gz"):
        data = gzip.decompress(data)
    if FORBIDDEN.search(data):
        sys.exit(f"refusing {name}: private path or key in its contents")


def copy_tree(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if any(part in SKIP_NAMES or part.startswith("._") for part in rel.parts):
            continue
        if any(part in REFUSE_DIRS for part in rel.parts) or p.name.startswith(".env"):
            sys.exit(f"refusing to copy {src / rel}: run output or secret file")
        if p.is_file():
            check(str(src / rel), p.read_bytes())
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst / rel)


def public_slides(src, dst):
    """Copy a slide PDF. In video 1, slide 9 (artwork whose rights are not cleared) gets a plain box instead of its picture."""
    if not src.name.startswith("video01_"):
        shutil.copy2(src, dst)
        return
    doc = pymupdf.open(src)
    page = doc[8]
    for img in page.get_images():
        rect = page.get_image_rects(img[0])[0]
        page.delete_image(img[0])
        page.draw_rect(rect, color=(0.45, 0.45, 0.45), fill=(0.93, 0.93, 0.93), width=1.5)
        text = "Image not included in the public slides"
        width = pymupdf.get_text_length(text, fontname="helv", fontsize=24)
        page.insert_text((rect.x0 + (rect.width - width) / 2, rect.y0 + rect.height / 2 + 8), text, fontname="helv", fontsize=24, color=(0.25, 0.25, 0.25))
    doc.save(dst, garbage=4, deflate=True, clean=True)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    demos, bank, pdfs = (Path(a) for a in sys.argv[1:])
    copy_tree(demos, ROOT / "AgentTeams")
    wanted = approved_problems(bank)
    shutil.rmtree(ROOT / "problems", ignore_errors=True)
    for folder, slug in wanted.items():
        dst = ROOT / "problems" / slug
        copy_tree(bank / folder / "public", dst)
        brief = dst / "brief.md"
        (dst / "README.md").write_text(re.sub(r"\{\{([^}]+)\}\}", r"\1", brief.read_text()))
        brief.unlink()
        # No zip files are committed: the problem's team is kept as a folder.
        team_zip = dst / "team.zip"
        with zipfile.ZipFile(team_zip) as z:
            for m in z.namelist():
                rel = Path(m).relative_to(Path(m).parts[0])
                if m.endswith("/") or not rel.parts:
                    continue
                out = dst / "team" / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(m))
        team_zip.unlink()
    slides = ROOT / "slides"
    slides.mkdir(exist_ok=True)
    for pdf in sorted(pdfs.glob("video*.pdf")):
        check(str(pdf), pdf.read_bytes())
        public_slides(pdf, slides / pdf.name)
    print(ROOT)


if __name__ == "__main__":
    main()
