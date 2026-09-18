---
name: source-processing
description: Scans 40-PKM/40-20-Sources/ for unprocessed source notes, extracts PDF text via Marker, fills in YAML metadata (summary, short_description, topics), and marks the source as processed. Use this skill when the user asks to process sources, check for new sources, or update source metadata.
---

# Source Processing Skill

Ensure every source note in `40-PKM/40-20-Sources/` has complete YAML metadata, extracted PDF content, and properly linked topics.

## Steps

1. **Identify unprocessed sources.**
   Sources may live in `40-PKM/40-20-Sources/` or in `00-Inbox/`. List `.md` files in both locations. A source is **unprocessed** if it is missing the `processed:` property or has `processed: false`. Skip any file where `processed: true`.

   If a source is in `00-Inbox/`, it also needs to be **moved** to `40-PKM/40-20-Sources/`. Do this with `shutil.move()` in Python (handles special characters in filenames). Delete the original after moving — do not archive it. **Preserve the original filename exactly — do not rename, lowercase, or hyphenate it.**

2. **Edit YAML in place — never recreate the file.**
   Always use the Edit tool to update frontmatter. Never use Write to recreate a source file from scratch — the body content (captured article text, notes) must be preserved.

   Read the body text and existing metadata, then fill in any blank YAML fields:
   - `title:` — infer from filename or body content
   - `author:` — look for bylines or attribution in the text
   - `published:` — look for publication dates
   - `source_type:` — classify as one of: `report`, `article`, `caselaw`, `statute`, `regulation`, `book`, `other`
   - `short_description:` — write 1–2 sentences summarizing what this source covers
   - `summary:` — write 2–4 sentences with more detail
   - `url:` — extract if present in body text
   Do NOT overwrite fields that already have values.

3. **Handle and Extract PDF content (if applicable -- unless the user specifies otherwise such as by saying "no need to extract text from the pdf).**
   Check the `pdf:` YAML property. If it contains a path or link to a PDF file:
   - Check if the PDF file is located in `90-System/attachments/`. If it is located elsewhere (like the inbox or a generic attachment folder), **move the PDF file** to `90-System/attachments/`. Ensure the `pdf:` YAML property link correctly reflects its location (e.g. `pdf: "[[pdf-filename.pdf]]"` using Obsidian's standard attachment resolution).
   - Check if there is text below the header `## PDF as markdown`. If there is, no need to extract the text from the pdf and go to step 4. If there is no text then proceed with the rest of this step.     
   - **Default: extract with `pypdf`** (fast, no ML, works well for born-digital PDFs):
     ```bash
     python3 -c "
     import pypdf, sys
     r = pypdf.PdfReader(sys.argv[1])
     print('\n\n'.join(p.extract_text() or '' for p in r.pages))
     " "/absolute/path/to/source.pdf"
     ```
   - **Fallback: use `marker_single`** if pypdf output looks garbled (wrong column order, missing text, scrambled tables). Signs you need marker: multi-column academic layout, scanned pages, heavy tables, or mostly blank pypdf output.
     ```bash
     /Library/Frameworks/Python.framework/Versions/3.13/bin/marker_single "/absolute/path/to/source.pdf" --output_format markdown --output_dir "/tmp/marker_out" --disable_image_extraction
     ```
     Marker output is in `/tmp/marker_out/<pdf-name>/<pdf-name>.md`. Clean up with `rm -rf /tmp/marker_out` after reading. Note: first run downloads ML models (~7 min); subsequent runs faster (cached at `~/Library/Caches/datalab/`).
   - Before writing anything, check whether the body already contains a PDF embed (`![[...pdf...]]`). If a PDF embed already exists anywhere in the body, do **not** add another one — only add the `## PDF as markdown` section with the extracted text. If no embed exists yet, write both:
     ```
     ## PDF

     ![[pdf-name.pdf]]

     ## PDF as markdown

     <extracted text>
     ```
     The embed (`![[...]]`) lets Obsidian display the PDF inline; the extracted markdown makes the content searchable and readable by Claude or Codex.
   - **CRITICAL: Unless the user specifies otherwise, write the full extracted text verbatim into `## PDF as markdown`.** Never substitute a placeholder, summary, or note like "[Full extracted text: N pages — see PDF embed]". The entire raw extraction output must appear in this section, no matter how long it is.
   - If the source body was mostly empty, also use the extracted text to populate `short_description:`, `summary:`, and the `## Notes` section with key takeaways.

4. **Determine and assign topics.**
   Read the full source text to identify the main subjects.
   - List all existing files in `40-PKM/40-30-Topics/` to know what topics already exist.
   - Select relevant existing topics that match this source's content.
   - If important subjects are **not** covered by any existing topic, propose new ones.
   - **Naming convention:** new topic names must be lowercase with spaces (e.g., `solar energy`, `defense authorization`, `permitting reform`). Existing topic files may use hyphens; do not rename them. Reuse existing hyphenated topics when they are the best match, but apply the space convention to newly proposed topics.
   - **Duplicate checking:** before proposing a new topic, check existing topic filenames for near-synonyms (e.g., don't create `[[solar power]]` if `[[solar-energy]]` already exists). When in doubt, reuse the existing topic.
   - **Prefer specific sub-topics over broad parent topics.** Many broad topics (e.g., `electricity-economics`, `data-centers`, `permitting-reform`) have sub-topic files that are more precise. Check whether a sub-topic (e.g., `electricity-markets`, `data-centers-grid-integration`, `nepa-reform`) is a better fit than the parent before assigning. For newly proposed sub-topics, use lowercase spaces unless an appropriate hyphenated topic already exists. Using both parent and sub-topic is fine when the source genuinely spans the full scope.
   - Update the `topics:` array in the source's YAML frontmatter. Format as wikilinks:
     ```yaml
     topics:
       - "[[existing-topic]]"
       - "[[newly proposed topic]]"
     ```

5. **Mark as processed.**
   After completing all the above, set `processed: true` in the source's YAML frontmatter.

## Notes

- Follow all vault conventions from AGENTS.md: YAML frontmatter required, wikilink syntax `[[Note Name]]`.
- The source template lives at `90-System/templates/source.md` — reference it if you need to verify the expected YAML structure.
- Do NOT delete or reorganize any files. Only modify the source note's content in-place.
- If a PDF extraction fails (e.g., Marker not installed), log the issue to the user and continue processing the remaining fields. Set `processed: false` so it can be retried.
