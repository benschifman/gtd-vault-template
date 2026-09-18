#!/usr/bin/env python3
"""Health-check the CRM in 30-CRM/.

Reports gaps and inconsistencies. Read-only — never modifies anything.

Usage:
    python3 90-System/scripts/crm_lint.py [--json] [--limit N]
    python3 90-System/scripts/crm_lint.py --fix-dates [--write]
"""

import os
import re
import sys
import json
import glob
import difflib
from collections import defaultdict

import crm_lib as C

try:
    import yaml
    HAVE_YAML = True
except ImportError:                       # keep the script dependency-free
    HAVE_YAML = False

# Frontmatter that fails to parse is invisible to EVERY Base query — the file
# still looks fine in the editor, so this fails silently. Seen in the wild:
# `attendees: []` followed by `  - "[[Name]]"` list items, which killed the
# whole frontmatter including `category` and `date`.
SCALAR_THEN_LIST = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_ -]*):[ \t]*(\[\]|\S[^\n]*)[ \t]*\n(?=[ \t]*-[ \t])", re.M
)
TAB_INDENT = re.compile(r"^\t", re.M)

# Folders whose frontmatter drives Bases views.
FM_SCAN_GLOBS = [
    "30-CRM/30-10-People/*.md",
    "30-CRM/30-20-Organizations/*.md",
    "10-Journal/10-10-Events/*.md",
]


def frontmatter_problems(path):
    """Return a short reason string if this file's frontmatter is broken."""
    text = C.read_note(path)
    if not text.startswith("---"):
        return None                        # no frontmatter is a different issue
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "unterminated frontmatter block"
    fm = parts[1]

    m = SCALAR_THEN_LIST.search(fm)
    if m:
        val = m.group(2).strip()
        kind = "empty-list `[]`" if val == "[]" else f"scalar {val[:20]!r}"
        return f"`{m.group(1)}:` set to {kind} but followed by list items"
    if TAB_INDENT.search(fm):
        return "tab indentation (YAML requires spaces)"

    if HAVE_YAML:
        try:
            yaml.safe_load(fm)
        except yaml.YAMLError as e:
            first = str(e).splitlines()[0]
            return f"YAML parse error: {first[:70]}"
    return None

# A body with less than this many characters of real prose (after stripping
# template scaffolding) counts as empty.
MIN_BODY_CHARS = 60

SCAFFOLD = [
    "## Photo", "## Background", "## Relationship", "## Meetings",
    "## Overview", "## People", "## Notes",
    "![[Events.base#Meetings-with-this-file]]",
    "![[People.base#LinksToNote]]",
]


def prose_length(body):
    text = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)  # embeds incl. photos
    for token in SCAFFOLD:
        text = text.replace(token, "")
    return len(text.strip())


def photo_refs(person):
    """Photo filenames referenced by a person file, from frontmatter or body."""
    refs = set(C.wikilinks(C.field_block(person["fm"], "photo")))
    refs |= set(C.wikilinks(person["body"]))
    return {r for r in refs if re.search(r"\.(webp|png|jpe?g|gif|avif)$", r, re.I)}


