# Dify 已运行但未返回 `final_minutes`

当页面显示“Dify 未返回 final_minutes”时，说明请求已进入 Dify；问题不在 Nginx、MarkItDown、桥接器或应用 API Key，而在发布版本的 Workflow 运行或 End 节点输出。

如果页面响应中的 `status` 是 `failed`，应先修复 `data.error` 所指的前置节点错误，再检查 End 节点。此前 Dify 1.15 会对本工作流的“是否有会议材料”条件节点出现 `Invalid actual value type: number or boolean`；当前 DSL 已移除此条件与变量聚合器，术语节点会在材料为空时直接返回空词表。

## 正确的 End 节点配置

打开 Workflow 画布的 **结束** 节点，确认至少存在这一项：

| 输出变量 | 取值 |
| --- | --- |
| `final_minutes` | `最终纪要`（`final-minutes` 节点）的 `text` |

保存并重新发布 Workflow。注意：编辑草稿不等于已发布；网页 API 只会运行发布后的版本。

本项目 DSL 中对应配置为：

```yaml
- variable: final_minutes
  value_selector: [final-minutes, text]
  value_type: string
```

## 从页面获得实际响应

更新 `frontend/index.html` 后，若仍没有纪要，页面下方会显示 Dify 完整响应和 `outputKeys`；浏览器 Console 也会记录完整响应。根据 `outputKeys` 处理：

- 包含 `final_minutes`，但值为空：检查“最终纪要”节点是否执行失败或 Prompt/模型返回为空；在 Dify 运行详情查看该节点日志。
- 包含其他文本键：说明当前发布版本的 End 节点变量名不同；可在 Dify End 节点改为 `final_minutes`，或记录该键名。
- 空数组或没有 `outputs`：End 节点没有输出，或仍运行旧发布版本；保存、发布后再试。

## Dify 中查看节点日志

在应用的 **监控 / 日志** 页面打开这次运行记录，依序检查：

1. `最终纪要` LLM 节点状态是否为成功，以及其 `text` 是否包含纪要；
2. `结束` 节点是否成功，以及输出变量列表是否含 `final_minutes`；
3. 当前页面调用的应用是否正是已修改并发布的那个 Workflow。
