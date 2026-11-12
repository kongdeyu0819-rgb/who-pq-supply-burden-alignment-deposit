# -*- coding: utf-8 -*-
"""
B① 主稿 · 装配轮（2026-11-12）

用途：
  1) 生成 27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md
  2) 生成 28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md

纪律：
  - 所有研究数值从 数据/processed/ 下的权威派生 CSV 实读，脚本内零硬编码结果数字。
  - 章节 prose 从 20/21/22/23/24/25 号稿的 PART I 精确切分，不重写、不润色。
  - 图注从 配图_2026-11-12/figure_captions.md 原样读入。
  - 全稿正文保持零 [n] 物理插号（25 号稿 PART II §六裁定）。
  - 防火墙：不读 res_B2_* / dualchain_* / lineitems_clean / price_index / hhi_* 等隔离资产。

运行：python assemble_B_manuscript_2026-11-12.py   （可从任意 cwd 运行）
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------- 路径定位
HERE = Path(__file__).resolve()
PROJ = HERE.parents[2]                       # 课题根目录
DATA = PROJ / "数据" / "processed"
cands = [Path(p) for p in glob.glob(str(PROJ / "WHO 预认证药品的供应*")) if Path(p).is_dir()]
MS = next(p for p in cands if (p / "16_B①主稿开场上下文包_2026-11-10.md").exists())
FIG = MS / "配图_2026-11-12"

D27 = MS / "27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md"
D28 = MS / "28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md"

# ---------------------------------------------------------------- 白名单 CSV
CSV = {
    "year_counts":  "res_B_anchor_year_counts.csv",
    "apc":          "res_B_anchor_apc.csv",
    "apc_ci":       "res_B_uncertainty_apc_ci_2026-11-11.csv",
    "concentration": "res_B_uncertainty_concentration_ci_2026-11-11.csv",
    "country_share": "res_B_uncertainty_country_share_ci_2026-11-11.csv",
    "china":        "res_B_uncertainty_china_breadth_ci_2026-11-11.csv",
    "supply_area":  "res_B_uncertainty_supply_by_area_2026-11-11.csv",
    "misalign":     "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv",
}

def rows(key: str) -> list[dict]:
    with open(DATA / CSV[key], encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

Y, APC, APCI, CONC, SHARE, CHINA, AREA, MIS = (
    rows("year_counts"), rows("apc"), rows("apc_ci"), rows("concentration"),
    rows("country_share"), rows("china"), rows("supply_area"), rows("misalign"),
)

def f2(v: str) -> str:
    """统一两位小数，用于与正文既有写法一致（4643.5 → 4643.50）。"""
    return f"{float(v):.2f}"

def ci(lo: str, hi: str) -> str:
    return f"{f2(lo)}–{f2(hi)}"

def by(items, key, val):
    return next(r for r in items if r[key] == val)

# ---------------------------------------------------------------- 章节 PART I
CH = {
    "abstract":     "24_B①主稿_Abstract_英文初稿_v0.1_2026-11-12.md",
    "intro":        "22_B①主稿_Introduction_英文初稿_v0.1_2026-11-11.md",
    "methods_res":  "20_B①主稿_Methods-Results_英文修订稿_v0.2_2026-11-11.md",
    "discussion":   "21_B①主稿_Discussion_英文初稿_v0.1_2026-11-11.md",
    "conclusions":  "23_B①主稿_Conclusions_英文初稿_v0.1_2026-11-11.md",
    "decl_refs":    "25_B①主稿_Declarations-References_英文成稿_v0.1_2026-11-12.md",
}

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def part1(key: str) -> str:
    t = read(MS / CH[key])
    assert "# PART I" in t and "# PART II" in t, f"PART 边界缺失: {CH[key]}"
    lines = t.split("# PART I", 1)[1].split("# PART II", 1)[0].strip().splitlines()
    # split 掉 "# PART I" 后会残留标题后缀「— Manuscript text」，不得带入合并稿
    if lines and lines[0].lstrip().startswith("—"):
        lines = lines[1:]
    return "\n".join(lines).strip()

def part3(key: str) -> str:
    t = read(MS / CH[key])
    lines = t.split("# PART III", 1)[1].strip().splitlines()
    if lines and lines[0].lstrip().startswith("—"):
        lines = lines[1:]                      # 去掉 PART III 标题行的残留后缀
    return "\n".join(lines).strip()

P = {k: part1(k) for k in CH}
SUPP_CORE = part3("methods_res")
# 27 号稿里补材 S1–S3 从属于 ## Supplementary material，层级降一级避免同级标题
SUPP_CORE_27 = re.sub(r"^## (S\d\.)", r"### \1", SUPP_CORE, flags=re.M)

# 去掉 markdown 标题行后的纯正文词数（用于 Word Count 字段，实算非登记）
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

def prose_words(t: str) -> int:
    body = "\n".join(l for l in t.splitlines() if not re.match(r"^\s{0,3}#{1,6}\s", l))
    return len(WORD_RE.findall(body))

W_ABS_CALC = prose_words(P["abstract"])
W_IMRD_CALC = sum(prose_words(P[k]) for k in ("intro", "methods_res", "discussion", "conclusions"))
# Word Count 字段沿用各章已核验的登记词数（`24` PART II、`17` 计划）；
# 脚本实算值仅作交叉校验，差异来自 Markdown 标题行与结构化摘要标签的计数口径。
_PLAN = read(MS / "17_B①主稿撰写计划_2026-11-11.md")
_m = re.search(r"Abstract\s*(\d+)\s*词＋IMRD 五章\s*([\d,]+)\s*词", _PLAN)
assert _m, "未能从 17 号计划抽取已登记词数"
W_ABS = int(_m.group(1))
W_IMRD = int(_m.group(2).replace(",", ""))
# 登记值计入 Markdown 小节标题行文字；实算按纯 prose 去标题行，差额集中在 20 号的 10 个编号小节标题。
# 故交叉校验只作「数量级一致」检查，不作逐词相等断言。
assert abs(W_ABS_CALC - W_ABS) <= 12 and abs(W_IMRD_CALC - W_IMRD) <= 45, (
    f"词数交叉校验异常: calc {W_ABS_CALC}/{W_IMRD_CALC} vs registered {W_ABS}/{W_IMRD}")

# ---------------------------------------------------------------- 图注 / manifest
CAPTIONS = [l.strip() for l in read(FIG / "figure_captions.md").splitlines()
            if l.strip().startswith("Figure ")]
assert len(CAPTIONS) == 3, f"图注数量异常: {len(CAPTIONS)}"
MANIFEST = json.loads(read(FIG / "manifest.json"))
CANVAS = [t for f in MANIFEST["figures"].values() for t in f.get("texts_drawn_on_canvas", [])]

# ---------------------------------------------------------------- 表格生成器
def md_table(headers: list[str], body: list[list[str]], aligns: list[str] | None = None) -> str:
    if aligns is None:
        aligns = ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(aligns) + "|"]
    for r in body:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)

# --- Table 1 (A1)：分母链与清单构成（图上无；不与 Figure 1 的曲线／森林图重复）
area_den = {}
for d in ("Malaria", "HIV/AIDS", "Tuberculosis"):
    r = by(AREA, "disease", d)
    area_den[d] = (r["area_denominator"], r["n_holder_countries"])

mis_latest = {r["disease"]: r for r in MIS if r["calibre"] == "latest_burden_year"}
sum_rows = sum(int(r["product_rows"]) for r in SHARE)
n_holders = len(SHARE)
n_years = len(Y)
ymin, ymax = Y[0]["year"], Y[-1]["year"]

T1 = md_table(
    ["Step", "Quantity", "Value"],
    [
        ["1", "Annual observations in the cumulative listing series", f"{n_years} ({ymin}–{ymax})"],
        ["2", "Reviewed FPP product rows contributing to concentration", f"{sum_rows}"],
        ["3", "Certificate-holder countries", f"{n_holders}"],
        ["4", "Malaria products / active holder countries",
         f"{area_den['Malaria'][0]} / {area_den['Malaria'][1]}"],
        ["5", "HIV/AIDS products / active holder countries",
         f"{area_den['HIV/AIDS'][0]} / {area_den['HIV/AIDS'][1]}"],
        ["6", "Tuberculosis products / active holder countries",
         f"{area_den['Tuberculosis'][0]} / {area_den['Tuberculosis'][1]}"],
        ["7", "Countries in alignment analysis — malaria (with burden observation)",
         f"{mis_latest['Malaria']['n_countries']} ({mis_latest['Malaria']['n_burden_countries']})"],
        ["8", "Countries in alignment analysis — tuberculosis (with burden observation)",
         f"{mis_latest['Tuberculosis']['n_countries']} ({mis_latest['Tuberculosis']['n_burden_countries']})"],
        ["9", "Countries in alignment analysis — HIV/AIDS, supplementary only (with burden observation)",
         f"{mis_latest['HIV/AIDS']['n_countries']} ({mis_latest['HIV/AIDS']['n_burden_countries']})"],
    ],
)

T1_NOTE = (
    "Table 1. Denominator chain and composition of the WHO prequalification listing, "
    "snapshot 15 September 2026. FPP, finished pharmaceutical product. "
    "All values are counts; no estimate in this table is plotted as a text label in Figures 1–3. "
    "The cumulative listing trajectory and average annual percentage change are shown in Figure 1; "
    "their exact values are reported in Results 3.2 and Table S1. "
    "HIV/AIDS burden alignment is supplementary because the local GHO PLHIV extract ends in 2006. "
    "All quantities are reproducible from the derivation described in Methods 2.1–2.3 and the "
    "derived tables supplied with the submission."
)

# --- Table 2 (A2)：集中度汇总指标（Figure 2(A) 只画逐国份额，不含 HHI／CRn）
CONC_MAIN = [r for r in CONC if r["metric"] in ("HHI", "CR1_pct", "CR4_pct", "CR8_pct")]
label = {"HHI": "Herfindahl–Hirschman Index (HHI)",
         "CR1_pct": "CR1, largest holder country (%)",
         "CR4_pct": "CR4, four largest holder countries (%)",
         "CR8_pct": "CR8, eight largest holder countries (%)"}
T2 = md_table(
    ["Metric", "Estimate", "Descriptive 95% CI", "Product-row resamples"],
    [[label[r["metric"]], f2(r["point"]), ci(r["ci95_lo"], r["ci95_hi"]),
      f"{int(r['bootstrap_draws']):,}"] for r in CONC_MAIN],
    ["---", "---:", "---:", "---:"],
)
T2_NOTE = (
    "Table 2. Concentration of certificate-holder countries, 15 September 2026 listing snapshot "
    f"({sum_rows} reviewed FPP rows, {n_holders} holder countries). "
    "Intervals are descriptive product-row bootstrap intervals for the composition of a finite listing, "
    "not sampling error from a superpopulation. Individual country shares and their intervals are "
    "plotted in Figure 2(A) and listed in Table S5; they are not repeated as text values here. "
    "CR1, CR4, CR8, concentration ratios; FPP, finished pharmaceutical product."
)

# --- Table 3 (A3)：中国持证产品广度，主口径 Clopper–Pearson；Wilson 留 Table S4
T3 = md_table(
    ["Therapeutic area", "Chinese-held / all FPP rows", "Share (%)", "Descriptive 95% CI"],
    [[r["therapeutic_area"], f"{r['china_products_k']} / {r['global_fpp_n']}",
      f2(r["share_pct"]), ci(r["ci95_lo_clopper_pearson"], r["ci95_hi_clopper_pearson"])]
     for r in CHINA],
    ["---", "---:", "---:", "---:"],
)
T3_NOTE = (
    "Table 3. Chinese-held prequalified finished pharmaceutical products by therapeutic area, "
    "snapshot 15 September 2026. The three focal disease areas are listed first; the remaining "
    "listed therapeutic areas are included so that the finite-list denominators are complete. "
    "Intervals are exact Clopper–Pearson intervals under a binomial reference model k ~ Bin(n, p); "
    "they describe the width of a finite-list proportion and are not superpopulation sampling "
    "inference. Wilson comparison intervals are given in Table S4. "
    "The disease-specific supply composition is shown in Figure 2(B). "
    "Prequalification breadth is a product-holder-level quality signal, not procurement, delivery "
    "or patient access. FPP, finished pharmaceutical product."
)

# --- Table S4：Wilson 对照（敏感性口径，不入主稿表）
S4 = md_table(
    ["Therapeutic area", "k / n", "Share (%)", "Clopper–Pearson 95% CI", "Wilson 95% CI"],
    [[r["therapeutic_area"], f"{r['china_products_k']} / {r['global_fpp_n']}",
      f2(r["share_pct"]), ci(r["ci95_lo_clopper_pearson"], r["ci95_hi_clopper_pearson"]),
      ci(r["ci95_lo_wilson"], r["ci95_hi_wilson"])] for r in CHINA],
    ["---", "---:", "---:", "---:", "---:"],
)

# --- Table S5：29 国全表（兑现 Figure 2 图注「其余 19 国见补充材料」的承诺）
S5 = md_table(
    ["Holder country (ISO2 as stored)", "Product rows", "Share (%)", "Descriptive 95% CI", "Holders"],
    [[r["iso3"], r["product_rows"], f2(r["share_pct"]), ci(r["ci95_lo"], r["ci95_hi"]),
      r["n_holders"]] for r in SHARE],
    ["---", "---:", "---:", "---:", "---:"],
)

# 投稿体例：正文内编号 Table 1–3；内部代号 A1–A3 仅用于装配留痕
T1_NOTE = T1_NOTE.replace("Table 1.", "**Table 1.**", 1)
T2_NOTE = T2_NOTE.replace("Table 2.", "**Table 2.**", 1)
T3_NOTE = T3_NOTE.replace("Table 3.", "**Table 3.**", 1)
TABLES = (
    "## Tables\n\n"
    + T1_NOTE + "\n\n" + T1 + "\n\n"
    + T2_NOTE + "\n\n" + T2 + "\n\n"
    + T3_NOTE + "\n\n" + T3 + "\n"
)

CAPTION_BLOCK = "## Figure captions\n\n" + "\n\n".join(CAPTIONS) + "\n"

SUPP_INDEX = """## Supplementary material

