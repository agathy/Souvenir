#!/usr/bin/env python3
"""
本地拼合服务 — 配合 figma_page.html 在导出后自动触发 stitch_tiles.py

用法:
    python3 server.py
然后在浏览器中打开 figma_page.html，点击导出，完成后自动拼合。
按 Ctrl+C 停止服务。
"""
import http.server
import subprocess
import sys
from pathlib import Path

PORT   = 8765
SCRIPT = Path(__file__).parent / 'stitch_tiles.py'


class Handler(http.server.BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != '/stitch':
            self.send_response(404)
            self.end_headers()
            return
        try:
            res = subprocess.run(
                [sys.executable, str(SCRIPT)],
                capture_output=True,
                text=True,
                cwd=str(SCRIPT.parent)
            )
            body = (res.stdout + res.stderr).strip().encode('utf-8')
        except Exception as e:
            body = str(e).encode('utf-8')

        self.send_response(200)
        self._cors()
        self.send_header('Content-Type',   'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        print('  ' + fmt % args)


if __name__ == '__main__':
    print(f'✓ 拼合服务已启动 → http://localhost:{PORT}')
    print(f'  脚本路径: {SCRIPT}')
    print('  在浏览器中导出图片后将自动触发拼合，按 Ctrl+C 停止。\n')
    with http.server.HTTPServer(('localhost', PORT), Handler) as s:
        s.serve_forever()
