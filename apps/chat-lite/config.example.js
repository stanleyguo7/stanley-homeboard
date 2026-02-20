window.CHATLITE_CONFIG = {
  host: "100.96.233.69",
  gatewayPort: 18789,
  gatewayProtocol: "ws", // https 页面可改为 "wss"
  // gatewayUrl: "wss://your-domain-or-tailnet:18789", // 优先级高于 host/gatewayPort
  token: "REPLACE_WITH_YOUR_GATEWAY_TOKEN",
  sessionKey: "agent:main:main",
  sessions: [
    "agent:main:main",
    "agent:main:topic:chat-project",
    "agent:main:topic:demos"
  ],
  refreshMs: 1800,
  maxRenderMessages: 120
};
