---
name: legislation coauthoring
description: Guide users through a structured workflow for co-authoring proposed legislation. Use when a user wants to write bills, resolutions, ordinances, statutory amendments, or similar legal/regulatory content. This workflow helps users efficiently transfer context, structure the legislation according to standard statutory conventions, refine legal language, and stress-test the text for loopholes or ambiguity. Trigger when the user mentions writing a bill, drafting an ordinance, proposing a law, or similar legislative tasks.
---
# Legislative Co-Authoring Workflow

This skill provides a structured workflow for guiding users through collaborative legislative drafting. Act as an active guide, walking users through three stages: Context & Intent Gathering, Statutory Structure & Refinement, and Scrutiny & Edge-Case Testing.

## When to Offer This Workflow

**Trigger conditions:**

- User mentions writing legislation: "draft a bill", "write a statute", "propose an ordinance", "draft an amendment"
    
- User mentions specific legislative types: "resolution", "state law", "municipal code", "regulatory framework"
    
- User seems to be starting a substantial policy-to-text translation task
    

**Initial offer:**

Offer the user a structured workflow for co-authoring the legislation. Explain the three stages:

1. **Context & Intent Gathering**: User provides the policy goals, jurisdictional context, and background while the Assistant asks clarifying questions.
    
2. **Statutory Structure & Refinement**: Iteratively build standard legislative sections (Findings, Definitions, Substantive Provisions, Penalties, etc.) through drafting and surgical editing.
    
3. **Scrutiny & Edge-Case Testing**: Stress-test the draft with a fresh AI instance to identify loopholes, vague definitions, or unintended consequences before legal counsel reviews it.
    

Explain that this approach ensures the draft is legally precise and structurally sound. Ask if they want to try this workflow or prefer to work freeform.

If user declines, work freeform. If user accepts, proceed to Stage 1.

## Stage 1: Context & Intent Gathering

**Goal:** Close the gap between the user's policy goals and the Assistant's understanding, enabling precise statutory drafting.

### Initial Questions

Start by asking the user for meta-context about the legislation:

1. **Jurisdiction & Level:** Where is this being introduced? (e.g., Federal, State, County, Municipal level? Which specific state/city?)
    
2. **Mechanism:** Is this a standalone new bill, or an amendment to existing code/statute? (If amending, ask for the specific code section).
    
3. **Legislative Intent:** What is the core problem this legislation is trying to solve? What is the intended real-world impact?
    
4. **Key Stakeholders & Targets:** Who does this regulate, protect, or fund? Are there specific agencies tasked with enforcement?
    
5. **Constraints:** Are there known constitutional limits, budget constraints, or political red lines to avoid?
    

Inform them they can answer in shorthand or dump information however works best for them.

**If user provides an existing code section or model legislation:**

- Ask if they have the text or a link to share.
    
- If they provide a file or link (and integrations are available), read it to understand the existing statutory language and formatting.
    

### Info Dumping

Once initial questions are answered, encourage the user to dump all the context they have. Request information such as:

- Background on the issue (e.g., statistics, past incidents, constituent complaints).
    
- Policy memos, white papers, or lobbyist recommendations.
    
- Similar laws passed in other jurisdictions (for model language).
    
- Why previous attempts at this legislation failed (if applicable).
    
- Preferred enforcement mechanisms (e.g., civil fines, criminal penalties, private right of action).
    

Advise them not to worry about "legalese" yet—just get the concepts out.

**Asking clarifying questions:**

When the user signals they've done their initial dump, generate 5-10 numbered questions based on gaps in the context (e.g., "If an entity violates this, who issues the fine?", "Does 'small business' need a specific employee headcount definition here?").

**Exit condition:**

Sufficient context has been gathered when the core mechanism of the bill is clear and you can ask about edge cases without needing the basic policy explained. Transition to Stage 2.

## Stage 2: Statutory Structure & Refinement

**Goal:** Build the legislation section by section, ensuring adherence to standard statutory formatting and precise legal terminology. If you have questions see the `leg text drafting helper` for guidance on legislative drafting.

**Instructions to user:**

Explain that the bill will be built section by section. For each section:

1. Clarifying questions will be asked about specific mechanics.
    
2. Options for scope and phrasing will be brainstormed.
    
3. User will select preferences.
    
4. The section will be drafted using formal legislative language (e.g., proper use of "shall" vs. "may").
    
5. It will be refined through surgical edits.
    

**Section ordering:**

Suggest a standard legislative structure based on the jurisdiction, typically including:

1. **Short Title** (Name of the act)
    
2. **Findings and Purpose** (Legislative intent)
    
3. **Definitions** (Crucial for preventing loopholes)
    
4. **Substantive Provisions** (The core rules/requirements)
    