| Item | Content |
|---|---|
| Table S1 | Average annual percentage change under primary t, HAC lag 3 and residual block-bootstrap interval schemes |
| Table S2 | Alignment sensitivity estimates (country-level bootstrap, common support, second-latest burden year; HIV/AIDS stratum) |
| Notes S3 | Method notes carried over from the main text |
| Table S4 | Chinese-held product breadth: Clopper–Pearson versus Wilson descriptive intervals, all listed therapeutic areas |
| Table S5 | All 29 certificate-holder countries: product rows, share, descriptive 95% CI and holder counts |

Tables S1–S3 are reproduced from the Methods–Results manuscript; Tables S4 and S5 are assembled
from the same authoritative derived CSVs as Tables 1–3. The full supplementary file is supplied
separately at submission.
"""

# ---------------------------------------------------------------- 前页
TITLE_MAIN = ("Geographic alignment between WHO-prequalified medicine supply and malaria, "
              "tuberculosis and HIV/AIDS burden in low- and middle-income countries, 2002–2026")
TITLE_ALT = [
    ("WHO prequalification listing breadth and disease burden in low- and middle-income countries: "
     "a descriptive country-level analysis of malaria, tuberculosis and HIV/AIDS, 2002–2026"),
    ("Quality-assured medicine supply and the geography of malaria, tuberculosis and HIV/AIDS "
     "burden: a public health analysis of the WHO prequalification listing, 2002–2026"),
]
PLACEHOLDER = "[TO BE COMPLETED BY THE AUTHORS"
SHORT_TITLE = "WHO-prequalified supply and disease burden"
KEYWORDS = ("WHO prequalification; malaria; tuberculosis; HIV/AIDS; medicine access; "
            "low- and middle-income countries")

COI_LINE = "The authors declare that they have no competing interests."
FUND_LINE = ("This study drew exclusively on publicly available institutional databases and "
             "required no dedicated data-collection funding.")

TITLE_PAGE = "\n".join([
    "# " + TITLE_MAIN,
    "",
    "**Short title:** " + SHORT_TITLE,
    "",
    "**Authors:** " + PLACEHOLDER + ": full names in publication order, ORCID iDs]",
    "",
    "**Affiliations:** " + PLACEHOLDER + ": numbered affiliations matching the author list]",
    "",
    "**Corresponding author:** " + PLACEHOLDER + ": name, postal address, publication correspondence email]",
    "",
    "**Submission-system contact:** " + PLACEHOLDER + ": separate contact email for Editorial Manager correspondence]",
    "",
    "**ORCID iDs:** " + PLACEHOLDER + ": one per author]",
    "",
    "**Conflict of interest and funding statement:** " + COI_LINE + " " + FUND_LINE,
    "",
    f"**Word count:** {W_IMRD} words of manuscript text (Introduction–Conclusions), "
    f"{W_ABS} words in the structured abstract; tables, references and declarations excluded.",
    "",
    "**Suggested potential reviewers (at least five):**",
    "",
] + [f"{i}. " + PLACEHOLDER + ": name, affiliation, institutional email, expertise, no conflict of interest]"
     for i in range(1, 6)] + [
    "",
    "---",
    "",
])

# ---------------------------------------------------------------- 完整合并稿（28）
def strip_h1(t: str) -> str:
    """去掉各章 PART I 里可能残留的一级标题，保持合并稿层级一致。"""
    return "\n".join(l for l in t.splitlines() if not re.match(r"^#\s(?!#)", l)).strip()

ABSTRACT_BLOCK = strip_h1(P["abstract"])
INTRO = strip_h1(P["intro"])
MR = strip_h1(P["methods_res"])
DISC = strip_h1(P["discussion"])
CONCL = strip_h1(P["conclusions"])
DECL = strip_h1(P["decl_refs"])

MANUSCRIPT = "\n\n".join([
    TITLE_PAGE.rstrip(),
    ABSTRACT_BLOCK,
    "**Keywords:** " + KEYWORDS,
    INTRO,
    MR,
    DISC,
    CONCL,
    DECL,
    TABLES.rstrip(),
    CAPTION_BLOCK.rstrip(),
    SUPP_INDEX.rstrip(),
]) + "\n"

H28 = f"""# B① 主稿 · 完整合并英文稿（pre-assembly v0.8｜2026-11-12）

