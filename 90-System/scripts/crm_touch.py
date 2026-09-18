#!/usr/bin/env python3
"""Advance `last_contact` on CRM person files from calendar and sent-mail touchpoints.

Companion to `crm_lint.py --fix-dates`, which uses curated meeting notes as the
authority. This covers the two sources that never become meeting notes: calendar
events Jordan attended, and mail Jordan sent. The touchpoints themselves come from the
Google Calendar and Gmail MCP connectors (only Claude can call those), written to a
JSON file that this script consumes:

    [{"email": "taylor@example.org", "date": "2026-09-09", "source": "calendar"},
     {"email": "casey.morgan@mail.house.gov", "date": "2026-09-11", "source": "sent"}]

Usage:
    python3 90-System/scripts/crm_touch.py touchpoints.json            # dry run
    python3 90-System/scripts/crm_touch.py touchpoints.json --write    # apply

Rules, matching fix_last_contact:
  - a person's `last_contact` only ever moves forward;
  - a file with no `last_contact:` key is reported, not modified;
  - matching is on the `emails` array and `email` scalar, case-insensitive.

Emails that match no person are reported grouped by domain -- that list is the
set of people Jordan is actually in contact with who have no CRM file, which is a
better enrichment queue than any lint finding.
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crm_lib as C  # noqa: E402

OWN = {"jordan@meridianpolicy.org", "jordan.lee@example.com"}
NOISE = re.compile(
    r"(no-?reply|noreply|calendar-invite|calendar-notification|drive-shares|"
    r"@calendar\.google\.com|@group\.calendar\.google\.com|@resource\.calendar\.google\.com|"
    r"@luma-mail\.com|@lu\.ma$|mailer-daemon|notifications?@|@docs\.google\.com|"
    r"@superhuman\.com|conference@ifp\.org|allstaff@ifp\.org|dcstaff@ifp\.org)",
    re.I,
)


def email_index(people):
    idx = {}
    for p in people:
        addrs = set()
        s = C.scalar(p["fm"], "email")
        if s:
            addrs.add(s.lower())
        for line in C.field_block(p["fm"], "emails").splitlines():
            m = re.match(r"\s*-\s*['\"]?([^'\"\s]+)", line)
            if m:
                addrs.add(m.group(1).lower())
        for a in addrs:
            idx.setdefault(a, p)
    return idx


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    apply = "--write" in sys.argv
    touches = json.load(open(args[0], encoding="utf-8"))

    people = C.load_people()
    idx = email_index(people)

    newest = {}          # person name -> (date, source)
    unmatched = defaultdict(set)
    for t in touches:
        e = (t.get("email") or "").strip().lower()
        d = (t.get("date") or "")[:10]
        if not e or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            continue
        if e in OWN or NOISE.search(e):
            continue
        p = idx.get(e)
        if not p:
            unmatched[e.split("@")[-1]].add(e)
            continue
        cur = newest.get(p["name"])
        if not cur or d > cur[0]:
            newest[p["name"]] = (d, t.get("source", "?"))

    changed, nokey = [], []
    by_name = {p["name"]: p for p in people}
    for name, (d, src) in sorted(newest.items()):
        p = by_name[name]
        current = C.scalar(p["fm"], "last_contact")[:10]
        if current and current >= d:
            continue
        if not re.search(r"^last_contact:", p["fm"], re.M):
            nokey.append((name, d))
            continue
        changed.append((name, current or "(blank)", d, src))
        if apply:
            text = C.read_note(p["path"])            # full read before any write
            head, _, rest = text.partition("---")
            fm, _, body = rest.partition("---")
            fm = re.sub(r"^last_contact:.*$", f"last_contact: {d}", fm, count=1, flags=re.M)
            with open(p["path"], "w", encoding="utf-8") as fh:
                fh.write(head + "---" + fm + "---" + body)

    verb = "Updated" if apply else "Would update"
    print(f"{verb} last_contact on {len(changed)} people "
          f"({len(touches)} touchpoints, {len(newest)} matched a CRM file)")
    for name, old, new, src in changed:
        print(f"  {name:<30} {old} -> {new}   [{src}]")
    if nokey:
        print(f"\n{len(nokey)} matched people have no last_contact key (not modified):")
        for name, d in nokey:
            print(f"  {name}  ({d})")
    if unmatched:
        n = sum(len(v) for v in unmatched.values())
        print(f"\n{n} contacted addresses with no CRM file, by domain:")
        for dom, addrs in sorted(unmatched.items(), key=lambda kv: -len(kv[1]))[:15]:
            print(f"  {dom:<32} {', '.join(sorted(addrs))[:90]}")
    if not apply and changed:
        print("\nDry run. Re-run with --write to apply.")


if __name__ == "__main__":
    main()
