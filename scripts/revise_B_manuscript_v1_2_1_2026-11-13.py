# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · 主稿修订（2026-11-13）

从冻结的 39 号 v1.2 主稿派生 49 号 v1.2.1 主稿。只改：
  - 名称变体计数的措辞（136 非空唯一名称 + 1 空白缺失行；不再把变体数与企业数并列）
  - 补材索引对已改名口径、India 留痕与效标小表的描述
  - 数据可得性声明的固定版本链接（v1.2.0 -> v1.2.1）
  - Word count 按同一纯 prose 口径实算回填
不改任何统计数值、不改结论方向、不重跑分析、不回写 39 号冻结件。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAIN = os.path.join(ROOT, "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）")
SRC = os.path.join(MAIN, "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md")
OUT = os.path.join(MAIN, "49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md")
AUDIT = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13",
                     "res_B_manuscript_v1_2_1_change_audit.json")

raw = open(SRC, encoding="utf-8").read()
part1 = raw.split("# PART II", 1)[0].rstrip() + "\n"
text = part1
changes = []


def replace_exact(old, new, label, note=""):
    global text
    n = text.count(old)
    assert n == 1, f"{label} 命中 {n} 次（应为 1）：{old[:100]!r}"
    text = text.replace(old, new)
    changes.append({"item": label, "before": old, "after": new, "note": note})


def prose_words(block):
    body = "\n".join(l for l in block.splitlines()
                     if not re.match(r"^\s{0,3}#{1,6}\s", l))
    return len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body))


def prose_counts(p):
    abstract = prose_words(p.split("## Abstract", 1)[1].split("---", 1)[0])
    imrd = prose_words(p.split("## 1 Introduction", 1)[1].split("## Declarations", 1)[0])
    return imrd, abstract


old_imrd, old_abs = prose_counts(part1)
assert (old_imrd, old_abs) == (3491, 300), f"v1.2 基线词数异常：{old_imrd}/{old_abs}"

# ---- 1) Methods 2.3：名称变体计数与企业数脱钩 ----
replace_exact(
    "Country attribution was defined at certificate-holder level from the free-text Applicant field. "
    "Names were normalised by rule, graded for confidence and reviewed where ambiguous; the reviewed "
    "mapping contains 137 applicant rows with 137 unique names covering all 649 product rows, of which "
    "110 assignments were graded high, 26 medium and one remained unresolved and was retained as "
    "missing rather than assigned. Sixteen Chinese applicant-name variants resolved to approximately "
    "15 firms.",
    "Country attribution was defined at certificate-holder level from the free-text Applicant field. "
    "Names were normalised, graded and reviewed; the reviewed mapping contains 137 applicant rows "
    "(136 unique non-blank names plus one blank row retained as missing) covering all 649 product "
    "rows, of which 110 assignments were graded high, 26 medium and one unresolved. Sixteen distinct "
    "Chinese applicant-name strings were recorded; these are name variants, not a count of firms.",
    "Methods 2.3 名称变体计数", "137 行 = 136 非空唯一名称 + 1 空白缺失行；不再声称约 15 家企业")

# ---- 2) Results 3.3 ----
replace_exact(
    "represented by 16 applicant-name variants resolving to approximately 15 firms",
    "represented by 16 distinct applicant-name strings",
    "Results 3.3 中国持证商表述", "去掉与家数并列的措辞")

# ---- 3) Discussion 4.x ----
replace_exact(
    "The 649 product rows were mapped through 137 applicant rows (137 unique names, 110 "
    "high-confidence, 26 medium, one unresolved retained as missing), and 16 Chinese name variants "
    "resolved to approximately 15 firms;",
    "The 649 product rows were mapped through 137 applicant rows (136 unique non-blank names plus "
    "one blank row, 110 high-confidence, 26 medium, one unresolved), including 16 distinct Chinese "
    "applicant-name strings recorded as name variants rather than a firm count;",
    "Discussion 名称变体计数", "与 Methods 2.3、Table S7 表注同口径")

# ---- 4) 数据可得性声明：唯一固定版本 ----
replace_exact(
    "(release v1.2.0: https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit/"
    "tree/v1.2.0). Release v1.0.0 is retained unchanged as the historical version of the earlier "
    "denominator.",
    "(release v1.2.1: https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit/"
    "tree/v1.2.1). Releases v1.0.0 and v1.2.0 are retained unchanged as historical versions.",
    "Declarations 数据可得性", "固定版本改指 v1.2.1；两个旧版本登记为历史版本")

# ---- 5) 补材索引同步 ----
replace_exact(
    "| Table S2 | Alignment sensitivity estimates (country-level bootstrap, common support, "
    "second-latest burden year, total-population malaria denominator; supplementary HIV/AIDS stratum) |",
    "| Table S2 | Alignment estimates under the primary denominator and sensitivity calibres "
    "(country-level bootstrap, burden-observed-only calibre, second-latest burden year, "
    "total-population malaria denominator; supplementary HIV/AIDS stratum) |",
    "补材索引 Table S2", "口径改名 burden_observed_only")

replace_exact(
    "| Notes S3 | Method notes on the primary and comparison malaria denominators, interval schemes, "
    "ISO code conversion, country-set reconciliation and the limits of listing-row indices |",
    "| Notes S3 | Method notes on the primary and comparison denominators, interval schemes, ISO code "
    "conversion, country-set reconciliation, the calibre label dictionary and the limits of "
    "listing-row indices |",
    "补材索引 Notes S3", "登记标签字典与按病种写实的方法注")