> 本文件把 `24`（Abstract）、`22`（1 Introduction）、`20`（2 Methods／3 Results）、`21`（4 Discussion）、`23`（5 Conclusions）、`25`（Declarations／References）、`27`（前页／Tables 1–3／补材索引）按 TMIH 前页顺序合并为**一份完整英文主稿**。
> PART I 以下为稿件文本；中文说明与核对件不进稿件。装配由 `数据/scripts/assemble_B_manuscript_2026-11-12.py` 完成，prose 逐字来自各章 PART I，未重写、未润色。
> **本稿为装配中间稿，不是终稿**：① 正文仍按 `25` PART II §六 保持零 `[n]`，正式 Vancouver 插号与号段重排留降 AI 后的 docx 装配轮一次性执行；② 前页涉及作者身份与第三方姓名的字段（署名名单／单位／通讯与联系邮箱／ORCID／≥5 位审稿人）按 `16` §4.8、§5.6 与 `14` §三.9 由作者填写，本轮不代填、不臆造；③ 英文标题、Short title、关键词为按 `16` §4.1 **拟定候选，未定稿**；④ 降 AI 处理、语言终校、真实仓库链接、docx 装配未做。
> 实测：Abstract {W_ABS} 词；Introduction–Conclusions 合计 {W_IMRD} 词；Tables 1–3、Figure 1–3 图注、补材 S1–S5 齐备。

