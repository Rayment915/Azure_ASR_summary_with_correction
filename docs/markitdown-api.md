# MarkItDown HTTP API

服务实现位于 `services/markitdown-service`，用于将会议材料转换为 Markdown。上传页面负责逐文件调用和合并文本；Dify 不直接下载私有文件 URL。

## `POST /v1/convert`

- 请求：`multipart/form-data`
- 字段：`file`（单个 PDF、PPTX 或 DOCX）
- 单文件最大：30 MB
- 成功：`200 OK`

```json
{
  "filename": "项目周会.pptx",
  "markdown": "# Slide 1\n...",
  "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
}
```

- 不支持格式：`415 Unsupported Media Type`
- 文件过大：`413 Payload Too Large`
- 转换失败：`422 Unprocessable Entity`

```json
{
  "detail": "MarkItDown conversion failed: ..."
}
```

## `GET /healthz`

返回 `{"status":"ok"}`，供容器健康检查使用。

## 访问边界

该 API 设计为 VM 内部服务，仅由 Nginx 反向代理调用。容器端口必须绑定到 `127.0.0.1:3333`，不配置 CORS，也不公开暴露到公网。
