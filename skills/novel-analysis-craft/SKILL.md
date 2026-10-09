---
name: "novel-analysis-craft"
description: "Use this skill whenever the user wants to systematically analyze or dissect a novel, story, or book; map plot structure, causality, characters, subplots, themes, or emotional turns; extract writing techniques into reusable cards or a writing SOP; analyze a long work in chapter batches and resume later; or design and assess a practice exercise. 当用户要求小说拆解、提取写作技巧、分章节续拆、生成技巧卡或评估练习时也要使用。Distinguish source-backed claims from tentative interpretations and report coverage honestly."
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
- examples/quick-demo.* shows a complete small example; examples/quick-demo-resume.* shows a same-work continuation. scripts/validate_output.py checks core structure, coverage, source chunks, and evidence links without third-party packages.

## 1. Intake and boundaries

1. Identify the work, requested scope, depth (quick, standard, or deep), and output preference. If depth is absent, use standard.
2. Identify what material is available. If no text or notes are visible, proceed with an exploratory analysis from general knowledge or accessible public summaries; label uncertain details and do not present them as checked against the novel. Request excerpts only when the user wants precise textual evidence.
3. When text or notes are supplied, ground specific claims in them. Prefer paraphrase, use brief exact quotations only from visible material, and turn techniques into original exercises rather than imitating distinctive prose.
4. Establish chapter coverage when chapters are supplied. Without visible source material, use `title_only` scope and unknown chapter coverage; do not invent chapter IDs, locations, quotations, or evidence records.

Use prompts/00-intake.md. If the user supplied source in an informal format, create stable IDs such as ch01 and c001 without changing the source.

## 2. Choose depth

Every depth runs all five phases. Depth changes how much is examined, not whether evidence and practice are omitted.

| Depth | Minimum useful analysis |
|---|---|
| quick | One concise synopsis and causal spine; the protagonist and main resistance; one subplot or a note that none is evidenced; one theme and one emotional turn; one technique card; one practice assignment and rubric. |
| standard | The full supplied scope; major plot beats; significant subplots; protagonist, main resistance, and 2–3 key supporting characters; 1–2 themes; emotional arc; three technique cards; reusable SOP and practice rubric. |
| deep | Chapter-by-chapter coverage; causal links and reversals; all significant subplots and key roles; competing theme readings and emotional transitions; 3–5 technique cards; alternative explanations, counterfactuals, limitations, and a detailed SOP. |

When evidence is sparse, continue with explicitly tentative interpretations and state what remains unverified. Do not fill a quota with invented details.

## 3. Run the five phases

Work in order. Keep source-backed claims separate from tentative interpretations. Cite evidence IDs when source material supports a claim; use empty `evidence_refs` and low confidence for unsourced inferences or evaluations.

1. **Skeleton** — use prompts/01-skeleton.md. Write a 200–300 Chinese-character synopsis when the supplied scope supports one, a one-sentence story, the protagonist's goal, the central resistance, the causal spine, opening/setup/climax/ending, and a short counterfactual about the opening. Mark provisional structure if coverage is incomplete.
2. **Flesh** — use prompts/02-flesh.md. Map subplots to characters, chapters, and main-plot function; run a deletion test. Analyze the protagonist's behavior, desire, weakness, and change; analyze the principal resistance (including a non-person force); and choose 2–3 supporting characters when evidence permits. Distinguish observed behavior from interpretation.
3. **Soul** — use prompts/03-soul.md. Identify 1–2 central themes, show how events and choices express them, map the dominant emotional movement and turning points, and note strengths and weaknesses with evidence.
4. **Technique extraction** — use prompts/04-techniques.md. Select the depth-appropriate number of techniques. For each, explain the author's observable move, reader effect, mechanism, counterfactual, conditions for reuse, pitfalls, and a transformed application. Store each as a structured technique card.
5. **Practice** — use prompts/05-practice.md. Convert a selected card into a reusable writing SOP, then produce a 500–1500 Chinese-character practice assignment and an evaluation rubric. The default deliverable is the assignment and rubric; write or assess the practice passage only when the user asks or supplies a draft. Evaluate against the technique and the user's own goals, not against copied source wording.

## 4. Evidence and confidence

Use the rules in references/evidence-and-coverage.md. Give each available evidence item a stable ID (E001...), source chunk, chapter, and locator. If page or paragraph numbers were not supplied, cite the chapter and chunk ID; never fabricate finer precision. Claims without source evidence may remain as low-confidence inferences or evaluations with empty `evidence_refs`; say what is uncertain. Grounded inferences explain their evidence and confidence.

Keep quotes brief and exact. If the source is not visible, do not quote. The analysis should remain useful through paraphrase and precise locators.

## 5. Long works, batches, and recovery

For long works, process only the new batch plus any earlier evidence needed to test continuity. Maintain an output checkpoint after every batch using the structure in templates/output.md and the output schema. Preserve:

- expected, received, and processed chapter IDs;
- evidence IDs and a source chunk manifest (chunk ID, chapter ID, SHA-256 of the exact UTF-8 content, and an optional source reference);
- completed/partial/blocked phase statuses and quality gates;
- unresolved questions, next source range, and the last processed chapter;
- a correction log when new evidence changes an earlier interpretation.