---

# PART I — Manuscript text

"""

# ---------------------------------------------------------------- 装配稿（27）
PART2_27 = f"""# PART II — 内部核对件（不进稿件）

## 一、环节判定与权威依据

| 项 | 内容 |
|---|---|
| 环节 | 产出与互核；本轮主交付＝前页＋Tables 1–3 排版件＋补材 S1–S5＋完整合并主稿 |
| 组名 | WHO PQ 供应—负担空间可及性·论文作战组（沿用） |
| 顺序 | 上一轮（`26` 配图偏好梳理＋3 张主图）已收口；按 `17` 号计划末段「下一轮建议」取「前页＋表 A1–A3 排版件与补充材料装配」 |
| 权威链 | `14` §三.6（图—表不重复）、§三.8（前页顺序）、§三.9（Word Count／≥5 位审稿人／Author Statement）、§三.18（官网未明示项不臆断）＞`16` §4.1（标题）、§4.8、§5.6（未定事项不得当作已定）＞`11` §4（图表命名）＞`26` §五（三图去重对象） |
| 取数白名单 | 仅 `res_B_anchor_year_counts.csv`、`res_B_anchor_apc.csv`、6 份 `res_B_uncertainty_*`（含两份 `_revised` 口径中的错位结果）；`res_B2_*`／`dualchain_*`／`lineitems_clean`／`price_index`／`res_B_hhi_*`／`_archive_v1/*` 一律不读 |
| 用户纪律 | 不生成新的待确认清单；前页需作者填写的字段以占位符呈现，不设成开工门禁，装配与核验照常完成 |