def lint():
    people = C.load_people()
    orgs = C.load_orgs()
    findings = defaultdict(list)

    # --- broken frontmatter (checked first: it makes every other check lie) ---
    for pattern in FM_SCAN_GLOBS:
        for path in sorted(glob.glob(os.path.join(C.VAULT, pattern))):
            if os.path.basename(path).startswith("_"):
                continue
            why = frontmatter_problems(path)
            if why:
                findings["broken_frontmatter"].append(f"{C.stem(path)} — {why}")

    # --- people gaps (schema-aware: checks both current and legacy fields) ---
    for p in people:
        schema = C.schema_of(p["fm"])
        if schema == "legacy":
            findings["people_legacy_schema"].append(p["name"])
        elif schema == "unknown":
            findings["people_unknown_schema"].append(p["name"])
        if not C.has_either(p["fm"], "organization"):
            findings["people_no_org"].append(p["name"])
        if not C.has_either(p["fm"], "role"):
            findings["people_no_role"].append(p["name"])
        if not C.has_value(p["fm"], "email"):
            findings["people_no_email"].append(p["name"])
        if C.has_value(p["fm"], "email") and not C.has_value(p["fm"], "emails"):
            findings["people_missing_emails_field"].append(p["name"])
        if prose_length(p["body"]) < MIN_BODY_CHARS:
            findings["people_empty_background"].append(p["name"])
        if not photo_refs(p):
            findings["people_no_photo"].append(p["name"])

    # --- missing org pages ---
    aliases = C.org_alias_map()
    refs = defaultdict(list)
    for p in people:
        for org in C.orgs_referenced_by(p):
            refs[org].append(p["name"])
    for org, who in refs.items():
        if not aliases.get(org.lower()):
            noun = "person" if len(who) == 1 else "people"
            findings["orgs_missing_page"].append(f"{org} ({len(who)} {noun})")

    # --- org gaps ---
    for o in orgs:
        if not C.has_value(o["fm"], "key_contacts"):
            findings["orgs_no_key_contacts"].append(o["name"])
        if prose_length(o["body"]) < MIN_BODY_CHARS:
            findings["orgs_empty_overview"].append(o["name"])


    # --- relational checks: things a single file cannot reveal ---
    import difflib as _dl
    meetings = C.meetings_by_person()
    dom2org = C.domain_to_org()
    by_email = defaultdict(list)

    for p in people:
        fm = p["fm"]
        addrs = C.EMAIL_RE.findall(C.field_block(fm, "emails")) or \
                C.EMAIL_RE.findall(C.field_block(fm, "email"))
        for a in addrs:
            by_email[a.lower()].append(p["name"])

        primary = C.scalar(fm, "email")
        if "@" in primary:
            local, _, host = primary.partition("@")
            # Name/address disagreement — how every misspelled filename so far
            # was caught (Mota/Mora, Kenen/Kenan, Jiminez/Jimenez).
            flat = re.sub(r"[^a-z]", "", local.lower())
            first = re.sub(r"[^a-z]", "", p["name"].split()[0].lower())
            last = re.sub(r"[^a-z]", "", p["name"].split()[-1].lower())
            if last and last not in flat and first not in flat:
                if _dl.SequenceMatcher(None, last, flat).ratio() > 0.55:
                    findings["name_email_mismatch"].append(
                        f"{p['name']} — address is {primary} (filename may be misspelled)")
            # Employer drift — address domain belongs to an org this person
            # does not list as current or prior.
            expected = dom2org.get(host.lower())
            if expected:
                known = C.orgs_referenced_by(p)
                if known and expected not in known:
                    findings["email_org_conflict"].append(
                        f"{p['name']} — {primary} implies {expected}, file says {known}")

        # Relationship context for people Jordan actually meets.
        seen = meetings.get(p["name"], [])
        if len(seen) >= 3:
            m = re.search(r"## Relationship(.*?)(?=^## |\Z)", p["body"], re.S | re.M)
            txt = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip() if m else ""
            if len(txt) < 40:
                findings["frequent_no_relationship"].append(
                    f"{p['name']} — {len(seen)} meetings, no relationship context")

        # last_contact behind the meeting record (safe to auto-fix).
        if seen:
            newest = max(x[:10] for x in seen)
            lc = C.scalar(fm, "last_contact")[:10]
            if lc and lc < newest:
                findings["stale_last_contact"].append(
                    f"{p['name']} — last_contact {lc}, most recent meeting {newest}")

    for addr, who in by_email.items():
        if len(who) > 1:
            findings["shared_email"].append(f"{addr} — {', '.join(who)}")

    # key_contacts pointing at someone whose file never mentions the org.
    # An org legitimately lists alumni, so `prior_organizations` counts too.
    by_name = {p["name"]: p for p in people}
    for o in orgs:
        for kc in C.wikilinks(C.field_block(o["fm"], "key_contacts")):
            p = by_name.get(kc)
            if not p:
                findings["orphan_key_contact"].append(f"{o['name']} — [[{kc}]] has no person file")
                continue
            known = C.orgs_referenced_by(p)
            if known and o["name"] not in known:
                findings["orphan_key_contact"].append(
                    f"{o['name']} — lists {kc}, whose file references {known}")

    # --- possible duplicate people ---
    names = [p["name"] for p in people]
    seen = set()
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
            if ratio >= 0.87:
                seen.add(key)
                findings["possible_duplicate_people"].append(f"{a}  ≈  {b}")

    # --- broken photo references ---
    on_disk = {os.path.basename(f) for f in glob.glob(os.path.join(C.IMAGES_DIR, "*"))}
    for p in people:
        for ref in photo_refs(p):
            if os.path.basename(ref) not in on_disk:
                findings["broken_photo_refs"].append(f"{p['name']} -> {ref}")

    return people, orgs, findings


