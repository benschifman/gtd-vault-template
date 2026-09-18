---
name: topic-writing
description: Creates topic files in 40-PKM/40-30-Topics/ for any topic referenced in a source's YAML that does not yet have a corresponding file. Use this skill when the user asks to create missing topics, scaffold topics, or after source processing identifies new topics.
---

# Topic Writing Skill

`40-PKM/40-30-Topics/` is the wiki — the LLM-maintained layer that synthesizes everything known about each subject. Topic files are both navigational hubs and Wikipedia-style articles. You own this layer entirely.

This skill handles **scaffolding**: creating topic files for every topic wikilink that exists in source YAML but has no corresponding `.md` file yet. After scaffolding, the PKM Librarian's Phase 3 handles synthesis (writing the `## Body`).

## Steps

1. **Identify missing topics.**
   Use the Obsidian CLI to get all unresolved wikilinks in the vault:
   ```bash
   obsidian unresolved format=json
   ```
   This returns every wikilink with no matching file. Filter the results to links that originate from `40-PKM/40-20-Sources/` — these are the missing topic references. (Links from other folders, e.g. daily notes or project files, are not your concern here.)

   To find which sources reference a specific unresolved topic:
   ```bash
   obsidian property:read name="topics" path="40-PKM/40-20-Sources/source-name.md"
   ```
   Or search across all sources at once:
   ```bash
   obsidian search query="[[topic-name]]" path="40-PKM/40-20-Sources" format=json
   ```

2. **Check for near-duplicates before creating.**
   Before creating a new topic file, scan the existing topic filenames for near-synonyms:
   - e.g., if `renewable-energy.md` exists, don't also create `clean-energy.md` unless they are genuinely distinct
   - If a near-duplicate is found, use `obsidian property:set` to update the source's `topics:` array to use the existing topic name, then skip creating a new file.

3. **Read the sources before writing.**
   For each missing topic, read the full body of every source file that references it — not just the YAML. This is the raw material for the Body section. Understand what those sources actually say about the topic before drafting anything.

4. **Create the topic file.**
   For each genuinely missing topic, create `40-PKM/40-30-Topics/[topic name].md` from the template and then write the body.

   Create the file from the template first (see "Creating the file" at the end of this file), then fill in the sections below.

   Use this structure, substituting real values:
   ```markdown
   ---
   category: topic
   created: '[[YYYY-MM-DD]]'
   modified: 'YYYY-MM-DD'
   short_description: "1–2 sentences defining what this topic covers."
   related_topics: []
   ---

   ## Description
   1–2 sentences defining what this topic covers. (Same as short_description.)

   ## Body
   [Wikipedia-style prose article — see instructions below]

   ## Key Notes

   ## Key Sources
   - [[source-filename-that-triggered-this-topic]]
   ```

   When populating:
   - **`created:`** — use today's actual date in `YYYY-MM-DD` format, wrapped in wikilinks: `'[[2026-04-03]]'`
   - **`modified:`** — set to today's date in plain `YYYY-MM-DD` format (no wikilink). Update this field every time the topic body is changed.
   - **`short_description:`** — write 1–2 sentences in the YAML. This is what the topic index base file surfaces for quick scanning. Keep it identical to `## Description`.
   - **`related_topics:`** — leave as `[]` in the initial file write; populate it in the next step using `property:set`
   - **`## Description`** — same text as `short_description`. Kept in the body for human readability in Obsidian.
   - **`## Body`** — write a Wikipedia-style prose article grounded in the sources you read. Structure it with a lead paragraph that defines and situates the topic, followed by `###` subsections that cover its key dimensions, mechanisms, debates, or policy context as the material warrants. Use wikilinks (e.g. `[[energy-infrastructure]]`) when referencing related topics inline. Use wikilinks (e.g. `[[source-example]]`) when referencing a particular source inline. Use wikilinks for sources and related topic liberally and frequently when called for in the prose. Write as much as the source material justifies — don't pad, but don't truncate either. A narrow topic with one source may need only a few paragraphs; a broad topic with multiple rich sources should be treated accordingly.
   - **`## Key Notes`** — leave empty; the librarian will populate over time.
   - **`## Key Sources`** — list all sources (as wikilinks) whose `topics:` array includes this topic.

   After writing the file, set `related_topics` using the CLI (more reliable than editing raw YAML):
   ```bash
   obsidian property:set name="related_topics" value='["[[related-topic-a]]","[[related-topic-b]]"]' path="40-PKM/40-30-Topics/new-topic.md"
   ```
   Related topics are the other topics that appear alongside this one in the same source files' `topics:` arrays.

5. **Verify resolution.**
   After creating all topic files, re-run:
   ```bash
   obsidian unresolved format=json
   ```
   Confirm that the newly created topic names no longer appear as unresolved links. If any still appear, the filename doesn't match the wikilink — fix the mismatch.

## Notes

- **Filename convention:** Use lowercase with spaces — e.g., `large load interconnection.md`, `ai policy.md`, `nuclear energy.md`. Do not use hyphens. Existing topic files use hyphens and should not be renamed; this convention applies to newly created files only.
- Follow all vault conventions from AGENTS.md: YAML frontmatter required, wikilink syntax.
- The canonical topic template is at `90-System/templates/topic.md`. Create topic files **from the template** (see the block at the end of this file) rather than hand-writing the frontmatter.
- If you're unsure whether two topics are duplicates, keep the existing one and note the ambiguity for the user to resolve.

## Topic granularity and sub-topics

**Prefer specific sub-topics over broad parent topics.** Before creating a new topic file, check whether it would fit better as a sub-topic of an existing broad topic rather than as a standalone. For example, `electricity-markets` is preferable to adding more sections to a sprawling `electricity-economics` file.

**Sub-topic naming convention:** `parent-subtopic` where the parent name is a meaningful prefix (e.g., `data-centers-grid-integration`, `nepa-reform`, `large-load-interconnection`). Not every sub-topic needs the full parent name as prefix — use judgment for clarity.

**When a topic file grows too large**, it should be split. Signs a topic needs splitting:
- More than ~2,000 words or 8+ sections
- Sections are intellectually separable (a reader interested in one wouldn't need the others)
- At least 3 sources back each proposed sub-topic

**How to split:** Create sub-topic files and move relevant sections into them. Rewrite the parent as a brief overview/index (300–500 words) with one short summary paragraph per sub-topic ending with *See [[sub-topic-name]] for full coverage.* Wire up `related_topics` bidirectionally on all files.

**When assigning topics in source processing:** prefer the most specific applicable sub-topic over the broad parent. Tag a source with `[[electricity-markets]]` rather than `[[electricity-economics]]` if that's where it belongs. Using both is fine when the source genuinely spans the parent's full scope.

### Creating the file — render the template, don't hand-write frontmatter

`90-System/templates/topic.md` is the single source of truth. Render it with the shared script so
this skill cannot drift from the template. Obsidian does not need to be open.

```bash
python3 90-System/scripts/new_from_template.py topic "40-PKM/40-30-Topics/<topic name>"
```

The script resolves the `{{date:...}}` placeholders, refuses to overwrite an existing file, and
prints the path it wrote. Then fill the frontmatter (`short_description`, `related_topics`,
`aliases`) and write the sections.