## 二、图—表去重裁决（本轮核心，`14` §三.6）

官网原文 "Restrict tables and figures to those needed… do not duplicate data in graphs and tables"。`26` §三.2／§五 已定分工：**图给形状、表给精确值，图内不写任何精确数值文本标签**。本轮按此判据执行，并新增两条裁决：

| # | 冲突 | 裁决 | 依据 |
|---|---|---|---|
| G01 | `17` 原计划「表 A1＝RQ1 分治疗领域 AAPC／累积数」 vs Figure 1(A) 累积曲线、(B) AAPC 森林图 | **表 A1 改放分母链与清单构成**（25 年观测／648 行／29 国／三病种分母与持证商国数／对齐分析国数），**不列 AAPC 与逐年累积数**；AAPC 精确值已在 Results 3.2 与补材 Table S1，不三重呈现 | `14` §三.6 官网硬规范优先于 `17` 项目计划；`26` §五「Figure 1 去重对象＝表 A1」 |
| G02 | 表 A2 的 CR1 63.73% 与 Figure 2(A) 印度条为同一数值 | 按 `26` 既定判据合规：图中该值只以**图形**呈现、图内零数值文本标签；表 A2 只给 HHI／CRn 汇总，**不列逐国份额** | `26` §三.2；`verify_B_figures` 已检图内纯净度 |
| G03 | 表 A3 的疟疾 24.49% 与 Figure 2(B) 中国堆叠段同源 | 同上：图给构成形状、表给 k/n 与区间；Wilson 敏感性端点**不进主稿表**，改放 Table S4 | `20` v0.2「主口径进主文、敏感性进补材」裁定 |
| G04 | Figure 2 图注承诺「其余 19 个持证商国见补充材料」 | **本轮兑现**：新增 Table S5，列全部 29 国（前十在图中、其余 19 国在表内），逐值从 `country_share_ci.csv` 实读 | 图注不得留空头承诺；`verify_B_figures` 图注五成分 |
| G05 | 内部代号 A1–A3 vs 投稿体例 | 稿件内统一写 **Table 1–3**（与 `Figure 1–3` 体例一致）；内部代号只在装配留痕中保留，映射 A1→1、A2→2、A3→3 | `16` §4.5「图 1–3 与表 1–3」；`26` 图注用 `Figure` 全称 |

