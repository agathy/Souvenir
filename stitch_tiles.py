#!/usr/bin/env python3
"""
stitch_tiles.py
将 Souvenir/export/ 中的分块 PNG 拼合为完整大图。

文件名规则（由 figma_page.html 导出按钮生成）：
  单块：周敦颐_W x H.png
  多块：周敦颐_W x H_r行_c列.png

用法：
  python3 stitch_tiles.py
"""

import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ 缺少 Pillow，请先安装：pip3 install pillow")
    sys.exit(1)

# ── 路径配置 ─────────────────────────────────────────────
EXPORT_DIR  = Path(__file__).parent / "export"   # 分块 PNG 所在目录
OUTPUT_DIR  = Path(__file__).parent / "export"   # 拼合结果保存目录
# ─────────────────────────────────────────────────────────

# 匹配：任意前缀_WxH.png  或  任意前缀_WxH_r行_c列.png
PATTERN = re.compile(
    r"^(.+?)_(\d+)x(\d+)(?:_r(\d+)_c(\d+))?\.png$",
    re.IGNORECASE,
)


def parse_tiles(export_dir: Path):
    """扫描目录，按 (前缀, W, H) 分组，返回分组字典。"""
    groups: dict[tuple, list] = {}

    for f in sorted(export_dir.glob("*.png")):
        m = PATTERN.match(f.name)
        if not m:
            print(f"  ⚠️  跳过（命名不匹配）：{f.name}")
            continue

        prefix = m.group(1)
        W      = int(m.group(2))
        H      = int(m.group(3))
        row    = int(m.group(4)) if m.group(4) else 1
        col    = int(m.group(5)) if m.group(5) else 1

        key = (prefix, W, H)
        groups.setdefault(key, []).append((row, col, f))

    return groups


def stitch(prefix: str, W: int, H: int, tiles: list, output_dir: Path):
    """将一组分块拼合为 W×H 的大图，保存到 output_dir。"""
    tiles_sorted = sorted(tiles, key=lambda t: (t[0], t[1]))

    # 单块且已是完整尺寸 → 直接另存
    if len(tiles_sorted) == 1:
        row, col, path = tiles_sorted[0]
        img = Image.open(path)
        if img.size == (W, H):
            out_name = f"{prefix}_{W}x{H}_merged.png"
            img.convert("RGBA").save(output_dir / out_name)
            img.close()
            print(f"  → 单块完整图，已另存为 {out_name}")
            return
        img.close()

    # 收集每行的高度、每列的宽度（从实际图片读取，无需假设 MAX_TILE）
    col_w: dict[int, int] = {}
    row_h: dict[int, int] = {}

    for row, col, path in tiles_sorted:
        with Image.open(path) as img:
            w, h = img.size
        col_w.setdefault(col, w)
        row_h.setdefault(row, h)

    # 计算各列的起始 x、各行的起始 y
    x_off: dict[int, int] = {}
    acc = 0
    for c in sorted(col_w):
        x_off[c] = acc
        acc += col_w[c]

    y_off: dict[int, int] = {}
    acc = 0
    for r in sorted(row_h):
        y_off[r] = acc
        acc += row_h[r]

    # 创建最终画布（RGBA 保留透明通道）
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 0))

    total = len(tiles_sorted)
    for i, (row, col, path) in enumerate(tiles_sorted, 1):
        px, py = x_off[col], y_off[row]
        print(f"  [{i:>3}/{total}] r{row},c{col}  →  ({px:>6}, {py:>6})", end="\r")
        with Image.open(path) as tile:
            canvas.paste(tile.convert("RGBA"), (px, py))

    print()  # 换行

    out_name = f"{prefix}_{W}x{H}_merged.png"
    out_path = output_dir / out_name
    print(f"  保存中… {out_path}")
    canvas.save(out_path, compress_level=6)
    canvas.close()
    print(f"  ✅ 完成：{out_name}  ({W} × {H} px)\n")


def main():
    print(f"扫描目录：{EXPORT_DIR}\n")

    if not EXPORT_DIR.exists():
        print(f"❌ 未找到 export 文件夹：{EXPORT_DIR}")
        sys.exit(1)

    groups = parse_tiles(EXPORT_DIR)

    if not groups:
        print("❌ export/ 中没有符合命名规则的 PNG 文件")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for (prefix, W, H), tiles in groups.items():
        # 跳过已拼合的结果文件（避免把上次的 _merged.png 再拼一遍）
        if any("_merged" in str(t[2]) for t in tiles):
            continue
        print(f"▶ {prefix}  {W} × {H} px  共 {len(tiles)} 块")
        stitch(prefix, W, H, tiles, OUTPUT_DIR)

    print("全部完成。")


if __name__ == "__main__":
    main()
