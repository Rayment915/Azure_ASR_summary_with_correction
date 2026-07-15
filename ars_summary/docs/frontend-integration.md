# Nginx 直接代理的上传页

`frontend/index.html` 由 Nginx 在 HTTP `4321` 提供。页面在 Mac 浏览器本地读取 Azure Speech JSON、自动解析 `speaker.id` 并生成姓名映射输入框。

点击“生成纪要”后，页面会按同域路径请求：

| 浏览器请求 | Nginx 上游 | 用途 |
| --- | --- | --- |
| `POST /markitdown/v1/convert` | `127.0.0.1:3333/v1/convert` | 转换 PPT/PDF/DOCX。 |
| `POST /dify-api/v1/workflows/run` | `127.0.0.1/v1/workflows/run` | 运行发布后的 Dify Workflow。 |

浏览器不会持有 Dify API Key。Nginx 从 `/etc/nginx/meeting-summary-dify-key.conf` 中读取 Key 并仅为 `/dify-api/v1/workflows/run` 注入 `Authorization` 请求头。

完整部署和排查说明见 `docs/vm-nginx-proxy-deployment.md`。

## Dify 请求内容

前端提交的 JSON 与 Dify Workflow Start 变量对应：

```json
{
  "inputs": {
    "transcript_json": "[{\"sentence_id\":\"0\",...}]",
    "speaker_mapping_json": "{\"1\":\"面试官\",\"2\":\"候选人\"}",
    "material_markdown": "## 会议材料：项目周会.pptx\n...",
    "meeting_template": "标准三段式纪要",
    "user_context": "重点关注下周风险和责任人"
  },
  "response_mode": "blocking",
  "user": "meeting-web-user"
}
```

页面优先读取 Dify 返回中的 `data.outputs.final_minutes`；为兼容已有应用，也会回退读取 `text` 或 End 节点中的第一个非空文本输出。若 Dify 返回没有任何文本输出，页面会显示完整响应和输出键名，供排查 End 节点。若某份材料转换失败，页面显示提示并仍使用其余成功材料和转写 JSON 生成纪要。
