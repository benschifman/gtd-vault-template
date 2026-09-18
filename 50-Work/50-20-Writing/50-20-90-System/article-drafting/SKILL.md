---
name: article-drafting
description: Guide a structured workflow for co-authoring an MPI article from a topic prompt to a draft that has passed a structural editorial pass. Six phases with explicit user sign-off gates. Use this skill when Jordan says "/article-drafting", "use the article-drafting skill", "let's draft an MPI article using the workflow", or otherwise explicitly invokes it. Do NOT auto-trigger on generic "write an article" requests — explicit invocation only.
---

# MPI Article Drafting Workflow

A six-phase workflow for co-authoring long-form MPI pieces (articles, op-eds, briefs, reports). The discipline points are the **sign-off gates** — pause and confirm before moving forward, especially before drafting prose. This is what catches wrong assumptions cheaply.

## Reference docs (read once at the start of Phase 1)

- `90-System/reference/drafting-guides/writing style.md` — your organization's voice and rules (add this file; the template ships without it)
- `90-System/reference/drafting-guides/Editorial Pass.md` — the editorial review framework

These are the source of truth for *what* good MPI writing looks like and *how* to review it. This skill is the *workflow* that organizes the drafting process around them.

---

## Phase 1: Intake

Use `AskUserQuestion` to gather the inputs below. Do not proceed until you have all of them. If Jordan provides them in free text, confirm back briefly and skip the questions.

**Required:**
1. **Topic and one-sentence thesis.** What is the piece arguing? If Jordan says "I'll type it," wait for the text.
2. **Audience.** Hill staff / agency officials / educated general policy / subject-matter experts / other.
3. **Theory of change.** Concrete policy proposal / cover for plan in motion / position author as expert / bat signal for allies. (Per `Editorial Pass.md` — this materially shapes feedback later.)
4. **Format and target length.** Blog post (~800–1500), op-ed (~700–900), Hill brief (~1–2 pages), long-form article (~3000+), report.
5. **Citation style.** Hyperlinked inline (blog register) or CMOS footnotes (report register).
6. **Editorial pass scope.** Structural only (default) / red-team / line / copy. Multi-select.

**Often relevant:**
7. **Comparators or related bills/policies** to analyze alongside the main subject.
8. **Specific sources to use** (links, vault paths, PDFs Jordan already has in mind).
9. **Where to save the draft.** Default: `20-GTD/20-10-Projects/<short-title> - draft.md`. Jordan usually drafts in Google Docs and uses the vault file as the working copy to copy over.

**Output of Phase 1:** a one-paragraph "locked inputs" summary back to Jordan for confirmation.

---

## Phase 2: Source gathering

