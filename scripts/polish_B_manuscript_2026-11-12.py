# -*- coding: utf-8 -*-
"""
B① 主稿 · 降 AI 修订（v0.8 -> v0.9），2026-11-12

职责：只做英文语言层去 AI 腔改写，产出 31 号稿。
硬约束（脚本内逐条断言，非口头承诺）：
  1) 全部数值 token 的 multiset 与改写前完全一致（含年份、n、CI、百分比、比值、编号）；
  2) 关键术语与三处诚实口径关键词零丢失；
  3) 章节标题、表格、References、Declarations、Figure captions 逐字不动；
  4) 26 组禁词／作废值／中文禁词零命中；防火墙零命中；
  5) 28 号 pre-assembly 稿冻结不动（本脚本只读）。

改写范围：Abstract + 1 Introduction + 2 Methods + 3 Results + 4 Discussion + 5 Conclusions
的 prose 句子；Methods 的口径定义句、Results 的全部数字句只做连接词与句式层调整。
Vancouver 插号与图表交叉引用不在本脚本，留 32 号 v1.0 定稿轮一次性插入。

运行：python polish_B_manuscript_2026-11-12.py
"""
import hashlib
import os
import re
from collections import Counter

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
SRC = os.path.join(MAIN, "28_B①主稿_完整合并稿_pre-assembly_v0.8_2026-11-12.md")
OUT = os.path.join(MAIN, "31_B①主稿_降AI修订稿_v0.9_2026-11-12.md")

NUM = re.compile(r"\d+(?:[.,]\d+)*")

