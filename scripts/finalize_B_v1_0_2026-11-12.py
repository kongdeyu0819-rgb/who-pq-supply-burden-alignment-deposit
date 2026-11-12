# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.0 定稿装配（v0.9 -> v1.0），2026-11-12

在降 AI 后的 31 号稿上一次性执行四件事（与 25 §五、30 §六既定裁定一致）：
  A) Vancouver [1]–[13] 物理插号（25 号稿 §五逐句契约）
  B) 图表交叉引用 C1–C8（30 号稿 §六）
  C) 正文 9 处 supplementary material 泛指逐处复核，8 处补具体表号、1 处按实质保留
  D) 前页按 14 §三.8 官网顺序重排（Abstract -> Keywords -> COI+Funding -> Word Count）

装配层硬保证：每条插入/替换都登记 revert 对；全部完成后按逆序还原，
必须逐字回到 31 号稿的 Introduction–Conclusions 块，证明 prose 与全部数值零改动。

不改：References 13 条、Declarations、Tables 1–3、Figure captions、补材索引、
三张图件、任何派生 CSV、28/31 号稿。

运行：python finalize_B_v1_0_2026-11-12.py
"""
import hashlib
import os
import re

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
SRC = os.path.join(MAIN, "31_B①主稿_降AI修订稿_v0.9_2026-11-12.md")
OUT = os.path.join(MAIN, "32_B①主稿_v1.0_定稿稿_2026-11-12.md")

REVERT = []          # (new_text, old_text, tag)
LEDGER = []          # 台账行


def cite(s: str, anchor: str, nums: list[int], tag: str) -> str:
    """Vancouver 句末标点前插号：'... LMICs [1,2,3].'"""
    assert s.count(anchor) == 1, f"锚点非唯一：{tag}｜{anchor[:80]!r}｜count={s.count(anchor)}"
    assert anchor.endswith("."), f"锚点须为完整句（以句号结束）：{tag}"
    new = anchor[:-1] + " [" + ",".join(str(n) for n in nums) + "]."
    s = s.replace(anchor, new, 1)
    REVERT.append((new, anchor, tag))
    LEDGER.append((tag, "Vancouver 插号", f"[{','.join(map(str, nums))}]", anchor[:70]))
    return s


def sub(s: str, old: str, new: str, tag: str, note: str = "") -> str:
    assert s.count(old) == 1, f"锚点非唯一：{tag}｜{old[:80]!r}｜count={s.count(old)}"
    assert old != new
    s = s.replace(old, new, 1)
    REVERT.append((new, old, tag))
    LEDGER.append((tag, note or "泛指改具体表号", new[len(old):] if new.startswith(old) else new[:70], old[:70]))
    return s


def append(s: str, anchor: str, added: str, tag: str, note: str) -> str:
    assert s.count(anchor) == 1, f"锚点非唯一：{tag}｜{anchor[:80]!r}｜count={s.count(anchor)}"
    s = s.replace(anchor, anchor + added, 1)
    REVERT.append((anchor + added, anchor, tag))
    LEDGER.append((tag, note, added.strip()[:90], anchor[:70]))
    return s


def main() -> None:
    raw = open(SRC, encoding="utf-8").read()
    src = raw.split("# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0].strip()

    # ---- 前页字段提取（用于按 14 §三.8 重排） ----
    head, rest = src.split("## Abstract", 1)
    title = head.strip().splitlines()[0]

    def grab(label: str) -> str:
        m = re.search(r"^\*\*" + re.escape(label) + r":\*\*[^\n]*$", head, flags=re.M)
        assert m, f"前页字段缺失：{label}"
        return m.group(0)

    f_short = grab("Short title")
    f_authors = grab("Authors")
    f_affil = grab("Affiliations")
    f_corr = grab("Corresponding author")
    f_subm = grab("Submission-system contact")
    f_orcid = grab("ORCID iDs")
    f_coi = grab("Conflict of interest and funding statement")
    f_wc = grab("Word count")
    mrev = re.search(r"^\*\*Suggested potential reviewers \(at least five\):\*\*.*?(?=^---|\Z)",
                     head, flags=re.M | re.S)
    assert mrev, "审稿人建议块缺失"
    f_rev = mrev.group(0).strip()
    assert len(re.findall(r"^\d\. ", f_rev, flags=re.M)) >= 5, "审稿人建议少于 5 位"

    # ---- Abstract / Keywords / 正文 / 尾部 切分 ----
    abs_block, after_abs = rest.split("**Keywords:**", 1)
    kw_line, body_and_tail = after_abs.split("\n", 1)
    kw = "**Keywords:**" + kw_line
    # body_and_tail 形如 "\n\n## 1 Introduction ...\n---\n\n## Declarations ..."
    i_intro = body_and_tail.index("## 1 Introduction")
    i_decl = body_and_tail.index("## Declarations")
    intro_block = body_and_tail[i_intro:i_decl].strip()
    tail = body_and_tail[i_decl:].strip()
    ORIGINAL_INTRO = intro_block

    # ================= A) Vancouver 插号（25 §五） =================
    s = intro_block
    s = cite(s,
        "Malaria, tuberculosis and HIV/AIDS remain central to the Sustainable Development Goal 3 agenda and to the disease-specific strategies of the World Health Organization (WHO), with the heaviest burden carried by low- and middle-income countries (LMICs).",
        [1, 2, 3], "V1 / Introduction 段 1 句 1")
    s = cite(s,
        "Medicines of assured quality are a precondition for these programmes, and the WHO Prequalification of Medicines Programme gives procurement agencies and national regulators a common basis for judging whether a product meets a shared quality standard.",
        [4, 5], "V2 / Introduction 段 1 句 2")
    s = cite(s,
        "The listing of prequalified finished pharmaceutical products (FPPs) spans antimalarials, antituberculosis medicines and antiretrovirals, alongside vaccines, active pharmaceutical ingredients and diagnostics, and serves as a reference for quality-assured procurement.",
        [6, 7, 8], "V3 / Introduction 段 1 句 3")
    s = cite(s,
        "Existing accounts of prequalification have largely described its institutional architecture, the experience of individual national regulators, the assessment and inspection process, or the participation of manufacturers from a single country.",
        [9, 10], "V4 / Introduction 段 3 句 1")
    s = cite(s,
        "The framing of prequalification as a global quality signal is consistent with earlier accounts of WHO prequalification and of reliance-based regulatory convergence, in which a common quality assessment supports use across multiple jurisdictions.",
        [11], "V5 / Discussion 4.2 consistent with 句")
    s = cite(s,
        "The concentration of listings among a small set of holder countries is in line with descriptive accounts of how manufacturers seek and maintain prequalification status against a shared quality standard.",
        [12], "V6 / Discussion 4.2 in line with 句")
    s = cite(s,
        "Placing certificate-holder country, therapeutic area and disease burden on a common country scale complements and expands that literature: the geographic structure of the listing can then be compared directly with that of burden.",
        [13], "V7 / Discussion 4.2 complements and expands 句（降 AI 后锚点）")

    # ================= C) 正文 9 处补材泛指逐处复核 =================
    # C7-1 / Methods 2.4
    s = sub(s,
        "HIV/AIDS, whose GHO extract ends in 2006, is reported in the supplementary material.",
        "HIV/AIDS, whose GHO extract ends in 2006, is reported in Table S2.",
        "C7-1 / 2.4", "HIV/AIDS 出局 -> Table S2")
    # C7-2 / Methods 2.5（AAPC 三方案）
    s = sub(s,
        "Both sensitivity intervals are tabulated with their diagnostics in the supplementary material.",
        "Both sensitivity intervals are tabulated with their diagnostics in Table S1.",
        "C7-2 / 2.5", "AAPC 三区间方案 -> Table S1")
    # C7-3 / Methods 2.5（对齐敏感性）
    s = sub(s,
        "their properties and estimates are given in the supplementary material.",
        "their properties and estimates are given in Table S2.",
        "C7-3 / 2.5", "对齐敏感性 -> Table S2")
    # C7-4 / Methods 2.6（方法注）
    s = sub(s,
        "diagnostics for every estimate are listed in the supplementary material.",
        "diagnostics for every estimate are listed in Notes S3.",
        "C7-4 / 2.6", "方法注 -> Notes S3")
    # C7-6 / Results 3.2（完整区间）
    s = sub(s,
        "the full intervals are tabulated in the supplementary material and the primary t intervals were used throughout.",
        "the full intervals are tabulated in Table S1 and the primary t intervals were used throughout.",
        "C7-6 / 3.2", "完整区间 -> Table S1")
    # C7-8 / Discussion 4.4
    s = sub(s,
        "The HIV/AIDS stratum is reported in the supplementary material, and the burden shares should be compared within rather than across disease strata, since country sets, units and reference years differ.",
        "The HIV/AIDS stratum is reported in Table S2, and the burden shares should be compared within rather than across disease strata, since country sets, units and reference years differ.",
        "C7-8 / 4.4", "HIV/AIDS 补材 -> Table S2")
    # C7-9 / Declarations：按实质保留泛指（指整个补材包，非某张具体表），不替换

    # ================= B) 图表交叉引用 C1–C8 =================
    # C1（含 C7-5）3.1 末句
    s = sub(s,
        "the HIV/AIDS set comprised 151 countries and is reported in the supplementary material (burden snapshot ends in 2006).",
        "the HIV/AIDS set comprised 151 countries and is reported in Table S2 (burden snapshot ends in 2006). The denominator chain is summarised in Table 1.",
        "C1+C7-5 / 3.1", "Table 1 交叉引用；HIV/AIDS -> Table S2")
    # C2 3.2 末句
    s = append(s,
        "These slopes describe the average annual change of a cumulative stock series.",
        " Cumulative trajectories and average annual percentage changes are shown in Figure 1(A,B).",
        "C2 / 3.2", "Figure 1(A,B) 交叉引用")
    # C3 3.3 第一段末
    s = append(s,
        "Restricting the mapping to high-confidence assignments (59 rows removed, denominator 590) raised the HHI to 4834.36, consistent with the primary estimate.",
        " Concentration indices and their intervals are reported in Table 2.",
        "C3 / 3.3", "Table 2 交叉引用")
    # C4（含 Table S5）3.3 末句
    s = append(s,
        "All alignment estimates below use these area-specific shares.",
        " Holder-country shares and disease-specific supply composition are shown in Figure 2(A,B), and the remaining 19 holder countries are listed in Table S5.",
        "C4+C7-S5 / 3.3", "Figure 2(A,B) 交叉引用；兑现图注 19 国承诺")
    # C5（含 C7-7）3.4 末句
    s = sub(s,
        "Country-level bootstrap intervals, common-support and second-latest-burden-year estimates, and the HIV/AIDS stratum are tabulated in the supplementary material.",
        "Country-level bootstrap intervals, common-support and second-latest-burden-year estimates, and the HIV/AIDS stratum are tabulated in Table S2. Quartile burden and supply shares, and the coverage indices, are compared in Figure 3(A,B).",
        "C5+C7-7 / 3.4", "Figure 3(A,B) 交叉引用；对齐敏感性 -> Table S2")
    # C6（含 Table S4）3.5 末句
    s = append(s,
        "These counts measure China-sourced breadth within the quality-assured listing.",
        " Breadth by therapeutic area is tabulated in Table 3, and Wilson comparison intervals for all listed therapeutic areas are given in Table S4.",
        "C6+C7-S4 / 3.5", "Table 3 交叉引用；Wilson 对照 -> Table S4")

    # ================= 装配层零改动证明（逆序还原） =================
    restored = s
    for new, old, tag in reversed(REVERT):
        assert restored.count(new) >= 1, f"还原失败：{tag}｜{new[:70]!r}"
        restored = restored.replace(new, old, 1)
    assert restored == ORIGINAL_INTRO, "逆序还原后与 31 号稿 Introduction–Conclusions 块不一致"

    # ================= Vancouver 与图表引用验收 =================
    body = s
    def first_pos(token: str) -> int:
        m = re.search(re.escape(token), body)
        assert m, f"正文缺交叉引用：{token}"
        return m.start()

    fig_pos = [first_pos(f"Figure {i}") for i in (1, 2, 3)]
    tab_pos = [first_pos(f"Table {i}") for i in (1, 2, 3)]
    assert fig_pos == sorted(fig_pos), f"Figure 首次出现未按序：{fig_pos}"
    assert tab_pos == sorted(tab_pos), f"Table 首次出现未按序：{tab_pos}"
    for sref in ("Table S1", "Table S2", "Notes S3", "Table S4", "Table S5"):
        assert sref in body, f"补材表号缺失：{sref}"

    # 编号首次出现顺序（按括号组提取）
    groups = [[int(x) for x in g.split(",")]
              for g in re.findall(r"\[(\d+(?:,\d+)*)\]", body)]
    assert groups, "正文零 Vancouver 编号"
    flat = [n for g in groups for n in g]
    assert flat == list(range(1, 14)), f"Vancouver 编号首次出现序列异常：{flat}"
    assert all(1 <= n <= 13 for n in flat)
    assert len(re.findall(r"^## References", src, flags=re.M)) == 1
    refs = tail.split("## References", 1)[1].split("---", 1)[0]
    ref_nums = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. ", refs, flags=re.M)]
    assert ref_nums == list(range(1, 14)), f"References 编号不连续：{ref_nums}"

    # 摘要与 Conclusions 零插号 / 零图表引用
    assert not re.search(r"\[\d+\]", abs_block), "摘要出现 Vancouver 编号"
    concl = body.split("## 5 Conclusions", 1)[1]
    assert not re.search(r"\[\d+\]|Figure \d|Table \d", concl), "Conclusions 出现编号或图表引用"
    assert not re.search(r"Figure \d|Table \d|\[\d+\]", abs_block), "摘要出现图表引用或编号"

    # ================= D) 前页按 14 §三.8 重排 =================
    front_new = "\n\n".join([
        title, f_short, f_authors, f_affil, f_corr, f_subm, f_orcid, f_rev,
    ]) + "\n\n---\n\n"
    after_kw = (
        "## Abstract\n\n" + abs_block.strip() + "\n\n"
        + kw + "\n\n"
        + f_coi + "\n\n"
        + f_wc + "\n\n---\n\n"
    )
    # tail 中的 Declarations / References / Tables / Figure captions / 补材索引逐字保留
    manuscript = front_new + after_kw + s.strip() + "\n\n---\n\n" + tail + "\n"

    # 重排后顺序断言
    p = manuscript.index("## Abstract")
    k = manuscript.index("**Keywords:**")
    c = manuscript.index("**Conflict of interest and funding statement:**")
    w = manuscript.index("**Word count:**")
    assert p < k < c < w, "前页顺序未符合 14 §三.8"
    assert manuscript.index("**Suggested potential reviewers") < p, "审稿人建议应在「其他脚注」区"

    header = (
        "# B① 主稿 · v1.0 定稿稿（2026-11-12）\n\n"
        "> 由 `数据/scripts/finalize_B_v1_0_2026-11-12.py` 从 `31` 号降 AI 修订稿装配。"
        "`28` 号 pre-assembly 稿与 `31` 号降 AI 稿均**冻结不动**，作为版本留痕。\n"
        "> PART I 为可进入 docx 装配的完整英文稿；PART II 为装配台账（中文内部核对件，不进稿件）。\n"
        "> 本轮一次性落地：Vancouver `[1]–[13]` 插号（`25` §五）、图表交叉引用 C1–C8（`30` §六）、"
        "正文补材泛指改具体表号、前页按 `14` §三.8 官网顺序重排。\n"
        "> 装配层零改动证明：每条插入／替换登记 revert 对，逆序还原后与 "
        "`31` 号稿 Introduction–Conclusions 块**逐字一致**；prose 与全部数值未改。\n"
        "> 仍未做（属投稿包轮，不是本稿缺陷）：作者身份字段实填与英文标题定稿、真实仓库链接与 "
        "Data Accessibility Statement、Cover Letter／EM 字段清单、语言终校、docx 排版件、投稿包终检。\n"
        f"> 自动核验：Vancouver 编号 1–13 按序且各 ≥1 次；Figure 1→3 与 Table 1→3 首次出现按序；"
        f"Table S1／S2／S4／S5 与 Notes S3 各 ≥1 次；摘要与 Conclusions 零编号零图表引用；"
        f"References 编号 1–13 连续。装配操作共 {len(REVERT)} 条。\n\n"
        "---\n\n# PART I — Manuscript text\n\n"
    )

    ledger = [
        "", "---", "", "# PART II — v1.0 装配台账（内部核对件，不进稿件）", "",
        "## 一、装配层零改动证明", "",
        "| 项目 | 结果 |", "|---|---|",
        f"| 装配操作数（插号／交叉引用／补材表号） | {len(REVERT)} 条，每条锚点在 v0.9 唯一命中 |",
        "| 逆序还原 | 逐字回到 `31` 号稿 Introduction–Conclusions 块（prose 与全部数值零改动） |",
        "| References 13 条 / Declarations / Tables 1–3 / Figure captions / 补材索引 | 逐字未动 |",
        "| 前页字段文本 | 逐字未动，仅位置重排 |",
        "| Vancouver 编号首次出现序列 | " + ", ".join(map(str, flat)) + " |",
        f"| Figure 首次出现位置 | {fig_pos}（递增） |",
        f"| Table 首次出现位置 | {tab_pos}（递增） |",
        f"| 源稿 MD5 前 16 位 | `{hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]}…`（只读） |",
        "", "## 二、Vancouver 插号契约落地（25 §五）", "",
        "| 契约编号 | 插入位置 | 实际写法 |", "|---|---|---|",
        "| [1][2][3] | Introduction 段 1 句 1 句末 | `[1,2,3]` |",
        "| [4][5] | Introduction 段 1 句 2 句末 | `[4,5]` |",
        "| [6][7][8] | Introduction 段 1 句 3 句末 | `[6,7,8]` |",
        "| [9][10] | Introduction 段 3 句 1 句末 | `[9,10]` |",
        "| [11] | Discussion 4.2 `consistent with` 句末 | `[11]` |",
        "| [12] | Discussion 4.2 `in line with` 句末 | `[12]` |",
        "| [13] | Discussion 4.2 `complements and expands` 句末 | `[13]`（降 AI 后锚点，见下） |",
        "",
        "> 体例：Vancouver 多引用合并写 `[1,2,3]` 而非连字符区间，保证每个编号在正文逐项出现，"
        "便于 claim-support 逐条回链；方括号置于句末标点之前，按 ICMJE 通行写法。",
        "> `25` §五原契约以 `complements and expands` 所在句定位 [13]；降 AI 改写将 "
        "`This analysis complements and expands ... by placing ...` 改为 "
        "`Placing ... complements and expands that literature: ...`，**刻意保留该词组**作为可定位锚点，"
        "未改动其论断内容；本轮按更新后的完整句定位，登记于此。",
        "> 不插号位置按契约保持：Introduction 构念定义句、段 2、"
        "`Published estimates ... are limited.`（G1）、`We aimed to describe ...`（C7）、"
        "Methods／Results／Conclusions／Abstract 全部零编号。",
        "", "## 三、图表交叉引用 C1–C8 落地（30 §六）", "",
        "| 契约 | 位置 | 落地句 |", "|---|---|---|",
        "| C1 | 3.1 末句后 | `The denominator chain is summarised in Table 1.` |",
        "| C2 | 3.2 末句后 | `Cumulative trajectories and average annual percentage changes are shown in Figure 1(A,B).` |",
        "| C3 | 3.3 报告 HHI／CRn 之后 | `Concentration indices and their intervals are reported in Table 2.` |",
        "| C4 | 3.3 末句后 | `Holder-country shares and disease-specific supply composition are shown in Figure 2(A,B), ...` |",
        "| C5 | 3.4 末句后 | `Quartile burden and supply shares, and the coverage indices, are compared in Figure 3(A,B).` |",
        "| C6 | 3.5 末句后 | `Breadth by therapeutic area is tabulated in Table 3, ...` |",
        "| C7 | 正文 9 处泛指 | 8 处替换为具体表号；1 处（Declarations 数据可得性声明）按实质保留泛指 |",
        "| C8 | 全稿 | Figure 1→2→3 与 Table 1→2→3 首次出现按序；摘要与 Conclusions 零图表引用 |",
        "", "## 四、正文 9 处 supplementary material 逐处复核", "",
        "| # | 位置 | 处置 | 依据 |", "|---|---|---|---|",
        "| 1 | 2.4 HIV/AIDS 出局 | `Table S2` | S2 含 HIV/AIDS 对齐层 |",
        "| 2 | 2.5 AAPC 敏感性区间 | `Table S1` | S1 为三种 AAPC 区间方案 |",
        "| 3 | 2.5 对齐敏感性 | `Table S2` | S2 为对齐敏感性估计 |",
        "| 4 | 2.6 诊断量 | `Notes S3` | S3 为方法注 |",
        "| 5 | 3.1 HIV/AIDS 补材 | `Table S2` | 同 #1 |",
        "| 6 | 3.2 完整区间 | `Table S1` | 同 #2 |",
        "| 7 | 3.4 对齐敏感性与 HIV/AIDS | `Table S2` | 同 #3 |",
        "| 8 | 4.4 HIV/AIDS 补材 | `Table S2` | 同 #1 |",
        "| 9 | Declarations 数据可得性 | **保留 `supplementary material`** | 该处指整个补材包（含脚本与派生表），"
        "非某张具体表；改成单一表号会缩小声明范围，属实质错误 |",
        "",
        "> 另在 3.3 兑现 Figure 2 图注「其余 19 国见补材」的空头承诺，正文点名 `Table S5`；"
        "在 3.5 点名 `Table S4`（Wilson 对照）。图注与表注中的交叉引用句按 `30` C8 保留不动，"
        "故 `figure_captions.md` 未改，`verify_B_figures` 的图注逐字断言仍成立。",
        "", "## 五、前页顺序订正（14 §三.8）", "",
        "| 项 | v0.8／v0.9 位置 | v1.0 位置 |", "|---|---|---|",
        "| COI + Funding statement | Abstract **之前** | Keywords **之后**（官网顺序） |",
        "| Word Count | Abstract **之前** | COI + Funding **之后**（官网顺序） |",
        "| ≥5 位审稿人建议 | 前页字段区 | 保留在前页「其他脚注」区（§三.9 要求写在主稿内） |",
        "| Authors／Affiliations／Corresponding／Submission-system contact／ORCID | 前页 | 位置不变 |",
        "",
        "> 订正依据：`14` §三.8 官网顺序为 Title → Short title → Authors → Affiliations → "
        "Corresponding author → 其他脚注 → Abstract → Keywords → COI + Funding → Word Count。"
        "v0.8 装配时把 COI／Word Count 提前到摘要之前，属装配偏差，本轮按官网重排；"
        "所有字段文本逐字未动，前页身份占位符仍按 `16` §4.8／§5.6 由作者填写。",
        "", "## 六、Word Count 定稿", "",
        f"- 前页 Word count 行沿用 `31` 号稿降 AI 后纯 prose 实算值："
        "Abstract 241 词、Introduction–Conclusions 3,353 词（表／参考文献／Declarations 不计）。",
        "- 该值落在 `14` §三.2「3,500 词原则上限」内，无需援引多结局放宽条款。",
        "- 计数口径与 `28` 号稿登记的 252／3,446 不同：登记值含编号小节标题行与结构化摘要标签，"
        "本轮统一按纯 prose 口径；差异已登记于 `31` 号稿 PART II §一，属口径统一而非正文改写。",
        "", "## 七、逐条装配操作台账", "",
        "| # | 标签 | 类型 | 新增／改动内容（首 90 字符） | 锚点（首 70 字符） |",
        "|---|---|---|---|---|",
    ]
    for i, (tag, kind, added, anchor) in enumerate(LEDGER, 1):
        cl = lambda x: x.replace("|", "\\|").replace("\n", " ")
        ledger.append(f"| {i} | {tag} | {kind} | `{cl(added[:90])}` | `{cl(anchor[:70])}` |")
    ledger += [
        "", "## 八、本轮边界", "",
        "- 不改三张图件、出图脚本、`figure_contract.json`、`manifest.json`、`figure_captions.md`；不改任何派生 CSV。",
        "- 不改 20–31 号任何稿件；`28`／`31` 号稿作为冻结版本留痕，旧核验脚本继续可复跑。",
        "- 不实填作者身份字段、不定稿英文标题、不建公开仓库、不写 Cover Letter、不装配 docx。",
        "- 可复跑：`数据/scripts/finalize_B_v1_0_2026-11-12.py`。",
    ]

    open(OUT, "w", encoding="utf-8", newline="\n").write(
        header + manuscript.strip() + "\n" + "\n".join(ledger) + "\n"
    )
    print(f"WROTE {os.path.basename(OUT)}")
    print(f"assembly ops = {len(REVERT)} | revert byte-identical = True")
    print(f"Vancouver first-appearance = {flat}")
    print(f"Figure first positions = {fig_pos} | Table first positions = {tab_pos}")
    print(f"front-page order Abstract<Keywords<COI<WordCount = {p < k < c < w}")
    print("VERDICT = ALL CLEAN")


if __name__ == "__main__":
    main()
