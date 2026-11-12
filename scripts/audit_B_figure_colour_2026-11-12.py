# -*- coding: utf-8 -*-
"""
B① 配图配色依据 · 只读审计脚本（2026-11-12）

触发：用户质询「此前生成的配图为何全部采用黑白配色；期刊风格归纳是否把
      '仅使用黑白图' 当作期刊特征；已发表论文中是否存在彩色插图」。

本脚本只做证据实测，不改任何稿件、图件、脚本或契约：
  组 1  TMIH 语料 46 张已发表论文导出位图的彩色像素实测（按张／按篇）
  组 2  重建图注中的期刊彩图在线声明
  组 3  本稿自生成 Figure1-3 的实际色域
  组 4  26 号梳理稿勘误后的关键表述与冲突仲裁留痕
  组 5  防火墙：订正未触碰任何图件／出图脚本／契约／图注

判据（可复核，非主观）：
  彩色像素 = RGB 三通道极差 > 25 且 max>45 且 min<240；
  为避免大图内存开销，先等比缩到最长边 400 px 再统计。
  「含彩图」= 彩色像素占比 > 2%；「纯灰阶」= < 0.5%。

输出：逐项 PASS/FAIL 与 VERDICT。
"""
from __future__ import annotations

import os
import re
import sys
import json
import glob
import collections
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
FIGS = ROOT / "TMIH写作DNA" / "figs"
CAPS = ROOT / "TMIH写作DNA" / "_meta" / "fig_captions.md"
OUT = MAIN / "配图_2026-11-12"
F26 = MAIN / "26_B①_TMIH配图偏好梳理_2026-11-12.md"
F29 = MAIN / "29_B①_TMIH配图配色依据核查与勘误_2026-11-12.md"

FAIL: list[str] = []
N = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global N
    N += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def coloured_fraction(path: Path) -> float:
    """返回彩色像素占比（%）。"""
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, 400 / max(w, h))
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        a = np.asarray(im).astype(int)
    sat = a.max(2) - a.min(2)
    mx, mn = a.max(2), a.min(2)
    return float(((sat > 25) & (mx > 45) & (mn < 240)).mean() * 100)


def group(title: str) -> None:
    print()
    print(f"=== {title} ===")


# ---------------------------------------------------------------- 组 1
group("1 · TMIH 已发表论文导出位图的彩色像素实测")
check("语料 figs/ 目录存在", FIGS.is_dir())
by_paper: dict[int, list[tuple[str, float]]] = collections.defaultdict(list)
flat: list[float] = []
for f in sorted(FIGS.iterdir()):
    m = re.match(r"^(\d{2})_f(\d+)\.(jpeg|jpg|png)$", f.name, flags=re.I)
    if not m:
        continue
    v = coloured_fraction(f)
    by_paper[int(m.group(1))].append((f.name, v))
    flat.append(v)

check("导出位图共 46 张", len(flat) == 46, f"实测 {len(flat)}")
coloured_figs = [v for v in flat if v > 2]
grey_figs = [v for v in flat if v < 0.5]
check("含彩图位图 ≥ 25 张", len(coloured_figs) >= 25, f"{len(coloured_figs)}/46 = {len(coloured_figs)/len(flat)*100:.1f}%")
check("纯灰阶位图 ≤ 15 张", len(grey_figs) <= 15, f"{len(grey_figs)}/46 = {len(grey_figs)/len(flat)*100:.1f}%")

coloured_papers = [k for k, v in by_paper.items() if any(x > 2 for _, x in v)]
grey_papers = [k for k, v in by_paper.items() if all(x < 0.5 for _, x in v)]
check("有导出位图的论文 18 篇", len(by_paper) == 18, f"实测 {len(by_paper)}")
check("至少一张彩图的论文 ≥ 12 篇", len(coloured_papers) >= 12,
      f"{len(coloured_papers)}/18 = {len(coloured_papers)/len(by_paper)*100:.1f}%；编号 {sorted(coloured_papers)}")
check("全灰阶论文 ≤ 6 篇", len(grey_papers) <= 6, f"编号 {sorted(grey_papers)}")

# 逐张具名物证：07 号视觉风格指南人工核验过的 6 张
named = {"02_f1.jpeg": 2.0, "18_f1.png": 10.0, "16_f1.png": 1.0,
         "09_f1.jpeg": 20.0, "23_f2.jpeg": 10.0, "13_f1.jpeg": 0.5}
