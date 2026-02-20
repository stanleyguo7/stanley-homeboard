# Chat Lite (Homeboard module)

一个轻量手机聊天页面，直连 OpenClaw Gateway WebSocket。

## 使用

1. 复制配置模板：

```bash
cp config.example.js config.js
```

2. 编辑 `config.js`，填入你的 `gateway token`。
   - 常规内网：使用 `host + gatewayPort`（默认 `ws`）
   - HTTPS/反代：设置 `gatewayProtocol: "wss"` 或直接设置 `gatewayUrl`

3. 推荐从仓库根目录启动（会先同步 GitHub 最新代码再启动）：

```bash
bash scripts/start-chat-lite.sh 8790
```

> 这样可以确保服务始终基于 GitHub 最新代码，并默认关闭浏览器缓存（避免看到旧页面）。

4. （可选）仅在当前目录临时启动静态服务：

```bash
python3 -m http.server 8790
```

5. 手机访问并可添加到主屏幕。

## 安全说明

- `config.js` 包含敏感 token，已在 `.gitignore` 中忽略，不会提交。
- 仅提交 `config.example.js` 模板。
