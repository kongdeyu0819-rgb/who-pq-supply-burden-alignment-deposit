# -*- coding: utf-8 -*-
"""
B① 主稿 · 装配轮只读核验 v0.8（2026-11-12）

核验对象：
  27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md
  28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md
  assemble_B_manuscript_2026-11-12.py

纪律：只读；不修改任何稿件、CSV 或图件；旧核验脚本以留痕方式复跑。
运行：python verify_B_manuscript_v0_8_2026-11-12.py
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parent
PROJ = HERE.parents[2]
DATA = PROJ / "数据" / "processed"
cands = [Path(p) for p in glob.glob(str(PROJ / "WHO 预认证药品的供应*")) if Path(p).is_dir()]
MS = next(p for p in cands if (p / "16_B①主稿开场上下文包_2026-11-10.md").exists())
FIG = MS / "配图_2026-11-12"

F27 = MS / "27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md"
F28 = MS / "28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md"
ASSEMBLE = SCRIPTS / "assemble_B_manuscript_2026-11-12.py"

FAILS: list[str] = []
N = 0

def check(name: str, ok: bool, detail: str = "") -> None:
    global N
    N += 1
    if not ok:
        FAILS.append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  · {detail}" if detail else ""))

def group(title: str) -> None:
    print(f"\n【{title}】")

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def rows(name: str) -> list[dict]:
    with open(DATA / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

def f2(v: str) -> str:
    return f"{float(v):.2f}"

def ci(lo: str, hi: str) -> str:
    return f"{f2(lo)}–{f2(hi)}"

def part_between(t: str, start_pat: str, end_pat: str | None) -> str:
    """含起始行的片段切分：起始行本身也要参与检查（如 Word count 行、表注行）。"""
    a = re.search(start_pat, t, flags=re.M)
    if not a:
        return ""
    b = re.search(end_pat, t[a.start():], flags=re.M) if end_pat else None
    return t[a.start(): a.start() + b.start()] if b else t[a.start():]

def chapter_part1(fn: str) -> str:
    t = read(MS / fn)
    lines = t.split("# PART I", 1)[1].split("# PART II", 1)[0].strip().splitlines()
    if lines and lines[0].lstrip().startswith("—"):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    return "\n".join(l for l in body.splitlines() if not re.match(r"^#\s(?!#)", l)).strip()

# ================================================================ 载入
group("组 1 · 产物与 PART 锚点")
for f in (F27, F28, ASSEMBLE):
    check(f"产物存在：{f.name}", f.exists())

t27, t28 = read(F27), read(F28)
a27 = re.search(r"^# PART I — .*$", t27, flags=re.M)
b27 = re.search(r"^# PART II — .*$", t27, flags=re.M)
a28 = re.search(r"^# PART I — .*$", t28, flags=re.M)
check("27 号稿 PART I／PART II 双锚点", bool(a27 and b27))
check("28 号稿 PART I 单锚点", bool(a28))
p27 = t27[a27.end():b27.start()] if a27 and b27 else ""
p28 = t28[a28.end():] if a28 else ""
check("PART I 正文非空", len(p27) > 8000 and len(p28) > 18000,
      f"27={len(p27)} / 28={len(p28)} chars")
check("零 PART 标题后缀残留（— Manuscript text 独立行）",
      not [l for l in p28.splitlines() if l.strip().startswith("— Manuscript")])

# ================================================================ 结构
group("组 2 · 完整稿章节顺序与部件齐全")
heads = ["## Abstract", "## 1 Introduction", "## 2 Methods", "## 3 Results",
         "## 4 Discussion", "## 5 Conclusions", "## Declarations", "## References",
         "## Tables", "## Figure captions", "## Supplementary material"]
pos = [p28.find(h) for h in heads]
check("11 个部件全部存在", all(x >= 0 for x in pos), str([h for h, x in zip(heads, pos) if x < 0]))
check("部件顺序符合 14 §三.8 + IMRD", pos == sorted(pos))
for h in ("### 2.1", "### 2.7", "### 3.1", "### 3.5", "### 4.1", "### 4.5"):
    check(f"子节存在 {h}", h in p28)

group("组 3 · prose 逐字来自各章 PART I（未重写、未润色）")
CH = {
    "Abstract": "24_B①主稿_Abstract_英文初稿_v0.1_2026-11-12.md",
    "Introduction": "22_B①主稿_Introduction_英文初稿_v0.1_2026-11-11.md",
    "Methods-Results": "20_B①主稿_Methods-Results_英文修订稿_v0.2_2026-11-11.md",
    "Discussion": "21_B①主稿_Discussion_英文初稿_v0.1_2026-11-11.md",
    "Conclusions": "23_B①主稿_Conclusions_英文初稿_v0.1_2026-11-11.md",
    "Declarations-References": "25_B①主稿_Declarations-References_英文成稿_v0.1_2026-11-12.md",
}
for label, fn in CH.items():
    block = chapter_part1(fn)
    check(f"{label} 文本块逐字一致", block in p28, f"{len(block)} chars")

# ================================================================ 词数 / 引文
group("组 4 · 词数、零 [n]、References 定表")
plan = read(MS / "17_B①主稿撰写计划_2026-11-11.md")
m = re.search(r"Abstract\s*(\d+)\s*词＋IMRD 五章\s*([\d,]+)\s*词", plan)
wa, wi = (int(m.group(1)), int(m.group(2).replace(",", ""))) if m else (0, 0)
wc = part_between(p28, r"^\*\*Word count:\*\*.*$", r"^\*\*Suggested potential reviewers")
check("Word Count 字段含 17 号计划登记值", str(wi) in wc and str(wa) in wc, f"{wi}/{wa}")
check("PART I 零 [n] 物理插号", not re.findall(r"\[\d+\]", p28),
      str(re.findall(r"\[\d+\]", p28)[:5]))
refs = part_between(p28, r"^## References\s*$", r"^## Tables\s*$")
nums = [int(x) for x in re.findall(r"^(\d+)\. ", refs, flags=re.M)]
check("References 13 条、编号 1–13 连续", nums == list(range(1, 14)), str(nums))
check("中文条目 7 条均标 [in Chinese]", refs.count("[in Chinese]") == 7,
      f"count={refs.count('[in Chinese]')}")
prose_no_refs = p28.replace(refs, "")
decls = part_between(p28, r"^## Declarations\s*$", r"^## References\s*$")
check("正文 prose 零 doi: 卷期页码", "doi:" not in prose_no_refs.replace(decls, ""))
check("Declarations 六项齐备", all(k in decls for k in (
    "Ethics approval", "Consent for publication", "Availability of data",
    "Competing interests", "Funding", "Authors' contributions")))

# ================================================================ 表值回链
group("组 5 · Tables 1–3 逐值回链权威 CSV")
tbl = part_between(p28, r"^## Tables\s*$", r"^## Figure captions\s*$")
Y = rows("res_B_anchor_year_counts.csv")
SHARE = rows("res_B_uncertainty_country_share_ci_2026-11-11.csv")
CONC = rows("res_B_uncertainty_concentration_ci_2026-11-11.csv")
CHINA = rows("res_B_uncertainty_china_breadth_ci_2026-11-11.csv")
AREA = rows("res_B_uncertainty_supply_by_area_2026-11-11.csv")
MIS = rows("res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv")
APCI = rows("res_B_uncertainty_apc_ci_2026-11-11.csv")

check("Table 1 观测窗与年数", f"{len(Y)} ({Y[0]['year']}–{Y[-1]['year']})" in tbl)
check("Table 1 集中度分母 648／国数 29",
      str(sum(int(r["product_rows"]) for r in SHARE)) in tbl and str(len(SHARE)) in tbl)
for d in ("Malaria", "HIV/AIDS", "Tuberculosis"):
    r = next(x for x in AREA if x["disease"] == d)
    check(f"Table 1 {d} 分母／持证商国数",
          f"{r['area_denominator']} / {r['n_holder_countries']}" in tbl)
    r2 = next(x for x in MIS if x["disease"] == d and x["calibre"] == "latest_burden_year")
    check(f"Table 1 {d} 对齐分析国数",
          f"{r2['n_countries']} ({r2['n_burden_countries']})" in tbl)
for r in CONC[:4]:
    check(f"Table 2 {r['metric']} 点估计与区间",
          f2(r["point"]) in tbl and ci(r["ci95_lo"], r["ci95_hi"]) in tbl)
check("Table 2 bootstrap 次数 10,000", "10,000" in tbl)
for r in CHINA:
    check(f"Table 3 {r['therapeutic_area']} k/n、份额、CP 区间",
          all(s in tbl for s in (
              f"{r['china_products_k']} / {r['global_fpp_n']}", f2(r["share_pct"]),
              ci(r["ci95_lo_clopper_pearson"], r["ci95_hi_clopper_pearson"]))))
check("三个表题均为投稿体例 Table 1–3",
      all(f"**Table {i}.**" in tbl for i in (1, 2, 3)))
check("作废 HHI 4073.76／4073.8 零出现", "4073.76" not in tbl and "4073.8" not in tbl)

# ================================================================ 图—表去重
group("组 6 · 图—表去重（14 §三.6 / 26 §五 既定判据）")
manifest = json.loads(read(FIG / "manifest.json"))
canvas = [t for f in manifest["figures"].values() for t in f.get("texts_drawn_on_canvas", [])]
decimals = [t for t in canvas if re.search(r"\d+\.\d+", t)]
check("图内零精确数值文本标签（含小数估计值）", not decimals, str(decimals[:5]))
data_lines = [l for l in tbl.splitlines() if l.startswith("| ")]
aapc_vals = [r["aapc_recomputed_pct"] for r in APCI]
check("Tables 数据行零 AAPC 四点估计（Figure 1(B) 承载）",
      not [l for l in data_lines if any(v in l for v in aapc_vals)])
check("Tables 数据行零逐年累积数（Figure 1(A) 承载）",
      not [l for l in data_lines if re.search(r"\|\s*20\d\d\s*\|", l)])
iso2 = {r["iso3"] for r in SHARE}
check("Tables 数据行零逐国份额（Figure 2(A) 承载）",
      not [l for l in data_lines if any(f"| {c} |" in l for c in iso2)])
for i in (1, 2, 3):
    note = part_between(tbl, rf"^\*\*Table {i}\.\*\*.*$", r"^\| Step|^\| Metric|^\| Therapeutic")
    k = len(re.findall(r"Figure \d", note))
    check(f"Table {i} 表注交叉引用句 ≤2 处", k <= 2, f"count={k}")
check("图—表去重五条裁决 G01–G05 已留痕于 27 号核对件",
      all(f"G0{i}" in t27 for i in range(1, 6)))

# ================================================================ 图注与补材
group("组 7 · 图注逐字一致与补材承诺兑现")
caps_file = [l.strip() for l in read(FIG / "figure_captions.md").splitlines()
             if l.strip().startswith("Figure ")]
cap_block = part_between(p28, r"^## Figure captions\s*$", r"^## Supplementary material\s*$")
check("28 号稿 3 条图注逐字等于 figure_captions.md",
      [l.strip() for l in cap_block.splitlines() if l.strip().startswith("Figure ")] == caps_file)
check("Figure 2 图注承诺「其余 19 国见补材」",
      "remaining 19 holder countries are tabulated in the supplementary material" in cap_block)
for s in ("### S1.", "### S2.", "### S3.", "Table S4.", "Table S5."):
    check(f"27 号稿补材含 {s}", s in p27)
check("补材 S1–S3 从属于 ## Supplementary material（层级正确）",
      p27.count("## Supplementary material\n") == 1
      and not re.search(r"^## S\d\.", p27, flags=re.M))
s5 = part_between(p27, r"^Table S5\.", r"^## Supplementary material index")
check("Table S5 覆盖全部 29 个持证商国",
      all(f"| {r['iso3']} | " in s5 for r in SHARE), f"rows={len(SHARE)}")
check("Figure 2 图注承诺已由 29 行 S5 兑现（10 图 + 19 表）", len(SHARE) == 29)
for s in ("Table S1", "Table S2", "Notes S3", "Table S4", "Table S5"):
    check(f"28 号稿补材索引含 {s}", s in p28)
check("Table 3 表注承诺的 Wilson 对照在 S4", "Wilson 95% CI" in p27)

# ================================================================ 前页
group("组 8 · 前页字段与作者占位裁定")
front = p28[:p28.find("## Abstract")]
order = ["**Short title:**", "**Authors:**", "**Affiliations:**",
         "**Corresponding author:**", "**Conflict of interest", "**Word count:**",
         "**Suggested potential reviewers"]
fp = [front.find(k) for k in order]
check("前页七项字段齐备", all(x >= 0 for x in fp))
check("字段顺序符合 14 §三.8（Keywords 单列于 Abstract 之后）",
      fp[0] < fp[1] < fp[2] < fp[3] < fp[4] < fp[5] < fp[6])
placeholders = front.count("[TO BE COMPLETED BY THE AUTHORS")
check("作者身份／第三方姓名占位符恰好 10 处", placeholders == 10, f"count={placeholders}")
check("≥5 位审稿人建议占位 5 行",
      len(re.findall(r"^\d\. \[TO BE COMPLETED BY THE AUTHORS", front, flags=re.M)) == 5)
check("主推标题含 malaria 与 low- and middle-income countries",
      "malaria" in front[:400] and "low- and middle-income countries" in front[:400])
check("主推标题不写 access（避免过度声称）",
      "access" not in front[:400].lower())
check("Short title／Keywords 存在", "**Short title:**" in front and "**Keywords:**" in p28)
check("COI／Funding 逐字取自 25 号 Declarations",
      "The authors declare that they have no competing interests." in front
      and "required no dedicated data-collection funding." in front)
check("通讯作者与投稿系统联系邮箱分列两行（双轨）",
      "**Corresponding author:**" in front and "**Submission-system contact:**" in front)

# ================================================================ 防火墙
group("组 9 · 防火墙与取数白名单")
BAD = ["4073.8", "4073.76", "1.9489", "1.2241", "1.9344", "10,324",
       "Comtrade", "出口额", "HS6", "res_B2_", "dualchain_", "lineitems_clean",
       "U1/U2/U3", "_archive_v1/"]
for label, txt in (("28 号稿 PART I", p28), ("27 号稿 PART I", p27)):
    hits = [w for w in BAD if w in txt]
    check(f"{label} 零隔离资产／作废值命中", not hits, str(hits))
src = read(ASSEMBLE)
csv_names = re.findall(r'"(res_B_[^"]+\.csv)"', src)
check("装配脚本 CSV 白名单恰 8 份", len(csv_names) == 8, str(len(csv_names)))
check("白名单全部为 anchor／uncertainty 前缀、零隔离前缀",
      all(n.startswith(("res_B_anchor_", "res_B_uncertainty_")) for n in csv_names)
      and not any(n.startswith(("res_B2_", "dualchain_", "res_B_fig", "res_B_hhi_")) for n in csv_names))
check("五份 anchor 底座未被本轮改写（脚本零写入 processed）",
      not re.search(r"DATA\s*/[^\n]*\.write_text|to_csv\(", src))

# ================================================================ 旧脚本留痕复跑
group("组 10 · 主稿核验链旧脚本留痕复跑")
# 边界：只复跑主稿核验链 v0.2–v0.7 与配图核验；数据层／B② 伴生核验脚本不属本轮装配链。
olds = sorted(p for p in SCRIPTS.glob("verify_B_manuscript_v0_[2-7]_*.py"))
olds += sorted(p for p in SCRIPTS.glob("verify_B_figures_*.py"))
for p in olds:
    try:
        r = subprocess.run([sys.executable, str(p)], cwd=str(SCRIPTS),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        out = (r.stdout or "") + (r.stderr or "")
        ok = "ALL CLEAN" in out and r.returncode == 0
        check(f"复跑 {p.name}", ok, "" if ok else f"rc={r.returncode} :: {out[-220:].strip()}")
    except Exception as e:                                   # noqa: BLE001
        check(f"复跑 {p.name}", False, f"{type(e).__name__}: {e}")

# ================================================================ 结论
print("\n" + "=" * 72)
print(f"CHECKS = {N}  |  FAIL = {len(FAILS)}")
print("VERDICT =", "ALL CLEAN" if not FAILS else "FAIL")
if FAILS:
    for f in FAILS:
        print("  -", f)
print("=" * 72)
sys.exit(0 if not FAILS else 1)