# (章节, 改动类型, 原文精确片段, 改写后片段)
REWRITES = [
    # ---------------- Abstract ----------------
    ("Abstract", "去缓冲语 with attention to",
     "Objectives: To characterise the 2002–2026 trajectory of the WHO-prequalified finished pharmaceutical product listing, the distribution of certificate-holder countries and the alignment of disease-specific supply shares with country-level malaria, tuberculosis and HIV/AIDS burden, with attention to low- and middle-income countries.",
     "Objectives: To characterise the 2002–2026 trajectory of the WHO-prequalified finished pharmaceutical product listing, the distribution of certificate-holder countries and the alignment of disease-specific supply shares with country-level malaria, tuberculosis and HIV/AIDS burden in low- and middle-income countries."),
    ("Abstract", "去断裂名词句",
     "The country was the spatial unit and the window 2002–2026 (25 years).",
     "Countries were the unit of analysis over 2002–2026 (25 years)."),
    ("Abstract", "拆对称分号句",
     "A single-slope log-linear fit summarised cumulative-stock trend; model-based or bootstrap intervals quantified uncertainty for concentration, finite-list proportions and alignment.",
     "A single-slope log-linear fit summarised the cumulative-stock trend. Model-based and bootstrap intervals quantified uncertainty in concentration, finite-list proportions and alignment."),
    ("Abstract", "去句首 However／去 whereas 对称；保留正面定义式诚实口径",
     "However, a prequalification listing records quality assurance at product-holder level, whereas national registration, procurement, delivery and patient use are captured in downstream records; the listing should therefore be read alongside procurement and delivery data.",
     "A prequalification listing records quality assurance at product-holder level. National registration, procurement, delivery and patient use are downstream records that should be read alongside it."),
    ("Abstract", "拆双谓语并列、保留 should",
     "Procurement agencies, funders and prequalification bodies should use this country-scale stratification to prioritise supplier-portfolio review and keep holder-country fields machine-readable with a dated snapshot and a versioned mapping.",
     "Procurement agencies, funders and prequalification bodies can use this country-scale stratification to review supplier portfolios, and should keep holder-country fields machine-readable with a dated snapshot and a versioned mapping."),

    # ---------------- 1 Introduction ----------------
    ("1 Introduction", "去句首 However",
     "However, the size of a quality-assured listing and its geographic composition are separate questions.",
     "The size of a quality-assured listing and its geographic composition are separate questions."),
    ("1 Introduction", "拆 whereas 长句",
     "A product count describes how many certificates are listed, whereas certificate-holder country, therapeutic area and the distribution of disease burden are distinct dimensions recorded in different data systems and at different levels of aggregation.",
     "A product count records how many certificates are listed. Certificate-holder country, therapeutic area and the distribution of disease burden are separate dimensions, held in different data systems and at different levels of aggregation."),
    ("1 Introduction", "去对仗套语、改具体",
     "This distinction matters for procurement and for monitoring: a listing can grow while the set of countries holding certificates remains narrow, and the interpretation of either pattern depends on keeping the listing separate from downstream availability.",
     "For procurement and monitoring, the distinction matters: a listing can grow even as the set of countries holding certificates stays narrow, and reading either pattern requires keeping the listing separate from downstream availability."),
    ("1 Introduction", "拆 but 长句／去 which limits 模板",
     "These accounts clarify how quality assurance operates, but most are aggregated at the level of the programme, the product or the institution, which limits the description of geographic heterogeneity in who holds certificates.",
     "These accounts explain how quality assurance operates. Most aggregate at the level of the programme, the product or the institution, which leaves little room to describe geographic heterogeneity in who holds certificates."),
    ("1 Introduction", "去与 Discussion 重复的 baseline 套语",
     "Placing both distributions on that scale yields a reproducible stratification and a baseline that can be recomputed as the listing is updated.",
     "Putting both distributions on that scale gives a stratification that can be recomputed as the listing is updated."),
    ("1 Introduction", "去 refines the understanding 空泛自评",
     "The analysis refines the understanding of what a quality-assured listing records and provides a baseline for monitoring how the geography of the listing changes across updates.",
     "The analysis sets out what a quality-assured listing records and gives a baseline for monitoring how the geography of the listing changes across updates."),

    # ---------------- 2 Methods ----------------
    ("2 Methods", "拆分号／去 with 尾巴；口径定义零改动",
     "Because the FPP list is a complete stock census, point estimates are exact for that listing; the intervals below quantify model uncertainty, compositional variation and sensitivity to definitional choices, with reference models given in 2.5.",
     "Because the FPP list is a complete stock census, point estimates are exact for that listing. The intervals below quantify model uncertainty, compositional variation and sensitivity to definitional choices; the reference models are specified in 2.5."),
    ("2 Methods", "拆三项并列",
     "The lag was set by convention, the t interval was prespecified as primary, and both sensitivity intervals are tabulated with their diagnostics in the supplementary material.",
     "The lag was set by convention and the t interval prespecified as primary. Both sensitivity intervals are tabulated with their diagnostics in the supplementary material."),

    # ---------------- 3 Results ----------------
    ("3 Results", "拆对称分号；全部数值零改动",
     "The dated rows produced a 25-year cumulative series rising from 10 products in 2002 to 558 in 2026; the 2026 value reflects a partial year, and all values denote stock.",
     "The dated rows produced a 25-year cumulative series rising from 10 products in 2002 to 558 in 2026. The 2026 value reflects a partial year, and all values denote stock."),
    ("3 Results", "去空泛短句 Concentration was high",
     "Concentration was high. The HHI was",
     "The holder-country distribution was highly concentrated. The HHI was"),

    # ---------------- 4 Discussion ----------------
    ("4 Discussion", "去机械计数框架",
     "Three properties of the underlying measure bound this reading.",
     "What the measure records sets the bounds on this reading."),
    ("4 Discussion", "去机械回指、保留口径边界",
     "The alignment discussed below is therefore a comparison between a listing-level supply distribution and a country-level burden distribution, and these three properties apply to every estimate that follows.",
     "The alignment discussed below is therefore a comparison between a listing-level supply distribution and a country-level burden distribution; these bounds apply to every estimate that follows."),
    ("4 Discussion", "去 This analysis 自指／拆 so that；保留 complements and expands 作为 [13] 锚点",
     "This analysis complements and expands that literature by placing certificate-holder country, therapeutic area and disease burden on a common country scale, so that the geographic structure of the listing can be compared directly with the geographic structure of burden.",
     "Placing certificate-holder country, therapeutic area and disease burden on a common country scale complements and expands that literature: the geographic structure of the listing can then be compared directly with that of burden."),
    ("4 Discussion", "去 The value lies in 套语",
     "The value lies in a reproducible stratification and a baseline for monitoring how the listing evolves.",
     "The result is a stratification that can be recomputed and used as a baseline for monitoring how the listing evolves."),
    ("4 Discussion", "去防御性双重 hedge",
     "Several features of the listing may partly explain the patterns we observed, and these remain candidate interpretations.",
     "Several features of the listing offer candidate interpretations of these patterns."),
    ("4 Discussion", "去套话外壳、保留实质限定",
     "This reading should be interpreted with caution, because the tuberculosis estimate is sensitive to the choice of supply denominator and the two disease strata rest on different country sets, units and reference years.",
     "The tuberculosis estimate is sensitive to the choice of supply denominator, and the two disease strata rest on different country sets, units and reference years."),
    ("4 Discussion", "改 so 为分号、时态收紧",
     "Distinguishing among these candidates would require procurement, registration and utilisation data, so the interpretation here stays at the level of listing structure.",
     "Distinguishing among these candidates requires procurement, registration and utilisation data; the interpretation here therefore stays at the level of listing structure."),
    ("4 Discussion", "去 inference is confined 防御句、保留设计边界",
     "The design is ecological and descriptive. It compares aggregate country-level distributions, so inference here is confined to description; distinguishing among the candidate explanations would require longitudinal or quasi-experimental designs with procurement or utilisation outcomes.",
     "The comparisons are ecological and descriptive. Testing the candidate explanations calls for longitudinal or quasi-experimental designs with procurement or utilisation outcomes."),
    ("4 Discussion", "删空泛主题句",
     "The value of this framework is a reproducible baseline. Repeated from the same dated extracts, the holder-country shares, HHI, C, R25 and quartile contrasts can be tracked as the listing changes, and the same calibre can be applied to other product classes.",
     "Repeated from the same dated extracts, the holder-country shares, HHI, C, R25 and quartile contrasts can be tracked as the listing changes, and the same calibre applied to other product classes."),
    ("4 Discussion", "去句首 However／拆长句",
     "However, expanding the number of prequalified products alone is unlikely to change the geographic distribution of certificate holders, and monitoring built on listing status should be paired with downstream procurement, registration and utilisation data before it is used to judge availability.",
     "Expanding the number of prequalified products alone is unlikely to change the geographic distribution of certificate holders. Monitoring built on listing status should be paired with downstream procurement, registration and utilisation data before it is used to judge availability."),
    ("4 Discussion", "去 Overall 空泛收束／拆句",
     "Overall, the expansion of the quality-assured listing and its concentrated, unevenly aligned geography are separate findings, and a stratification that keeps them separate provides a clearer basis for monitoring than a single aggregate count of prequalified products.",
     "The expansion of the quality-assured listing and its concentrated, unevenly aligned geography are separate findings. A stratification that keeps them apart gives monitoring a firmer basis than a single aggregate count of prequalified products."),

    # ---------------- 5 Conclusions ----------------
    ("5 Conclusions", "去句首 However",
     "However, the alignment remains uneven: the heaviest-burden quartile held most estimated malaria burden against a small share of listed malaria products, whereas tuberculosis products were concentrated in a single high-burden country.",
     "The alignment remains uneven: the heaviest-burden quartile held most estimated malaria burden against a small share of listed malaria products, while tuberculosis products were concentrated in a single high-burden country."),
]

