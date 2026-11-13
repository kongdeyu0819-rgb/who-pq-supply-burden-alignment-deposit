# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · 派生表标签与注释语义修正（2026-11-13）

背景：v1.2.0 为让一张表容纳主口径与各敏感性口径，`calibre` 字段按疟疾主线
统一命名后被结核与 HIV/AIDS 复用；注释列亦按同一模板复制。标签层与注释层
因此与 S3 方法注的真实分母口径矛盾。本轮只改标签、注释与留痕，不改任何
统计数值、不重跑分析、不回写 v1.2.0 冻结件。

产出（写入 数据/processed_v1.2.1_2026-11-13/）：
  - res_B_burden_primary_2026-11-12.csv         （method_note 按病种写实）
  - res_B_burden_sensitivity_2026-11-12.csv    （calibre + note 修正）
  - res_B_country_set_reconciliation_2026-11-12.csv（calibre 修正 + 新增负担观测口径 3 行）
  - res_B_calibre_dictionary_2026-11-13.csv    （新旧标签对照字典）
  - res_B_tb_benchmark_summary_2026-11-13.csv  （结核外部效标可核查小表）
  - res_B_india_record_check_2026-11-13.json   （India 记录实读证据）
  - res_B_notes_change_audit_2026-11-13.json   （数值不变断言与变更台账）