5. **Enforcement & Penalties** (Agencies involved, fines, actions)
    
6. **Appropriations/Funding** (If applicable)
    
7. **Severability Clause & Effective Date**
    

Ask if this structure aligns with their jurisdiction's drafting manual or if they need to adjust it.

**Once structure is agreed:**

Create the initial document structure with placeholder text for all sections.

Use `create_file` (if available) to create an artifact named appropriately (e.g., `Draft_Bill_Name.md`).

**For each section:**

### Step 1: Clarifying Questions & Step 2: Brainstorming

Announce work will begin on the `[SECTION NAME]`.

- _For Definitions:_ Brainstorm which terms from their info-dump are ambiguous and need strict bounding.
    
- _For Substantive Provisions:_ Brainstorm the exact requirements, exemptions, and compliance timelines.
    
    Generate 5-10 numbered options/questions based on section complexity.
    

### Step 3: Curation & Step 4: Gap Check

Ask which mechanics should be kept, removed, or altered. Request brief justifications (e.g., "Remove 3, the state constitution forbids that kind of tax"). Based on their selections, ask if there are any glaring loopholes left in this specific section.

### Step 5: Drafting

Use `str_replace` (or standard text replacement) to replace the placeholder text with the drafted legal language.

_Drafting Rule:_ Default to plain, precise legal English. Avoid archaic "legalese" (like "heretofore" or "party of the first part") unless specifically requested, but strictly adhere to operational words like _shall_ (mandatory), _may_ (discretionary), and _must_ (condition precedent). 

### Step 6: Iterative Refinement

As user provides feedback, surgically edit the text.

_Key instruction for user:_ Ask them to provide specific directional feedback (e.g., "Broaden the exemption in subsection (b) to include non-profits," or "Change the fine from $500 to $1000").

### Quality Checking

After 3 iterations on a section, check for consistency with previously drafted sections (e.g., "You used the term 'Provider' here, but we defined it as 'Operator' in Section 3. I will standardize this to 'Operator'.").

**Repeat for all sections.**

### Near Completion

Review the entire draft for:

- Internal consistency and cross-reference accuracy (e.g., "Pursuant to Section 4(a)...").
    
- Undefined terms that carry operational weight.
    
- Proper numbering/lettering hierarchy (e.g., Section 1, (a), (1), (A), (i)).
    

## Stage 3: Scrutiny & Edge-Case Testing

**Goal:** Test the legislation with at least one fresh AI instance, ideally several, (acting as a judge, opposing counsel, or regulatory agency) to find loopholes, vagueness, unconstitutional provisions, or unintended consequences.

**Instructions to user:**

Explain that the draft will now be stress-tested. This simulates how a defense attorney, a skeptical judge, or a confused citizen might interpret the text, catching blind spots before formal introduction.

### Testing Approach

**If access to sub-agents/fresh context is available:**

### Step 1: Predict Scrutiny Vectors

Announce intention to predict how this law might be challenged or misunderstood. Generate 5-10 "stress-test" questions (e.g., "How could a corporation technically comply with the letter of Section 4 while violating the spirit?", "Does the definition of 'Vehicle' accidentally include bicycles?").

### Step 2: Test with Sub-Agent (Adversarial Reading)

Invoke a sub-agent with _only_ the draft legislation (no background context) and the stress-test questions. Instruct the sub-agent to act as a strict textualist interpreting the law.

### Step 3: Run Additional Checks

Have the sub-agent check for:

- **Ambiguity:** Words that could have multiple legal meanings.
    
- **Overbreadth:** Does the law ban/regulate more than intended?
    
- **Underinclusiveness:** Are there obvious loopholes?
    
- **Conflicts:** Does it obviously contradict standard constitutional principles (e.g., Due Process, First Amendment)?
    

### Step 4: Report and Fix

Report the vulnerabilities found by the "Adversarial AI." List the specific loopholes or vague clauses. Loop back to Stage 2 refinement to patch the statutory language.

---

**If no access to sub-agents (e.g., manual web interface):**

### Step 1 & 2: Setup Manual Testing

Generate 5-10 adversarial questions. Instruct the user to open a fresh conversation, paste the drafted bill, and ask the fresh AI to interpret the text based on those questions.

### Step 3: Additional Checks

Suggest the user ask the fresh AI:

- "Are there any loopholes in this text that a motivated party could exploit?"
    
- "Which definitions are the most ambiguous?"
    
- "If you were a judge, how would you interpret the phrase `[insert contentious phrase]`?"
    

### Step 4: Iterate Based on Results

Ask the user what vulnerabilities the fresh AI found, and patch the text accordingly.

## Final Review

When Scrutiny Testing passes:

Announce the draft is structurally complete.