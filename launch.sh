#!/bin/bash
# Souvenir 启动脚本
# 同时启动拼合服务和在浏览器中打开页面

DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查 8765 端口是否已被占用
if lsof -i :8765 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "✓ 拼合服务已在运行 (port 8765)"
else
  echo "→ 启动拼合服务..."
  python3 "$DIR/server.py" &
  SERVER_PID=$!
  echo "  PID: $SERVER_PID"
  sleep 0.5
fi

# 检查 8080 端口（用于正确加载本地字体）
if lsof -i :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "✓ 文件服务已在运行 (port 8080)"
else
  echo "→ 启动文件服务..."
  python3 -m http.server 8080 --directory "$DIR" &
  echo "  PID: $!"
  sleep 0.5
fi

echo ""
echo "✓ 在浏览器打开: http://localhost:8080/figma_page.html"
echo "  (按 Ctrl+C 停止所有服务)"
echo ""

open "http://localhost:8080/figma_page.html"

# 等待，Ctrl+C 退出时同时关掉后台进程
trap "echo ''; echo '停止服务...'; kill 0" INT
wait
