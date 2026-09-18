#!/usr/bin/env python3
"""List organizations wikilinked from person frontmatter that have no page.

Sorted by how many people reference them, so the highest-leverage pages
get written first. Alias-aware: an org already covered by an existing
page's `aliases:` field is not reported as missing.

Usage:
    python3 90-System/scripts/crm_missing_orgs.py [--json]
"""

import sys
import json
from collections import defaultdict

import crm_lib as C


def find_missing():
    aliases = C.org_alias_map()
    refs = defaultdict(list)

    for person in C.load_people():
        for org in C.orgs_referenced_by(person):
            refs[org].append(person["name"])

    missing, covered = {}, {}
    for org, people in refs.items():
        canonical = aliases.get(org.lower())
        if canonical:
            covered.setdefault(canonical, []).extend(people)
        else:
            missing[org] = sorted(people)

    return missing, covered


def main():
    missing, covered = find_missing()
    ranked = sorted(missing.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    if "--json" in sys.argv:
        print(json.dumps(
            [{"org": o, "count": len(p), "people": p} for o, p in ranked],
            indent=2,
        ))
        return

    if not ranked:
        print("No missing organization pages. ✅")
    else:
        print(f"{len(ranked)} organizations referenced with no page:\n")
        for org, people in ranked:
            shown = ", ".join(people[:6])
            more = f", +{len(people) - 6} more" if len(people) > 6 else ""
            print(f"  [{len(people):>2}]  {org}")
            print(f"        referenced by: {shown}{more}")

    # Near-duplicate names among the missing orgs — the same body referenced
    # under two spellings. Creating a page for each would fork the CRM.
    import difflib
    names = [o for o, _ in ranked]
    dupes, seen = [], set()
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            aw, bw = set(a.lower().split()), set(b.lower().split())
            overlap = len(aw & bw) / max(1, min(len(aw), len(bw)))
            ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
            if overlap >= 0.75 or ratio >= 0.8:
                seen.add(key)
                dupes.append((a, b))
    if dupes:
        print(f"\n⚠️  {len(dupes)} possible duplicate org names — resolve to ONE page before writing:")
        for a, b in dupes:
            print(f"      {a}\n        ≈ {b}")

    if covered:
        print(f"\n{len(covered)} referenced via an existing page's alias (no action needed):")
        for org, people in sorted(covered.items()):
            print(f"  {org} ({len(people)})")


if __name__ == "__main__":
    main()
