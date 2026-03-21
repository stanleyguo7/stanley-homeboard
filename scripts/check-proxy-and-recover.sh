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
#   PASSWALL_GLOBAL_SECTION    全局 section（默认 @global[0]，用于自动探测）
#   PASSWALL_TARGET_SECTION    实际写入 section（默认自动探测）
#   PASSWALL_NODE_OPTION       实际写入字段（默认自动探测）
#
# 防抖与回切（可选，默认开启）：
#   PROXY_STATE_FILE           状态文件（默认 /tmp/check-proxy-state）
#   FAIL_THRESHOLD             连续失败达到阈值才执行恢复（默认 3）
#   RECOVER_THRESHOLD          连续成功达到阈值后允许回切主节点（默认 2）
#   PREFER_PRIMARY             1=优先回切主节点，0=不回切（默认 1）
#   PASSWALL_PRIMARY_NODE      主节点 ID（默认取候选列表第一个）
#
#   自动探测逻辑：
#   1) @global[0].tcp_node 存在 -> 写 @global[0].tcp_node
#   2) @global[0].node 指向某节点，且该节点有 default_node -> 写 <node>.default_node
#   3) 否则写 @global[0].node

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
PASSWALL_TARGET_SECTION="${PASSWALL_TARGET_SECTION:-}"
PASSWALL_NODE_OPTION="${PASSWALL_NODE_OPTION:-}"

PROXY_STATE_FILE="${PROXY_STATE_FILE:-/tmp/check-proxy-state}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-3}"
RECOVER_THRESHOLD="${RECOVER_THRESHOLD:-2}"
PREFER_PRIMARY="${PREFER_PRIMARY:-1}"
PASSWALL_PRIMARY_NODE="${PASSWALL_PRIMARY_NODE:-}"

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

read_state() {
  FAIL_COUNT=0
  SUCCESS_COUNT=0
  [[ -f "$PROXY_STATE_FILE" ]] || return 0
  while IFS='=' read -r k v; do
    case "$k" in
      FAIL_COUNT) FAIL_COUNT="${v:-0}" ;;
      SUCCESS_COUNT) SUCCESS_COUNT="${v:-0}" ;;
    esac
  done < "$PROXY_STATE_FILE"
}

write_state() {
  cat > "$PROXY_STATE_FILE" <<EOF
FAIL_COUNT=${FAIL_COUNT:-0}
SUCCESS_COUNT=${SUCCESS_COUNT:-0}
EOF
}

current_passwall_node() {
  detect_passwall_target
  remote_run "uci -q get passwall2.${PASSWALL_TARGET_SECTION}.${PASSWALL_NODE_OPTION} || true" | tr -d '\r\n'
}

switch_to_node() {
  local node="$1"
  detect_passwall_target
  remote_run "uci set passwall2.${PASSWALL_TARGET_SECTION}.${PASSWALL_NODE_OPTION}='${node}' && uci commit passwall2"
}

detect_passwall_target() {
  if [[ -n "$PASSWALL_TARGET_SECTION" && -n "$PASSWALL_NODE_OPTION" ]]; then
    return 0
  fi

  local gnode has_tcp has_default
  has_tcp="$(remote_run "uci -q get passwall2.${PASSWALL_GLOBAL_SECTION}.tcp_node >/dev/null 2>&1; echo $?" | tr -d '\r\n')"
  if [[ "$has_tcp" == "0" ]]; then
    PASSWALL_TARGET_SECTION="$PASSWALL_GLOBAL_SECTION"
    PASSWALL_NODE_OPTION="tcp_node"
    return 0
  fi

  gnode="$(remote_run "uci -q get passwall2.${PASSWALL_GLOBAL_SECTION}.node || true" | tr -d '\r\n')"
  if [[ -n "$gnode" ]]; then
    has_default="$(remote_run "uci -q get passwall2.${gnode}.default_node >/dev/null 2>&1; echo $?" | tr -d '\r\n')"
    if [[ "$has_default" == "0" ]]; then
      PASSWALL_TARGET_SECTION="$gnode"
      PASSWALL_NODE_OPTION="default_node"
      return 0
    fi
  fi

  PASSWALL_TARGET_SECTION="$PASSWALL_GLOBAL_SECTION"
  PASSWALL_NODE_OPTION="node"
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

  local current next idx=-1

  detect_passwall_target
  log "节点切换目标：passwall2.${PASSWALL_TARGET_SECTION}.${PASSWALL_NODE_OPTION}"

  current="$(remote_run "uci -q get passwall2.${PASSWALL_TARGET_SECTION}.${PASSWALL_NODE_OPTION} || true" | tr -d '\r' | tr -d '\n')"
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
  remote_run "uci set passwall2.${PASSWALL_TARGET_SECTION}.${PASSWALL_NODE_OPTION}='${next}' && uci commit passwall2"
}

maybe_return_to_primary() {
  [[ "$PREFER_PRIMARY" == "1" ]] || return 0
  [[ -n "$PASSWALL_NODE_CANDIDATES" ]] || return 0

  local primary current
  if [[ -n "$PASSWALL_PRIMARY_NODE" ]]; then
    primary="$PASSWALL_PRIMARY_NODE"
  else
    IFS=',' read -r -a CANDS <<< "$PASSWALL_NODE_CANDIDATES"
    primary="${CANDS[0]:-}"
  fi
  [[ -n "$primary" ]] || return 0

  current="$(current_passwall_node)"
  if [[ "$current" == "$primary" ]]; then
    return 0
  fi

  if [[ ${SUCCESS_COUNT:-0} -ge ${RECOVER_THRESHOLD:-2} ]]; then
    log "连续成功 ${SUCCESS_COUNT} 次，回切主节点：$current -> $primary"
    switch_to_node "$primary"
    remote_run "/etc/init.d/passwall2 restart"
    SUCCESS_COUNT=0
    write_state
  fi
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
  read_state

  if check_connectivity; then
    FAIL_COUNT=0
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    write_state
    maybe_return_to_primary
    log "网络检测通过，无需恢复。连续成功：$SUCCESS_COUNT"
    exit 0
  fi

  SUCCESS_COUNT=0
  FAIL_COUNT=$((FAIL_COUNT + 1))
  write_state

  if [[ $FAIL_COUNT -lt $FAIL_THRESHOLD ]]; then
    log "外网疑似不可达，连续失败 $FAIL_COUNT/$FAIL_THRESHOLD，暂不切换。"
    exit 1
  fi

  log "外网疑似不可达，连续失败 $FAIL_COUNT 次，执行软路由恢复流程。"
  recover_proxy

  sleep 3
  if check_connectivity; then
    FAIL_COUNT=0
    SUCCESS_COUNT=1
    write_state
    log "恢复成功。"
    exit 0
  fi

  log "恢复后仍不可达，请人工检查。"
  exit 2
}

main "$@"
