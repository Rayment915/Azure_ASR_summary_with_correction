# Dify 导入故障排查

如果导入 DSL 后画布显示“渲染此组件时发生了意外错误”，优先查看浏览器错误和 Dify `web` 容器日志。这个错误通常来自前端画布解析节点，而不一定会在 `api` 容器中记录。

## 1. 获取日志

在 Dify Docker Compose 目录（包含 `docker-compose.yaml` 的目录）执行：

```bash
docker compose ps
docker compose logs --tail=200 web
docker compose logs --tail=200 api
```

实时观察并重新导入 DSL：

```bash
docker compose logs -f web api
```

如果你的 Compose 服务名不是 `web` 和 `api`，先用 `docker compose ps --services` 确认后替换命令中的服务名。

同时在浏览器打开 Dify 页面后按 `F12`（macOS 可用 `Option + Command + I`），在 **Console** 复制第一条红色错误和调用栈；在 **Network** 中找到 DSL 导入请求，保存其 Response。前端组件渲染异常最有价值的是浏览器 Console，而不是仅看 API 日志。

## 2. 本项目已修复的 1.15 DSL 兼容问题

更新后的 `dify/long-meeting-summary.yml` 已按 Dify `1.15.0` 导出结构修复：

- Iteration 内部的开始节点和 LLM 节点改为画布**顶层节点**，并使用 `parentId`、`iteration_id` 与 `custom-iteration-start` 关联；旧文件将子节点嵌套在 Iteration 节点中，会导致前端画布无法渲染。
- 补齐 Iteration 的 `iterator_input_type`、`is_parallel`、`parallel_nums`、`error_handle_mode`、`flatten_output`、`_children` 和内部连线元数据。
- 将迭代项引用修复为 `{{#chunk-iteration.item#}}`；`iteration.item` 不是有效节点变量。
- 将变量聚合器输出改为 Dify 固定输出变量 `output`，并将条件节点比较符改为 Dify 使用的 `=`。

## 3. 重新导入

1. 使用当前目录里更新后的 `dify/long-meeting-summary.yml`，不要继续使用先前下载的副本。
2. 在 Dify Studio 新建一个空白 Workflow，再选择“导入 DSL”；不要在已损坏的草稿画布上继续编辑。
3. 导入成功后，逐个打开三个 LLM 节点，将模型重新选择为你的 Azure OpenAI `gpt-5.4` 部署；不同 Provider 插件的内部标识可能不完全一致。
4. 保存后先使用 `tests/fixtures/azure-speech-sample.json` 的内容，以最小输入测试工作流。

## 4. 若仍失败，请提供以下内容

- Dify 的精确版本（在管理控制台或 `docker compose images` 中可见）。
- `docker compose logs --tail=200 web` 与 `docker compose logs --tail=200 api` 中从导入时刻开始的错误段，注意删除 API Key、数据库密码和内部域名。
- 浏览器 Console 的首条错误及完整 stack trace。
- Network 中导入请求的 HTTP 状态码与响应正文。

有了这些信息可以确定是 DSL 字段兼容性、Provider 插件、Dify 前端构建版本不一致，还是浏览器缓存造成的问题。
