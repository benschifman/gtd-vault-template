---
name: pkm-lint
description: Health-checks the PKM wiki in 40-PKM/40-30-Topics/. Finds orphan topics, unresolved links, stale synthesis, and concept gaps. Used by the PKM Librarian agent. Run periodically after multiple ingests.
---
# PKM Lint Skill

Audit the wiki for health issues and produce a prioritized report with specific suggested fixes. Ask for approval before making any changes.

## Step 0: Run the deterministic scorer first

Before any LLM-based checks, run the scorer script from the vault root:

```bash
cd "<vault-root>" && python3 90-System/scripts/score_pkm.py --json
```

This produces `90-System/scripts/score_report.json` and prints a summary. Read the JSON for the full issue list. The scorer checks:

- **frontmatter_validity** — required fields present (`category`, `created`, `short_description`)
- **description_quality** — `short_description` is 10–120 words, no placeholder text
- **has_body** — `## Body` section exists and has content
- **link_syntax** — no empty `[[]]` or malformed `[[[` wikilinks
- **link_resolution** — every `[[wikilink]]` in `related_topics` resolves to an existing topic file
- **cross_ref_symmetry** — if A lists B in `related_topics`, B must list A back
- **hub_threshold** — any topic referenced 3+ times in source `topics:` fields must have a topic file
- **source_coverage** — every source with `processed: true` lists at least one topic that resolves to an existing topic file (catches sources marked done without ever being wired into the wiki)

Use the scorer results to populate the **Unresolved links**, **Symmetry gaps**, **Hub gaps**, and **Uncovered sources** sections of the lint report directly — no need to re-derive them manually.

Other scorer flags: `--build` additionally rebuilds `40-PKM/catalog.jsonl` (one JSON object per topic and per source — path, title, short_description, topic/source links, processed state). `--build-only` rebuilds the catalog and skips all checks. The catalog lets agents survey the wiki via grep/jq without Obsidian running; rebuild it whenever a lint run fixed files.

To fix symmetry gaps in bulk, use `obsidian property:set` to append to `related_topics` arrays. Since `property:set` doesn't support appending to lists, read the current array first and rewrite it with the new entry added:
```bash
obsidian property:read name="related_topics" path="40-PKM/40-30-Topics/topic-name.md"
# then set the full updated array:
obsidian property:set name="related_topics" value='["[[a]]","[[b]]","[[c]]"]' path="40-PKM/40-30-Topics/topic-name.md"
```

---

## LLM-based checks

Run these after the scorer. They require judgment that the script can't provide.

### 1. Orphan topics
Topics with no backlinks from sources — they exist but nothing references them.
```bash
obsidian orphans
```
Filter results to `40-PKM/40-30-Topics/`. Flag any topic file with no backlinks from `40-PKM/40-20-Sources/`.

Cross-check with:
```bash
obsidian backlinks file="topic-name" format=json
```

**Suggested fix:** Either find sources that should reference this topic and update their `topics:` array, or flag the topic for Jordan to decide if it's worth keeping.

### 2. Stale synthesis
Topics whose `## Body` may be outdated because sources have been added since the topic was last modified.

```bash
obsidian eval code="const topicFiles=app.vault.getFiles().filter(f=>f.path.startsWith('40-PKM/40-30-Topics/')&&f.extension==='md'&&!f.name.startsWith('_')); JSON.stringify(topicFiles.map(f=>({path:f.path,modified:f.stat.mtime})))"
```

For topics with 3+ source backlinks, compare the topic's modification time against the most recently added source that references it. If any source is newer than the topic, the synthesis may be stale.

**Suggested fix:** Re-read the newer sources and update the topic body to integrate them.

### 3. Concept gaps
Important terms or entities that appear frequently across topic pages but don't have their own topic file. Also check the scorer's `hub_threshold` results — any topic in source `topics:` fields referenced 3+ times without a file is a concept gap candidate.

Approach: read several topic `## Body` sections and note any concept mentioned in multiple topics that lacks a `[[wikilink]]` or has only an unresolved link. Also check for proper nouns (organizations, laws, people) that recur without their own page.

**Suggested fix:** Propose new topic files for recurring concepts. List them for Jordan's approval before creating.

### 4. Topics without a Body
Topic files that were scaffolded (have a `## Description`) but whose `## Body` is empty or a stub, and that now have enough source material (3+ backlinks) to warrant a full writeup. The scorer's `has_body` check will surface these.

**Suggested fix:** Trigger a Phase 3 synthesis pass on these topics.

### 5. Oversized topics that should be split
Topics that have grown too broad to be useful — many large sections covering intellectually separable subjects.

For each topic file, check:
- Word count (approximate) and number of H2/H3 sections
- Whether sections are separable: could a reader interested in one section skip the others?
- Whether at least 3 sources back each proposed sub-topic

A topic is a **split candidate** if it has 2,000+ words OR 8+ sections AND its sections are clearly separable. Do not flag topics where sections form an integrated narrative (e.g., a technology overview that flows from basics to policy).

**Suggested fix:** Propose specific sub-topic names for Jordan's approval before splitting. Follow the split procedure from `topic-writing/SKILL.md`: create sub-topic files, rewrite parent as a 300–500-word overview/index, wire up `related_topics` bidirectionally.

---

## Output format

Present findings as a grouped report:

```
## Lint Report — YYYY-MM-DD

### Scorer results (deterministic)
- Frontmatter issues (N): ...
- Broken links (N): ...
- Symmetry gaps (N): ...
- Hub gaps (N): ...
- Uncovered sources (N): ...

### Orphan topics (N)
- [[topic-name]] — no source backlinks

### Stale synthesis (N)
- [[topic-name]] — last updated YYYY-MM-DD, newer sources: [[source-name]]

### Concept gaps (N)
- "term" — appears in [[topic-a]], [[topic-b]], [[topic-c]]

### Topics ready for synthesis (N)
- [[topic-name]] — N source backlinks, body is stub

### Oversized topics (N)
- [[topic-name]] — ~N words, N sections; proposed split: sub-topic-a, sub-topic-b
```

Then ask: "Want me to fix any of these categories?" Fix only with explicit approval.