replace_exact(
    "| Table S6 | Country-set reconciliation for every calibre, including the WHO official malaria "
    "denominator and its total-population sensitivity |",
    "| Table S6 | Country-set reconciliation for every calibre including the burden-observed-only "
    "calibre, WHO denominator provenance with an India-record check, and the tuberculosis external "
    "magnitude benchmark |",
    "补材索引 Table S6", "登记新增对账行、India 列与效标小表")

replace_exact(
    "| Table S7 | Reviewed applicant-to-country mapping with confidence grades (137 rows) |",
    "| Table S7 | Reviewed applicant-to-country mapping with confidence grades (137 rows; 136 unique "
    "non-blank names plus one blank row; 649 product rows) |",
    "补材索引 Table S7", "与表注同口径")

# ---- 6) 词数：同一纯 prose 口径实算，必要时定向压缩 ----
new_imrd, new_abs = prose_counts(text)
if new_imrd > 3500:
    replace_exact(
        "Names were normalised, graded and reviewed; the reviewed mapping contains 137 applicant rows",
        "Names were normalised and graded; the mapping contains 137 applicant rows",
        "词数压缩", f"改写后 {new_imrd} 词超 3,500 上限，压缩 Methods 2.3 一处措辞")
    new_imrd, new_abs = prose_counts(text)
assert new_imrd <= 3500, f"正文 {new_imrd} 词，超过 TMIH 3,500 词上限"
assert new_abs == old_abs == 300, f"摘要词数被改动：{new_abs}"

replace_exact(
    f"**Word count:** {old_imrd} words of manuscript text (Introduction–Conclusions), "
    f"{old_abs} words in the structured abstract; tables, references and declarations excluded.",
    f"**Word count:** {new_imrd} words of manuscript text (Introduction–Conclusions), "
    f"{new_abs} words in the structured abstract; tables, references and declarations excluded.",
    "Word count 回填", f"同一口径实算 {old_imrd} -> {new_imrd}")

# ---- 7) 断言：统计数值零改动 ----
NUM_TOKENS = ("4175.53", "3737.94–4643.50", "63.73%", "1.9225", "1.8613–1.9634",
              "0.3082", "0.0652", "93.92%", "6.12%", "102 (81)", "13.19%",
              "1.3983", "0.5174", "0.9535", "1.9760", "0.2062", "0.0084",
              "24.85", "14.75", "18.28", "19.11", "649", "648")
p1_old = part1.split("## Declarations", 1)[0]
p1_new = text.split("## Declarations", 1)[0]
for tok in NUM_TOKENS:
    assert abs(p1_old.count(tok) - p1_new.count(tok)) <= 1, \
        f"统计数值 token {tok} 命中次数变化异常"
for tok in ("137 unique names", "approximately 15 firms", "common support", "release v1.2.0"):
    assert tok not in text.split("# PART II", 1)[0], f"旧措辞残留：{tok}"
assert "release v1.2.1" in text and "/tree/v1.2.1" in text

# ---- 8) 输出：PART I + 简短内部留痕（docx 装配只取 PART I） ----
ledger = """
# PART II — v1.2.1 版本留痕（内部核对件，不进稿件）

本文件是唯一送审版本的正文源。相对 v1.2 的变化全部为标签、定义、措辞、留痕与排版，
不重跑分析、不改动任何统计数值、结论方向不变。逐处替换如下。

| 位置 | 修改前 | 修改后 | 说明 |
|---|---|---|---|
"""
for c in changes:
    b = c["before"].replace("|", "\\|").replace("\n", " ")
    a = c["after"].replace("|", "\\|").replace("\n", " ")
    ledger += f"| {c['item']} | {b[:150]} | {a[:150]} | {c['note']} |\n"
ledger += f"""
- 纯 prose 词数（同一口径）：正文 {old_imrd} -> {new_imrd}，摘要 {old_abs} -> {new_abs}；上限 3,500 词。
- 固定版本：v1.2.1；v1.0.0 与 v1.2.0 作为历史版本保留，不再随送审包提交。
- 历史主稿与历史补充材料已移入归档目录，送审目录只保留本版本主稿、补充材料、图件、清单与哈希。
"""
open(OUT, "w", encoding="utf-8").write(text.rstrip() + "\n" + ledger)

os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
json.dump({
    "version": "v1.2.1",
    "source": os.path.basename(SRC),
    "output": os.path.basename(OUT),
    "scope": "wording, definitions, traceability and fixed-version link only",
    "word_count_imrd": {"before": old_imrd, "after": new_imrd, "limit": 3500},
    "word_count_abstract": {"before": old_abs, "after": new_abs},
    "replacements": [{"item": c["item"], "note": c["note"]} for c in changes],
    "assertions": ["no statistical value changed", "no old denominator wording remains",
                   "fixed-version link points to v1.2.1", "word count within journal limit"],
}, open(AUDIT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"v1.2.1 主稿已生成：{os.path.basename(OUT)}")
print(f"  替换 {len(changes)} 处 | 正文 {old_imrd} -> {new_imrd} 词 | 摘要 {new_abs} 词")
print(f"  变更留痕 -> {os.path.relpath(AUDIT, ROOT)}")
print("VERDICT = MANUSCRIPT V1.2.1 OK")
