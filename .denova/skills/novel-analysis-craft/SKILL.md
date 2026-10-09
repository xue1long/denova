---
name: "novel-analysis-craft"
description: "Use this skill whenever the user wants to systematically analyze or dissect a novel, story, or book; map plot structure, causality, characters, subplots, themes, or emotional turns; extract writing techniques into reusable cards or a writing SOP; analyze a long work in chapter batches and resume later; or design and assess a practice exercise. 当用户要求小说拆解、提取写作技巧、分章节续拆、生成技巧卡或评估练习时也要使用。Keep every claim tied to supplied source evidence and report coverage honestly."
category: "general"
---

# Novel Analysis and Craft Extraction

Turn supplied novel material into a traceable analysis and a small set of usable writing tools. Follow the sequence **skeleton → flesh → soul → technique extraction → practice**. The goal is to understand how the work functions and convert observations into original craft choices, not to reproduce the author's prose.

默认使用中文回复，除非用户指定其他语言。

## Read the supporting files

- For each run, use references/evidence-and-coverage.md and references/quality-gates.md.
- Use references/analysis-methods.md for the interpretation framework.
- Use the matching prompt in prompts/ for each phase. For a resumed run, use prompts/06-resume-and-finalize.md.
- Use schemas/input.schema.json and schemas/output.schema.json for machine-readable input and output.
- Use templates/input.md, templates/output.md, and templates/technique-card.md when the user prefers Markdown.
- examples/quick-demo.* shows a complete small example. scripts/validate_output.py checks output structure and evidence links without third-party packages.

## 1. Intake and boundaries

1. Identify the work, requested scope, depth (quick, standard, or deep), and output preference. If depth is absent, use standard.
2. Identify the source actually available in this conversation or in user-provided files. A title or memory of a book is not source evidence. If the text or usable notes are absent, ask for them before making plot-specific claims.
3. Ask the user to confirm that the material is their own, public-domain, licensed, or otherwise provided for this analysis. If that is unclear, pause analysis of the text and request clarification or a short excerpt/notes they can share.
4. Do not retrieve or reconstruct a copyrighted novel from memory or the internet. Analyze only supplied material. Prefer paraphrase; use only the shortest quote needed to identify evidence. Do not imitate a living author's distinctive style. Convert techniques into abstract mechanics and original exercises.
5. Establish the coverage manifest: expected chapter IDs, received chapter IDs, source chunk IDs, and the requested scope. If the user supplied only selected chapters, label the scope as selected material rather than the complete novel.

Use prompts/00-intake.md. If the user supplied source in an informal format, create stable IDs such as ch01 and c001 without changing the source. Never invent missing chapter titles, page numbers, events, or quotations.

## 2. Choose depth

Every depth runs all five phases. Depth changes how much is examined, not whether evidence and practice are omitted.

| Depth | Minimum useful analysis |
|---|---|
| quick | One concise synopsis and causal spine; the protagonist and main resistance; one subplot or a note that none is evidenced; one theme and one emotional turn; one technique card; one practice assignment and rubric. |
| standard | The full supplied scope; major plot beats; significant subplots; protagonist, main resistance, and 2–3 key supporting characters; 1–2 themes; emotional arc; three technique cards; reusable SOP and practice rubric. |
| deep | Chapter-by-chapter coverage; causal links and reversals; all significant subplots and key roles; competing theme readings and emotional transitions; 3–5 technique cards; alternative explanations, counterfactuals, limitations, and a detailed SOP. |

When a phase lacks enough evidence, mark it partial or blocked and state what source would resolve the gap. Do not fill a quota with invented claims.

## 3. Run the five phases

Work in order. Keep analysis claims separate from source evidence. Each plot, character, theme, emotional, or technique claim must point to one or more evidence IDs.

1. **Skeleton** — use prompts/01-skeleton.md. Write a 200–300 Chinese-character synopsis when the supplied scope supports one, a one-sentence story, the protagonist's goal, the central resistance, the causal spine, opening/setup/climax/ending, and a short counterfactual about the opening. Mark provisional structure if coverage is incomplete.
2. **Flesh** — use prompts/02-flesh.md. Map subplots to characters, chapters, and main-plot function; run a deletion test. Analyze the protagonist's behavior, desire, weakness, and change; analyze the principal resistance (including a non-person force); and choose 2–3 supporting characters when evidence permits. Distinguish observed behavior from interpretation.
3. **Soul** — use prompts/03-soul.md. Identify 1–2 central themes, show how events and choices express them, map the dominant emotional movement and turning points, and note strengths and weaknesses with evidence.
4. **Technique extraction** — use prompts/04-techniques.md. Select the depth-appropriate number of techniques. For each, explain the author's observable move, reader effect, mechanism, counterfactual, conditions for reuse, pitfalls, and a transformed application. Store each as a structured technique card.
5. **Practice** — use prompts/05-practice.md. Convert a selected card into a reusable writing SOP, then produce a 500–1500 Chinese-character practice assignment and an evaluation rubric. The default deliverable is the assignment and rubric; write or assess the practice passage only when the user asks or supplies a draft. Evaluate against the technique and the user's own goals, not against copied source wording.

## 4. Evidence and confidence

Use the rules in references/evidence-and-coverage.md. Give each evidence item a stable ID (E001...), source chunk, chapter, and locator. If page or paragraph numbers were not supplied, cite the chapter and chunk ID; never fabricate finer precision. A claim without evidence is not an analysis fact: omit it, or label it as an open question and request source material. Inferences must be labeled as inferences, explain the evidence that supports them, and carry a confidence level.

Keep quotes brief and exact. If the source is not visible, do not quote. The analysis should remain useful through paraphrase and precise locators.

## 5. Long works, batches, and recovery

For long works, process only the new batch plus any earlier evidence needed to test continuity. Maintain an output checkpoint after every batch using the structure in templates/output.md and the output schema. Preserve:

- expected, received, and processed chapter IDs;
- evidence IDs and source chunk IDs;
- completed/partial/blocked phase statuses and quality gates;
- unresolved questions, next source range, and the last processed chapter;
- a correction log when new evidence changes an earlier interpretation.

On resume, read the saved checkpoint and new batch, validate IDs, process only unprocessed chunks, and then revisit earlier claims only when new evidence bears on them. Do not silently overwrite a claim; log the old claim, new evidence, and revised conclusion. Never call the whole novel complete while expected chapters remain unreceived or unprocessed. The coverage rules are detailed in references/evidence-and-coverage.md.

## 6. Output and final gate

Return both:

1. a readable Chinese report following templates/output.md; and
2. a structured JSON object following schemas/output.schema.json, unless the user explicitly asks for Markdown only.

Include technique cards in a separately reusable section or file when helpful. Before calling the work complete, apply references/quality-gates.md. If Python is available and a JSON file was created, run python scripts/validate_output.py <output.json> from this skill folder and fix reported structural or evidence-link errors. This check does not judge literary quality or establish that a citation is true; the model must still verify the claims against the supplied source.

The final report must state the analyzed scope, depth, chapter coverage, phase gates, limitations, next action, and whether the practice draft has actually been submitted and assessed. Do not claim an exercise was completed if only its assignment was generated.
