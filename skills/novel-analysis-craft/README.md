# 小说拆解与写作技巧提炼 Skill

这是一个可独立安装的 AI Skill，支持 Denova 书籍设定补全、章节组细纲和带证据的小说拆解。拆解流程可分批续跑：

**骨架 → 血肉 → 灵魂 → 技巧卡片 → 写作 SOP 与创作练习**

## 文件结构

- SKILL.md：触发条件、运行步骤、深度模式和最终输出要求。
- references/：Denova 可读取的书籍设定补全流程与文件模板、章节组模板、分析提示词、JSON Schema、Markdown 模板和质量规则。
- examples/：原创微型故事的输入与完整示例输出。
- scripts/validate_output.py：仅使用 Python 标准库，检查核心必需字段、章节覆盖、来源批次和证据引用。

Denova 的技能阅读工具可加载 `references/` 下的文件；`examples/` 与 `scripts/` 供能够访问本地 Skill 目录的环境使用。

## 安装

解压后，将整个 novel-analysis-craft 文件夹放进任一受支持的 Skill 目录，例如：

- Windows：%USERPROFILE%\.codex\skills\novel-analysis-craft\
- 通用 Agent 目录：~/.agents/skills/novel-analysis-craft/

也可以把文件夹交给支持 SKILL.md 的 Agent 手动加载。

## 使用

在 Denova 的书籍项目中说“补全书籍设定”，Skill 会先检查现有章节、设定文件和 Lore，再按 `references/book-setting-templates.md` 补齐有材料支持的缺失文件或空白栏目；已有的有效内容和等价栏目会保留。完成后会列出实际修改、未能确认的事项及已核对的章节范围。长篇分批处理时会记录覆盖范围，不会把抽样结果说成全书完成。

说“生成/补全章节组细纲”时会使用 `references/chapter-group-outline-template.md`，按实际章节和项目设定填写。

以下是小说拆解流程：

提供书名即可开始探索性拆解；有原文、笔记或章节摘要时可进一步核对细节。可直接这样说：

> 用这个 Skill 按 standard 深度拆解我提供的小说章节。请按骨架、血肉、灵魂、技巧卡片、创作练习依次分析。有原文时标注章节和证据 ID；没有原文时继续做探索性分析并标明不确定性。

长篇可按批次输入，并沿用稳定章节 ID：

> 继续拆解。上次 checkpoint 在 ch08；本批是 ch09–ch12。请读取 checkpoint，只处理新章节，检查它们是否改变旧判断，并输出更新后的 checkpoint。

如果只知道书名而没有原文或可用笔记，Skill 会继续分析，标出未经原文核实的判断，不伪造引文或章节位置。

## 深度模式

- **quick**：五阶段全部保留，每项做最小有效分析，产出一张技巧卡和练习题。
- **standard**：覆盖显著情节、支线、关键角色，产出三张技巧卡、SOP 和练习评价标准。
- **deep**：按章节追踪因果、反转、主题与情感，产出 3–5 张技巧卡和更完整的反事实检验。

深度控制分析范围。材料不够时仍可给出探索性分析，并区分低置信度判断与可核对的结论。

## 来源与证据

Skill 可使用用户材料、一般知识或可访问的公开简介进行分析，无需先确认材料来源或分享权限。报告以转述为主；不输出长段原文，也不仿写特定作者的独特表达。技巧卡描述可迁移的结构机制，并要求用新的场景、人物和措辞练习。

有可见来源的分析判断使用证据 ID；其他判断明确标为低置信度推断或评价，`evidence_refs` 留空。没有原文时不编造页码、章节号或引文。引用位置不够精确时，退回到实际可见的章节/批次定位；只有书名时章节覆盖标为 unknown。

## 练习评估

默认生成一项 500–1500 字的练习任务和评价量表，不自动冒充用户完成了练习。用户交来片段后，Skill 再按量表反馈：技巧是否落地、因果是否清楚、读者效果是否成立、表达是否原创，以及下一轮可改之处。

## 示例

查看 examples/quick-demo.input.json 和 examples/quick-demo.output.json。示例中的故事为本包原创短例；examples/quick-demo-resume.input.json 与 examples/quick-demo-resume.output.json 展示同一作品的第 4 章续跑和有据可查的结论修订。

## 可选结构检查

在 Skill 文件夹中运行：

~~~text
python scripts/validate_output.py path/to/analysis-output.json
~~~

续跑前可核对新批次与旧 checkpoint 是否属于同一作品，以及重复 chunk ID 是否保持同一章节和内容：

~~~text
python scripts/validate_output.py path/to/checkpoint.json --input path/to/new-batch.input.json
~~~

输出 schema 为 1.1，checkpoint 的 `source_chunks` 保存 chunk ID、章节 ID 和解码后内容的 UTF-8 SHA-256，不复制小说原文。旧版 1.0 checkpoint 缺少这份清单，续跑前需从原始输入重建。

该检查器不需要第三方 Python 套件。它检查核心结构和引用链接，不能代替完整 JSON Schema 校验，也不能判断解释是否合理；分析仍须对照原文审阅。

回归测试可运行 `python scripts/test_validate_output.py -v`；若环境安装了 `jsonschema`，测试还会核对所有随包示例与正式 JSON Schema 是否一致。
