#!/usr/bin/env python3
"""People named as meeting attendees who have no CRM file.

This is the main signal for "who needs a CRM entry", and the thing that makes
the system compound: the Granola sync plugin matches future attendees against
person files by their `emails` array, so every entry created here makes the
next meeting note link itself.

Works with Obsidian closed — it resolves links by filename rather than through
the metadata cache.

Usage:
    python3 90-System/scripts/crm_unresolved_attendees.py [--json] [--all]

    --all   include one-off names; default hides names seen only once that
            look like bare handles (no space), which are usually Granola
            artefacts rather than people.
"""

import os
import re
import sys
import json
import glob
from collections import defaultdict

import crm_lib as C

EVENTS = os.path.join(C.VAULT, "10-Journal", "10-10-Events")

# Room and resource names Granola records as attendees.
NOT_A_PERSON = re.compile(
    r"\b(conference|room|zoom|floor|huddle|boardroom|phone|line|\d{3})\b", re.I
)


def person_filenames():
    return {C.stem(p) for p in C.person_files()}


def main():
    show_all = "--all" in sys.argv
    known = person_filenames()
    # Aliases resolve in Obsidian's UI for display, but a link to an alias does
    # NOT register in the link graph — so only real filenames count here.
    refs = defaultdict(list)

    for path in sorted(glob.glob(os.path.join(EVENTS, "*.md"))):
        text = C.read_note(path)
        fm, _ = C.split_frontmatter(text)
        block = C.field_block(fm, "attendees")
        for link in re.findall(r"\[\[([^\]]+)\]\]", block):
            name = link.split("|")[0].strip()
            if name and name not in known:
                refs[name].append(C.stem(path))

    rows = sorted(refs.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    if not show_all:
        rows = [(n, m) for n, m in rows
                if not (len(m) == 1 and " " not in n) and not NOT_A_PERSON.search(n)]

    if "--json" in sys.argv:
        print(json.dumps([{"name": n, "count": len(m), "meetings": m} for n, m in rows], indent=2))
        return

    if not rows:
        print("No unresolved meeting attendees. ✅")
        print("Every person named in every meeting note has a CRM file.")
        return

    print(f"{len(rows)} people named in meetings with no CRM file:\n")
    for name, meetings in rows:
        flag = "  ⚠ bare handle — identify before creating" if " " not in name else ""
        print(f"  [{len(meetings):>2}]  {name}{flag}")
        for m in meetings[:3]:
            print(f"        {m}")
        if len(meetings) > 3:
            print(f"        … +{len(meetings) - 3} more")
    if not show_all:
        print("\n(one-off bare handles hidden; use --all to see them)")


if __name__ == "__main__":
    main()