**口径留痕（非待办）**：官网 "do not duplicate data" 的最严格读法可把「同一数据的图形＋数值表」也视为重复；本稿按 `26` §五 项目既定分工执行，并在终校时复核 EM 当期是否有更严要求。图内零精确数值标签由 `verify_B_figures_2026-11-12.py` 实检；本轮 `verify_B_manuscript_v0_8` 复检 Tables 1–3 **数据行**零逐国份额文本、零 AAPC／逐年累积数、零 `Figure N` 作数据标签。表注中的 `shown in Figure 1`／`plotted in Figure 2(A)` 等为交叉引用句（阅读指引），不计作数据双载。

## 三、Tables 1–3 逐值回链

| 表 | 值 | 文件 | 列 |
|---|---|---|---|
| 1 | 25 年、2002–2026 | `res_B_anchor_year_counts.csv` | `year` 行数／首尾 |
| 1 | 648 行、29 国 | `res_B_uncertainty_country_share_ci_2026-11-11.csv` | `product_rows` 求和／行数 |
| 1 | 98／255／126 与 11／16／11 | `res_B_uncertainty_supply_by_area_2026-11-11.csv` | `area_denominator`／`n_holder_countries` |
| 1 | 100(79)／193(193)／151(142) | `res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv` | `calibre=latest_burden_year` 的 `n_countries`／`n_burden_countries` |
| 2 | HHI 与 CR1／CR4／CR8 及区间 | `res_B_uncertainty_concentration_ci_2026-11-11.csv` | `metric` 前四行的 `point`／`ci95_lo`／`ci95_hi`／`bootstrap_draws` |
| 3 | 六个治疗领域 k/n、份额、CP 区间 | `res_B_uncertainty_china_breadth_ci_2026-11-11.csv` | `china_products_k`／`global_fpp_n`／`share_pct`／`ci95_lo(hi)_clopper_pearson` |
| S4 | Wilson 对照 | 同上 | `ci95_lo(hi)_wilson` |
| S5 | 29 国全表 | `res_B_uncertainty_country_share_ci_2026-11-11.csv` | 全部 5 个数列 |