LABELS = [
    ("broken_frontmatter", "BROKEN FRONTMATTER — file is invisible to all Bases queries"),
    ("people_missing_emails_field", "People with `email` but no `emails` array (breaks Granola attendee linking)"),
    ("orgs_missing_page", "Organizations referenced with no page"),
    ("possible_duplicate_people", "Possible duplicate people (verify before merging)"),
    ("name_email_mismatch", "Filename disagrees with the person's own email address"),
    ("shared_email", "Same address on more than one person file"),
    ("email_org_conflict", "Email domain implies an org the file does not list"),
    ("orphan_key_contact", "Org key_contact whose file never mentions that org"),
    ("frequent_no_relationship", "3+ meetings but no relationship context"),
    ("stale_last_contact", "last_contact behind the meeting record (auto-fixable)"),
    ("broken_photo_refs", "Photo references with no file in 90-System/images/"),
    ("people_no_org", "People with no organization"),
    ("people_no_role", "People with no role"),
    ("people_no_email", "People with no email"),
    ("people_no_photo", "People with no photo"),
    ("people_empty_background", "People with an empty Background"),
    ("orgs_no_key_contacts", "Organizations with no key_contacts"),
    ("orgs_empty_overview", "Organizations with an empty Overview"),
    ("people_legacy_schema", "People on the legacy (Face cards) schema"),
    ("people_unknown_schema", "People on an unrecognized schema"),
]



def fix_last_contact(apply=False):
    """Set `last_contact` to the date of each person's most recent meeting.

    Purely mechanical — the meeting notes are the authority — so this is the
    one lint finding safe to fix without judgment.
    """
    meetings = C.meetings_by_person()
    changed = []
    for p in C.load_people():
        seen = meetings.get(p["name"], [])
        if not seen:
            continue
        newest = max(x[:10] for x in seen)
        current = C.scalar(p["fm"], "last_contact")[:10]
        if current and current >= newest:
            continue
        if not re.search(r"^last_contact:", p["fm"], re.M):
            continue
        changed.append((p["name"], current or "(blank)", newest))
        if apply:
            text = C.read_note(p["path"])
            head, _, rest = text.partition("---")
            fm, _, body = rest.partition("---")
            fm = re.sub(r"^last_contact:.*$", f"last_contact: {newest}", fm, count=1, flags=re.M)
            with open(p["path"], "w", encoding="utf-8") as fh:
                fh.write(head + "---" + fm + "---" + body)
    verb = "Updated" if apply else "Would update"
    print(f"{verb} last_contact on {len(changed)} people")
    for name, old, new in changed:
        print(f"  {name:<28} {old} -> {new}")
    if not apply and changed:
        print("\nDry run. Re-run with --fix-dates --write to apply.")


def main():
    if "--fix-dates" in sys.argv:
        fix_last_contact(apply="--write" in sys.argv)
        return

    limit = 15
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    people, orgs, findings = lint()

    if "--json" in sys.argv:
        print(json.dumps({
            "totals": {"people": len(people), "organizations": len(orgs)},
            "findings": {k: v for k, v in findings.items()},
        }, indent=2))
        return

    print(f"CRM lint — {len(people)} people, {len(orgs)} organizations\n")
    for key, label in LABELS:
        items = findings.get(key, [])
        if not items:
            print(f"✅ {label}: none")
            continue
        print(f"⚠️  {label}: {len(items)}")
        for item in sorted(items)[:limit]:
            print(f"      {item}")
        if len(items) > limit:
            print(f"      … +{len(items) - limit} more (use --limit to see more)")
        print()


if __name__ == "__main__":
    main()
