# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.0 定稿链只读终检，2026-11-12

覆盖：版本链冻结、降 AI 零数值改动、Vancouver 插号、C1–C8 图表引用与补材表号、
前页官网顺序、两份 docx 读回一致性、图件未改动、防火墙／禁词、旧核验脚本留痕复跑。

不写任何文件。运行：python verify_B_manuscript_v1_0_2026-11-12.py
"""
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from docx import Document
from PIL import Image

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = Path(ROOT) / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
SCRIPTS = Path(ROOT) / "数据" / "scripts"
PROCESSED = Path(ROOT) / "数据" / "processed"
OUTDIR = MAIN / "投稿包_2026-11-12"
FIGDIR = MAIN / "配图_2026-11-12"
HERE = Path(__file__).resolve()

F28 = MAIN / "28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md"
F27 = MAIN / "27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md"
F31 = MAIN / "31_B①主稿_降AI修订稿_v0.9_2026-11-12.md"
F32 = MAIN / "32_B①主稿_v1.0_定稿稿_2026-11-12.md"
F33 = MAIN / "33_B①主稿_降AI-Vancouver-docx定稿链装配说明_2026-11-12.md"
DOCX_MAN = OUTDIR / "B①_TMIH_主稿_v1.0_2026-11-12.docx"
DOCX_SUPP = OUTDIR / "B①_TMIH_补充材料_S1-S5_2026-11-12.docx"

NUM = re.compile(r"\d+(?:[.,]\d+)*")
FAILS, N = [], 0


def group(name):
    print(f"\n=== {name} ===")


def check(label, ok, detail=""):
    global N
    N += 1
    if not ok:
        FAILS.append(f"{label} :: {detail}")
    print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail and not ok else ""))


def part1(path):
    t = path.read_text(encoding="utf-8")
    a = re.search(r"^# PART I — Manuscript text\s*$", t, flags=re.M)
    assert a, f"PART I 标题缺失：{path.name}"
    b = re.search(r"^# PART II", t, flags=re.M)
    return t[a.end(): b.start() if b else len(t)].strip()


def nums(s):
    return Counter(NUM.findall(s))


def docx_text(path):
    d = Document(path)
    paras = "\n".join(p.text for p in d.paragraphs)
    tables = "\n".join(" | ".join(c.text for c in r.cells) for t in d.tables for r in t.rows)
    return d, paras + "\n" + tables


BANNED = [
    r"\bfirst (?:study|report|analysis|evidence|description|attempt|to\b)",
    r"\bfirst-ever\b", r"\bfor the first time\b",
    r"\bnovel\b", r"theoretical contribution", r"the present study",
    r"\bMoreover\b", r"\bFurthermore\b", r"near-complete mismatch",
    r"\bprove\b", r"\bconfirm\b", r"\bestablish\b", r"\bclearly\b", r"\bdefinitive\b",
    r"UN Comtrade", r"\bHS6?\b", r"\bUSD\b", r"10,324", r"U1/U2/U3", r"\b2\.137\b",
    r"4073\.8", r"4073\.76", r"1\.9489", r"1\.2241", r"1\.9344",
    r"joinpoint", r"causal identification was attempted",
    r"(?i)export value|trade volume|出口额",
    r"res_B2_", r"res_B_fig", r"res_B_hhi_", r"res_B_price_index", r"dualchain_",
]
CN_BAN = ["Phase", "工作包", "go-no-go", "背书", "延伸许铭", "综上所述", "值得注意的是"]

# ================================================================ 1
group("组 1 · 版本链与文件齐备")
for p in (F28, F27, F31, F32, F33, DOCX_MAN, DOCX_SUPP):
    check(f"存在 {p.name}", p.is_file(), str(p))
for n in ("polish_B_manuscript_2026-11-12.py", "finalize_B_v1_0_2026-11-12.py",
          "build_B_docx_2026-11-12.py"):
    check(f"脚本存在 {n}", (SCRIPTS / n).is_file())
p28, p31, p32 = part1(F28), part1(F31), part1(F32)
check("28 号 pre-assembly 稿冻结（正文零 [n]）", not re.search(r"\[\d+\]", p28))
check("31 号降 AI 稿正文零 [n]（插号不在降 AI 轮）", not re.search(r"\[\d+\]", p31))
check("28 号稿 mtime 早于 31／32", F28.stat().st_mtime < F31.stat().st_mtime
      and F28.stat().st_mtime < F32.stat().st_mtime)
check("32 号稿头部标注 v1.0 定稿", "v1.0 定稿稿" in F32.read_text(encoding="utf-8")[:400])

# ================================================================ 2
group("组 2 · 降 AI 零数值改动与改写台账")
# Word count 是前页元数据行，降 AI 后按实算值 3446/252 -> 3353/241 更新；
# 该行属登记值更新而非 prose 数字，须从「零数值改动」比对中剔除并单独断言。
def strip_wc(s):
    return re.sub(r"\*\*Word count:\*\*[^\n]*", "", s)
check("28→31 数值 token multiset 完全一致（剔除 Word count 元数据行）",
      nums(strip_wc(p28)) == nums(strip_wc(p31)),
      f"diff {nums(strip_wc(p28))-nums(strip_wc(p31))} / {nums(strip_wc(p31))-nums(strip_wc(p28))}")
check("Word count 行由 3446／252 更新为降 AI 后实算 3353／241",
      "3446 words" in p28 and "252 words" in p28
      and "3353 words" in p31 and "241 words" in p31)
t31 = F31.read_text(encoding="utf-8")
led = t31.split("# PART II", 1)[1] if "# PART II" in t31 else ""
check("31 号稿逐条改写台账 27 条", len(re.findall(r"^\| \d+ \| (?:Abstract|1 Introduction|2 Methods|3 Results|4 Discussion|5 Conclusions) \|", led, flags=re.M)) == 27,
      f"count={len(re.findall(r'^\\| \\d+ \\|', led, flags=re.M))}")
terms = ["product-holder-level quality signal", "Prequalification breadth",
         "registration, procurement, delivery and patient use", "Herfindahl–Hirschman Index",
         "Clopper–Pearson", "common country scale", "complements and expands",
         "consistent with", "in line with", "15 September 2026"]
check(f"降 AI 后关键术语 {len(terms)} 项零丢失", all(x in p31 for x in terms),
      str([x for x in terms if x not in p31]))
check("28→31 References 区块逐字未动",
      p28.split("## References", 1)[1].split("## Tables", 1)[0]
      == p31.split("## References", 1)[1].split("## Tables", 1)[0])
def tail_norm(s):
    # 31 号稿 PART I 与 PART II 台账之间留了 --- 分隔线，规范化后比对区块正文；
    # 去掉分隔线会残留一个换行，须再 strip 一次才能与 28 号稿逐字对齐
    return re.sub(r"\n-{3,}\s*$", "", s.split("## Tables", 1)[1].strip()).strip()
check("28→31 Tables/图注/补材索引区块逐字未动（规范化台账分隔线）",
      tail_norm(p28) == tail_norm(p31))
check("28→31 Declarations 区块逐字未动",
      p28.split("## Declarations", 1)[1].split("## References", 1)[0]
      == p31.split("## Declarations", 1)[1].split("## References", 1)[0])
check("31 号稿 Word count 实算 3353／241", "3353 words" in p31 and "241 words" in p31)

# ================================================================ 3
group("组 3 · v1.0 Vancouver 插号")
body32 = p32.split("## 1 Introduction", 1)[1].split("## Declarations", 1)[0]
groups32 = [[int(x) for x in g.split(",")] for g in re.findall(r"\[(\d+(?:,\d+)*)\]", p32)]
flat = [n for g in groups32 for n in g]
check("正文 Vancouver 编号组 7 组", len(groups32) == 7, str(groups32))
check("编号首次出现序列 1→13 连续无跳号", flat == list(range(1, 14)), str(flat))
check("编号均置于句末标点之前（ICMJE 写法）",
      all(f"{g}." in p32 for g in
          ["[1,2,3]", "[4,5]", "[6,7,8]", "[9,10]", "[11]", "[12]", "[13]"]))
# g 本身已含右方括号，写成 f"{g}." 才是 "[1,2,3]."；此前误写 f"{g}]." 属判据笔误
refs32 = p32.split("## References", 1)[1].split("---", 1)[0]
ref_nums = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. ", refs32, flags=re.M)]
check("References 编号 1–13 连续", ref_nums == list(range(1, 14)), str(ref_nums))
check("References 区块与 28 号稿逐字一致",
      refs32.strip() == p28.split("## References", 1)[1].split("---", 1)[0].strip())
abs32 = p32.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
concl32 = body32.split("## 5 Conclusions", 1)[1]
check("Abstract 零 Vancouver 编号／零图表引用",
      not re.search(r"\[\d+\]|Figure \d|Table \d", abs32))
check("Conclusions 零 Vancouver 编号／零图表引用",
      not re.search(r"\[\d+\]|Figure \d|Table \d", concl32))
mres = body32.split("## 2 Methods", 1)[1].split("## 4 Discussion", 1)[0]
check("Methods／Results 零 Vancouver 编号", not re.search(r"\[\d+\]", mres))

# ================================================================ 4
group("组 4 · C1–C8 图表引用与补材表号")
def first(s, tok):
    m = re.search(re.escape(tok), s)
    return m.start() if m else -1
figpos = [first(body32, f"Figure {i}") for i in (1, 2, 3)]
tabpos = [first(body32, f"Table {i}") for i in (1, 2, 3)]
check("Figure 1／2／3 正文各 ≥1 处", all(x >= 0 for x in figpos), str(figpos))
check("Table 1／2／3 正文各 ≥1 处", all(x >= 0 for x in tabpos), str(tabpos))
check("Figure 首次出现按序", figpos == sorted(figpos), str(figpos))
check("Table 首次出现按序", tabpos == sorted(tabpos), str(tabpos))
for sref in ("Table S1", "Table S2", "Notes S3", "Table S4", "Table S5"):
    check(f"正文含 {sref}", sref in body32)
check("正文（Introduction–Conclusions）零 supplementary material 泛指",
      "supplementary material" not in body32,
      f"count={body32.count('supplementary material')}")
dec32 = p32.split("## Declarations", 1)[1].split("## References", 1)[0]
check("Declarations 保留 1 处补材整体泛指", dec32.count("supplementary material") == 1,
      f"count={dec32.count('supplementary material')}")
caps32 = p32.split("## Figure captions", 1)[1].split("## Supplementary material", 1)[0]
check("Figure captions 图注保持逐字未动（含 1 处补材泛指）",
      caps32.strip() == p28.split("## Figure captions", 1)[1].split("## Supplementary material", 1)[0].strip())
check("32 号稿 PART II 装配台账 19 条操作",
      "装配操作共 19 条" in F32.read_text(encoding="utf-8")[:1200])
check("逆序还原逐字一致已在 finalize 脚本内断言",
      "逐字一致" in F32.read_text(encoding="utf-8")[:1200])

# ================================================================ 5
group("组 5 · 前页按 14 §三.8 官网顺序")
def order(s):
    return [s.find(x) for x in ("## Abstract", "**Keywords:**",
                                "**Conflict of interest and funding statement:**",
                                "**Word count:**")]
o = order(p32)
check("32 号 md 顺序 Abstract<Keywords<COI<WordCount", all(x >= 0 for x in o) and o == sorted(o), str(o))
check("≥5 位审稿人建议位于 Abstract 之前（其他脚注区）",
      0 <= p32.find("**Suggested potential reviewers") < o[0])
d_man, txt_man = docx_text(DOCX_MAN)
paras = [p.text for p in d_man.paragraphs if p.text.strip()]
def idx(prefix):
    return next((i for i, x in enumerate(paras) if x.startswith(prefix)), -1)
do = [idx("Abstract"), idx("Keywords:"), idx("Conflict of interest and funding statement:"),
      idx("Word count:")]
check("主稿 docx 前页顺序与官网一致", all(x >= 0 for x in do) and do == sorted(do), str(do))
check("主稿 docx 标题页字段齐备（Short/Authors/Affiliations/Corresponding/Submission/ORCID）",
      all(any(x.startswith(k) for x in paras) for k in
          ("Short title:", "Authors:", "Affiliations:", "Corresponding author:",
           "Submission-system contact:", "ORCID iDs:")))
check("主稿 docx 审稿人占位 ≥5 条",
      len([x for x in paras if re.match(r"^[1-5]\. \[TO BE COMPLETED", x)]) >= 5)
check("前页身份字段仍为占位符（按 16 §4.8 由作者填写，不代填）",
      p32.count("[TO BE COMPLETED BY THE AUTHORS") == 10,
      f"count={p32.count('[TO BE COMPLETED BY THE AUTHORS')}")

# ================================================================ 6
group("组 6 · docx 读回一致性")
check("主稿 docx 段落数 ≥100", len(paras) >= 100, str(len(paras)))
check("主稿 docx 真表格 4 张（Tables 1–3 + 补材索引）", len(d_man.tables) == 4, str(len(d_man.tables)))
check("主稿 docx 内嵌图 3 张", len(d_man.inline_shapes) == 3, str(len(d_man.inline_shapes)))
check("docx Vancouver 编号组与 32 号 md 一致",
      re.findall(r"\[\d+(?:,\d+)*\]", txt_man) == re.findall(r"\[\d+(?:,\d+)*\]", p32))
check("docx 数值 token multiset 与 32 号 md 一致", nums(txt_man) == nums(p32),
      f"diff {nums(p32)-nums(txt_man)} / {nums(txt_man)-nums(p32)}")
check("docx References 13 条",
      len([x for x in paras if re.match(r"^\d+\. ", x) and re.search(r"(?:doi:|\[in Chinese\]|New York|Geneva|20\d\d;)", x)]) >= 13,
      str(len([x for x in paras if re.match(r"^\d+\. ", x)])))
check("docx 中文文献 7 条",
      len([x for x in paras if re.match(r"^\d+\. ", x) and re.search(r"[\u4e00-\u9fff]", x)]) == 7)
check("docx Figure captions 3 条",
      len([x for x in paras if re.match(r"^Figure [123] ", x)]) == 3)
check("docx Table 1 首行数值 25 (2002–2026)",
      "25 (2002–2026)" in txt_man)
check("docx Word count 为降 AI 后实算值", "3353 words" in txt_man and "241 words" in txt_man)

d_sup, txt_sup = docx_text(DOCX_SUPP)
check("补材 docx 真表格 4 张（S1/S2/S4/S5）", len(d_sup.tables) == 4, str(len(d_sup.tables)))
for k in ("S1. AAPC sensitivity intervals", "S2. Alignment sensitivity estimates",
          "S3. Method notes", "Table S4.", "Table S5."):
    check(f"补材 docx 含 {k}", k in txt_sup)
check("补材 S5 为 29 国全表（表头 + 29 行）",
      any(len(t.rows) == 30 for t in d_sup.tables),
      str([len(t.rows) for t in d_sup.tables]))
check("补材 docx 关键敏感性数值回链", "13.22–16.30" in txt_sup and "1.6831–1.9775" in txt_sup)
check("补材 docx S3 防御句已在排版层对齐（零 joinpoint／零 no segmented）",
      "joinpoint" not in txt_sup.lower() and "no segmented" not in txt_sup.lower())
check("排版层对齐未回写 27 号冻结源稿（旧核验仍可复跑）",
      "joinpoint" in F27.read_text(encoding="utf-8").lower())
check("补材对齐零数值改动（S3 第 5 条仅删自证句）",
      "single-slope log-linear OLS model over 25 annual observations" in txt_sup
      and "The slope estimates the average annual change" in txt_sup)

# ================================================================ 7
group("组 7 · 防火墙、禁词与图件未改动")
for label, s in (("32 号 md", p32), ("主稿 docx", txt_man), ("补材 docx", txt_sup)):
    hits = [b for b in BANNED if re.search(b, s, flags=re.I)]
    check(f"{label} {len(BANNED)} 组禁词／作废值／隔离资产零命中", not hits, str(hits))
    cn = [w for w in CN_BAN if w in s]
    check(f"{label} 中文禁词零命中", not cn, str(cn))
first_ctx = [p32[max(0, m.start()-30):m.start()+40] for m in re.finditer(r"\bfirst\b", p32, flags=re.I)]
check("32 号稿 first 仅 3 处技术性用法",
      len(first_ctx) == 3 and all(("first-order autocorrelation" in c or "are listed first" in c) for c in first_ctx),
      str(first_ctx))
for n in (1, 2, 3):
    f = FIGDIR / f"Figure{n}.png"
    with Image.open(f) as im:
        check(f"Figure{n}.png 仍为 RGB 600dpi 4133×1771",
              im.mode == "RGB" and im.size == (4133, 1771)
              and abs(im.info.get("dpi", (0, 0))[0] - 600) < 1,
              f"mode={im.mode} size={im.size} dpi={im.info.get('dpi')}")
for n in ("res_B_uncertainty_apc_ci_2026-11-11.csv",
          "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv",
          "res_B_uncertainty_country_share_ci_2026-11-11.csv"):
    check(f"派生 CSV 仍存在 {n}", (PROCESSED / n).is_file())
check("33 号装配说明标注排版口径待 EM 核实", "NOT STATED" in F33.read_text(encoding="utf-8"))

# ================================================================ 8
group("组 8 · 旧核验脚本留痕复跑")
olds = sorted(p for p in SCRIPTS.glob("verify_B_manuscript_v0_[2-8]_*.py") if p.resolve() != HERE)
olds += sorted(SCRIPTS.glob("verify_B_figures_*.py"))
olds += sorted(SCRIPTS.glob("verify_B_figure_count_and_citations_*.py"))
olds += sorted(SCRIPTS.glob("audit_B_figure_colour_*.py"))
for p in olds:
    try:
        r = subprocess.run([sys.executable, str(p)], cwd=str(SCRIPTS),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=240)
        out = (r.stdout or "") + (r.stderr or "")
        ok = "ALL CLEAN" in out and r.returncode == 0
        check(f"复跑 {p.name}", ok, "" if ok else f"rc={r.returncode} :: {out[-200:].strip()}")
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
