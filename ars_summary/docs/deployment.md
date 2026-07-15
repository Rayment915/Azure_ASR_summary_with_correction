# 部署与导入说明

## 1. 部署 MarkItDown 服务

### 本地虚拟环境（开发、测试或直接启动服务）

本项目**不使用全局 Python 包**。在项目根目录创建 `.venv` 并通过其解释器安装所有 Python 依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r services/markitdown-service/requirements.txt
```

本地启动服务：

```bash
.venv/bin/python -m uvicorn app:app --app-dir services/markitdown-service --host 127.0.0.1 --port 3333
```

运行离线验证：

```bash
.venv/bin/python tests/validate_transcript.py
.venv/bin/python tests/test_splitter.py
```

### 单容器 Docker 运行

该服务只有一个容器，不需要运行 Docker Compose。以下命令构建镜像并在后台运行服务：

```bash
docker build -t markitdown-service:local services/markitdown-service

docker run -d \
  --name markitdown-service \
  --restart unless-stopped \
  --publish 127.0.0.1:3333:3333 \
  --read-only \
  --tmpfs /tmp:size=256m \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  markitdown-service:local
```

安全部署中，浏览器通过同域 Nginx 路径访问 MarkItDown；Nginx 再通过 `127.0.0.1:3333` 调用它，因此无需配置 CORS。Azure VM 的 Nginx 直接代理部署见 `docs/vm-nginx-proxy-deployment.md`。

镜像构建时会在容器内创建 `/opt/venv`，所有 `requirements.txt` 依赖和 Uvicorn 进程都从该虚拟环境执行；不会安装到容器的全局 Python site-packages。

查看健康状态：

```bash
curl http://127.0.0.1:3333/healthz
```

停止并删除容器：

```bash
docker rm -f markitdown-service
```

默认服务仅监听本机 `127.0.0.1:3333`，仅供 VM 上的 Nginx 反向代理使用；不要开放到公网，也不要让浏览器直接调用。

生产环境应在反向代理层增加身份验证、请求大小限制、TLS 与访问日志，并将端口从宿主机暴露配置中移除，仅保留 Docker 内部网络。

## 2. 配置 Dify 模型

1. 打开 Dify 控制台的模型供应商设置。
2. 配置 Azure OpenAI endpoint、API key、API version 和 deployment。
3. 确认可用模型的部署名为 `gpt-5.4`。
4. 导入 DSL 后，分别打开“材料术语提取”“分块事实抽取”“最终纪要”三个 LLM 节点，确认它们均选择 Azure OpenAI 的 `gpt-5.4`。

> 不同 Dify Provider 插件可能使用不同内部 provider ID。DSL 默认 `azure_openai`；若导入时模型未自动绑定，在画布中重新选择一次模型即可，节点 Prompt、变量及流程无需改动。

## 3. 导入工作流

在 Dify Studio 创建“工作流”应用，使用“导入 DSL”选择 `dify/long-meeting-summary.yml`。发布应用后，将 API Key 写入 VM 上 `/etc/nginx/meeting-summary-dify-key.conf`；不要交给上传页面或浏览器。

## 4. 资源建议

- 长会议场景需要设置足够的 Workflow 最大执行时间，并使 Azure OpenAI 部署有适当 TPM/RPM 配额。
- 分块默认约 9,000 字符；如果模型上下文或配额较紧，改 DSL 中“切分逐字稿”代码的 `target_size` 为 `6000`。若会议术语很多，优先压缩材料而非提高块大小。
- 不要将原始会议转写、材料文件或 Dify API Key 写入浏览器日志、代理日志或公开对象存储。
