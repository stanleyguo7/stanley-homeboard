#!/usr/bin/env bash
set -euo pipefail

# 检测外网连通性（默认 google.com），失败后通过 SSH 登录软路由，
# 执行 passwall2 重载；可选自动轮换代理节点。
#
# 用法：
#   chmod +x scripts/check-proxy-and-recover.sh
#   ROUTER_HOST=192.168.8.1 ROUTER_USER=root scripts/check-proxy-and-recover.sh
#
# 常用环境变量：
#   CHECK_URLS                 逗号分隔待检测 URL（默认见下方）
#   CHECK_RETRIES              每个 URL 重试次数（默认 2）
#   CHECK_TIMEOUT              每次请求超时秒数（默认 8）
#   ROUTER_HOST                软路由地址（必填）
#   ROUTER_USER                SSH 用户（默认 root）
#   ROUTER_PORT                SSH 端口（默认 22）
#   ROUTER_SSH_OPTS            额外 SSH 参数（可选）
#   ROUTER_RELOAD_CMD          重载命令（默认 passwall2 reload/restart）
#
# 自动切换节点（可选）：
#   PASSWALL_NODE_CANDIDATES   候选节点 ID（逗号分隔）
#                              例："hk_node,sg_node,jp_node"
#   PASSWALL_GLOBAL_SECTION    UCI section（默认 @global[0]）
#   PASSWALL_NODE_OPTION       节点字段（默认 tcp_node）

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

CHECK_URLS="${CHECK_URLS:-https://www.google.com/generate_204,https://www.gstatic.com/generate_204,https://www.youtube.com}"
CHECK_RETRIES="${CHECK_RETRIES:-2}"
CHECK_TIMEOUT="${CHECK_TIMEOUT:-8}"

ROUTER_HOST="${ROUTER_HOST:-}"
ROUTER_USER="${ROUTER_USER:-root}"
ROUTER_PORT="${ROUTER_PORT:-22}"
ROUTER_SSH_OPTS="${ROUTER_SSH_OPTS:-}"
ROUTER_RELOAD_CMD="${ROUTER_RELOAD_CMD:-/etc/init.d/passwall2 reload || /etc/init.d/passwall2 restart}"

PASSWALL_NODE_CANDIDATES="${PASSWALL_NODE_CANDIDATES:-}"
PASSWALL_GLOBAL_SECTION="${PASSWALL_GLOBAL_SECTION:-@global[0]}"
PASSWALL_NODE_OPTION="${PASSWALL_NODE_OPTION:-tcp_node}"

IFS=',' read -r -a URLS <<< "$CHECK_URLS"

url_ok() {
  local url="$1"
  curl -fsSIL --max-time "$CHECK_TIMEOUT" "$url" >/dev/null 2>&1
}

check_connectivity() {
  local url attempt
  for url in "${URLS[@]}"; do
    for ((attempt=1; attempt<=CHECK_RETRIES; attempt++)); do
      if url_ok "$url"; then
        log "连通性正常：$url"
        return 0
      fi
      log "检测失败（$attempt/$CHECK_RETRIES）：$url"
      sleep 1
    done
  done
  return 1
}

remote_run() {
  local cmd="$1"
  ssh -p "$ROUTER_PORT" $ROUTER_SSH_OPTS "${ROUTER_USER}@${ROUTER_HOST}" "$cmd"
}

rotate_node_if_configured() {
  if [[ -z "$PASSWALL_NODE_CANDIDATES" ]]; then
    log "未配置 PASSWALL_NODE_CANDIDATES，跳过节点切换。"
    return 0
  fi

  IFS=',' read -r -a CANDIDATES <<< "$PASSWALL_NODE_CANDIDATES"
  if [[ ${#CANDIDATES[@]} -lt 2 ]]; then
    log "PASSWALL_NODE_CANDIDATES 至少需要 2 个节点，当前不足，跳过切换。"
    return 0
  fi

  local candidates_joined current next idx=-1
  candidates_joined="${CANDIDATES[*]}"

  current="$(remote_run "uci -q get passwall2.${PASSWALL_GLOBAL_SECTION}.${PASSWALL_NODE_OPTION} || true" | tr -d '\r' | tr -d '\n')"
  log "当前节点：${current:-<empty>}"

  for i in "${!CANDIDATES[@]}"; do
    if [[ "${CANDIDATES[$i]}" == "$current" ]]; then
      idx="$i"
      break
    fi
  done

  if [[ "$idx" -ge 0 ]]; then
    next="${CANDIDATES[$(((idx + 1) % ${#CANDIDATES[@]}))]}"
  else
    next="${CANDIDATES[0]}"
  fi

  log "尝试切换节点：$current -> $next"
  remote_run "uci set passwall2.${PASSWALL_GLOBAL_SECTION}.${PASSWALL_NODE_OPTION}='${next}' && uci commit passwall2"
}

recover_proxy() {
  if [[ -z "$ROUTER_HOST" ]]; then
    log "ROUTER_HOST 未设置，无法自动恢复。"
    return 1
  fi

  log "开始恢复：重载 passwall2"
  remote_run "$ROUTER_RELOAD_CMD"

  rotate_node_if_configured || true

  # 切换后再重启一次确保生效
  remote_run "/etc/init.d/passwall2 restart"
}

main() {
  if check_connectivity; then
    log "网络检测通过，无需恢复。"
    exit 0
  fi

  log "外网疑似不可达，执行软路由恢复流程。"
  recover_proxy

  sleep 3
  if check_connectivity; then
    log "恢复成功。"
    exit 0
  fi

  log "恢复后仍不可达，请人工检查。"
  exit 2
}

main "$@"