1. Search the vault for relevant sources, topics, and existing project files. Use `grep -ril` or `obsidian search` across `40-PKM/40-20-Sources/`, `40-PKM/40-30-Topics/`, and `20-GTD/20-10-Projects/`.
2. List what was found. Flag any obvious gaps (Jordan mentioned X but it's not in the vault — does he have a link/PDF, or should I search the web?).
3. Read the highest-value sources in parallel using `Read`. For source files >25k tokens (bill texts, long PDFs), use offset/limit or read just the YAML summary plus a targeted excerpt.
4. Read the topic pages for any concept central to the argument — they often contain synthesized framing the source files don't.

**Output of Phase 2:** a brief inventory ("here's what I found, here's what I think we're missing") and any web-search asks.

---

## Phase 3: Issue map and reverse outline → SIGN-OFF GATE

This is the most important phase. Do not skip it. Do not draft prose before Jordan signs off.

1. **Issue map.** A structured breakdown of the argument: what's the problem in one paragraph, what tactics or facts are in play, what existing law/policy applies, what the proposed solution is, what counterarguments need addressing, what known gaps exist that need verification. Should be specific — names, numbers, dates, statutory cites.
2. **Reverse outline.** One sentence per section. Read them in order — do they form a coherent argument? Per the MPI Editorial Pass: "Does each section build on the previous one, or could you rearrange sections without anyone noticing?"
3. **Open questions.** 2–4 specific decisions Jordan needs to make before drafting (title framing, which counterarguments to interleave vs. silo, whether to add or drop specific examples, etc.). Use `AskUserQuestion`.

**Sign-off requirement:** explicitly ask Jordan to confirm the outline before moving to Phase 4. Do not assume silence is approval.

---

## Phase 4: Draft

1. Write the draft as a single Write tool call to the agreed-upon path. Frontmatter: `category: draft`, `status: draft`, `created`, `audience`, `theory_of_change`, `target_length`.
2. Apply the MPI style guide aggressively while drafting:
   - Bold-claim, concrete-story, or striking-stat opening — never throat-clearing
   - Named actors and named actions in every recommendation
   - Specific numbers, named organizations, named people
   - Hyperlinked citations inline (or footnote markers if CMOS)
   - Em dashes spaced ` — `; sentence-case headings; "US"/"UK"/"AI" not "U.S." etc.
   - No LLM-isms ("delve," "crucial," "landscape," "Moreover," "It's worth noting," "In conclusion," "This isn't just X, it's Y," excessive bolded bullet summaries)
   - Confidence up front; caveats in footnotes
   - Every paragraph earns its place
3. Include 2–4 title options at the top of the file if a title isn't locked.

**Output of Phase 4:** the file path and a one-line note on what to look for in review.

---

## Phase 5: Self-check

Before reporting Phase 4 complete, scan the draft once against the MPI style guide. Look for:
- Vague quantifiers without numbers ("significant," "substantial," "many," "growing")
- Passive recommendations without named actors
- Banned words ("impactful," "the landscape of," "the intersection of")
- LLM-isms (em dashes overused, "this isn't just X, it's Y" constructions, "Moreover/Notably/Importantly")
- Paragraphs that don't add new information
- Opening that fails the 300-word "so what" test
- Any section the draft could lose without weakening the argument

Fix what you can in place. Note anything that needs Jordan's judgment as a one-line list at the end of your Phase 4 message.

---

## Phase 6: Structural editorial pass

Apply Stage 1 of `90-System/reference/drafting-guides/Editorial Pass.md`. Stage 1 only by default.

Output format per the editorial guide:
- Reverse outline of the actual draft (1 sentence per section)
- 3–5 issues, ranked by severity
- Each issue: state the problem, explain why it matters, suggest a direction
- Total feedback under 500 words unless the piece has fundamental problems

After delivering the structural pass, ask Jordan whether to also run red-team/fact-check, line, or copy edits. Do not run them automatically.

---

## Phase 7 (conditional): Subsequent passes

Only if Jordan asks. Each pass per the MPI Editorial Pass guide:
- **Red-team / fact-check** — Stage 2: argument stress-test (3–5 strongest objections) plus systematic fact-check table
- **Line edit** — Stage 3: paragraph and sentence quality, 5–15 representative issues grouped by type
- **Copy edit** — Stage 4: house style, consistency, banned words — 3–5 patterns that recur in this draft

When fixing flagged issues directly: edit in place where confident, flag for Jordan where uncertain. Preserve his voice.

---

## Anti-patterns

- **Drafting before reverse-outline sign-off.** Wastes time and forces rework. The sign-off gate exists for a reason.
- **Skipping Phase 1 questions because the topic seems obvious.** Audience and theory of change shape everything downstream.
- **Reading sources serially.** Use parallel `Read` calls.
- **Running multiple editorial passes without asking.** Default is structural only.
- **Inventing sources or citations.** Every fact and citation must come from the vault, the user, or a verified web search.
- **Praising the draft to seem useful.** Per the editorial guide: "The most common AI editor failure is to praise and then suggest minor tweaks." If something is weak, say so.
- **Making the file longer than the target without flagging it.** If the draft drifts past target length, note it and suggest the cleanest cut.
