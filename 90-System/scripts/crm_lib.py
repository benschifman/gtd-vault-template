"""Shared helpers for CRM scripts. Parses person/organization frontmatter
without requiring Obsidian to be running.

Deliberately dependency-free (no pyyaml) so these run anywhere.
"""

import os
import re
import glob

VAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PEOPLE_DIR = os.path.join(VAULT, "30-CRM", "30-10-People")
ORGS_DIR = os.path.join(VAULT, "30-CRM", "30-20-Organizations")
IMAGES_DIR = os.path.join(VAULT, "90-System", "images")

# The CRM contains two person schemas. Tooling must read both.
#
#   "current" (category: person)  — organization / role / linkedin / status ...
#   "legacy"  (Face cards import) — organizations_current / title / linkedin_id ...
#
# Both share created / email / phone / photo.
CURRENT_ORG_FIELDS = ("organization", "prior_organizations")
LEGACY_ORG_FIELDS = ("organizations_current", "organizations_former")
ORG_FIELDS = CURRENT_ORG_FIELDS + LEGACY_ORG_FIELDS

# Equivalent fields across the two schemas, current name first.
EQUIVALENT = {
    "organization": ("organization", "organizations_current"),
    "prior_organizations": ("prior_organizations", "organizations_former"),
    "role": ("role", "title"),
    "linkedin": ("linkedin", "linkedin_id"),
    "first_name": ("first_name", "first name"),
    "last_name": ("last_name", "last name"),
}


def schema_of(fm):
    """'current', 'legacy', or 'unknown' for a person frontmatter block."""
    if re.search(r"^category:\s*person\s*$", fm, re.M):
        return "current"
    if re.search(r"^(full name|organizations_current):", fm, re.M):
        return "legacy"
    return "unknown"


def split_frontmatter(text):
    """Return (frontmatter, body). Both empty-safe."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def read_note(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# A top-level YAML key at column 0. Legacy files use keys containing spaces
# ("full name", "partner of"), so the character class must allow them —
# otherwise a field block swallows every following space-named field.
_NEXT_KEY = r"^[A-Za-z_][A-Za-z0-9_ ]*:"


def field_block(fm, key):
    """Return the raw text of a frontmatter field, including any
    indented list items that follow it on subsequent lines."""
    m = re.search(
        rf"^{re.escape(key)}:(.*?)(?={_NEXT_KEY}|\Z)",
        fm,
        re.S | re.M,
    )
    return m.group(1) if m else ""


def scalar(fm, key):
    """Value of a simple scalar field, stripped of quotes. '' if absent/blank."""
    m = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", fm, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'").strip()


def has_value(fm, key):
    """True if the field has a scalar value OR a non-empty list."""
    block = field_block(fm, key)
    if not block:
        return False
    # strip an inline empty list marker like `key: []`
    stripped = block.strip()
    if stripped in ("", "[]", '""', "''"):
        return False
    if re.search(r"^\s*-\s+\S", block, re.M):
        return True
    first = stripped.splitlines()[0].strip() if stripped.splitlines() else ""
    return bool(first) and first != "[]"


def wikilinks(text):
    """All wikilink targets in text, aliases and headings stripped."""
    return [t.strip() for t in re.findall(r"\[\[([^\]|#]+)", text)]


def person_files():
    """Person notes only. Files starting with `_` are index/dashboard notes
    (e.g. `_people.md`, which just embeds People.base), not contacts."""
    return sorted(
        f for f in glob.glob(os.path.join(PEOPLE_DIR, "*.md"))
        if not os.path.basename(f).startswith("_")
    )


def org_files():
    return sorted(glob.glob(os.path.join(ORGS_DIR, "*.md")))


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def load_people():
    """[{name, path, fm, body}] for every person file."""
    out = []
    for path in person_files():
        text = read_note(path)
        fm, body = split_frontmatter(text)
        out.append({"name": stem(path), "path": path, "fm": fm, "body": body})
    return out


def load_orgs():
    out = []
    for path in org_files():
        text = read_note(path)
        fm, body = split_frontmatter(text)
        out.append({"name": stem(path), "path": path, "fm": fm, "body": body})
    return out


def has_either(fm, logical_key):
    """True if any schema's variant of a logical field has a value.

    e.g. has_either(fm, "organization") checks `organization` (current schema)
    and `organizations_current` (legacy schema).
    """
    for key in EQUIVALENT.get(logical_key, (logical_key,)):
        if has_value(fm, key):
            return True
    return False


def orgs_referenced_by(person):
    """Distinct org names wikilinked from a person's organization fields,
    across both schemas."""
    names = []
    for key in ORG_FIELDS:
        names.extend(wikilinks(field_block(person["fm"], key)))
    seen, out = set(), []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def org_alias_map():
    """Map every org page name AND alias -> canonical page name, lowercased."""
    mapping = {}
    for org in load_orgs():
        mapping[org["name"].lower()] = org["name"]
        for alias in re.findall(r"^\s*-\s*(.+)$", field_block(org["fm"], "aliases"), re.M):
            alias = alias.strip().strip("\"'").strip()
            if alias:
                mapping[alias.lower()] = org["name"]
        inline = scalar(org["fm"], "aliases")
        if inline and inline != "[]":
            for alias in inline.strip("[]").split(","):
                alias = alias.strip().strip("\"'").strip()
                if alias:
                    mapping[alias.lower()] = org["name"]
    return mapping


def rel(path):
    return os.path.relpath(path, VAULT)

EVENTS_DIR = os.path.join(VAULT, "10-Journal", "10-10-Events")

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def event_files():
    return sorted(glob.glob(os.path.join(EVENTS_DIR, "*.md")))


def load_events():
    """[{name, path, fm, body, text}] for every meeting note."""
    out = []
    for path in event_files():
        text = read_note(path)
        fm, body = split_frontmatter(text)
        out.append({"name": stem(path), "path": path, "fm": fm,
                    "body": body, "text": text})
    return out


def meetings_by_person(events=None):
    """{person name -> [meeting note names]}, from attendee wikilinks."""
    events = events if events is not None else load_events()
    out = {}
    for e in events:
        for link in wikilinks(field_block(e["fm"], "attendees")):
            out.setdefault(link, []).append(e["name"])
    return {k: sorted(v) for k, v in out.items()}


def domain_to_org():
    """{email domain -> org page name}, derived from each org page's `url:`.

    Built from the vault rather than a hardcoded list, so it stays correct as
    orgs are added. Generic hosts are excluded — a gmail address says nothing
    about an employer.
    """
    generic = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
               "icloud.com", "proton.me", "protonmail.com", "me.com", "aol.com"}
    out = {}
    for org in load_orgs():
        url = scalar(org["fm"], "url")
        m = re.search(r"https?://(?:www\.)?([^/\s]+)", url)
        if not m:
            continue
        host = m.group(1).lower()
        if host in generic:
            continue
        out[host] = org["name"]
    return out
