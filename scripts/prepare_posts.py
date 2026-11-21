#!/usr/bin/env python3
"""Assign concise, stable post URLs at build time.

Existing explicit permalinks always win. For a new article, use one
distinctive word from its title, falling back to a short two-word slug
and then a numeric suffix to avoid collisions.

Authors can choose any exact path with either:
  permalink: /my-slug/
or:
  slug: my-slug
"""
from pathlib import Path
import re
import unicodedata
import yaml

POSTS = Path("_posts")
STOP = set("""
a an and as at be been being but by can did do does for from get how i if in is
it its my of on or our out the their them there these this those to was we were
what when where which who why with you your about after all are before better
build building business businesses freelance freelancer freelancers work working
new notes post posts things thing thoughts think thinking thoughts learned
learning some more most one that tell they way ways will would should could
""".split())
reserved = set()
files = sorted(list(POSTS.glob("*.md")) + list(POSTS.glob("*.markdown")))
for file in files:
    text = file.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        continue
    info = yaml.safe_load(m.group(1)) or {}
    manual = str(info.get("permalink") or "").strip("/")
    if manual:
        reserved.add(manual)

def slugify(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

for file in files:
    text = file.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        continue
    info = yaml.safe_load(m.group(1)) or {}
    if info.get("permalink"):
        continue
    original = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", file.stem)
    provided = slugify(info.get("slug", ""))
    if provided:
        candidate = provided
    else:
        words = re.findall(r"[a-z0-9]+", slugify(info.get("title", original)))
        meaningful = [w for w in words if w not in STOP and not w.isdigit() and len(w) > 2]
        choices = meaningful or [w for w in words if len(w) > 2] or ["post"]
        candidate = choices[0]
        if candidate in reserved and len(choices) > 1:
            candidate = "-".join(choices[:2])
    root = candidate
    number = 2
    while candidate in reserved or candidate in {"hyperlinks", "assets", "feed", "field-journal"}:
        candidate = f"{root}-{number}"
        number += 1
    reserved.add(candidate)
    addition = f"permalink: /{candidate}/\n"
    if original != candidate and "redirect_from" not in info:
        addition += f"redirect_from:\n  - /{original}/\n"
    updated = text[:m.start(1)] + m.group(1).rstrip() + "\n" + addition + text[m.end(1):]
    file.write_text(updated, encoding="utf-8")
    print(f"{file}: /{candidate}/")