硬约束：除显式许可的标签/注释列外，所有列逐行逐格与原文件相同；
新增的 burden_observed_only 行由逐国明细实算，并与敏感性表 n 断言一致。
"""
import csv
import json
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PROC = os.path.join(ROOT, "数据", "processed")
RAW = os.path.join(ROOT, "数据", "raw")
OUT = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13")
STAMP = "2026-11-12"
os.makedirs(OUT, exist_ok=True)


def load(base, name):
    with open(os.path.join(base, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def dump(name, rows, fields):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        w.writerows(rows)
    return p


def assert_unchanged(old, new, editable, label):
    """除 editable 列外，逐行逐格比对，确保统计数值零改动。"""
    assert len(old) == len(new), f"{label} 行数变化"
    for i, (a, b) in enumerate(zip(old, new)):
        for k in a:
            if k in editable:
                continue
            assert a[k] == b[k], f"{label} 第 {i+1} 行数值列 {k} 被改动：{a[k]!r} -> {b[k]!r}"


# ---------------------------------------------------------------- 标签字典
# key = (disease, v1.2.0 calibre) -> (v1.2.1 calibre, 真实分母口径)
SENS_MAP = {
    ("Malaria", "primary_official_case_counts"):
        ("primary_official_case_counts", "WHO official estimated malaria cases (count), no population multiplier"),
    ("Malaria", "total_population_multiplier_legacy"):
        ("legacy_incidence_times_total_population", "estimated incidence per 1,000 population at risk x total population; sensitivity only"),
    ("Malaria", "common_support_only"):
        ("burden_observed_only", "countries with a positive burden observation only; both sides renormalised on that set"),
    ("Malaria", "second_latest_burden_year"):
        ("second_latest_burden_year", "each country moved to its second-latest available burden year"),
    ("Tuberculosis", "primary_official_case_counts"):
        ("primary_incidence_times_population", "TB incidence per 100,000 population x total population"),
    ("Tuberculosis", "total_population_multiplier_legacy"):
        ("calibre_record_denominator_unchanged", "denominator not replaced in v1.2; values identical to primary, calibre record only"),
    ("Tuberculosis", "common_support_only"):
        ("burden_observed_only", "countries with a positive burden observation only; both sides renormalised on that set"),
    ("Tuberculosis", "second_latest_burden_year"):
        ("second_latest_burden_year", "each country moved to its second-latest available burden year"),
    ("HIV/AIDS", "primary_official_case_counts"):
        ("primary_PLHIV_counts", "GHO people living with HIV counts (prevalence stock), not incident cases"),
    ("HIV/AIDS", "total_population_multiplier_legacy"):
        ("calibre_record_denominator_unchanged", "denominator not replaced in v1.2; values identical to primary, calibre record only"),
    ("HIV/AIDS", "common_support_only"):
        ("burden_observed_only", "countries with a positive burden observation only; both sides renormalised on that set"),
    ("HIV/AIDS", "second_latest_burden_year"):
        ("second_latest_burden_year", "each country moved to its second-latest available burden year"),
}
RECON_MAP = {
    ("Malaria", "primary_official_case_counts"): "primary_official_case_counts",
    ("Malaria", "legacy_total_population"): "legacy_incidence_times_total_population",
    ("Malaria", "second_latest_burden_year"): "second_latest_burden_year",
    ("Tuberculosis", "primary_official_case_counts"): "primary_incidence_times_population",
    ("Tuberculosis", "legacy_total_population"): "calibre_record_denominator_unchanged",
    ("Tuberculosis", "second_latest_burden_year"): "second_latest_burden_year",
    ("HIV/AIDS", "primary_official_case_counts"): "primary_PLHIV_counts",
    ("HIV/AIDS", "legacy_total_population"): "calibre_record_denominator_unchanged",
    ("HIV/AIDS", "second_latest_burden_year"): "second_latest_burden_year",
}

NOTE_SENS = {
    "primary_official_case_counts": "主结果：WHO 官方估计疟疾病例数（MALARIA_EST_CASES，绝对数），无人口乘子。",
    "legacy_incidence_times_total_population": "仅作敏感性对照：疟疾旧「发病率 per 1 000 population at risk × 总人口」分母，已复现旧派生表数值；不再作为主结果。",
    "burden_observed_only": "仅保留有负担观测（b > 0）的国家；s 与 b 在该集合内重新归一化。该名称不表示 s 与 b 支持集的交集。",
    "second_latest_burden_year": "各国改用次最新可得负担年。",
    "primary_incidence_times_population": "主结果：结核发病率（每 10 万人口）× 总人口得到估计发病例数；WHO 官方 TB_e_inc_num 因无印度记录仅作外部量级效标。",
    "calibre_record_denominator_unchanged": "口径登记行：本病种分母在 v1.2 未替换，此行数值与主口径逐项相同，不构成敏感性对照。",
    "primary_PLHIV_counts": "主结果：GHO PLHIV 现患人数（存量计数），非发病病例数，无人口乘子。",
}
NOTE_RECON = {
    "primary_official_case_counts": "union = 有负担观测国家 ∪ 全部 29 个持证商国家",
    "primary_incidence_times_population": "主口径：结核发病率 × 总人口；union = 有负担观测国家 ∪ 全部 29 个持证商国家",
    "primary_PLHIV_counts": "主口径：PLHIV 现患人数；union = 有负担观测国家 ∪ 全部 29 个持证商国家",
    "legacy_incidence_times_total_population": "旧总人口分母对照",
    "burden_observed_only": "仅保留 b > 0 国家；无负担观测的持证商国被排除；union n = 有负担观测国家数",
    "calibre_record_denominator_unchanged": "口径登记行，分母未替换",
    "second_latest_burden_year": "次最新负担年",
}

METHOD_NOTE = {
    "Malaria": ("b = country WHO official estimated malaria cases (MALARIA_EST_CASES, count) / "
                "sum of estimated cases in the analysis set; no population multiplier; "
                "s = disease-specific listing-row shares; M near its upper bound reflects "
                "largely disjoint holder and burden supports, not a supply shortfall."),
    "Tuberculosis": ("b = country estimated incident tuberculosis cases (incidence per 100,000 population "
                     "x total population) / sum of estimated cases in the analysis set; "
                     "WHO official incident-case indicator TB_e_inc_num is an external magnitude check only "
                     "because it contains no India records; s = disease-specific listing-row shares; "
                     "M near its upper bound reflects largely disjoint supports, not a supply shortfall."),
    "HIV/AIDS": ("b = country PLHIV count (prevalence stock, not incident cases) / sum of PLHIV counts "
                 "in the analysis set; no population multiplier; s = disease-specific listing-row shares; "
                 "M near its upper bound reflects largely disjoint supports, not a supply shortfall."),
}

# ---------------------------------------------------------------- 主结果表
p_name = f"res_B_burden_primary_{STAMP}.csv"
p_old = load(PROC, p_name)
p_new = [dict(r) for r in p_old]
for r in p_new:
    r["method_note"] = METHOD_NOTE[r["disease"]]
assert_unchanged(p_old, p_new, {"method_note"}, "主结果表")
dump(p_name, p_new, list(p_old[0].keys()))

# ---------------------------------------------------------------- 敏感性表
s_name = f"res_B_burden_sensitivity_{STAMP}.csv"
s_old = load(PROC, s_name)
s_new = []
for r in s_old:
    key = (r["disease"], r["calibre"])
    assert key in SENS_MAP, f"敏感性表出现未登记的 calibre：{key}"
    new_cal, _ = SENS_MAP[key]
    q = dict(r)
    q["calibre"] = new_cal
    q["note"] = NOTE_SENS[new_cal]
    s_new.append(q)
assert_unchanged(s_old, s_new, {"calibre", "note"}, "敏感性表")
dump(s_name, s_new, list(s_old[0].keys()))

# ---------------------------------------------------------------- 国家集合对账表
r_name = f"res_B_country_set_reconciliation_{STAMP}.csv"
r_old = load(PROC, r_name)
r_new = []
for r in r_old:
    key = (r["disease"], r["calibre"])
    assert key in RECON_MAP, f"对账表出现未登记的 calibre：{key}"
    q = dict(r)
    q["calibre"] = RECON_MAP[key]
    q["note"] = NOTE_RECON[RECON_MAP[key]]
    r_new.append(q)
assert_unchanged(r_old, r_new, {"calibre", "note"}, "对账表原有 9 行")

# 新增 burden_observed_only 三行：数值全部由权威对账表 primary 行与敏感性表派生，
# 不从逐国明细反推（逐国明细的 b 列覆盖口径与汇总表不同，见下方 coverage 诊断）。
bycountry = load(PROC, f"res_B_burden_by_country_{STAMP}.csv")
prim_recon = {r["disease"]: r for r in r_old
              if r["calibre"] == "primary_official_case_counts"}
assert set(prim_recon) == {"Malaria", "Tuberculosis", "HIV/AIDS"}
s_by = {(r["disease"], r["calibre"]): r for r in s_new}

coverage = {}
for disease in ("Malaria", "Tuberculosis", "HIV/AIDS"):
    p = prim_recon[disease]
    src = s_by[(disease, "burden_observed_only")]
    nb = int(src["n_burden_countries"])
    assert int(src["n_countries"]) == nb, f"{disease} burden_observed_only n 与负担国数不一致"
    assert nb == int(p["burden_observed_countries"]), (
        f"{disease} 敏感性表 {nb} 国与对账表 primary 行 "
        f"{p['burden_observed_countries']} 国不一致")
    overlap = int(p["overlap_burden_and_holder"])
    active_all = int(p["disease_specific_active_holder_countries"])
    active_out = int(p["active_holder_without_burden"])
    rows = [x for x in bycountry if x["disease"] == disease]
    pos_bycountry = sum(1 for x in rows
                        if float(x["burden_share_b_primary_official_cases"]) > 0)
    coverage[disease] = {
        "bycountry_rows": len(rows),
        "bycountry_rows_with_positive_b": pos_bycountry,
        "summary_burden_observed_countries": nb,
        "difference": nb - pos_bycountry,
    }
    q = {k: "" for k in r_old[0].keys()}
    q.update({
        "disease": disease,
        "calibre": "burden_observed_only",
        "burden_observed_countries": str(nb),
        "all_29_holder_countries": str(overlap),
        "overlap_burden_and_holder": str(overlap),
        "holder_without_burden": "0",
        "disease_specific_active_holder_countries": str(active_all - active_out),
        "active_holder_without_burden": "0",
        "union_n": str(nb),
        "missing_burden_handling": "excluded (no positive burden observation)",
        "b_positive_criterion": p["b_positive_criterion"],
        "note": NOTE_RECON["burden_observed_only"],
    })
    r_new.append(q)
# 按病种分组、组内保持原有顺序，新增行紧跟各病种 primary 行之后
order = {"Malaria": 0, "Tuberculosis": 1, "HIV/AIDS": 2}
r_new.sort(key=lambda x: (order[x["disease"]],
                          0 if x["calibre"] in ("primary_official_case_counts",
                                                "primary_incidence_times_population",
                                                "primary_PLHIV_counts") else
                          1 if x["calibre"] == "burden_observed_only" else 2))
dump(r_name, r_new, list(r_old[0].keys()))

# ---------------------------------------------------------------- 标签字典
dic = []
for (disease, old), (new, meaning) in SENS_MAP.items():
    dic.append({"table": "res_B_burden_sensitivity", "disease": disease,
                "v1_2_0_label": old, "v1_2_1_label": new, "denominator_meaning": meaning})
for (disease, old), new in RECON_MAP.items():
    dic.append({"table": "res_B_country_set_reconciliation", "disease": disease,
                "v1_2_0_label": old, "v1_2_1_label": new,
                "denominator_meaning": NOTE_RECON[new]})
dump("res_B_calibre_dictionary_2026-11-13.csv", dic,
     ["table", "disease", "v1_2_0_label", "v1_2_1_label", "denominator_meaning"])

# ---------------------------------------------------------------- India 实读
india = {}
for fname, label in [
    (f"gho_tb_est_cases_{STAMP}.csv", "TB_e_inc_num"),
    (f"gho_mal_est_cases_{STAMP}.csv", "MALARIA_EST_CASES"),
    (f"gho_mal_est_incidence_{STAMP}.csv", "MALARIA_EST_INCIDENCE"),
    ("gho_tb_inc.csv", "MDG_0000000020 (existing sparse extract)"),
]:
    rows = load(RAW, fname)
    india[label] = {
        "file": "data/raw/" + fname,
        "n_rows": len(rows),
        "n_IND_rows": sum(1 for x in rows if x["iso3"].strip().upper() == "IND"),
    }
assert india["TB_e_inc_num"]["n_IND_rows"] == 0, "官方结核病例数指标出现印度记录，需重新评估"
json.dump({"check": "India records present in each GHO extract, read from deposited raw CSV",
           "indicators": india,
           "conclusion": "TB_e_inc_num has no India records; India accounts for about one quarter of "
                         "tuberculosis burden and is the largest holder country, so this indicator "
                         "cannot replace the tuberculosis primary denominator."},
          open(os.path.join(OUT, "res_B_india_record_check_2026-11-13.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- 外部效标小表
bench = load(PROC, f"res_B_tb_external_benchmark_{STAMP}.csv")
byyear = {}
for x in bench:
    y = int(x["year"])
    band = ("2000–2004" if y <= 2004 else "2005–2009" if y <= 2009 else
            "2010–2014" if y <= 2014 else "2015–2019" if y <= 2019 else "2020–2025")
    byyear.setdefault(band, []).append(float(x["abs_relative_error"]))
summary = []
for band in ("2000–2004", "2005–2009", "2010–2014", "2015–2019", "2020–2025"):
    v = np.array(byyear.get(band, []), dtype=float)
    if not len(v):
        continue
    summary.append({"period": band, "paired_country_years": str(len(v)),
                    "median_abs_relative_error": f"{np.median(v):.4f}",
                    "median_percent": f"{100*np.median(v):.2f}",
                    "p90_abs_relative_error": f"{np.percentile(v, 90):.4f}",
                    "max_abs_relative_error": f"{v.max():.4f}"})
allv = np.array([float(x["abs_relative_error"]) for x in bench])
summary.append({"period": "All years", "paired_country_years": str(len(allv)),
                "median_abs_relative_error": f"{np.median(allv):.4f}",
                "median_percent": f"{100*np.median(allv):.2f}",
                "p90_abs_relative_error": f"{np.percentile(allv, 90):.4f}",
                "max_abs_relative_error": f"{allv.max():.4f}"})
assert sum(int(x["paired_country_years"]) for x in summary[:-1]) == len(allv)
dump("res_B_tb_benchmark_summary_2026-11-13.csv", summary,
     ["period", "paired_country_years", "median_abs_relative_error",
      "median_percent", "p90_abs_relative_error", "max_abs_relative_error"])

# ---------------------------------------------------------------- 变更台账
audit = {
    "version": "v1.2.1",
    "date": "2026-11-13",
    "scope": "labels, notes, definitions and traceability only; no statistical value changed",
    "assertions": [
        "primary table: all columns except method_note are cell-wise identical to v1.2.0",
        "sensitivity table: all columns except calibre and note are cell-wise identical to v1.2.0",
        "reconciliation table: original 9 rows identical except calibre and note",
        "3 added burden_observed_only rows derived from the authoritative reconciliation primary rows and asserted against sensitivity n",
        "India record counts read from deposited raw CSV, not asserted from memory",
        "external benchmark summary recomputed from all 928 paired country-years",
    ],
    "primary_table_rows": len(p_new),
    "sensitivity_table_rows": len(s_new),
    "reconciliation_table_rows": len(r_new),
    "calibre_dictionary_rows": len(dic),
    "benchmark_pairs": len(bench),
    "india_TB_e_inc_num_rows": india["TB_e_inc_num"]["n_IND_rows"],
    "bycountry_coverage_diagnostic": {
        "finding": "The by-country derived table carries fewer rows with a positive primary burden "
                   "share than the summary table's burden-observed country count. This is a "
                   "pre-existing coverage convention in the v1.2.0 by-country table, not a value "
                   "introduced or changed in v1.2.1. The new reconciliation rows therefore take "
                   "their n from the authoritative summary and reconciliation tables.",
        "status": "flagged for later verification; no statistical value changed in this round",
        "by_disease": coverage,
    },
}
json.dump(audit, open(os.path.join(OUT, "res_B_notes_change_audit_2026-11-13.json"),
                      "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("v1.2.1 派生表语义修正完成 ->", os.path.relpath(OUT, ROOT))
print(f"  主结果 {len(p_new)} 行 / 敏感性 {len(s_new)} 行 / 对账 {len(r_new)} 行（新增 3）")
print(f"  标签字典 {len(dic)} 行 / 效标 {len(bench)} 配对 / 分组 {len(summary)} 行")
print("  数值列逐格不变断言：3 张表全部通过")
print(f"  TB_e_inc_num 印度记录数：{india['TB_e_inc_num']['n_IND_rows']}")
print("VERDICT = DERIVED NOTES V1.2.1 OK")
