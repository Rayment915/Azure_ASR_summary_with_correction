# 不修改 Dify Compose 的 API 桥接方案

如果不希望修改 Dify 的 Docker Compose 或直接发布 `api:5001`，运行一个独立 Nginx 容器作为桥接器：

```text
会议页面 Nginx（宿主机）
  → 127.0.0.1:2222
    → dify-api-bridge Docker 容器
      → Dify Docker 网络中的 api:5001
```

桥接器只将端口绑定到 VM 回环地址，Azure NSG/UFW 不需要开放 `2222`。

## 1. 找到 Dify 的 Docker 网络名称

根据你的容器名称 `docker-api-1`，Dify Compose 项目通常叫 `docker`，默认网络通常是 `docker_default`。先确认：

```bash
docker inspect docker-api-1 --format '{{range $name, $_ := .NetworkSettings.Networks}}{{println $name}}{{end}}'
```

记下输出。例如输出为：

```text
docker_default
```

下方命令将 `docker_default` 替换为你的实际网络名。

也可以让 Shell 自动读取网络名：

```bash
DIFY_NETWORK="$(docker inspect docker-api-1 --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}')"
echo "$DIFY_NETWORK"
```

## 2. 在 VM 上运行独立桥接器

```bash
cd /data/asr_summary

# 若已执行上一步自动读取命令，可将下方 docker_default 改为 "$DIFY_NETWORK"。

docker run -d \
  --name dify-api-bridge \
  --restart unless-stopped \
  --network docker_default \
  --publish 127.0.0.1:2222:2222 \
  --read-only \
  --tmpfs /var/cache/nginx:size=16m \
  --tmpfs /var/run:size=1m \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --mount type=bind,source="$(pwd)/nginx/dify-api-bridge.conf",target=/etc/nginx/conf.d/default.conf,readonly \
  nginx:1.27-alpine
```

桥接器运行在只读根文件系统中，配置已将访问日志和错误日志写入 Docker stdout/stderr；使用以下命令查看：

```bash
docker logs --tail=100 dify-api-bridge
```

这个容器不会修改 Dify 的镜像、Compose 文件或容器。它只加入 Dify 已有 Docker 网络，通过服务名 `api` 访问容器内部端口 `5001`。

## 3. 验证桥接器

```bash
docker ps --filter name=dify-api-bridge
curl -i http://127.0.0.1:2222/health
curl -i -X POST http://127.0.0.1:2222/v1/workflows/run
```

期望：

- `docker ps` 显示 `127.0.0.1:2222->2222/tcp`；
- `/health` 返回 `200`；
- 未附应用 API Key 的 `/v1/workflows/run` 返回 `401`、`400` 或 `422`，不能是 `404`。

查看桥接器错误：

```bash
docker logs --tail=100 dify-api-bridge
```

## 4. 使用会议页面 Nginx

会议页面 Nginx 已配置为：

```nginx
proxy_pass http://127.0.0.1:2222/v1/workflows/run;
```

桥接器通过验证后，更新会议页面配置并重启：

```bash
sudo install -m 0644 nginx/meeting-summary.conf /etc/nginx/sites-available/meeting-summary
sudo sed -i 's/YOUR_DOMAIN/20.171.8.48/g' /etc/nginx/sites-available/meeting-summary
sudo nginx -t
sudo systemctl restart nginx
```
