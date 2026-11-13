# -*- coding: utf-8 -*-
"""派生 v1.2.1 补材生成脚本并运行。

从冻结的 build_B_supplement_v1_2_2026-11-12.py 读取源码，按块精确替换后
写出独立的 build_B_supplement_v1_2_1_2026-11-13.py（可读、可复跑），再执行它。
本轮只改标签、定义、措辞、小节标题与留痕表，不改任何统计数值。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "build_B_supplement_v1_2_2026-11-12.py")
DST = os.path.join(HERE, "build_B_supplement_v1_2_1_2026-11-13.py")

code = open(SRC, encoding="utf-8").read()


def rep(old, new, n=1):
    global code
    assert code.count(old) == n, f"替换锚点命中 {code.count(old)} 次（应为 {n}）：{old[:90]!r}"
    code = code.replace(old, new)


def block(start, end, new):
    """用新块替换 start 与 end 之间的源码（含 start，不含 end）。"""
    global code
    i = code.index(start)
    j = code.index(end, i)
    code = code[:i] + new + code[j:]


# ---- 头部与路径 ----
rep('"""B① 返修 · 生成 v1.2 补充材料 S1–S8（2026-11-12）',
    '"""B① 唯一固定版本 · 生成 v1.2.1 补充材料 S1–S8（2026-11-13）')
rep('OUT = os.path.join(MAIN, "40_B①主稿_补充材料_v1.2_S1-S8_2026-11-12.md")',
    'OUT = os.path.join(MAIN, "48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md")')
rep('STAMP = "2026-11-12"\n',
    'STAMP = "2026-11-12"\n'
    'VSTAMP = "2026-11-13"\n'
    'PROC_V = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13")\n')

rep('prim = read(os.path.join(PROC, f"res_B_burden_primary_{STAMP}.csv"))\n'
    'sens = read(os.path.join(PROC, f"res_B_burden_sensitivity_{STAMP}.csv"))\n'
    'recon = read(os.path.join(PROC, f"res_B_country_set_reconciliation_{STAMP}.csv"))',
    'prim = read(os.path.join(PROC_V, f"res_B_burden_primary_{STAMP}.csv"))\n'
    'sens = read(os.path.join(PROC_V, f"res_B_burden_sensitivity_{STAMP}.csv"))\n'
    'recon = read(os.path.join(PROC_V, f"res_B_country_set_reconciliation_{STAMP}.csv"))')

rep('bench = read(os.path.join(PROC, f"res_B_tb_external_benchmark_{STAMP}.csv"))\n',
    'bench = read(os.path.join(PROC, f"res_B_tb_external_benchmark_{STAMP}.csv"))\n'
    'dic = read(os.path.join(PROC_V, f"res_B_calibre_dictionary_{VSTAMP}.csv"))\n'
    'bsum = read(os.path.join(PROC_V, f"res_B_tb_benchmark_summary_{VSTAMP}.csv"))\n'
    'india = json.load(open(os.path.join(PROC_V, f"res_B_india_record_check_{VSTAMP}.json"),\n'
    '                      encoding="utf-8"))\n')

rep('L += ["# B① Manuscript — Supplementary material (v1.2)", "",\n'
    '      "12 November 2026. All values below are read from the derived tables deposited with the manuscript. "',
    'L += ["# Supplementary material (v1.2.1, single fixed version)", "",\n'
    '      "13 November 2026. This is the only version submitted for review. All values below are read from the derived tables deposited with the manuscript. "')

# ---- 八个小节：独立标题（以 S 编号起首）+ 表题文字 ----
rep('L += ["## Table S1. Average annual percentage change and robustness of interval schemes", "",',
    'L += ["## S1. Trend sensitivity", "",\n'
    '      "Table S1. Average annual percentage change and robustness of interval schemes.", "",')
rep('L += ["## Notes S3. Method notes carried over from the main text", "",',
    'L += ["## S3. Method notes", "",\n'
    '      "Notes S3. Method notes carried over from the main text.", "",')
rep('L += ["## Table S4. Chinese-held product breadth under two descriptive interval schemes", "",',
    'L += ["## S4. Chinese-held product breadth", "",\n'
    '      "Table S4. Chinese-held product breadth under two descriptive interval schemes.", "",')
rep('L += ["## Table S5. All 29 certificate-holder countries in the 15 September 2026 listing snapshot", "",',
    'L += ["## S5. All 29 certificate-holder countries", "",\n'
    '      "Table S5. All 29 certificate-holder countries in the 15 September 2026 listing snapshot.", "",')
rep('L += ["## Table S7. Reviewed applicant-to-country mapping with confidence grades", "",',
    'L += ["## S7. Applicant-to-country mapping", "",\n'
    '      "Table S7. Reviewed applicant-to-country mapping with confidence grades.", "",')
rep('L += ["## Table S8. Explicit 29-country ISO 3166-1 alpha-2 to alpha-3 conversion", "",',
    'L += ["## S8. ISO 3166-1 alpha-2 to alpha-3 conversion", "",\n'
    '      "Table S8. Explicit 29-country ISO 3166-1 alpha-2 to alpha-3 conversion.", "",')

