#!/usr/bin/env python3
"""Create a vault note from a template in 90-System/templates/.

The templates use Notebook Navigator's built-in placeholder syntax
({{date:YYYY-MM-DD}}, {{title}}, {{time}}, ...). Notebook Navigator renders
them when Jordan creates a note in Obsidian; this script renders the same
placeholders so Claude Code skills can create notes from the same templates
without Obsidian running. The template stays the single source of truth —
never hand-write frontmatter that a template already defines.

Supports the placeholders NN documents: {{date}}, {{date:FORMAT}}, {{time}},
{{title}}, {{today}}, {{yesterday}}, {{tomorrow}}, {{monday}}, {{sunday}},
{{now}}, {{folder}}, {{path}}. {{cursor}} is stripped. FORMAT is a moment.js
format string; the tokens the vault's templates use are all supported.

--date sets the date the placeholders resolve against, so a backdated daily
note gets the right `created`/`date` fields and the right path.

Refuses to overwrite an existing file.

Usage:
    python3 90-System/scripts/new_from_template.py TEMPLATE DEST [--date YYYY-MM-DD] [--title T]

    TEMPLATE  name in 90-System/templates/ (with or without .md) or a path
    DEST      vault-relative path of the note to create (.md optional)

Examples:
    python3 90-System/scripts/new_from_template.py daily-note 10-Journal/2026/09/2026-09-18
    python3 90-System/scripts/new_from_template.py project "20-GTD/20-10-Projects/Ship the thing"
    python3 90-System/scripts/new_from_template.py daily-note 10-Journal/2026/09/2026-09-17 --date 2026-09-17

Prints the created path on success.
"""

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
TEMPLATES = VAULT / "90-System" / "templates"

# moment.js token -> strftime (or callable). Longest tokens first.
_MOMENT = [
    ("YYYY", "%Y"), ("YY", "%y"),
    ("MMMM", "%B"), ("MMM", "%b"), ("MM", "%m"), ("M", lambda d: str(d.month)),
    ("DDDD", "%j"), ("DD", "%d"), ("D", lambda d: str(d.day)),
    ("dddd", "%A"), ("ddd", "%a"), ("d", lambda d: str((d.weekday() + 1) % 7)),
    ("HH", "%H"), ("H", lambda d: str(d.hour)),
    ("hh", "%I"), ("h", lambda d: str(int(d.strftime("%I")))),
    ("mm", "%M"), ("ss", "%S"),
    ("A", "%p"), ("a", lambda d: d.strftime("%p").lower()),
    ("WW", lambda d: f"{d.isocalendar()[1]:02d}"), ("W", lambda d: str(d.isocalendar()[1])),
    ("ww", lambda d: f"{d.isocalendar()[1]:02d}"), ("w", lambda d: str(d.isocalendar()[1])),
    ("GGGG", lambda d: str(d.isocalendar()[0])), ("gggg", lambda d: str(d.isocalendar()[0])),
    ("Q", lambda d: str((d.month - 1) // 3 + 1)),
]
_TOKEN_RE = re.compile("|".join(re.escape(t) for t, _ in _MOMENT))
_MAP = dict(_MOMENT)


def moment_format(fmt: str, dt: datetime) -> str:
    """Render a moment.js format string. [text] is a literal."""
    out = []
    pos = 0
    for lit in re.finditer(r"\[([^\]]*)\]", fmt):
        out.append(_render_tokens(fmt[pos:lit.start()], dt))
        out.append(lit.group(1))
        pos = lit.end()
    out.append(_render_tokens(fmt[pos:], dt))
    return "".join(out)


def _render_tokens(chunk: str, dt: datetime) -> str:
    def sub(m):
        spec = _MAP[m.group(0)]
        return spec(dt) if callable(spec) else dt.strftime(spec)
    return _TOKEN_RE.sub(sub, chunk)


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(VAULT))
    except ValueError:
        return str(p)


def render(text: str, dt: datetime, title: str, dest: Path) -> str:
    def repl(m):
        key, arg = m.group(1), m.group(2)
        if key == "date":
            return moment_format(arg or "YYYY-MM-DD", dt)
        if key == "time":
            return moment_format(arg or "HH:mm", dt)
        if key == "now":
            return moment_format(arg or "YYYY-MM-DD HH:mm", dt)
        if key == "today":
            return moment_format(arg or "YYYY-MM-DD", dt)
        if key == "yesterday":
            return moment_format(arg or "YYYY-MM-DD", dt - timedelta(days=1))
        if key == "tomorrow":
            return moment_format(arg or "YYYY-MM-DD", dt + timedelta(days=1))
        if key == "monday":
            return moment_format(arg or "YYYY-MM-DD", dt - timedelta(days=dt.weekday()))
        if key == "sunday":
            return moment_format(arg or "YYYY-MM-DD", dt + timedelta(days=6 - dt.weekday()))
        if key == "title":
            return title
        if key == "folder":
            return dest.parent.name
        if key == "path":
            return _rel(dest.parent)
        if key == "cursor":
            return ""
        return m.group(0)  # unknown placeholder: leave it visible
    return re.sub(r"\{\{(\w+)(?::([^}]*))?\}\}", repl, text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("dest")
    ap.add_argument("--date", help="YYYY-MM-DD the date placeholders resolve to (default: today)")
    ap.add_argument("--title", help="value for {{title}} (default: DEST filename)")
    a = ap.parse_args()

    tpl = Path(a.template)
    if not tpl.suffix:
        tpl = tpl.with_suffix(".md")
    if not tpl.is_absolute() and not tpl.exists():
        tpl = TEMPLATES / tpl.name
    if not tpl.exists():
        sys.exit(f"template not found: {tpl}")

    dest = Path(a.dest)
    if not dest.suffix:
        dest = dest.with_suffix(".md")
    if not dest.is_absolute():
        dest = VAULT / dest
    if dest.exists():
        sys.exit(f"refusing to overwrite existing file: {_rel(dest)}")

    if a.date:
        d = date.fromisoformat(a.date)
        now = datetime.now()
        dt = datetime(d.year, d.month, d.day, now.hour, now.minute, now.second)
    else:
        dt = datetime.now()

    text = render(tpl.read_text(), dt, a.title or dest.stem, dest)
    if "<%" in text:
        sys.exit(f"template still contains Templater syntax: {tpl.name}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    print(_rel(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
