#!/usr/bin/env python3
"""
PKM scorer — deterministic quality checks for 40-PKM/40-30-Topics/.

Checks:
  Per-topic:
    - frontmatter_validity   required fields present (category, created, short_description)
    - description_quality    short_description is 10–120 words, no placeholder text
    - has_body               ## Body section exists and has content
    - link_syntax            no empty [[]] or malformed [[[ wikilinks

  Cross-topic:
    - link_resolution        every [[wikilink]] in related_topics resolves to an existing topic file
    - cross_ref_symmetry     if A lists B in related_topics, B lists A back
    - hub_threshold          any topic referenced 3+ times in source topics: fields must exist
    - source_coverage        every processed source lists >= 1 topic that resolves to a topic file

Usage:
    python3 90-System/scripts/score_pkm.py
    python3 90-System/scripts/score_pkm.py --json         # also write score_report.json
    python3 90-System/scripts/score_pkm.py --build        # also rebuild 40-PKM/catalog.jsonl
    python3 90-System/scripts/score_pkm.py --build-only   # rebuild catalog only, skip checks, exit 0
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to vault root — run from vault root)
# ---------------------------------------------------------------------------
VAULT = Path(__file__).parent.parent.parent
TOPICS_DIR = VAULT / "40-PKM" / "40-30-Topics"
SOURCES_DIR = VAULT / "40-PKM" / "40-20-Sources"
REPORT_PATH = VAULT / "90-System" / "scripts" / "score_report.json"
CATALOG_PATH = VAULT / "40-PKM" / "catalog.jsonl"

PLACEHOLDERS = {"todo", "tbd", "placeholder", "lorem", "fixme", "stub"}

# ---------------------------------------------------------------------------
# Frontmatter parser (stdlib only)
# ---------------------------------------------------------------------------

QUOTE_CHARS = "\"'“”‘’"  # straight + curly quotes


def _strip_quotes(s: str) -> str:
    return s.strip().strip(QUOTE_CHARS).strip()


def _parse_inline_array(val: str) -> list[str]:
    """Parse an inline YAML array like ["[[a]]","[[b]]"] (any quote style)."""
    inner = val.strip()[1:-1]
    return [_strip_quotes(item) for item in inner.split(",") if _strip_quotes(item)]


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from a markdown file. Returns a dict."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    result = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip blank lines
        if not line.strip():
            i += 1
            continue
        # Key: value line
        m = re.match(r'^(\w[\w_-]*):\s*(.*)', line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        # Check if next lines are list items (indented or at column 0)
        list_items = []
        j = i + 1
        while j < len(lines) and re.match(r'^\s*-\s+', lines[j]):
            item = _strip_quotes(re.sub(r'^\s*-\s+', '', lines[j]))
            list_items.append(item)
            j += 1
        if list_items:
            result[key] = list_items
            i = j
        elif val.startswith("[") and val.endswith("]") and not val.startswith("[["):
            result[key] = _parse_inline_array(val)
            i += 1
        else:
            result[key] = _strip_quotes(val)
            i += 1
    return result


def extract_wikilinks(text: str) -> list[str]:
    """Return all [[target]] targets from text (strips aliases: [[target|alias]] → target)."""
    raw = re.findall(r'\[\[([^\[\]]+)\]\]', text)
    return [r.split("|")[0].strip() for r in raw]


def topic_filename(name: str) -> str:
    """Convert a wikilink target to the expected .md filename."""
    return name + ".md"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_topics() -> dict[str, dict]:
    """Returns {stem: {frontmatter, body, path, text}} — only files with category: topic."""
    topics = {}
    for p in sorted(TOPICS_DIR.glob("*.md")):
        if p.stem.startswith("_"):
            continue
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm.get("category", "").lower() != "topic":
            continue
        body_match = re.search(r'^## Body', text, re.MULTILINE)
        body = text[body_match.end():].strip() if body_match else ""
        topics[p.stem] = {"fm": fm, "body": body, "path": p, "text": text}
    return topics


def load_sources() -> dict[str, dict]:
    """Returns {stem: {fm, path, topics}} for every source file. `topics` is the
    cleaned list from its Topics section, falling back to legacy YAML."""
    sources = {}
    for p in sorted(SOURCES_DIR.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        topics_section = re.search(
            r'^## Topics\s*\n(.*?)(?=^#{1,2} |\Z)', text, re.MULTILINE | re.DOTALL
        )
        topics_val = (extract_wikilinks(topics_section.group(1))
                      if topics_section else fm.get("topics", []))
        if isinstance(topics_val, str):
            topics_val = [topics_val] if topics_val else []
        cleaned = [t.strip("[]").split("|")[0].strip() for t in topics_val]
        sources[p.stem] = {"fm": fm, "path": p, "topics": [t for t in cleaned if t]}
    return sources


def source_topic_refs(sources: dict[str, dict]) -> dict[str, int]:
    """Count how many sources reference each topic wikilink target."""
    counts: dict[str, int] = {}
    for data in sources.values():
        for t in data["topics"]:
            counts[t] = counts.get(t, 0) + 1
    return counts


def is_processed(fm: dict) -> bool:
    return str(fm.get("processed", "")).lower() == "true"


# ---------------------------------------------------------------------------
# Per-topic checks
# ---------------------------------------------------------------------------

def check_frontmatter_validity(stem: str, data: dict) -> list[str]:
    fm = data["fm"]
    issues = []
    if fm.get("category", "").lower() not in ("topic",):
        issues.append(f"category is '{fm.get('category', '')}', expected 'topic'")
    if not fm.get("created"):
        issues.append("missing 'created' field")
    if not fm.get("short_description"):
        issues.append("missing 'short_description' field")
    if "modified" not in fm:
        issues.append("missing 'modified' field")
    return issues


def check_description_quality(stem: str, data: dict) -> list[str]:
    desc = data["fm"].get("short_description", "")
    if not desc:
        return []  # already caught by frontmatter check
    issues = []
    words = desc.split()
    if len(words) < 10:
        issues.append(f"short_description too brief ({len(words)} words, min 10)")
    if len(words) > 120:
        issues.append(f"short_description too long ({len(words)} words, max 120)")
    lower = desc.lower()
    for p in PLACEHOLDERS:
        if p in lower:
            issues.append(f"short_description contains placeholder '{p}'")
    return issues


def check_has_body(stem: str, data: dict) -> list[str]:
    body = data["body"]
    if not body or len(body.strip()) < 50:
        return ["## Body section missing or empty (< 50 chars)"]
    return []


def check_link_syntax(stem: str, data: dict) -> list[str]:
    text = data["text"]
    issues = []
    if "[[]]" in text:
        issues.append("contains empty [[]] wikilink")
    if "[[[" in text:
        issues.append("contains malformed [[[ wikilink")
    return issues


# ---------------------------------------------------------------------------
# Cross-topic checks
# ---------------------------------------------------------------------------

def check_link_resolution(topics: dict[str, dict]) -> list[str]:
    """All [[wikilinks]] in related_topics must resolve to an existing topic file."""
    issues = []
    for stem, data in topics.items():
        related = data["fm"].get("related_topics", [])
        if isinstance(related, str):
            related = [related]
        for link in related:
            target = link.strip("[]").split("|")[0].strip()
            if target not in topics:
                issues.append(f"{stem}: related_topics [[{target}]] does not resolve")
    return issues


def check_cross_ref_symmetry(topics: dict[str, dict]) -> list[str]:
    """If A lists B in related_topics, B must list A back."""
    # Build adjacency
    adj: dict[str, set[str]] = {}
    for stem, data in topics.items():
        related = data["fm"].get("related_topics", [])
        if isinstance(related, str):
            related = [related]
        targets = set()
        for link in related:
            t = link.strip("[]").split("|")[0].strip()
            if t in topics:
                targets.add(t)
        adj[stem] = targets

    issues = []
    for a, neighbors in adj.items():
        for b in neighbors:
            if a not in adj.get(b, set()):
                issues.append(f"symmetry: {a} → {b} but {b} does not list {a} back")
    return issues


def check_hub_threshold(topics: dict[str, dict], source_refs: dict[str, int], threshold: int = 3) -> list[str]:
    """Any topic referenced >= threshold times in sources must have a topic file."""
    issues = []
    for topic_name, count in source_refs.items():
        if count >= threshold and topic_name not in topics:
            issues.append(f"hub missing: '{topic_name}' referenced in {count} sources but has no topic file")
    return issues


def check_source_coverage(topics: dict[str, dict], sources: dict[str, dict]) -> list[str]:
    """Every source marked processed must list at least one topic that resolves
    to an existing topic file — otherwise it was marked done without ever being
    wired into the wiki."""
    # Obsidian resolves links case-insensitively; match the same way
    topic_lookup = {stem.casefold() for stem in topics}
    issues = []
    for stem, data in sources.items():
        if not is_processed(data["fm"]):
            continue
        if not data["topics"]:
            issues.append(f"{stem}: processed but topic assignments are empty")
        elif not any(t.casefold() in topic_lookup for t in data["topics"]):
            issues.append(f"{stem}: processed but none of its topics resolve to a topic file "
                          f"({', '.join(data['topics'])})")
    return issues


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def build_catalog(topics: dict[str, dict], sources: dict[str, dict]) -> int:
    """Write 40-PKM/catalog.jsonl — one JSON object per topic and per source.
    Lets agents survey the wiki (grep/jq) without Obsidian running."""
    lines = []
    # Reverse map: topic stem -> source stems whose topics: field references it
    topic_lookup = {stem.casefold(): stem for stem in topics}
    topic_sources: dict[str, list[str]] = {stem: [] for stem in topics}
    for src_stem, data in sorted(sources.items()):
        for t in data["topics"]:
            resolved = topic_lookup.get(t.casefold())
            if resolved:
                topic_sources[resolved].append(src_stem)

    for stem, data in sorted(topics.items()):
        fm = data["fm"]
        related = fm.get("related_topics", [])
        if isinstance(related, str):
            related = [related] if related else []
        lines.append({
            "kind": "topic",
            "path": str(data["path"].relative_to(VAULT)),
            "title": stem,
            "short_description": fm.get("short_description", ""),
            "related_topics": [r.strip("[]").split("|")[0].strip() for r in related],
            "sources": topic_sources[stem],
            "source_count": len(topic_sources[stem]),
            "modified": fm.get("modified", ""),
        })
    for stem, data in sorted(sources.items()):
        fm = data["fm"]
        lines.append({
            "kind": "source",
            "path": str(data["path"].relative_to(VAULT)),
            "title": fm.get("title", stem),
            "short_description": fm.get("short_description", ""),
            "topics": data["topics"],
            "processed": is_processed(fm),
        })

    with CATALOG_PATH.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return len(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    write_json = "--json" in sys.argv
    build = "--build" in sys.argv
    build_only = "--build-only" in sys.argv

    print(f"Loading topics from {TOPICS_DIR.relative_to(VAULT)} ...")
    topics = load_topics()
    print(f"  {len(topics)} topic files found")

    print(f"Loading sources from {SOURCES_DIR.relative_to(VAULT)} ...")
    sources = load_sources()
    print(f"  {len(sources)} source files found")
    source_refs = source_topic_refs(sources)

    if build_only:
        n = build_catalog(topics, sources)
        print(f"\nCatalog written to {CATALOG_PATH.relative_to(VAULT)} ({n} entries)")
        return

    report = {
        "topics_checked": len(topics),
        "per_topic": {},
        "cross_topic": {},
        "summary": {}
    }

    # --- Per-topic ---
    per_topic_issues: dict[str, list[str]] = {}
    checks = [
        ("frontmatter_validity", check_frontmatter_validity),
        ("description_quality", check_description_quality),
        ("has_body", check_has_body),
        ("link_syntax", check_link_syntax),
    ]
    for stem, data in topics.items():
        topic_issues = []
        for check_name, fn in checks:
            found = fn(stem, data)
            topic_issues.extend(found)
        if topic_issues:
            per_topic_issues[stem] = topic_issues
        report["per_topic"][stem] = topic_issues

    # --- Cross-topic ---
    cross_issues = {
        "link_resolution": check_link_resolution(topics),
        "cross_ref_symmetry": check_cross_ref_symmetry(topics),
        "hub_threshold": check_hub_threshold(topics, source_refs),
        "source_coverage": check_source_coverage(topics, sources),
    }
    report["cross_topic"] = cross_issues

    # --- Summary ---
    total_per_topic = sum(len(v) for v in per_topic_issues.values())
    total_cross = sum(len(v) for v in cross_issues.values())
    topics_with_issues = len(per_topic_issues)

    report["summary"] = {
        "topics_with_issues": topics_with_issues,
        "total_per_topic_issues": total_per_topic,
        "total_cross_topic_issues": total_cross,
        "link_resolution_failures": len(cross_issues["link_resolution"]),
        "symmetry_failures": len(cross_issues["cross_ref_symmetry"]),
        "hub_gaps": len(cross_issues["hub_threshold"]),
        "source_coverage_failures": len(cross_issues["source_coverage"]),
    }

    # --- Print report ---
    print()
    print("=" * 60)
    print("PKM SCORE REPORT")
    print("=" * 60)

    if per_topic_issues:
        print(f"\n[PER-TOPIC ISSUES] — {topics_with_issues} topics, {total_per_topic} issues")
        for stem, issues in sorted(per_topic_issues.items()):
            print(f"\n  {stem}")
            for issue in issues:
                print(f"    • {issue}")
    else:
        print("\n[PER-TOPIC] ✓ All topics pass")

    for check_name, issues in cross_issues.items():
        label = check_name.replace("_", " ").upper()
        if issues:
            print(f"\n[{label}] — {len(issues)} issues")
            for issue in sorted(issues):
                print(f"  • {issue}")
        else:
            print(f"\n[{label}] ✓ All pass")

    print()
    print("=" * 60)
    print(f"SUMMARY: {topics_with_issues} topics with per-topic issues | "
          f"{len(cross_issues['link_resolution'])} broken links | "
          f"{len(cross_issues['cross_ref_symmetry'])} symmetry gaps | "
          f"{len(cross_issues['hub_threshold'])} missing hubs | "
          f"{len(cross_issues['source_coverage'])} uncovered sources")
    print("=" * 60)

    if write_json:
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nReport written to {REPORT_PATH.relative_to(VAULT)}")

    if build:
        n = build_catalog(topics, sources)
        print(f"Catalog written to {CATALOG_PATH.relative_to(VAULT)} ({n} entries)")

    # Exit non-zero if any issues found
    if total_per_topic + total_cross > 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
