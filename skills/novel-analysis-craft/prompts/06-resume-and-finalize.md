# 06 · 续跑与最终检查

读取已有 checkpoint 和新批次，然后：

1. 先检查 checkpoint 与新批次的作品名是否一致，再对比章节、批次 ID、批次内容 SHA-256 和证据 ID。不同作品或同 ID 不同内容都不得合并；JSON 批次可先运行 `python scripts/validate_output.py <checkpoint.json> --input <new-input.json>`。
2. 只处理尚未处理的批次，分别更新 received 和 processed 章节集合。
3. 仅当新证据可能影响旧结论时才回查；在 correction_log 中记录旧判断、新证据和修订结论。
4. 按声明范围重新计算覆盖。没有预期章节清单时保持 unknown；缺章或未处理章节时不能称该范围完整。
5. 对受新材料影响的阶段重新跑质量门槛，未受影响的阶段保留原门槛状态。
6. 核对有来源的 claim 和技巧卡所引用的 evidence ID；无来源的判断改为低置信度推断或评价，引用数组留空。
7. 如实确认五个阶段状态，包括练习草稿是否已提交和评估。
8. 返回可读报告、结构化结果、未解决缺口和明确下一步。

遵循 references/quality-gates.md。有 JSON 时可运行内置检查器。检查器只核对结构和引用链接，不替代原文审阅。
