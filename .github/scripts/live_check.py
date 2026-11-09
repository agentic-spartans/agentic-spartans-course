"""Check the public release download (standard library only).

  live_check.py --tag release/<stamp> --repo OWNER/REPO [--download-base URL] [--tries 8] [--wait 15]

Downloads AgentTeams_V<n>_<stamp>.zip (<n> from release-notes/<stamp>.json), each problem team zip and SHA256SUMS.txt from the public
release URL (DOWNLOAD_BASE overrides the base; default https://github.com/<repo>/releases/download),
and checks the sums, the top folder, VERSION.txt, and that every committed AgentTeams/ file
is in the zip with the same bytes. Exit 1 on any difference.
"""
import argparse
import hashlib
import json
import io
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "release-live-check"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def problems_of(stamp):
    return [p.parent.name for p in sorted(Path("problems").glob("*/team"))]


def check(base, tag, stamp):
    bad = []
    sums = {}
    for line in fetch(f"{base}/{tag}/SHA256SUMS.txt").decode().splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    files_v = json.loads(Path(f"release-notes/{stamp}.json").read_text(encoding="utf-8"))["version"]
    names = [f"AgentTeams_V{files_v}_{stamp}.zip"] if Path("AgentTeams").is_dir() else []
    names += [f"{pid}-team_{stamp}.zip" for pid in problems_of(stamp)]
    for name in names:
        if name not in sums:
            bad.append(f"{name} missing from SHA256SUMS.txt")
            continue
        data = fetch(f"{base}/{tag}/{name}")
        if hashlib.sha256(data).hexdigest() != sums[name]:
            bad.append(f"{name}: downloaded bytes do not match SHA256SUMS.txt")
            continue
        top = name[:-4]
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members = set(z.namelist())
            if any(not m.startswith(top + "/") for m in members):
                bad.append(f"{name}: a member is outside {top}/")
            version = z.read(f"{top}/VERSION.txt").decode() if f"{top}/VERSION.txt" in members else ""
            if not version.split("\n", 1)[0].endswith(stamp):
                bad.append(f"{name}: VERSION.txt does not carry the stamp {stamp}")
            if name.startswith("AgentTeams_"):
                if version.split("\n", 1)[0] != f"AgentTeams V{files_v} {stamp}":
                    bad.append(f"{name}: VERSION.txt does not start with 'AgentTeams V{files_v} {stamp}'")
                src = Path("AgentTeams")
            else:
                src = Path("problems") / name.split("-team_")[0] / "team"
            for p in sorted(src.rglob("*")):
                if p.is_file() and not any(x in (".DS_Store", ".stfolder", ".stignore") for x in p.parts):
                    arc = f"{top}/{p.relative_to(src).as_posix()}"
                    if arc not in members:
                        bad.append(f"{name}: {arc} missing")
                    elif z.read(arc) != p.read_bytes():
                        bad.append(f"{name}: {arc} differs from the committed file")
    return names, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--download-base", default=os.environ.get("DOWNLOAD_BASE"))
    ap.add_argument("--tries", type=int, default=8)
    ap.add_argument("--wait", type=float, default=15)
    a = ap.parse_args()
    stamp = a.tag.removeprefix("release/")
    base = (a.download_base or f"https://github.com/{a.repo}/releases/download").rstrip("/")
    bad = ["not run"]
    for n in range(a.tries):
        try:
            names, bad = check(base, a.tag, stamp)
        except Exception as why:  # release or CDN not ready yet
            bad = [f"{type(why).__name__}: {why}"]
        if not bad:
            print(f"live check ok: {', '.join(names)}")
            return
        print(f"try {n + 1}/{a.tries}: {len(bad)} problem(s), first: {bad[0]}")
        time.sleep(a.wait)
    print("\n".join(bad))
    sys.exit(1)


if __name__ == "__main__":
    main()