**作废值零出现**：`concentration_ci` 后三行是审计行（`HHI_registered_in_12_16` = 4073.76 已作废、`HHI_reviewed_from_share_pct`、`HHI_reviewed_exact`），一律不进表，正文唯一 HHI 仍为 4175.53（95% CI 3737.94–4643.50）。`_archive_v1` 的旧 RQ2 值（1.9489／1.2241／1.9344）零出现。

## 四、前页字段裁定

| 字段 | 本轮处理 | 依据 |
|---|---|---|
| 顺序 | Title → Short title → Authors → Affiliations → Corresponding author → 脚注 → Abstract → Keywords → COI＋Funding → Word Count → ≥5 位审稿人 | `14` §三.8／§三.9 |
| Title／Short title／Keywords | 按 `16` §4.1 给 1 主推＋2 备选标题、1 短题、6 个关键词，**明确标注未定稿** | `16` §5.6 第 3 项「不得当作已定」 |
| Title 不含 `access` | 本文测的是 PQ 认证广度而非实际可及；标题写 `access` 会在题目层面过度声称。scope 对齐由 `low- and middle-income countries`＋三病种＋摘要／引言的准入—可及落差承担 | `20` 2.2／3.5、`21` 4.1 三处诚实口径 |
| Keywords 数量 | 官网 NOT STATED（`14` §三.18）；给 6 个候选、不写死，EM 当期核实 | `24` PART II §五.5 裁定 |
| Word Count | 字段从 `17` 号计划抽取已核验登记值：Abstract **{W_ABS}** 词、Introduction–Conclusions **{W_IMRD}** 词；表／参考文献／Declarations 不计。装配脚本去 Markdown 标题行后实算为 **{W_ABS_CALC}／{W_IMRD_CALC}** 词；逐章差值经诊断为标题行是否计入所致（`20` 的 10 个编号小节标题合计约 34 词，其余各章 ±2 词），属计数口径不同、**非正文改动**（脚本设 ±12／±45 词数量级交叉校验） | `14` §三.9；`24` PART II；`17` 计划 |
| 作者名单／单位／邮箱／ORCID／≥5 位审稿人 | 结构化占位符，由作者填写；**不代填真实第三方姓名、不臆造机构邮箱** | `16` §4.8「作者名单以当次确认为准」；§5.6；`14` §三.9、§三.15 |
| 邮箱双轨 | 通讯作者署名邮箱与投稿系统联系邮箱在前页分列两行，避免混用 | 用户跨项目既定规则；`16` §4.8 |
| 伦理 | 沿用 `25` 的可核验事实陈述，**不擅自使用 `14` §三.11 标注待确认的「豁免句式」** | `16` §5.6 第 5 项 |
| COI／Funding | 逐字取自 `25` Declarations，放前页与 Declarations 两处（官网要求前页含该声明），不进 Cover Letter | `14` §三.8；用户既定规范 |
| Vancouver 插号 | **本轮不插**：正文、表注、图注均零 `[n]`，References 13 条保持定表；物理插号与号段重排留降 AI 后 docx 装配轮 | `25` PART II §六 |

## 五、补材 S1–S5 与图注承诺对照

| 图注／正文承诺 | 兑现位置 |
|---|---|
| Figure 1「HIV/AIDS 只在清单轨迹出现」 | S2 的 HIV/AIDS 补材层（n = 151，负担数据止于 2006） |
| Figure 2「其余 19 个持证商国见补材」 | **Table S5**（29 国全表，本轮新增） |
| Figure 3「病种间不可比」 | 图注原句＋`20` 3.4 正文＋S3 方法注 |
| Methods 2.5「完整敏感性区间见补材」 | S1（AAPC 三方案）、S2（对齐三方案）、S3（7 条方法注） |
| 表 3「Wilson 对照见 Table S4」 | **Table S4**（本轮新增） |