TERMS = [
    "product-holder-level quality signal",
    "Prequalification breadth",
    "registration, procurement, delivery and patient use",
    "finished pharmaceutical product",
    "Herfindahl–Hirschman Index",
    "Clopper–Pearson",
    "ordinary least squares",
    "burden-weighted supply coverage",
    "machine-readable",
    "descriptive ecological analysis",
    "15 September 2026",
    "common country scale",
    "complements and expands",
    "consistent with",
    "in line with",
]

BANNED = [
    # 「首创声明」而非 first 一词的全部用法；first-order autocorrelation 等属技术术语，见 FIRST_TECH
    r"\bfirst (?:study|report|analysis|evidence|description|attempt|to\b)",
    r"\bfirst-ever\b", r"\bfor the first time\b",
    r"\bnovel\b", r"theoretical contribution", r"the present study",
    r"\bMoreover\b", r"\bFurthermore\b", r"near-complete mismatch",
    r"\bprove\b", r"\bconfirm\b", r"\bestablish\b", r"\bclearly\b", r"\bdefinitive\b",
    r"UN Comtrade", r"\bHS6?\b", r"\bUSD\b", r"10,324", r"U1/U2/U3", r"\b2\.137\b",
    r"4073\.8", r"4073\.76", r"1\.9489", r"1\.2241", r"1\.9344",
    r"joinpoint", r"causal identification was attempted",
]
CN_BAN = ["Phase", "工作包", "go-no-go", "背书", "延伸许铭", "综上所述", "值得注意的是"]
FIRST_TECH = ["first-order autocorrelation", "are listed first"]


