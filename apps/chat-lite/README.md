# Chat Lite (Homeboard module)

一个轻量手机聊天页面，直连 OpenClaw Gateway WebSocket。

## 使用

1. 复制配置模板：

```bash
cp config.example.js config.js
```

2. 编辑 `config.js`，填入你的 `gateway token`。

3. 在该目录启动静态服务（示例）：

```bash
python3 -m http.server 8790
```

4. 手机访问并可添加到主屏幕。

## 安全说明

- `config.js` 包含敏感 token，已在 `.gitignore` 中忽略，不会提交。
- 仅提交 `config.example.js` 模板。