On resume, read the saved checkpoint and new batch. Confirm the work title matches; compare each incoming chunk ID, chapter ID, and content SHA-256 with the checkpoint manifest. A repeated ID with different content is a conflict, not new evidence. Process only unprocessed chunks, and then revisit earlier claims only when new evidence bears on them. Do not silently overwrite a claim; log the old claim, new evidence, and revised conclusion. Never call the whole novel complete while expected chapters remain unreceived or unprocessed. The coverage rules are detailed in references/evidence-and-coverage.md. For JSON batches, run `python scripts/validate_output.py <checkpoint.json> --input <new-input.json>` before resuming. A version 1.0 checkpoint has no source manifest and must be rebuilt from its original inputs before ID reuse can be checked.

> 🔴 **CHECKPOINT · STOP** — 续跑时**必须**先做三步：① 核对作品名与 chunk ID/章节/内容哈希，冲突则暂停合并；② 对照 `expected_chapter_ids` 与 `processed_chapter_ids` 确认增量；③ 仅当新证据明确推翻旧 claim 时走修订流程，否则原 evidence / claim 一律保留。任何"无声覆盖"行为视为 skill 失效。

## 6. Output and final gate

Return both:

1. a readable Chinese report following templates/output.md; and
2. a structured JSON object following schemas/output.schema.json (version 1.1, including `source_chunks`), unless the user explicitly asks for Markdown only.

Include technique cards in a separately reusable section or file when helpful. Before calling the work complete, apply references/quality-gates.md. If Python is available and a JSON file was created, run python scripts/validate_output.py <output.json> from this skill folder and fix reported structural or evidence-link errors. This check does not judge literary quality or establish that a citation is true; the model must still verify the claims against the supplied source.

> 🔴 **CHECKPOINT · STOP** — 调用 `validate_output.py` **之前**必须自检：① 有来源的 claim 是否引用对应 evidence ID，无来源的判断是否明确为低置信度推断或评价；② coverage 是否与 received/processed 一致；③ practice 阶段 draft_status 是否真实反映"未提交"。脚本只查结构与引用，**不替代**模型对可用材料的核对——脚本通过 ≠ 分析完成。

The final report must state the analyzed scope, depth, chapter coverage, phase gates, limitations, next action, and whether the practice draft has actually been submitted and assessed. Do not claim an exercise was completed if only its assignment was generated.

## 7. Don'ts · 反模式黑名单（永不触犯）

下列每条都是本 skill 历次实战中**真实触发过的失败模式**。每条都给出"反模式 / 触发条件 / 为什么不要做 / 替代做法"。

| # | 反模式 | 触发条件 | 为什么不要做 | 替代做法 |
|---|---|---|---|---|
| 1 | **把记忆中的信息冒充为已核对的原文证据** | 只有书名或材料未覆盖该细节 | 虚构的引文和定位无法追溯 | 继续给出明确标为待核实、低置信度的解读；不生成虚假的 evidence ID、原句或章节定位 |
| 2 | **跨章节的"全部完成 / 整本完成"误报** | 用户只给了部分章节 | `coverage_percent=100`、`completeness=complete` 仅表示声明范围内的预期章节均已收到并处理，不表示整本完成 | 严格按 §1.5 的 coverage manifest 写三列；`work.scope` 选 selected_chapters/excerpt，scope_note 明示"本批仅覆盖声明范围" |
| 3 | **技巧卡描述中带具体章节 / 场景 / 道具 / 关系** | 试图让技巧"具体可感" | 技巧卡的迁移性来自**抽象机制**，不是具体元素——列了"土坯胡同 + 寡妇 + 盲弟"就只对《人世间》有用 | 技巧卡只保留 mechanism / counterfactual / adaptation 三个抽象维度；用 adaptation 段说"在全新场景中……" |
| 5 | **把零材料的探索性分析说成原文核验结果** | 只有书名，coverage 为 unknown | 用户无法分清已核对事实和试探性解读 | 使用 `title_only` 范围继续分析，将未核实判断标为低置信度，不填写虚假证据或章节覆盖 |
| 6 | **超出声明范围做"全书评价"** | 用户的 scope=excerpt / selected | 全书评价所需的 evidence 永远不够 | 在 `work.scope_note` 显式写"本分析仅基于用户声明的 N 章 / N 段"，所有 strengths / limitations 限定在该范围内 |
| 8 | **把缺乏依据的评价写成定论** | soul / technique 判断缺少可见支持 | 读者容易把猜测当成已核对结论 | 保留有用的解释，但标为低置信度或待核实；避免具体而无依据的细节 |
| 9 | **把 `validate_output.py` 通过 = "分析完成"** | 看到"Structural check passed"就收工 | 脚本只查 JSON 结构与引用关系，**不查引用是否为真** | 有原文时抽查 evidence 能否回到来源；只有书名时核对所有未核实判断是否已明确标注 |
| 10 | **练习题自带答案 / 自写范文** | 用户的练习题被代写 | 用户要的是"练习"而非"成品"；代写剥夺了用户的写作训练 | assignment 只写 prompt + rubric；评估草稿留给 draft_evaluation；自评只能在用户提交后才做 |
