"""Build the release downloads from the committed folders (standard library only).

  build_release.py --tag release/<stamp> --out DIR

Writes into DIR: AgentTeams_V<n>_<stamp>.zip (top folder AgentTeams_V<n>_<stamp>/, VERSION.txt first),
<id>-team_<stamp>.zip for every problems/<id>/team/ folder, and SHA256SUMS.txt.
The course files version <n>, the note and the action line in VERSION.txt come from release-notes/<stamp>.json.
Refuses symbolic links, run output, secrets and backup folders.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

STAMP = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:-([2-9]|[1-9]\d+))?")
SKIP_NAMES = {".DS_Store", ".stfolder", ".stignore"}
REFUSE_DIRS = {"runs", "node_modules", ".git"}


def junk(part):
    low = part.lower()
    return low.endswith(("_bk", ".bak")) or "backup" in low or low.startswith(".trash")


def files(src):
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if any(x in SKIP_NAMES or x.startswith("._") for x in rel.parts):
            continue
        if p.is_symlink():
            sys.exit(f"refusing {rel}: symbolic link")
        if any(x in REFUSE_DIRS for x in rel.parts) or p.name.startswith(".env"):
            sys.exit(f"refusing {rel}: run output, version control or secret file")
        if any(junk(x) for x in rel.parts):
            sys.exit(f"refusing {rel}: backup or junk folder")
        if p.is_file():
            yield p, rel


def build(src, top, name, version_text, day, out):
    path = out / f"{top}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo(f"{top}/VERSION.txt", day)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, version_text)
        for p, rel in files(src):
            info = zipfile.ZipInfo.from_file(p, f"{top}/{rel.as_posix()}")
            info.date_time = day
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    stamp = a.tag.removeprefix("release/")
    m = STAMP.fullmatch(stamp)
    if not m:
        sys.exit(f"tag {a.tag!r} is not release/YYYY-MM-DD or release/YYYY-MM-DD-N")
    day = (int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, 0)
    notes = json.loads(Path(f"release-notes/{stamp}.json").read_text(encoding="utf-8"))
    for key in ("student_note", "action"):
        if not notes.get(key, "").strip() or "\n" in notes[key].strip():
            sys.exit(f"release-notes/{stamp}.json needs a one-line {key}")
    version = notes.get("version")
    if type(version) is not int or version < 1:
        sys.exit(f"release-notes/{stamp}.json needs a version number")
    a.out.mkdir(parents=True, exist_ok=True)
    made = []

    def text(label):
        return f"{label} {stamp}\n\n{notes['student_note'].strip()}\n\nWhat to do: {notes['action'].strip()}\n"

    if Path("AgentTeams").is_dir():
        made.append(build(Path("AgentTeams"), f"AgentTeams_V{version}_{stamp}", "AgentTeams", text(f"AgentTeams V{version}"),
                          day, a.out))
    for team in sorted(Path("problems").glob("*/team")):
        pid = team.parent.name
        made.append(build(team, f"{pid}-team_{stamp}", pid, text(f"{pid}-team"), day, a.out))
    if not made:
        sys.exit("nothing to build: no AgentTeams/ folder and no problems/*/team/ folders")
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in made)
    (a.out / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    for p in made:
        print(p, p.stat().st_size)


if __name__ == "__main__":
    main()
