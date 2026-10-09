# Book-setting backfill in Denova

Use this workflow for requests such as “补全书籍设定” or “检查项目缺少哪些书籍文件并补全”. Work in the active book project. This is a workspace update, not the five-phase analysis report.

## 1. Inventory before writing

1. Confirm the active book project. If there is no identifiable project, ask which book to update. Never mix material from different books.
2. List and read `ideas.md`, `CREATOR.md`, `setting/outline.md`, `setting/progress.md`, `setting/character-states.md`, `setting/chapter-groups/`, and the actual chapter paths under `chapters/`. Query existing Lore with `query_lore_items` (stored in `setting/lore/items.json`); do not edit that JSON directly.
3. For each target, distinguish **missing file**, **empty/default template**, **partly filled**, and **meaningful content**. A file containing only headings, TODOs, or “（自定义）” is not complete. Record the missing sections, not just missing filenames.
4. Read available chapters in order before deriving facts. Written prose and chapter paths outrank stale summaries for what has happened; explicit author plans govern unwritten future events. Existing author instructions in `CREATOR.md` remain authoritative. Use summaries only for scope they actually cover.
5. Read `skill://novel-analysis-craft/references/book-setting-templates.md` for each file's section guide. Match equivalent headings already in the project instead of adding duplicate sections.

## 2. Fill supported gaps

Use Denova's `write`/`edit` tools for workspace Markdown and `write_lore_items` for Lore. Create a missing file when there is grounded content for it. Fill only missing or placeholder sections using the book-setting templates as guides; preserve meaningful user-written content and its wording. If sources disagree, leave the disputed field unchanged, note the conflict, and continue with independent fields. Re-running this workflow should add nothing when no new gaps or evidence exist.

For an ongoing book, fill a missing next-group plan only when the user or existing plan gives enough direction; read `skill://novel-analysis-craft/references/chapter-group-outline-template.md`. Do not invent a next group for a completed or imported work.

Do not create empty boilerplate to make the file list appear complete. Missing source support is an unresolved item, not a reason to stop the whole task.

## 3. Long works and completion

Inspect all available chapters needed for the requested scope. If the work is too long for one pass, process contiguous batches and keep `setting/book-setting-coverage.md` with exact chapter paths already read, the batch's updated files, and remaining paths. On continuation, check whether previously read chapters changed before relying on that record. Never claim whole-book coverage from a sample.

Read back every changed file or Lore item. Check that placeholders were actually replaced, existing user content survived, chapter counts match actual paths, facts remain attributable to available material, and no duplicate Lore item was added. Finish with a concise file-by-file report: **filled**, **preserved**, **unresolved/conflicted**, **chapter coverage**, and any remaining batches. Claim completion only for verified writes and inspected chapters.
