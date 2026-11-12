# -*- coding: utf-8 -*-
"""
B① 三张主图数量充分性与图表引用契约 · 只读核验（2026-11-12）

触发：用户问「三张图够吗？」。本脚本不改任何文件，只核对：
  组 1  语料数量惯例（18 篇 / 46 张 / 中位 2 / 78% ≤3 张）
  组 2  28 号稿的图表部件齐备与 5 个 Results 小节覆盖
  组 3  30 号契约 C1–C8 覆盖全部 3 图 3 表与补材表
  组 4  装配缺口 D1/D2 如实留痕（INFO，不判 FAIL）
  组 5  边界：未新增图、未改出图链路、未改数值

注意：正文当前「零图表交叉引用」是**已登记待装配轮修复**的缺口，
      本脚本以 INFO 输出以便追溯，不作为 FAIL；FAIL 只留给「缺口未登记」。
"""
from __future__ import annotations

import os
import re
import sys
import json
import statistics
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
FIGS = ROOT / "TMIH写作DNA" / "figs"
OUT = MAIN / "配图_2026-11-12"
F28 = MAIN / "28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md"
F30 = MAIN / "30_B①主稿_配图数量充分性与图表引用契约_2026-11-12.md"

FAIL: list[str] = []
N = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global N
    N += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


def info(label: str, detail: str) -> None:
    print(f"  [INFO] {label}  {detail}")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def group(title: str) -> None:
    print()
    print(f"=== {title} ===")


# ---------------------------------------------------------------- 组 1
group("1 · 语料数量惯例（可复跑实算）")
by_paper: dict[int, int] = collections.defaultdict(int)
n_figs = 0
for f in FIGS.iterdir():
    m = re.match(r"^(\d{2})_f(\d+)\.(jpeg|jpg|png)$", f.name, flags=re.I)
    if m:
        by_paper[int(m.group(1))] += 1
        n_figs += 1
counts = sorted(by_paper.values())
check("导出位图 46 张", n_figs == 46, str(n_figs))
check("有导出位图论文 18 篇", len(counts) == 18, str(len(counts)))
check("每篇 1–6 张", min(counts) == 1 and max(counts) == 6, f"{min(counts)}–{max(counts)}")
check("中位数 2 张", statistics.median(counts) == 2, str(statistics.median(counts)))
le3 = sum(1 for c in counts if c <= 3)
check("≤3 张的论文 14/18（78%）", le3 == 14, f"{le3}/18 = {le3/18*100:.1f}%")
check("本稿 3 张落在主流区间且高于中位", 3 <= max(counts) and 3 > statistics.median(counts))

# ---------------------------------------------------------------- 组 2
group("2 · 28 号稿图表部件与 Results 覆盖")
t28 = read(F28)
p1 = t28.split("# PART I", 1)[1]
cap_block = p1.split("## Figure captions", 1)[1].split("## Supplementary material", 1)[0]
captions = [l for l in cap_block.splitlines() if l.strip().startswith("Figure ")]
check("恰好 3 条图注", len(captions) == 3, str(len(captions)))
check("图注编号 Figure 1/2/3 按序",
      [re.match(r"Figure (\d)", c).group(1) for c in captions] == ["1", "2", "3"])
tbl_block = p1.split("## Tables", 1)[1].split("## Figure captions", 1)[0]
check("恰好 3 个投稿体例表题",
      all(f"**Table {i}.**" in tbl_block for i in (1, 2, 3)))
check("3 图 × 2 面板共 6 个子图（(A)(B) 各 3 次）",
      sum(len(re.findall(r"\([AB]\)", c)) for c in captions) == 6)
sections = re.findall(r"^### 3\.\d .*$", p1, flags=re.M)
check("Results 3.1–3.5 五小节齐备", len(sections) == 5, str(len(sections)))
check("5 小节均有载体（契约矩阵登记 3.1–3.5）",
      all(f"3.{i}" in read(F30) for i in range(1, 6)))
check("补材索引 S1–S5 齐备",
      all(s in p1 for s in ("Table S1", "Table S2", "Notes S3", "Table S4", "Table S5")))

# ---------------------------------------------------------------- 组 3
group("3 · 30 号图表引用契约 C1–C8")
t30 = read(F30)
for c in range(1, 9):
    check(f"契约 C{c} 已登记", re.search(rf"\| C{c} \|", t30) is not None)
for k in ("Figure 1", "Figure 2", "Figure 3", "Table 1", "Table 2", "Table 3",
          "Table S1", "Table S2", "Table S4", "Table S5"):
    check(f"契约覆盖 {k}", k in t30)
check("契约明确『首次出现须按序』", "首次出现须按序" in t30)
check("契约明确物理插入留降 AI 后 docx 装配轮",
      "降 AI 之后" in t30 and "docx 装配轮" in t30)
check("契约明确不进摘要与 Conclusions", "不进摘要" in t30 and "Conclusions" in t30)

# ---------------------------------------------------------------- 组 4
group("4 · 装配缺口 D1/D2 如实留痕（INFO，不判 FAIL）")
body = p1.split("## 1 Introduction", 1)[1].split("## Tables", 1)[0]
fig_hits = {i: len(re.findall(rf"Figure {i}", body)) for i in (1, 2, 3)}
tab_hits = {i: len(re.findall(rf"Table {i}\b", body)) for i in (1, 2, 3)}
info("D1 正文 Figure 1/2/3 引用", str(fig_hits))
info("D1 正文 Table 1/2/3 引用", str(tab_hits))
supp = len(re.findall("supplementary material", body))
s_hits = {k: len(re.findall(re.escape(k), body)) for k in
          ("Table S1", "Table S2", "Table S4", "Table S5", "Notes S3")}
info("D2 正文补材泛指／具体表号", f"泛指 {supp} 处；具体表号 {s_hits}")
check("D1 已在 30 号件登记为待装配轮修复", "正文零图表交叉引用" in t30 and "D1" in t30)
check("D2 已在 30 号件登记为待装配轮修复", "补材只泛指、无具体表号" in t30 and "D2" in t30)
check("D3 过时标注已登记为『被 G01–G05 取代』", "已被 `27` G01–G05 取代" in t30)
check("未把零引用误判为已完成（诚实留痕）",
      "会被退修" in t30 and "核验盲区" in t30)

# ---------------------------------------------------------------- 组 5
group("5 · 边界：图件与出图链路未被触碰")
check("主图仍恰好 3 张 PNG",
      len([f for f in OUT.glob("Figure*.png") if re.fullmatch(r"Figure\d+\.png", f.name)]) == 3)
con = json.loads(read(OUT / "figure_contract.json"))
check("契约尺寸／dpi／灰阶未变",
      con.get("width_mm") == 175.0 and con.get("dpi_png") == 600 and
      len(con.get("greys", [])) == 4)
check("29 号配色勘误结论未被推翻（颜色方案不调整）", "颜色方案不调整" in t30 or "不改颜色方案" in t30)
check("30 号件明示不新增图、不改 prose 与数值",
      "不新增图" in t30 and "不改 prose" in t30 and "不改任何数值" in t30)
for k in ("4073.8", "1.9489", "10,324", "res_B2_", "dualchain_"):
    check(f"30 号件零隔离资产残留：{k}", k not in t30)

# ---------------------------------------------------------------- 汇总
print()
print(f"--- 共 {N} 项检查，FAIL {len(FAIL)} 项 ---")
if FAIL:
    for x in FAIL:
        print("  FAIL:", x)
    print("VERDICT = FAIL")
    sys.exit(1)
print("VERDICT = ALL CLEAN")