for fn, lo in named.items():
    p = FIGS / fn
    v = coloured_fraction(p) if p.exists() else -1.0
    if fn == "13_f1.jpeg":
        check(f"{fn} 为白／灰双系列（彩像素 < 0.5%）", v < 0.5, f"{v:.2f}%")
    else:
        check(f"{fn} 含彩色（彩像素 > {lo:.0f}%）", v > lo, f"{v:.2f}%")

# ---------------------------------------------------------------- 组 2
group("2 · 期刊图注中的彩图在线声明")
tcap = read(CAPS)
hits = re.findall(r"\[Colour figure can be viewed at wileyonlinelibrary\.com\]", tcap, flags=re.I)
check("重建图注含期刊标准彩图在线声明", len(hits) >= 1, f"命中 {len(hits)} 处")

# ---------------------------------------------------------------- 组 3
group("3 · 本稿自生成 3 张主图的实际色域")
for n in (1, 2, 3):
    p = OUT / f"Figure{n}.png"
    v = coloured_fraction(p)
    with Image.open(p) as im:
        mode = im.mode
    check(f"Figure{n}.png 为 RGB 且零彩色像素", mode == "RGB" and v == 0.0,
          f"mode={mode}, 彩像素={v:.3f}%")
con = json.loads(read(OUT / "figure_contract.json"))
check("契约色板仍为 4 档中性灰（颜色方案未改）",
      con.get("greys") == ["#1A1A1A", "#4A4A4A", "#808080", "#B8B8B8"],
      str(con.get("greys")))

# ---------------------------------------------------------------- 组 4
group("4 · 26 号梳理稿勘误留痕")
t26 = read(F26)
check("26 号稿已附勘误指针", "29_B①_TMIH配图配色依据核查与勘误" in t26)
check("26 号稿明示『非期刊要求』", "非期刊要求" in t26)
check("26 号稿已订正 [18] 单色渐变绿误读", "单色渐变绿" in t26 and "single-hue" in t26)
check("G04 冲突仲裁已增至 9 条", len(re.findall(r"^\| \d \|", t26, flags=re.M)) >= 9,
      f"{len(re.findall(r'^[|] [0-9] [|]', t26, flags=re.M))} 条")
check("既有五类规格关键词未被破坏",
      all(k in t26 for k in ["图片数量区间", "清晰度与分辨率", "版式与标注规范", "配色与视觉风格", "一致性"]))
check("既有 NOT STATED 诚实口径未被破坏", "NOT STATED" in t26 and "不声称" in t26)
check("29 号核查件存在且结论明确", F29.exists() and "归纳偏差" in read(F29))

# ---------------------------------------------------------------- 组 5
group("5 · 订正边界：图件与出图链路未被触碰")
draw = read(ROOT / "数据" / "scripts" / "draw_B_figures_2026-11-12.py")
check("出图脚本仍为灰阶色板常量", "#1A1A1A" in draw and "#B8B8B8" in draw)
# 判据：脚本内所有 6 位 hex 常量的 R/G/B 必须相等（中性灰或白）。
# 出图脚本除 4 档契约灰外还合法使用 #FFFFFF（白）、#6B6B6B（中灰）、#D6D6D6（浅灰网格），
# 故不能判「零额外 hex」，只能判「零彩色 hex」。
_hexes = re.findall(r"#[0-9A-Fa-f]{6}\b", draw)
_neutral = [h for h in _hexes
            if len({h[1:3].lower(), h[3:5].lower(), h[5:7].lower()}) == 1]
check("出图脚本全部 hex 常量均为中性灰／白（零彩色常量）",
      len(_neutral) == len(_hexes),
      f"{len(_hexes)} 个 hex／{len(set(_hexes))} 种：{sorted(set(_hexes))}")
caps = read(OUT / "figure_captions.md")
check("图注未新增彩图在线声明（颜色方案未改）",
      "Colour figure can be viewed" not in caps)
check("三图 PNG/PDF/TIF 各 3 份仍在", all((OUT / f"Figure{n}.{e}").exists()
                                          for n in (1, 2, 3) for e in ("png", "pdf", "tif")))

# ---------------------------------------------------------------- 汇总
print()
print(f"--- 共 {N} 项检查，FAIL {len(FAIL)} 项 ---")
if FAIL:
    for x in FAIL:
        print("  FAIL:", x)
    print("VERDICT = FAIL")
    sys.exit(1)
print("VERDICT = ALL CLEAN")