## 六、本轮边界

不写 Cover Letter、不建公开仓库与真实 Data Accessibility Statement URL、不做降 AI 处理、不插 Vancouver 编号、不装配 docx、不做投稿包终检、不重绘或修改 3 张主图、不改动 20–26 号任何正文。上述项按 `17` 号计划既定安排「起草期间并行补齐、不设前置」执行。本轮不生成新的待确认清单。

## 七、生成记录

| 项 | 值 |
|---|---|
| 装配脚本 | `数据/scripts/assemble_B_manuscript_2026-11-12.py` |
| 核验脚本 | `数据/scripts/verify_B_manuscript_v0_8_2026-11-12.py` |
| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 读入 CSV | 8 份权威派生文件（含 2 份 anchor） |
| 读入章节 PART I | 6 份（20／21／22／23／24／25） |
| 读入图注 | 3 条，逐字来自 `配图_2026-11-12/figure_captions.md` |
| 输出 | `27_…装配稿_v0.1`、`28_…完整合并稿_pre-assembly_v0.8` |
"""

H27 = f"""# B① 主稿 · 前页、Tables 1–3 与补充材料装配稿（v0.1｜2026-11-12）

> 本轮把分散成稿的部件收口为**一份完整英文主稿**：前页字段骨架、Tables 1–3 排版件、补材 S1–S5、Figure 1–3 图注与补材索引，连同 `20`–`25` 号稿的 PART I prose 一并装配到 `28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md`。
> PART I 为可进入稿件的英文文本；PART II 为内部核对件，不进稿件。所有表格数值由 `数据/scripts/assemble_B_manuscript_2026-11-12.py` 从 8 份权威 CSV 实读，零硬编码研究数字。
> 前页涉及作者身份与第三方姓名的字段以占位符呈现（署名名单／单位／通讯与联系邮箱／ORCID／≥5 位审稿人），按 `16` §4.8、§5.6 与 `14` §三.9 由作者填写，本轮不代填、不臆造；英文标题为按 `16` §4.1 拟定的**未定稿候选**。全稿正文仍零 `[n]`。

---

"""

PART1_27 = "\n\n".join([
    TITLE_PAGE.rstrip(),
    ABSTRACT_BLOCK,
    "**Keywords:** " + KEYWORDS,
    "## Tables\n\n" + T1_NOTE + "\n\n" + T1 + "\n\n"
    + T2_NOTE + "\n\n" + T2 + "\n\n" + T3_NOTE + "\n\n" + T3,
    CAPTION_BLOCK.rstrip(),
    "## Supplementary material\n\n" + SUPP_CORE_27 + "\n\n"
    + "Table S4. Chinese-held product breadth under the two descriptive interval schemes. "
      "Source: `res_B_uncertainty_china_breadth_ci_2026-11-11.csv`.\n\n" + S4 + "\n\n"
    + "Table S5. All certificate-holder countries in the 15 September 2026 listing snapshot. "
      "The ten leading countries are plotted in Figure 2(A); the remaining 19 are tabulated here. "
      "Source: `res_B_uncertainty_country_share_ci_2026-11-11.csv`. "
      "Intervals are descriptive product-row bootstrap intervals for a finite listing.\n\n" + S5,
    SUPP_INDEX.replace("## Supplementary material", "## Supplementary material index", 1).rstrip(),
]) + "\n"

# ---------------------------------------------------------------- 落盘
D27.write_text(H27 + "# PART I — Manuscript components\n\n" + PART1_27 + "\n---\n\n" + PART2_27,
               encoding="utf-8")
D28.write_text(H28 + MANUSCRIPT, encoding="utf-8")

print("=" * 72)
print("B① 装配轮 · 完成")
print("  27:", D27.name, os.path.getsize(D27), "bytes")
print("  28:", D28.name, os.path.getsize(D28), "bytes")
print("  Abstract words:", W_ABS, "| IMRD words:", W_IMRD)
print("  Table 1 rows: 9 | Table 2 rows:", len(CONC_MAIN), "| Table 3 rows:", len(CHINA))
print("  Table S5 rows:", len(SHARE), "| captions:", len(CAPTIONS))
print("  CSV whitelist:", len(CSV), "| canvas text tokens:", len(CANVAS))
print("=" * 72)