def prose_words(block: str) -> int:
    body = "\n".join(l for l in block.splitlines() if not re.match(r"^\s{0,3}#{1,6}\s", l))
    return len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body))


def main() -> None:
    raw = open(SRC, encoding="utf-8").read()
    assert "# PART I — Manuscript text" in raw
    src = raw.split("# PART I — Manuscript text", 1)[1].strip()

    cur = src
    applied = []
    for sec, kind, old, new in REWRITES:
        n = cur.count(old)
        assert n == 1, f"锚点匹配 {n} 次（应为 1）｜{sec}｜{kind}｜{old[:90]!r}"
        assert old != new
        cur = cur.replace(old, new, 1)
        applied.append((sec, kind, old, new))

    # ---- 硬断言 1：数值 token multiset 完全一致 ----
    a, b = Counter(NUM.findall(src)), Counter(NUM.findall(cur))
    assert a == b, f"数值 multiset 变化：减少 {a-b} / 新增 {b-a}"

    # ---- 硬断言 2：关键术语与诚实口径零丢失 ----
    lost = [t for t in TERMS if t not in cur]
    assert not lost, f"关键术语丢失：{lost}"

    # ---- 硬断言 3：结构件逐字未动 ----
    markers = [
        "## Tables", "**Table 1.**", "**Table 2.**", "**Table 3.**",
        "## Figure captions", "Figure 1 Cumulative", "Figure 2 Geographic", "Figure 3 Alignment",
        "## Declarations", "## References", "## Supplementary material",
        "**Ethics approval and consent to participate.**", "United Nations General Assembly.",
        "Xu M, Zhang L, Feng X, Zhang Z, Huang Y.",
    ]
    for m in markers:
        assert m in src and m in cur, f"结构件缺失：{m}"
    ref_block_src = src.split("## References", 1)[1].split("## Tables", 1)[0]
    ref_block_cur = cur.split("## References", 1)[1].split("## Tables", 1)[0]
    assert ref_block_src == ref_block_cur, "References 区块被改动"
    tbl_src = src.split("## Tables", 1)[1]
    tbl_cur = cur.split("## Tables", 1)[1]
    assert tbl_src == tbl_cur, "Tables / Figure captions / 补材索引区块被改动"
    dec_src = src.split("## Declarations", 1)[1].split("## References", 1)[0]
    dec_cur = cur.split("## Declarations", 1)[1].split("## References", 1)[0]
    assert dec_src == dec_cur, "Declarations 区块被改动"

    # ---- 硬断言 4：禁词、作废值、防火墙 ----
    hits = [p for p in BANNED if re.search(p, cur, flags=re.I)]
    assert not hits, f"禁词命中：{hits}"
    first_ctx = [
        cur[max(0, m.start() - 30):m.start() + 40]
        for m in re.finditer(r"\bfirst\b", cur, flags=re.I)
    ]
    assert len(first_ctx) == 3, f"first 技术性用法数量变化：{len(first_ctx)}（应为 3）"
    assert all(any(w in c for w in FIRST_TECH) for c in first_ctx), \
        f"出现非技术性 first 用法：{first_ctx}"
    assert not [w for w in CN_BAN if w in cur], "中文禁词命中"
    assert not re.search(r"(?i)export value|trade volume|出口额", cur), "六章防火墙命中"
    assert not re.search(r"\[\d+\]", cur), "降 AI 稿仍须保持零 [n]（插号留 v1.0）"

    # ---- 硬断言 5：摘要与结论无 >=12 词连续重合 ----
    abstract = cur.split("## Abstract", 1)[1].split("---", 1)[0]
    concl = cur.split("## 5 Conclusions", 1)[1].split("---", 1)[0]
    tok = lambda s: re.findall(r"[a-z]+", s.lower())
    ta, tc = tok(abstract), tok(concl)
    longest, best = 0, ""
    for i in range(len(ta) - 11):
        for j in range(len(tc) - 11):
            k = 0
            while i + k < len(ta) and j + k < len(tc) and ta[i + k] == tc[j + k]:
                k += 1
            if k > longest:
                longest, best = k, " ".join(ta[i:i + k])
    assert longest < 12, f"摘要与结论连续重合 {longest} 词：{best!r}"

    # ---- 词数实算（同一口径：去 Markdown 标题行） ----
    abs_block = cur.split("## Abstract", 1)[1].split("---", 1)[0]
    intro_to_concl = cur.split("## 1 Introduction", 1)[1].split("## Declarations", 1)[0]
    w_abs = prose_words(abs_block)
    w_imrd = prose_words(intro_to_concl)
    src_abs = prose_words(src.split("## Abstract", 1)[1].split("---", 1)[0])
    src_imrd = prose_words(src.split("## 1 Introduction", 1)[1].split("## Declarations", 1)[0])

    cur = re.sub(
        r"\*\*Word count:\*\*[^\n]*",
        f"**Word count:** {w_imrd} words of manuscript text (Introduction–Conclusions), "
        f"{w_abs} words in the structured abstract; tables, references and declarations excluded.",
        cur, count=1,
    )

    header = (
        "# B① 主稿 · 降 AI 修订稿（v0.9｜2026-11-12）\n\n"
        "> 由 `数据/scripts/polish_B_manuscript_2026-11-12.py` 从 `28` 号 pre-assembly v0.8 稿生成；"
        "`28` 号稿**冻结不动**，作为改写前留痕。\n"
        "> PART I 为降 AI 后的英文稿；PART II 为逐条改写台账与零数值改动证明（中文内部核对件，不进稿件）。\n"
        "> **本稿仍非终稿**：Vancouver `[1]–[13]` 插号、图表交叉引用（C1–C8）、前页按 `14` §三.8 重排、"
        "Word Count 定稿与 docx 装配留 `32` 号 v1.0 定稿轮；本稿正文保持零 `[n]`。\n"
        "> 改写只作用于 Abstract 与 IMRD 五章的语言层；Methods 口径定义、Results 全部数值句、"
        "Declarations、References、Tables 1–3、Figure captions 与补材索引逐字未动。\n"
        f"> 自动核验：{len(applied)} 条改写全部唯一命中；数值 token multiset 完全一致；"
        f"关键术语 {len(TERMS)} 项零丢失；禁词／作废值／防火墙零命中；"
        f"纯正文实算 Abstract {src_abs}→{w_abs} 词、IMRD {src_imrd}→{w_imrd} 词。\n\n"
        "---\n\n# PART I — Manuscript text\n\n"
    )

    ledger = [
        "", "---", "", "# PART II — 降 AI 改写台账（内部核对件，不进稿件）", "",
        "## 一、改写边界与硬断言", "",
        "| 断言 | 结果 |", "|---|---|",
        f"| 改写条数（每条 old 在 v0.8 中唯一命中） | {len(applied)} |",
        f"| 数值 token multiset（年份／n／CI／百分比／比值／编号） | 改写前后完全一致，共 {sum(a.values())} 个 token |",
        f"| 关键术语与诚实口径关键词 | {len(TERMS)} 项零丢失 |",
        "| References / Declarations / Tables 1–3 / Figure captions / 补材索引 | 区块逐字一致 |",
        f"| 禁词／作废值／中文禁词／六章防火墙 | 零命中（{len(BANNED)} 组正则 + {len(CN_BAN)} 个中文词）；`first` 3 处均为 `first-order autocorrelation`／`are listed first` 技术性用法，非首创声明 |",
        "| 正文 `[n]` | 零（插号留 v1.0） |",
        f"| 摘要与 Conclusions 最长连续重合 | {longest} 词（<12） |",
        "| 词数（去 Markdown 标题行纯正文口径） | "
        f"Abstract {src_abs}→{w_abs}；IMRD {src_imrd}→{w_imrd} |",
        "",
        "> 词数变化的两个来源需分开看：① 改写前 `28` 号稿登记 252／3446 计入了编号小节标题行与结构化摘要标签，"
        "纯 prose 口径实算为 "
        f"{src_abs}／{src_imrd}（差 {3446 - src_imrd} 词，纯计数口径）；② 降 AI 本身使纯 prose 由 "
        f"{src_abs}／{src_imrd} 变为 {w_abs}／{w_imrd}（差 {src_imrd - w_imrd} 词，来自删除空泛主题句与套话外壳）。"
        "本稿统一按纯 prose 口径实算并更新前页 Word count，改写后正文 "
        f"{w_imrd} 词，落在 `14` §三.2 的 3,500 词原则上限之内。"
        "", "## 二、逐条改写台账", "",
        "| # | 章节 | 类型 | 改写前（首 90 字符） | 改写后（首 90 字符） |",
        "|---|---|---|---|---|",
    ]
    for i, (sec, kind, old, new) in enumerate(applied, 1):
        cl = lambda s: s.replace("|", "\\|").replace("\n", " ")
        ledger.append(f"| {i} | {sec} | {kind} | `{cl(old[:90])}` | `{cl(new[:90])}` |")

    ledger += [
        "", "## 三、AI 腔诊断与处置对照", "",
        "| 诊断项 | v0.8 表现 | v0.9 处置 |", "|---|---|---|",
        "| 句首转折词模板 | `However,` 出现在 Introduction 段 2、Conclusions 段 2、Abstract Conclusions、Discussion 4.5 | 全部去除，改以句内逻辑承接 |",
        "| 对称 whereas／分号对仗 | 多处 `A, whereas B`、`X; Y` 同长并列 | 拆句或改介词，句长产生自然变异 |",
        "| 机械计数框架 | `Three properties ...` ＋ `these three properties apply ...` | 改为实质边界叙述，去掉回指计数 |",
        "| 空泛自评 | `refines the understanding`、`The value lies in`、`The value of this framework is` | 改为具体动作或整句删除 |",
        "| 防御性双重 hedge | `may partly explain ... and these remain candidate interpretations`、`inference here is confined to description` | 改为单一正面陈述，保留设计边界但不自证 |",
        "| 套话外壳 | `This reading should be interpreted with caution, because ...` | 删外壳，直接给出实质限定 |",
        "| 自我指涉 | `This analysis complements and expands ...` | 改以方法动作起句；**保留 `complements and expands` 词组**作为 `25` 号稿 [13] 插号锚点 |",
        "| 空泛收束 | `Overall, ...` | 删除并拆为两句 |",
        "", "## 四、未改动清单（证据链护栏）", "",
        "- Introduction 前三句（`[1,2,3]`／`[4,5]`／`[6,7,8]` 锚点）、段 3 首句（`[9,10]` 锚点）、"
        "`Published estimates ... are limited.`（G1 裁定保留）、`We aimed to describe ...`（C7 不插号）逐字未动。",
        "- Discussion 4.2 的 `consistent with` 与 `in line with` 两句（`[11]`／`[12]` 锚点）逐字未动。",
        "- Methods 2.2–2.4 全部口径定义、`M / D / C / R25` 公式说明、`k ~ Bin(n, p)` 参考模型、"
        "HAC／block bootstrap 规格、ISO 码表说明、种子 `20261111` 逐字未动。",
        "- Results 3.1–3.5 全部估计值、95% CI、绝对数、n、R² 与三处诚实口径逐字未动；"
        "仅 3.1 一句分号、3.3 一句空泛短句作语言层调整。",
        "- 三处诚实口径关键词 `product-holder-level quality signal`、"
        "`registration, procurement, delivery and patient use`、`Prequalification breadth` 全部保留。",
        "", "## 五、本轮边界", "",
        "- 不做 Vancouver 插号、不插图表交叉引用、不做前页字段实填、不建公开仓库、不装配 docx、不写 Cover Letter。",
        "- 不改 20–30 号任何稿件、三张图件、出图脚本、契约、manifest、图注与任何派生 CSV。",
        f"- 可复跑：`数据/scripts/polish_B_manuscript_2026-11-12.py`；源稿 MD5 `{hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]}…`（只读）。",
    ]

    open(OUT, "w", encoding="utf-8", newline="\n").write(
        header + cur.strip() + "\n" + "\n".join(ledger) + "\n"
    )
    print(f"WROTE {os.path.basename(OUT)}")
    print(f"rewrites = {len(applied)} | numeric tokens = {sum(a.values())} (unchanged)")
    print(f"word count pure prose: Abstract {src_abs}->{w_abs}, IMRD {src_imrd}->{w_imrd}")
    print(f"max abstract/conclusions overlap = {longest} words")
    print("VERDICT = ALL CLEAN")


if __name__ == "__main__":
    main()
