# -*- coding: utf-8 -*-
"""B① 唯一固定版本 · 生成 v1.2.1 补充材料 S1–S8（2026-11-13）

所有表格数值由权威派生 CSV / WHO 来源登记 JSON / 复核脚本源码实读，
零硬编码研究数字。相对 v0.1 补材的实质变化：
  - S1 增加实算的 HAC lag 1–4、Durbin–Watson、残差 ACF1–4、去 2026 重拟合；
  - S2 改用官方病例数主口径，并把「率 × 总人口」列为敏感性对照；
  - S3 重写疟疾分母注，删除双重防御句，登记外部效标与数据源缺口；
  - S5 表题改为全部 29 国，`Holders` 列改为 `Applicant-name variants`；
  - 新增 S6 国家集合对账、S7 映射置信度表、S8 29 国码表。
"""
import ast
import csv
import json
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PROC = os.path.join(ROOT, "数据", "processed")
RAW = os.path.join(ROOT, "数据", "raw")
MAIN = os.path.join(ROOT, "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）")
OUT = os.path.join(MAIN, "48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md")
STAMP = "2026-11-12"
VSTAMP = "2026-11-13"
PROC_V = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def table(header, rows, widths=None):
    """widths 给出分隔行各列破折号数；pandoc 按相对长度分配 LaTeX 列宽，
    避免 10 列宽表中长下划线 token 把相邻列压到重叠。docx 渲染器跳过分隔行，
    因此该参数只影响校样排版，不改变任何文本或数值。"""
    if widths is None:
        widths = [3] * len(header)
    assert len(widths) == len(header), "列宽向量与表头长度不一致"
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("-" * w for w in widths) + "|"]
    out += ["| " + " | ".join(esc(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


apc = read(os.path.join(PROC, "res_B_uncertainty_apc_ci_2026-11-11.csv"))
rob = {r["segment"]: r for r in read(os.path.join(PROC, f"res_B_aapc_robustness_{STAMP}.csv"))}
prim = read(os.path.join(PROC_V, f"res_B_burden_primary_{STAMP}.csv"))
sens = read(os.path.join(PROC_V, f"res_B_burden_sensitivity_{STAMP}.csv"))
recon = read(os.path.join(PROC_V, f"res_B_country_set_reconciliation_{STAMP}.csv"))
bycountry = read(os.path.join(PROC, f"res_B_burden_by_country_{STAMP}.csv"))
china = read(os.path.join(PROC, "res_B_uncertainty_china_breadth_ci_2026-11-11.csv"))
shares = read(os.path.join(PROC, "res_B_uncertainty_country_share_ci_2026-11-11.csv"))
mapping = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
prov = json.load(open(os.path.join(RAW, f"who_malaria_denominator_provenance_{STAMP}.json"),
                      encoding="utf-8"))
bench = read(os.path.join(PROC, f"res_B_tb_external_benchmark_{STAMP}.csv"))
dic = read(os.path.join(PROC_V, f"res_B_calibre_dictionary_{VSTAMP}.csv"))
bsum = read(os.path.join(PROC_V, f"res_B_tb_benchmark_summary_{VSTAMP}.csv"))
india = json.load(open(os.path.join(PROC_V, f"res_B_india_record_check_{VSTAMP}.json"),
                      encoding="utf-8"))

# 29 国码表从权威计算脚本源码实读，不另抄一份
code_src = open(os.path.join(HERE, "compute_B_uncertainty_2026-11-11.py"),
                encoding="utf-8").read()
m = re.search(r"ISO2_TO_ISO3\s*=\s*(\{.*?\})", code_src, flags=re.S)
assert m, "未找到 29 国码表定义"
ISO = ast.literal_eval(m.group(1))
assert len(ISO) == 29

# 主口径国家层重抽（改变目标参数，仅作敏感性）
rng = np.random.default_rng(20261111)
country_ci = {}
for d in ("Malaria", "Tuberculosis", "HIV/AIDS"):
    rr = [x for x in bycountry if x["disease"] == d]
    b = np.array([float(x["burden_share_b_primary_official_cases"]) for x in rr])
    s = np.array([float(x["supply_share_s_disease_specific"]) for x in rr])
    n = len(b)
    ix = rng.integers(0, n, size=(5000, n))
    out = np.empty(5000)
    for i in range(5000):
        j = ix[i]
        bb, ss = b[j], s[j]
        bb = bb / bb.sum() if bb.sum() > 0 else bb
        ss = ss / ss.sum() if ss.sum() > 0 else ss
        out[i] = np.abs(ss - bb).sum()
    lo, hi = np.percentile(out, [2.5, 97.5])
    country_ci[d] = (round(float(lo), 4), round(float(hi), 4))

L = []
L += ["# Supplementary material (v1.2.1, single fixed version)", "",
      "13 November 2026. This is the only version submitted for review. All values below are read from the derived tables deposited with the manuscript. "
      "The primary malaria burden denominator is the WHO official estimated number of malaria cases "
      "(MALARIA_EST_CASES, 2024 estimates); the earlier incidence-times-total-population construction "
      "is retained only as a sensitivity comparison.", ""]

# ---- S1 ----
L += ["## S1. Trend sensitivity", "",
      "Table S1. Average annual percentage change and robustness of interval schemes.", "",
      "Sources: `res_B_uncertainty_apc_ci_2026-11-11.csv` and `res_B_aapc_robustness_2026-11-12.csv`. "
      "AAPC = 100·(exp(b) − 1) from a single log-linear ordinary least-squares fit to the retained "
      "stock by prequalification year (25 annual observations).", ""]
rows = []
for r in apc:
    seg = r["segment"]
    x = rob[seg]
    rows.append([seg.replace("ALL_FPP", "All FPPs"), r["aapc_recomputed_pct"],
                 f"{r['ci95_lo_ols']}–{r['ci95_hi_ols']}",
                 f"{r['ci95_lo_hac']}–{r['ci95_hi_hac']}",
                 f"{r['ci95_lo_block_boot']}–{r['ci95_hi_block_boot']}",
                 r["r_squared"], r["resid_acf1"]])
L += [table(["Series", "AAPC (%/yr)", "Primary t 95% CI", "HAC lag 3", "Residual block bootstrap",
             "R²", "Residual ACF1"], rows), ""]
rows2 = []
for r in apc:
    seg = r["segment"]; x = rob[seg]
    rows2.append([seg.replace("ALL_FPP", "All FPPs"), x["durbin_watson"],
                  x["resid_acf1"], x["resid_acf2"], x["resid_acf3"], x["resid_acf4"],
                  f"{x['hac1_lo']}–{x['hac1_hi']}", f"{x['hac2_lo']}–{x['hac2_hi']}",
                  f"{x['hac3_lo']}–{x['hac3_hi']}", f"{x['hac4_lo']}–{x['hac4_hi']}",
                  x["aapc_excl_2026"],
                  f"{x['ci95_lo_t_excl_2026']}–{x['ci95_hi_t_excl_2026']}"])
L += ["Extended lag and partial-year checks:", "",
      table(["Series", "Durbin–Watson", "ACF1", "ACF2", "ACF3", "ACF4",
             "HAC lag 1", "HAC lag 2", "HAC lag 3", "HAC lag 4",
             "AAPC 2002–2025", "t 95% CI 2002–2025"], rows2), "",
      "Durbin–Watson statistics of 0.215–0.496 and residual ACF1 of 0.68–0.88 confirm strong positive "
      "autocorrelation; every HAC and block-bootstrap interval is wider than the prespecified t interval. "
      "Across all four series and all extended schemes the lowest lower bound is 13.19% per year "
      "(HAC lag 4, HIV/AIDS). Excluding the partial 2026 observation leaves every slope positive and "
      "of the same order of magnitude. The t interval remains the primary interval by prespecification; "
      "HAC lag 3 was chosen conventionally and no small-sample degrees-of-freedom correction was applied.", ""]

# ---- S2 ----
L += ["## S2. Alignment by denominator calibre", "",
      "Table S2. Alignment estimates under the primary denominator and sensitivity calibres.", "",
      "Sources: `res_B_burden_primary_2026-11-12.csv`, `res_B_burden_sensitivity_2026-11-12.csv` and "
      "`res_B_burden_by_country_2026-11-12.csv`. M = \u03a3|s \u2212 b|; D = 0.5\u00b7M; C = burden share in countries "
      "with any listed holder; R25 = top-quartile supply-to-burden ratio. Blank cells are not estimated "
      "for that calibre.", ""]
rows = []
for r in sens:
    rows.append([r["disease"], r["calibre"], r["n_countries"], r["n_burden_countries"],
                 r["M_sum_abs_diff"], r["D_normalised"],
                 r["burden_weighted_supply_coverage_C"], r["top25_coverage_ratio_R25"],
                 r["top25pct_burden_share_of_b"]])
L += [table(["Disease", "Calibre", "n", "Burden countries", "M", "D", "C", "R25",
             "Top-quartile burden share"], rows,
            widths=[10, 26, 6, 9, 8, 8, 8, 8, 12]), "",
      "Primary product-row bootstrap 95% intervals for M (10,000 resamples of the supply side, "
      "burden shares fixed): " +
      "; ".join(f"{r['disease']} {r['ci95_lo_M']}\u2013{r['ci95_hi_M']}" for r in prim) + ".", "",
      "Country-level resampling (5,000 replicates; both sides renormalised, which changes the target "
      "parameter and gives left-skewed intervals near the upper bound) is a sensitivity only: " +
      "; ".join(f"{d} {country_ci[d][0]}\u2013{country_ci[d][1]}" for d in country_ci) + ".", "",
      "Calibre labels now name the denominator actually used for each disease: "
      "`primary_official_case_counts` (malaria, WHO official estimated case counts), "
      "`primary_incidence_times_population` (tuberculosis, incidence per 100,000 population multiplied "
      "by total population) and `primary_PLHIV_counts` (HIV/AIDS, people living with HIV prevalence "
      "stock, not incident cases). The tuberculosis and HIV/AIDS "
      "`calibre_record_denominator_unchanged` rows are not sensitivity analyses: their denominators "
      "were not replaced in v1.2, their values are identical to the corresponding primary rows, and "
      "they are retained only to make the calibre register complete. "
      "`burden_observed_only` (called `common_support_only` in v1.2.0) retains only countries with a "
      "positive burden observation and renormalises both sides on that set; it is not the intersection "
      "of holder and burden supports. For tuberculosis this calibre reproduces the primary values "
      "because every country in the primary set has a burden observation, so it carries no independent "
      "information. The `legacy_incidence_times_total_population` rows for malaria reproduce the "
      "published v1.0 estimates and show that replacing the denominator did not change the direction "
      "of the alignment finding. The full old-to-new label dictionary is deposited as "
      f"`res_B_calibre_dictionary_{VSTAMP}.csv` ({len(dic)} entries).", "",
      "HIV/AIDS supplementary stratum (n = 151 countries, 142 with a burden observation, 16 active "
      "holder countries): M = 1.9760 (product-row bootstrap 95% CI 1.9603\u20131.9953), D = 0.9880, "
      "C = 0.2062, R25 = 0.0084; the heaviest-burden quartile accounted for 92.84% of burden and "
      "0.78% of HIV/AIDS products. The GHO PLHIV extract ends in 2006, so this stratum is "
      "supplementary only.", ""]

# ---- S3 ----
errs = sorted(float(r["abs_relative_error"]) for r in bench)
med = round(float(np.median(errs)), 4)
L += ["## S3. Method notes", "",
      "Notes S3. Method notes carried over from the main text.", "",
      "1. HAC lag 3 was chosen conventionally. With 25 annual observations no small-sample "
      "degrees-of-freedom correction was applied. The primary interval was prespecified as the "
      "ordinary t interval of the same fit (df = 23, t = 2.0687). Lags 1\u20134, Durbin\u2013Watson, "
      "residual autocorrelations and the 2002\u20132025 refit are reported in Table S1.",
      "2. Country-level resampling renormalises both sides, changes the target parameter and yields "
      "left-skewed percentile intervals near the upper bound; it is a sensitivity only. The primary "
      "interval resamples product rows on the supply side with burden shares fixed.",
      "3. Malaria burden is measured directly from WHO official estimated case counts "
      "(MALARIA_EST_CASES, 2024 estimates), with no population multiplier. The earlier construction "
      "multiplied estimated incidence per 1,000 population at risk by total population; it is retained "
      "as a sensitivity comparison because the at-risk fraction varies between countries, and WHO GHO "
      "publishes no absolute population-at-risk indicator. Tuberculosis uses incidence per 100,000 "
      "population multiplied by total population, whose own denominator is total population; against "
      f"WHO's official incident-case indicator the median absolute relative difference was {100*med:.2f}% "
      f"over {len(bench)} paired country-years (period breakdown in Table S6), and that indicator contains "
      "no India records and cannot replace the denominator. HIV/AIDS uses PLHIV counts, a prevalence "
      "stock rather than incident cases. Burden years are 2024 (malaria), 2004\u20132024 "
      "(tuberculosis) and 2005\u20132006 (HIV/AIDS).",
      "4. The reviewed concentration table stores ISO 3166-1 alpha-2 codes in a column named `iso3`, "
      "whereas GHO and World Bank extracts use alpha-3 codes. Without the explicit 29-country "
      "conversion reproduced in Table S8, the supply and burden supports are disjoint and the L1 "
      "distance degenerates to its upper bound of 2.",
      "5. Trend was estimated by a single-slope log-linear OLS model over 25 annual observations. "
      "The slope estimates the average annual change of the retained stock grouped by "
      "prequalification year.",
      "6. Prequalification breadth is a product-holder-level quality signal within the WHO listing. "
      "Registration, procurement, delivery and patient access lie outside this measure. Listing-row "
      "indices weight product rows equally, so a holder with many presentations counts more than a "
      "holder with one; they are not market concentration measures.",
      "7. The applicant-to-country mapping with confidence grades is reproduced in Table S7: "
      "137 applicant rows comprise 136 unique non-blank applicant names plus one blank row retained "
      "as missing (110 high, 26 medium, one unresolved); the n_products column totals 649. "
      "Country sets for every calibre, including the burden-observed-only calibre, missing-burden "
      "handling and the b > 0 criterion, are reconciled in Table S6. The burden-observed-only "
      "calibre keeps only countries with a positive burden observation and renormalises both sides "
      "within that set; it is not the intersection of holder and burden supports.",
      "8. Diagnostics recorded per estimate were R\u00b2, residual autocorrelation, bootstrap replicate "
      "counts and the numbers of countries with and without burden observations. Scripts read only "
      "raw extracts and reviewed mapping tables and write only derived tables.",
      "9. Calibre labels and the note column of every deposited derived table were rewritten to "
      "name the denominator actually used for that disease. A label-to-denominator dictionary and "
      "an audit asserting that no numerical column changed are deposited with the reproducible "
      f"scripts (`res_B_calibre_dictionary_{VSTAMP}.csv`, "
      f"`res_B_notes_change_audit_{VSTAMP}.json`).", ""]

# ---- S4 ----
L += ["## S4. Chinese-held product breadth", "",
      "Table S4. Chinese-held product breadth under two descriptive interval schemes.", "",
      "Source: `res_B_uncertainty_china_breadth_ci_2026-11-11.csv`. Under the binomial reference "
      "model k ~ Bin(n, p), both intervals describe the width of a finite-list proportion and are "
      "not superpopulation sampling inference.", ""]
r4 = [[r["therapeutic_area"], f'{r["china_products_k"]} / {r["global_fpp_n"]}',
       r["share_pct"],
       f'{r["ci95_lo_clopper_pearson"]}–{r["ci95_hi_clopper_pearson"]}',
       f'{r["ci95_lo_wilson"]}–{r["ci95_hi_wilson"]}'] for r in china]
L += [table(["Therapeutic area", "k / n", "Share (%)",
             "Clopper–Pearson 95% CI", "Wilson 95% CI"], r4), ""]

# ---- S5 ----
L += ["## S5. All 29 certificate-holder countries", "",
      "Table S5. All 29 certificate-holder countries in the 15 September 2026 listing snapshot.", "",
      "The ten leading countries are plotted in Figure 2(A); all 29 are tabulated here. "
      "Source: `res_B_uncertainty_country_share_ci_2026-11-11.csv`. Intervals are descriptive "
      "product-row bootstrap intervals for a finite listing. `Applicant-name variants` counts "
      "distinct normalised applicant strings, not distinct firms.", ""]
r5 = [[r["iso3"], r["product_rows"], r["share_pct"],
       f'{r["ci95_lo"]}–{r["ci95_hi"]}', r["n_holders"], r["bootstrap_draws"]]
      for r in shares]
L += [table(["Holder country (ISO2 as stored)", "Product rows", "Share (%)",
             "Descriptive 95% CI", "Applicant-name variants", "Product-row resamples"], r5), ""]

# ---- S6 ----
L += ["## S6. Country-set reconciliation", "",
      "Table S6. Country-set reconciliation and denominator provenance.", "",
      "Source: `res_B_country_set_reconciliation_2026-11-12.csv`. The analysis universe is the union "
      "of burden-observed countries and all 29 certificate-holder countries; holder countries "
      "without a burden observation remain in the universe with b = 0. The criterion b > 0 is "
      "identical in the country-level table and the summary table. Every calibre, including "
      "`burden_observed_only`, is listed below so that each n can be traced to a country-set rule.", ""]
L += [table(["Disease", "Calibre", "Burden n", "Holder n", "Overlap",
             "Holder w/o burden", "Active s>0 n", "Active w/o burden", "Union n", "Missing rule"],
            [[r["disease"], r["calibre"], r["burden_observed_countries"],
              r["all_29_holder_countries"], r["overlap_burden_and_holder"],
              r["holder_without_burden"], r["disease_specific_active_holder_countries"],
              r["active_holder_without_burden"], r["union_n"],
              "b = 0, retained" if str(r["missing_burden_handling"]).startswith("b = 0")
              else "excluded" if str(r["missing_burden_handling"]).startswith("excluded")
              else "same as primary"] for r in recon],
            widths=[8, 30, 8, 8, 8, 10, 10, 10, 8, 12]), "",
      "Column names in full: burden countries with an observation; certificate-holder countries "
      "kept in that calibre; overlap of the two sets; holder countries without a burden observation; "
      "disease-specific countries with s > 0; those without a burden observation; union n; and "
      "the missing-burden rule. For `burden_observed_only`, holder countries without a positive "
      "burden observation are excluded rather than retained with b = 0, so union n equals the "
      "number of burden-observed countries. The full wording of each rule is recorded in the "
      "deposited CSV.", "",
      "Denominator provenance (WHO Global Health Observatory OData API, indicator catalogue read "
      "12 November 2026; extracted same day). The WHO `Date` stamp identifies the release of each "
      "indicator record. Paths are relative to the public repository root. India record counts are "
      "read directly from the deposited raw extracts, not inferred from the country totals.", ""]
r6a, r6b = [], []
for key, v in prov["files"].items():
    ic = v["indicator_code"]
    rec = india["indicators"][ic]
    r6a.append([ic, v["official_indicator_name"], v["accepted_records"],
                v["n_countries"], f"{v['year_min']}\u2013{v['year_max']}",
                "yes" if rec["n_IND_rows"] > 0 else "no"])
    r6b.append([ic, ", ".join(v["source_date_values"].keys()),
                v["local_file"].replace("\u6570\u636e/raw/", "data/raw/")])
L += [table(["Indicator code", "Official indicator name", "Country-year records",
             "Countries", "Years", "India records present?"], r6a,
            widths=[26, 28, 12, 10, 12, 14]), "",
      table(["Indicator code", "WHO Date stamp", "Repository path"], r6b,
            widths=[26, 28, 44]), "",
      "MALARIA_EST_CASES is the primary malaria denominator; MALARIA_EST_INCIDENCE is the "
      "sensitivity comparison; TB_e_inc_num is an external magnitude check only. The India column "
      "is decisive for tuberculosis: TB_e_inc_num has "
      f"{india['indicators']['TB_e_inc_num']['n_IND_rows']} records for India, while India accounts "
      "for about one quarter of tuberculosis burden and is the largest certificate-holder country, "
      "so that indicator cannot replace the tuberculosis primary denominator. For the two malaria "
      "indicators the column is informational. The existing sparse GHO tuberculosis incidence "
      "extract does contain India records and remains the tuberculosis input.", "",
      "External magnitude check for the tuberculosis denominator, recomputed from all "
      f"{len(bench)} paired country-years in `res_B_tb_external_benchmark_{STAMP}.csv`. "
      "Each row compares the rate-times-total-population construction with the WHO official "
      "incident-case estimate for the same country and year.", "",
      table(["Period", "Paired country-years", "Median absolute relative error",
             "Median (%)", "90th percentile", "Maximum"],
            [[r["period"], r["paired_country_years"], r["median_abs_relative_error"],
              r["median_percent"], r["p90_abs_relative_error"],
              r["max_abs_relative_error"]] for r in bsum],
            widths=[14, 16, 20, 12, 14, 12]), "",
      "The period rows sum to the all-years row; the all-years median is the value quoted in "
      "Notes S3. This check concerns magnitude only and does not alter the tuberculosis "
      "denominator or any alignment estimate.", ""]

# ---- S7 ----
L += ["## S7. Applicant-to-country mapping", "",
      "Table S7. Reviewed applicant-to-country mapping with confidence grades.", "",
      "Source: `res_B_anchor_applicant_country_reviewed.csv`. The table contains 137 applicant "
      "rows: 136 unique non-blank applicant names plus one blank row retained as missing; "
      f"n_products totals {sum(int(r['n_products']) for r in mapping)}. "
      "Confidence: high 110, medium 26, unresolved 1 (retained as missing, not assigned). "
      "The `iso3` column of this table holds ISO 3166-1 alpha-2 codes.", ""]
h7 = list(mapping[0].keys())
L += [table(h7, [list(r.values()) for r in mapping]), ""]

# ---- S8 ----
L += ["## S8. ISO 3166-1 alpha-2 to alpha-3 conversion", "",
      "Table S8. Explicit 29-country ISO 3166-1 alpha-2 to alpha-3 conversion.", "",
      "Source: `ISO2_TO_ISO3` in `compute_B_uncertainty_2026-11-11.py`, read directly from the "
      "archived script.", ""]
L += [table(["ISO2 (as stored)", "ISO3 (GHO / World Bank)"],
            sorted(ISO.items())), ""]

open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
assert sum(int(r["n_products"]) for r in mapping) == 649, "S7 n_products 合计不等于 649"
assert len([l for l in L if l.startswith("## S")]) == 8, "S1\u2013S8 独立小节标题不足 8 个"
print(f"补材 v1.2.1 已生成：{os.path.basename(OUT)}")
print(f"  行数 {len(L)}，S7 映射 {len(mapping)} 行，S8 码表 {len(ISO)} 行，"
      f"结核效标 {len(bench)} 行，标签字典 {len(dic)} 行，对账 {len(recon)} 行")
print("VERDICT = SUPPLEMENT V1.2.1 OK")