# ---- S2 整块 ----
S2_NEW = '''# ---- S2 ----
L += ["## S2. Alignment by denominator calibre", "",
      "Table S2. Alignment estimates under the primary denominator and sensitivity calibres.", "",
      "Sources: `res_B_burden_primary_2026-11-12.csv`, `res_B_burden_sensitivity_2026-11-12.csv` and "
      "`res_B_burden_by_country_2026-11-12.csv`. M = \\u03a3|s \\u2212 b|; D = 0.5\\u00b7M; C = burden share in countries "
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
      "; ".join(f"{r['disease']} {r['ci95_lo_M']}\\u2013{r['ci95_hi_M']}" for r in prim) + ".", "",
      "Country-level resampling (5,000 replicates; both sides renormalised, which changes the target "
      "parameter and gives left-skewed intervals near the upper bound) is a sensitivity only: " +
      "; ".join(f"{d} {country_ci[d][0]}\\u2013{country_ci[d][1]}" for d in country_ci) + ".", "",
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
      "holder countries): M = 1.9760 (product-row bootstrap 95% CI 1.9603\\u20131.9953), D = 0.9880, "
      "C = 0.2062, R25 = 0.0084; the heaviest-burden quartile accounted for 92.84% of burden and "
      "0.78% of HIV/AIDS products. The GHO PLHIV extract ends in 2006, so this stratum is "
      "supplementary only.", ""]

'''
block("# ---- S2 ----", "# ---- S3 ----", S2_NEW)

# ---- S3 整块（保留 1-6、8，重写 7，新增 9） ----
S3_NEW = '''# ---- S3 ----
errs = sorted(float(r["abs_relative_error"]) for r in bench)
med = round(float(np.median(errs)), 4)
L += ["## S3. Method notes", "",
      "Notes S3. Method notes carried over from the main text.", "",
      "1. HAC lag 3 was chosen conventionally. With 25 annual observations no small-sample "
      "degrees-of-freedom correction was applied. The primary interval was prespecified as the "
      "ordinary t interval of the same fit (df = 23, t = 2.0687). Lags 1\\u20134, Durbin\\u2013Watson, "
      "residual autocorrelations and the 2002\\u20132025 refit are reported in Table S1.",
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
      "stock rather than incident cases. Burden years are 2024 (malaria), 2004\\u20132024 "
      "(tuberculosis) and 2005\\u20132006 (HIV/AIDS).",
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
      "8. Diagnostics recorded per estimate were R\\u00b2, residual autocorrelation, bootstrap replicate "
      "counts and the numbers of countries with and without burden observations. Scripts read only "
      "raw extracts and reviewed mapping tables and write only derived tables.",
      "9. Calibre labels and the note column of every deposited derived table were rewritten to "
      "name the denominator actually used for that disease. A label-to-denominator dictionary and "
      "an audit asserting that no numerical column changed are deposited with the reproducible "
      f"scripts (`res_B_calibre_dictionary_{VSTAMP}.csv`, "
      f"`res_B_notes_change_audit_{VSTAMP}.json`).", ""]

'''
block("# ---- S3 ----", "# ---- S4 ----", S3_NEW)

# ---- S6 整块 ----
S6_NEW = '''# ---- S6 ----
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
                v["n_countries"], f"{v['year_min']}\\u2013{v['year_max']}",
                "yes" if rec["n_IND_rows"] > 0 else "no"])
    r6b.append([ic, ", ".join(v["source_date_values"].keys()),
                v["local_file"].replace("\\u6570\\u636e/raw/", "data/raw/")])
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

'''
block("# ---- S6 ----", "# ---- S7 ----", S6_NEW)

# ---- S7 表注 ----
rep('      "Source: `res_B_anchor_applicant_country_reviewed.csv` (137 rows, 137 unique applicant names). "\n'
    '      "Confidence: high 110, medium 26, unresolved 1 (retained as missing, not assigned). "\n'
    '      "The `iso3` column of this table holds ISO 3166-1 alpha-2 codes.", ""',
    '      "Source: `res_B_anchor_applicant_country_reviewed.csv`. The table contains 137 applicant "\n'
    '      "rows: 136 unique non-blank applicant names plus one blank row retained as missing; "\n'
    '      f"n_products totals {sum(int(r[\'n_products\']) for r in mapping)}. "\n'
    '      "Confidence: high 110, medium 26, unresolved 1 (retained as missing, not assigned). "\n'
    '      "The `iso3` column of this table holds ISO 3166-1 alpha-2 codes.", ""')

# ---- 收尾 ----
rep('print(f"补材 v1.2 已生成：{os.path.basename(OUT)}")',
    'assert sum(int(r["n_products"]) for r in mapping) == 649, "S7 n_products 合计不等于 649"\n'
    'assert len([l for l in L if l.startswith("## S")]) == 8, "S1\\u2013S8 独立小节标题不足 8 个"\n'
    'print(f"补材 v1.2.1 已生成：{os.path.basename(OUT)}")')
rep('print(f"  行数 {len(L)}，S7 映射 {len(mapping)} 行，S8 码表 {len(ISO)} 行，"\n'
    '      f"结核效标 {len(bench)} 行")',
    'print(f"  行数 {len(L)}，S7 映射 {len(mapping)} 行，S8 码表 {len(ISO)} 行，"\n'
    '      f"结核效标 {len(bench)} 行，标签字典 {len(dic)} 行，对账 {len(recon)} 行")')
rep('print("VERDICT = SUPPLEMENT V1.2 OK")',
    'print("VERDICT = SUPPLEMENT V1.2.1 OK")')

open(DST, "w", encoding="utf-8").write(code)
print("已派生", os.path.basename(DST))
r = subprocess.run([sys.executable, DST], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip())
if r.returncode:
    print(r.stderr.strip())
    sys.exit(r.returncode)
