---
name: crm-lint
description: Health-checks the CRM in 30-CRM/. Runs the deterministic linter, then the judgment-based checks a script cannot do — contacts whose job changed, relationships with no context, orgs worth a page. Produces a prioritized report and hands fixes to crm-update or the crm-librarian agent. Use when the user asks to audit, lint, or health-check the CRM, or asks whether their contacts are up to date.
---
# CRM Lint Skill

Audit `30-CRM/` and produce a prioritized report with specific suggested fixes. **Ask before changing anything** — the one exception is noted below.

The CRM decays in a particular way: people change jobs, and nothing in the vault notices. Most of this skill is about catching that.

## Step 0 — Run the deterministic linter first

```bash
python3 90-System/scripts/crm_lint.py --limit 20
```

Twenty checks, no judgment required. Three tiers:

**Integrity — fix immediately, these break things silently**
- `broken_frontmatter` — file is invisible to *every* Bases query while looking fine in the editor. Makes all other findings unreliable, so clear it first.
- `people_missing_emails_field` — `email` set but no `emails` array. Granola attendee matching reads `emails`; without it that person never auto-links.
- `broken_photo_refs`, `people_legacy_schema`, `people_unknown_schema`

**Contradictions — someone's details have drifted**
- `name_email_mismatch` — filename disagrees with the person's own address. Every misspelled name found so far surfaced this way: Mota/Mora, Kenen/Kenan, Jiminez/Jimenez. **Their email is the authority, not the filename.**
- `email_org_conflict` — address domain belongs to an org the file doesn't list. Usually means a job change, occasionally a stale address at a former employer.
- `shared_email` — same address on two files, i.e. a duplicate person.
- `orphan_key_contact` — an org lists someone whose file never mentions that org.
- `possible_duplicate_people`

**Gaps — incomplete, not wrong**
- `orgs_missing_page`, `people_no_org`, `people_no_role`, `people_no_email`, `people_no_photo`, `people_empty_background`, `orgs_no_key_contacts`, `orgs_empty_overview`
- `frequent_no_relationship` — 3+ meetings but no relationship context. The most useful gap in this tier: these are people Jordan actually works with.

### The one safe auto-fix

```bash
python3 90-System/scripts/crm_lint.py --fix-dates          # dry run
python3 90-System/scripts/crm_lint.py --fix-dates --write  # apply
```

`stale_last_contact` is mechanical — the meeting notes are the authority for when Jordan last spoke to someone. Everything else needs judgment. Show the dry run, then apply.

### Supporting scripts

```bash
python3 90-System/scripts/crm_unresolved_attendees.py   # who needs a CRM entry
python3 90-System/scripts/crm_missing_orgs.py           # org backlog, ranked
```

---

## LLM-based checks

Run after the script. These need judgment it can't provide.

### 1. Job changes announced in meeting notes but never recorded

**The highest-value check in this skill.** Jordan's meeting notes routinely record that someone is moving, and that fact dies in the note unless a human moves it to the CRM. Real examples: a staffer's departure from a Senate office, a co-founder stepping back from an executive role, an analyst moving to another think tank.

Grep recent meeting notes for departure and arrival language:

```bash
grep -rliE "last day|is leaving|has left|stepping down|new role|joining|starts at|moving to|successor|taking over|replaced by" \
  10-Journal/10-10-Events/ | tail -25
```

For each hit, read the surrounding lines and check whether the person's CRM file reflects it. Flag mismatches — do **not** auto-update, since these are often anticipated ("her last day is next week") rather than completed.

Also check `status:` — someone who left a role Jordan tracked and hasn't appeared since may warrant `inactive`. **Never set that automatically:** people resurface elsewhere and Jordan wants the history intact.

### 2. Contradiction between `## Background` prose and frontmatter

`## Background` is written once and rarely revisited; frontmatter gets updated. When they disagree, the prose is usually the stale one.

Read `## Background` for the ~20 most-met contacts and compare against `role` and `organization`. Flag any file where the prose describes a position the frontmatter no longer lists.

### 3. Orgs worth a page

`crm_missing_orgs.py` ranks by how many people reference an org, but not every org deserves a page. Jordan's rule: **incidental prior employers don't get one.** Figma, Notion, DoorDash, HashiCorp, IBM, Substack, Primer and similar are deliberately skipped — expect them to appear in the missing list permanently.

Propose pages for orgs that are actual counterparties in Jordan's work: think tanks, congressional offices, agencies, advocacy groups, companies he negotiates with. Skip places someone happened to work a decade ago.

### 4. People with no meetings and no recent contact

Contacts who exist but appear in no meeting note and have an old `last_contact` — imported once and never used.

```bash
python3 90-System/scripts/crm_unresolved_attendees.py --json >/dev/null  # sanity check the tooling runs
```

Cross-reference `crm_lint.py --json` against `C.meetings_by_person()`. These aren't errors — Jordan may keep them deliberately — so report as "consider archiving", never act.

### 5. Photo gaps worth closing

`people_no_photo` lists everyone, but only some are findable. Prioritize people who appear in meetings and work at an organization with a public team page — those are one fetch away. Skip contacts with no public presence; Jordan supplies those or they stay blank.

---

## Output format

```
## CRM Lint — YYYY-MM-DD
N people, N organizations

### Integrity (fix first)
- ...  or  "none — clean"

### Contradictions (N)
- Name — filename says X, their email says Y
- Name — email domain implies [[Org]], file says [[Other]]

### Job changes seen in meeting notes but not in the CRM (N)
- Name — "quote from the meeting note" (note name)

### Gaps worth closing (N)
- N people with 3+ meetings and no relationship context
- N orgs worth a page (excluding incidental employers)
- N photo gaps with a public team page available

### Auto-fixable
- N people with stale last_contact
```

Then ask which categories to fix. Route the work:
- **Single contact or quick edit** → handle inline via the `crm-update` skill
- **Research-heavy or a batch of 5+** → spawn the `crm-librarian` agent
- **Org pages** → `crm-librarian`, Operation 2

## Rules

- **Blank beats wrong.** A gap costs nothing; a fabricated role poisons every decision made from this CRM.
- **Never rename a file or set `status: inactive` without asking**, even when the evidence looks decisive.
- Report `stale_last_contact` as auto-fixable; everything else needs approval.
- Finish by prepending a `lint | ...` entry to `30-CRM/log.md` and verifying it appears.
