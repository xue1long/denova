# Denova book-setting templates

Use these as **section guides** when the book-setting backfill workflow creates a missing Markdown file or fills a missing section. The examples use Chinese headings for a Chinese-language book; match the project's language when different. Replace every `<...>` slot with supported content or omit that optional line/section. Do not copy placeholders into a finished file, rename equivalent existing headings, or rewrite meaningful author content merely to match this layout.

For an existing book, separate facts observed in written chapters from author-confirmed intentions and plans. A blank field is an unresolved input, not permission to invent it.

## `ideas.md` — creative direction

```md
# 灵感

## 当前方向
- 一句话方向：<作者确认的方向，或明确标注“从现有正文归纳”>

## 作品定位
- 类型：<已确认或可从正文判断的类型>
- 目标读者：<作者明确指定时填写>
- 整体基调：<注明作者确认或正文归纳>

## 核心吸引力
- 核心卖点：<有依据的吸引力>
- 独特前提或设定：<适用时填写>

## 已确认的创作取舍
- <作者确认的选择及理由>

## 待决定的问题
- <确实尚待作者选择的事项>

## 参考作品
- <作者明确指定时填写>
```

Do not infer target readers, reference works, or the author's original intent from prose. An existing `## 核心卖点`, `## 作品信息`, `## 金手指 / 独特设定`, or `## 其他要求` section can serve the equivalent role; preserve its content and heading.

## `CREATOR.md` — author-owned long-term instructions

```md
# 创作者指令

## 篇幅与结构
- <作者确认的长期要求>

## 叙事视角与文风
- <作者确认的长期要求>

## 对话与描写
- <作者确认的长期要求>

## 禁止内容
- <作者明确禁止的内容或写法>

## 其他长期要求
- <作者确认的规则>
```

Only explicit author instructions belong here. Existing `## 创作约束`, `## 写作风格`, `## 禁止内容 必须遵守`, and `## 其他要求` can serve these roles. Preserve their rules; do not infer new instructions from observed prose or add empty headings just to complete the template. If a preference is unknown, report it as unspecified outside `CREATOR.md`.

## `setting/outline.md` — long-term structure

```md
# 全书大纲

## 核心主线
- 主角目标：<有依据的目标>
- 核心阻力：<有依据的阻力>
- 故事推进方向：<已确认或标注为正文回顾>

## 已写正文的结构（回顾）
### 阶段一｜<名称>
- 章节范围：<实际章节路径或编号>
- 结构作用：<这一段如何推进主线>
- 关键转折与结果：<正文实际发生的结果>

## 未写部分的规划
### 阶段二｜<名称>
- 计划章节范围：<已有计划时填写>
- 阶段目标：<作者或既有规划确认的目标>
- 主要冲突：<已有规划>
- 预期转折：<已有规划>

## 待作者决定
- <没有既定答案的结构选择>
```

Repeat stage blocks as needed. Omit the retrospective section for a new book without prose and the future-plan section for a completed work without a sequel plan. Summarize structural function rather than copying chapter recaps from `progress.md`. Never present planned events as completed or invent future outcomes.

## `setting/progress.md` — actual writing progress

```md
# 写作进度

## 已完成范围
- 已写章节：<实际存在且有正文的章节范围与数量>
- 最新正文文件：<实际路径>
- 故事当前时间与位置：<正文可确认时填写>

## 最近章节
### 第 X 章｜<标题>
- 实际发生：<简短摘要>
- 章末结果：<已发生的状态变化>
- 对下一章的影响：<正文留下的承接点>

## 下一章承接
- 尚未解决的事件：<真实遗留>
- 需要保持的连续性：<写作时必须记住的事实>
```

Repeat recent-chapter blocks only as useful. Chapter paths and non-empty prose determine completion, not chapter plans or UI status. For a finished book, say that the prose ends there instead of inventing a next chapter.

## `setting/character-states.md` — latest continuity state

```md
# 人物状态

记录基准：<最后核对的章节或时间点>

## <人物姓名>
- 最近出场：<章节>
- 当前位置：<可确认时填写>
- 身体与心理状态：<当前可确认的变化>
- 当前目标：<当前可确认的目标>
- 关系变化：<与此前相比发生的变化>
- 物品或能力变化：<影响后续连续性时填写>
- 未解事项：<仍在持续的压力或线索>
```

Repeat only for characters whose current state matters. Omit unknown or unchanged optional fields. Record death or departure as the latest state; do not assign a current goal to someone who no longer has one. Stable identity, background, and enduring relationships belong in Lore.

## Lore — structured collection and item content

`setting/lore/items.json` is a managed collection with a version, categories, and items. Denova initializes its structure. Query existing items first and create/update entries with `write_lore_items`; never write the JSON file directly or reset the project's categories. Keep each item focused on stable facts:

| Item type | Suggested `content` fields |
| --- | --- |
| `character` | Stable identity, background, enduring traits and relationships. |
| `location` | Location, lasting features, and access constraints. |
| `faction` | Purpose, membership or hierarchy, lasting relationships. |
| `item` | Identity, persistent properties, origin, and usage rules. |
| `world` | Setting facts, systems, rules, scope, and exceptions. |

Use only fields supported by the source, and include a chapter locator when available. Current injury, mood, location, possessions, and short-term goals belong in `character-states.md` instead.
