# -*- coding: utf-8 -*-
"""B① 返修 · 以 WHO 官方估计病例数为主分母重算疾病负担与全部对齐指标

修订要点
--------
旧链路：疟疾发病率（per 1 000 population at risk）× 世界银行总人口。
        结核发病率（per 100 000 population）× 世界银行总人口。
问题：疟疾率的分母是「高危人口」，不是总人口；两者之比是随国家变化的
      异质变量，归一化不会约掉。结核率虽以总人口为分母，但世界银行人口
      与 WHO 估计所用人口不同源，且负担年与人口年错配。

错误的准确定性
--------------
错误不是「用了总人口」，而是「把一个以高危人口为分母的率乘了总人口」。
同一段 rate_x_pop 代码对结核成立（结核率的分母本就是总人口），对疟疾
不成立（疟疾率的分母是高危人口，两者之比是国别异质变量，归一化不约掉）。
因此不能一刀切把三个病种都换成官方绝对数。

主口径（primary），按各指标自身的分母语义分别定值：
        Malaria       MALARIA_EST_CASES   WHO 估计疟疾病例数（绝对数，无乘子）
        Tuberculosis  MDG_0000000020 × 总人口（率的分母即总人口，语义成立）
        HIV/AIDS      HIV_0000000001      PLHIV 计数（既有，仅补材）
      负担份额 b = 该国估计人数 / 样本内估计人数合计。

对照口径（sensitivity / legacy）：仅疟疾额外保留旧的「率 × 总人口」链路，
      作为敏感性对照，**不进入主结果**。脚本断言该对照口径能复现
      res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv 的旧数值；
      并断言结核与 HIV 因分母未改，全部指标与旧值一致。由此保证本轮
      任何数值变化 100% 来自疟疾分母替换，而非算法或随机流漂移。

数据源缺口（已实读证实，禁止掩盖）
----------------------------------
WHO GHO 的 TB_e_inc_num（估计结核发病病例数）不含印度 IND，而印度约占
结核负担四分之一、且是最大持证商国。若用它替换结核分母会把最大负担国
错误剔除，制造虚假的结论剧变。故该指标仅作外部效标（排除印度后比较），
不作主分母；缺口连同印度在既有提取中的可得年份一并登记入对照文件。

不变的裁定
----------
- 供应份额 s 仍为病种特异（Therapeutic Area × Applicant，29 国码表）。
- M=Σ|s−b|、D=M/2、C=Σ b·1[s>0]、R25=前 25% 高负担国供应/负担份额比。
- 主 CI 为产品行级 bootstrap（只重抽 s 侧、b 固定，10000 次）。
- 病种间 M 不可比；M 贴上限主要反映持证商国与负担国支持集不重叠。
- 只新增文件；既有 raw / processed / 稿件一律不改动。

判据统一（修复 X7）
------------------
w 只保留 weight>0 的国家；universe = set(w) ∪ 全部 29 个持证商国；
n_burden_countries 与逐国明细统一定义为 universe 中 b>0 的国家数，
并在写出前 assert 两者相等。零负担持证商国 b=0，保留在 universe 内。
"""
import collections
import csv
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
RAW = os.path.join(ROOT, "raw")
PROC = os.path.join(ROOT, "processed")
STAMP = "2026-11-12"
SEED = 20261111
B_BOOT = 10000
rng = np.random.default_rng(SEED)

ISO2_TO_ISO3 = {
    "IN": "IND", "CN": "CHN", "CH": "CHE", "GB": "GBR", "DE": "DEU",
    "US": "USA", "ES": "ESP", "NL": "NLD", "KR": "KOR", "RO": "ROU",
    "FR": "FRA", "PK": "PAK", "BD": "BGD", "SE": "SWE", "AT": "AUT",
    "LV": "LVA", "DK": "DNK", "BE": "BEL", "UA": "UKR", "ID": "IDN",
    "IE": "IRL", "EG": "EGY", "IT": "ITA", "NG": "NGA", "PT": "PRT",
    "JP": "JPN", "CA": "CAN", "UG": "UGA", "ZA": "ZAF",
}
ISO3_TO_ISO2 = {v: k for k, v in ISO2_TO_ISO3.items()}
ALL_ISO3 = set(ISO2_TO_ISO3.values())

AGG_NOTE = "World Bank/WHO 聚合码已在源提取阶段剔除"


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, header, rows):
    path = os.path.join(PROC, name)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {name}  ({len(rows)} 行)")
    return path


def tidy(path):
    """iso3,year,value -> {iso3: {year: value}}，排除聚合码与非法行。"""
    out = collections.defaultdict(dict)
    for r in read(path):
        iso = (r.get("iso3") or "").strip().upper()
        if len(iso) != 3 or not iso.isalpha():
            continue
        try:
            y = int(r["year"]); v = float(r["value"])
        except (ValueError, TypeError, KeyError):
            continue
        out[iso][y] = v
    return out


pop = tidy(os.path.join(RAW, "wb_pop.csv"))


def pop_at(iso, year):
    d = pop.get(iso, {})
    if not d:
        return None
    y = min(year, 2023)
    if y in d:
        return d[y]
    cand = [x for x in d if x <= y]
    return d[max(cand)] if cand else d[min(d)]


# ---- 分母定义表：主分母（官方绝对数）与对照分母（旧率×总人口）----
PRIMARY = {
    "Malaria": dict(file=f"gho_mal_est_cases_{STAMP}.csv",
                    indicator="MALARIA_EST_CASES",
                    name="Estimated number of malaria cases",
                    unit="estimated cases (count)", mode="count"),
    "Tuberculosis": dict(file="gho_tb_inc.csv",
                         indicator="MDG_0000000020",
                         name="Incidence of tuberculosis (per 100 000 population per year) × total population",
                         unit="estimated incident cases (rate per 100 000 population × total population)",
                         mode="rate_x_pop"),
    "HIV/AIDS": dict(file="gho_hiv_pl.csv",
                     indicator="PLHIV count (existing GHO extract)",
                     name="People living with HIV (existing extract)",
                     unit="PLHIV (count)", mode="count"),
}
LEGACY = {
    "Malaria": dict(file="gho_mal_inc.csv", indicator="MALARIA_EST_INCIDENCE",
                    unit="per 1 000 population at risk × total population",
                    mode="rate_x_pop"),
    "Tuberculosis": dict(file="gho_tb_inc.csv", indicator="TB incidence per 100 000",
                         unit="per 100 000 population × total population",
                         mode="rate_x_pop"),
    "HIV/AIDS": dict(file="gho_hiv_pl.csv", indicator="PLHIV count (existing GHO extract)",
                     unit="PLHIV (count)", mode="count"),
}


def weight_for(cfg, iso, year, val):
    """按分母定义把原始指标值转成「人数绝对量」。"""
    if val is None or val <= 0:
        return None
    if cfg["mode"] == "count":
        return val
    p = pop_at(iso, year)
    if p is None or p <= 0:
        return None
    return val * p          # 忠实复现旧脚本（不额外除以 1000/100000）


def build_series(cfg, drop_second_latest=False):
    """取各国最新（或次最新）可得年的负担绝对量，返回 {iso: weight}。"""
    series = tidy(os.path.join(RAW, cfg["file"]))
    out = {}
    for iso, ys in series.items():
        years = sorted(ys)
        if not years:
            continue
        if drop_second_latest and len(years) >= 2:
            y = years[-2]
        else:
            y = years[-1]
        w = weight_for(cfg, iso, y, ys[y])
        if w is not None and w > 0:
            out[iso] = w
    return out, series


def build_supply_by_area():
    """复用既有裁定的病种特异供应份额，并从 FPP 重建产品行国别标签。"""
    fpp = read(os.path.join(RAW, "who_pq_fpp_2026-09-15.csv"))
    mp = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
    app2iso2 = {}
    for r in mp:
        a = (r.get("applicant") or "").strip()
        i2 = (r.get("iso3") or "").strip()
        if a and i2:
            app2iso2[a] = i2
    by_ta = collections.defaultdict(list)
    for r in fpp:
        by_ta[(r.get("Therapeutic Area") or "").strip()].append(r)
    out = {}
    for ta in ("Malaria", "Tuberculosis", "HIV/AIDS"):
        cnt, labels = collections.Counter(), []
        for r in by_ta.get(ta, []):
            i2 = app2iso2.get((r.get("Applicant") or "").strip())
            if i2 not in ISO2_TO_ISO3:
                raise AssertionError(f"{ta} 存在未匹配 applicant，禁止继续")
            iso3 = ISO2_TO_ISO3[i2]
            cnt[iso3] += 1
            labels.append(iso3)
        matched = len(labels)
        out[ta] = dict(shares={k: v / matched for k, v in cnt.items()},
                       counts=dict(cnt), labels=labels, matched=matched,
                       n_holder_countries=len(cnt))

    # 与既有权威派生表交叉核对（该表为 2 位小数，容差 0.005 个百分点）
    ref = read(os.path.join(PROC, "res_B_uncertainty_supply_by_area_2026-11-11.csv"))
    for r in ref:
        ta, iso = r["disease"], r["iso3_gho_wb"]
        got = 100 * out[ta]["shares"].get(iso, 0.0)
        exp = float(r["disease_specific_share_pct"])
        assert abs(got - exp) <= 0.0051, f"供应份额 s 与既有裁定表不一致 {ta}/{iso}"
    return out


def boot_m_supply(labels, universe, b, draws=B_BOOT):
    pos = {iso: i for i, iso in enumerate(universe)}
    lab_ix = np.array([pos[l] for l in labels], dtype=int)
    K = len(lab_ix)
    out = np.empty(draws)
    ix = rng.integers(0, K, size=(draws, K))
    for i in range(draws):
        cnt = np.bincount(lab_ix[ix[i]], minlength=len(universe))
        out[i] = np.abs(cnt.astype(float) / K - b).sum()
    lo, hi = np.percentile(out, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


def metrics(w, svec, sd, with_ci=True):
    """统一构造 universe / b / s 与全部对齐指标；零值判据在此唯一定义。"""
    universe = sorted(set(w) | ALL_ISO3)
    raw = np.array([w.get(iso, 0.0) for iso in universe], dtype=float)
    b = raw / raw.sum()
    s = np.array([svec.get(iso, 0.0) for iso in universe], dtype=float)
    n_burden = int((b > 0).sum())
    assert n_burden == len(w), f"零值判据不一致：b>0={n_burden}, w={len(w)}"
    M = float(np.abs(s - b).sum())
    C = float(b[s > 0].sum())
    order = np.argsort(b)[::-1]
    k = max(1, int(math.ceil(0.25 * len(universe))))
    top_b = float(b[order[:k]].sum())
    top_s = float(s[order[:k]].sum())
    R25 = top_s / top_b if top_b > 0 else float("nan")
    ci = boot_m_supply(sd["labels"], universe, b) if with_ci else (None, None)
    return dict(universe=universe, b=b, s=s, n=len(universe), n_burden=n_burden,
                M=M, D=M / 2, C=C, R25=R25, top_b=top_b, top_s=top_s,
                k=k, ci=ci, years=None)


def tb_external_benchmark():
    """结核旧链路的外部效标：率×总人口推算病例数 vs WHO 官方估计病例数。

    旧复核体系只有内部一致性检查，没有任何外部语义效标，因此上游口径
    错误能被每一轮 ALL CLEAN 反复确证。本函数补上这一层。
    WHO GHO 的 TB_e_inc_num 不含印度，故只用于量级校验，不作主分母。
    """
    off = tidy(os.path.join(RAW, f"gho_tb_est_cases_{STAMP}.csv"))
    rate = tidy(os.path.join(RAW, "gho_tb_inc.csv"))
    rows = []
    for iso, ys in rate.items():
        for y, v in ys.items():
            if iso not in off or y not in off[iso] or v <= 0 or off[iso][y] <= 0:
                continue
            p = pop_at(iso, y)
            if p is None or p <= 0:
                continue
            pred = v * p / 1e5
            official = off[iso][y]
            rows.append([iso, y, round(v, 4), int(p), round(pred, 1),
                         round(official, 1), round(abs(pred - official) / official, 4)])
    errs = sorted(r[6] for r in rows)
    stats = {
        "paired_country_years": len(rows),
        "median_abs_relative_error": round(float(np.median(errs)), 4) if errs else None,
        "p90_abs_relative_error": round(float(errs[int(0.9 * (len(errs) - 1))]), 4) if errs else None,
        "share_within_5pct": round(sum(1 for e in errs if e < 0.05) / len(errs), 4) if errs else None,
        "india_in_TB_e_inc_num": "IND" in off,
        "verdict": "TB_e_inc_num cannot replace the TB burden denominator: India absent",
    }
    write(f"res_B_tb_external_benchmark_{STAMP}.csv",
          ["iso3", "year", "tb_rate_per_100k", "total_population",
           "predicted_cases_rate_x_pop", "who_official_estimated_cases",
           "abs_relative_error"], rows)
    return stats


def main():
    prov = json.load(open(os.path.join(RAW, f"who_malaria_denominator_provenance_{STAMP}.json"),
                          encoding="utf-8"))
    tb_bench = tb_external_benchmark()
    assert tb_bench["india_in_TB_e_inc_num"] is False, "数据源结构已变，需重新评估"
    print(f"  结核外部效标：配对 {tb_bench['paired_country_years']} 条，"
          f"中位相对偏差 {tb_bench['median_abs_relative_error']}，"
          f"官方指标缺印度={not tb_bench['india_in_TB_e_inc_num']} → 不作主分母")
    sd_all = build_supply_by_area()
    print("供应份额 s 与既有病种特异裁定表逐国一致（容差 0.005 个百分点）")

    old_rows = read(os.path.join(PROC, "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv"))
    old = {r["disease"]: r for r in old_rows if r["calibre"] == "latest_burden_year"}

    primary_rows, sens_rows, recon_rows, by_country_rows = [], [], [], []
    audit = {
        "date": STAMP,
        "change": "Malaria burden denominator: incidence per 1 000 population at risk × "
                  "total population → WHO official estimated malaria case counts",
        "scope": "Only the malaria denominator changed. Tuberculosis and HIV/AIDS "
                 "denominators are unchanged because their indicator denominators "
                 "are total population and a direct count, respectively.",
        "external_benchmark": tb_bench,
        "data_source_limitations": [
            "WHO GHO TB_e_inc_num contains no India (IND) records; India accounts for "
            "roughly a quarter of TB burden and is the largest certificate-holder "
            "country, so this indicator is used only as an external magnitude check.",
            "WHO GHO has no absolute 'population at risk' indicator; the at-risk "
            "fraction was recovered diagnostically as 1 000 × estimated cases / "
            "estimated incidence, for bias documentation only.",
            "The existing sparse GHO extracts use each country's latest available "
            "burden year; malaria now resolves to 2024 for all included countries.",
        ],
        "diseases": {},
    }

    for disease in ("Malaria", "Tuberculosis", "HIV/AIDS"):
        sd = sd_all[disease]
        svec = sd["shares"]
        pcfg, lcfg = PRIMARY[disease], LEGACY[disease]

        w_new, series_new = build_series(pcfg)
        w_old, series_old = build_series(lcfg)
        m_new = metrics(w_new, svec, sd, with_ci=True)
        m_old = metrics(w_old, svec, sd, with_ci=True)

        o = old.get(disease)
        keys = (("M", "M_sum_abs_diff"), ("C", "burden_weighted_supply_coverage_C"),
                ("R25", "top25_coverage_ratio_R25"))
        if disease == "Malaria":
            # 对照口径必须忠实复现旧派生表，证明差异只来自分母替换
            assert o, "旧派生表缺疟疾行"
            for key, col in keys:
                assert abs(m_old[key] - float(o[col])) <= 0.0002, (
                    f"疟疾对照口径未能复现旧值 {col}: {m_old[key]} vs {o[col]}")
            print(f"  疟疾：总人口对照口径复现旧数值 M={m_old['M']:.4f} "
                  f"C={m_old['C']:.4f} R25={m_old['R25']:.4f} ✓")
        else:
            # 分母未改：主口径必须逐项等于旧值；CI 沿用既有已验证值，避免随机流漂移
            assert o, f"旧派生表缺 {disease} 行"
            for key, col in keys:
                assert abs(m_new[key] - float(o[col])) <= 0.0002, (
                    f"{disease} 分母未改却偏离旧值 {col}: {m_new[key]} vs {o[col]}")
            m_new["ci"] = (float(o["ci95_lo_M"]), float(o["ci95_hi_M"]))
            print(f"  {disease}: 分母未改，主口径与旧值逐项一致 "
                  f"M={m_new['M']:.4f} C={m_new['C']:.4f} R25={m_new['R25']:.4f} ✓")

        years_new = {iso: max(ys) for iso, ys in series_new.items() if iso in w_new}
        ymin, ymax = min(years_new.values()), max(years_new.values())
        med = float(np.median(list(years_new.values())))

        primary_rows.append([
            disease, pcfg["indicator"], pcfg["unit"], ymin, ymax, round(med, 1),
            sd["matched"], sd["n_holder_countries"],
            m_new["n"], m_new["n_burden"],
            round(m_new["M"], 4), round(m_new["D"], 4), m_new["ci"][0], m_new["ci"][1],
            round(m_new["C"], 4), round(m_new["R25"], 4),
            round(m_new["top_b"], 4), round(m_new["top_s"], 4), m_new["k"],
            "no (n / unit / burden year differ)",
            "b = country estimated cases / sum of estimated cases in the analysis set; "
            "no population multiplier; s = disease-specific listing-row shares; "
            "M near its upper bound reflects disjoint holder/burden country supports, "
            "not near-complete volume mismatch; interpretation rests on C and R25",
        ])

        sens_rows.append([disease, "primary_official_case_counts", pcfg["indicator"],
                          m_new["n"], m_new["n_burden"], round(m_new["M"], 4),
                          round(m_new["D"], 4), round(m_new["C"], 4),
                          round(m_new["R25"], 4), round(m_new["top_b"], 4),
                          round(m_new["top_s"], 4), "主结果：WHO 官方估计病例数（绝对数）"])
        legacy_note = (
            "仅作敏感性对照：疟疾旧「发病率 per 1 000 population at risk × 总人口」"
            "分母，已复现旧派生表数值；不再作为主结果"
            if disease == "Malaria" else
            "该病种分母未改（结核率的分母即总人口／HIV 直接计数）；"
            "此行与主口径相同，仅用于口径登记，不构成敏感性对照")
        sens_rows.append([disease, "total_population_multiplier_legacy", lcfg["indicator"],
                          m_old["n"], m_old["n_burden"], round(m_old["M"], 4),
                          round(m_old["D"], 4), round(m_old["C"], 4),
                          round(m_old["R25"], 4), round(m_old["top_b"], 4),
                          round(m_old["top_s"], 4), legacy_note])

        # 共同支持敏感性（主分母）
        common = [iso for iso in m_new["universe"] if iso in w_new]
        bc = np.array([w_new.get(iso, 0.0) for iso in common], dtype=float)
        sc = np.array([svec.get(iso, 0.0) for iso in common], dtype=float)
        bc, sc = bc / bc.sum(), sc / sc.sum()
        Mc = float(np.abs(sc - bc).sum())
        sens_rows.append([disease, "common_support_only", pcfg["indicator"],
                          len(common), int((bc > 0).sum()), round(Mc, 4),
                          round(Mc / 2, 4), "", "", "", "",
                          "只保留有负担观测的国家；s 与 b 在共同集合内重新归一化"])

        # 次最新负担年敏感性（主分母）
        w_prev, _ = build_series(pcfg, drop_second_latest=True)
        mp = metrics(w_prev, svec, sd, with_ci=False)
        sens_rows.append([disease, "second_latest_burden_year", pcfg["indicator"],
                          mp["n"], mp["n_burden"], round(mp["M"], 4),
                          round(mp["D"], 4), round(mp["C"], 4),
                          round(mp["R25"], 4), round(mp["top_b"], 4),
                          round(mp["top_s"], 4), "各国改用次最新可得负担年"])

        # 国家集合对账表（主分母，逐项可回链）
        B = set(w_new)
        H = set(ALL_ISO3)
        A = {iso for iso, v in svec.items() if v > 0}
        rec = [
            disease, "primary_official_case_counts",
            len(B), len(H), len(B & H), len(H - B), len(A), len(A - B),
            len(B | H), "b = 0 for holder countries without a burden observation; they remain in the universe",
            "b > 0 (equivalently w > 0); identical criterion in by-country table and summary",
            "union = burden-observed countries ∪ all 29 holder countries",
        ]
        recon_rows.append(rec)
        for calibre, ww, label in (
                ("legacy_total_population", w_old, "旧分母对照"),
                ("second_latest_burden_year", w_prev, "次最新负担年")):
            BB = set(ww)
            recon_rows.append([
                disease, calibre, len(BB), len(H), len(BB & H), len(H - BB),
                len(A), len(A - BB), len(BB | H),
                "same as primary", "b > 0", label,
            ])

        # 逐国明细（主分母 + 对照分母并列，供全文与图件回链）
        for iso, si, bi, bo in zip(m_new["universe"], m_new["s"], m_new["b"],
                                   [w_old.get(x, 0.0) / sum(w_old.values())
                                    for x in m_new["universe"]]):
            by_country_rows.append([
                disease, iso, ISO3_TO_ISO2.get(iso, ""), years_new.get(iso, ""),
                round(float(si), 6), round(float(bi), 6), round(float(bo), 6),
                round(abs(float(si) - float(bi)), 6),
                int(sd["counts"].get(iso, 0)),
            ])

        # 变更前后对照（机器可读）
        audit["diseases"][disease] = {
            "denominator_changed": disease == "Malaria",
            "primary_denominator": {
                "indicator": pcfg["indicator"], "official_name": pcfg["name"],
                "unit": pcfg["unit"], "local_file": f"数据/raw/{pcfg['file']}",
                "burden_year_range": [ymin, ymax],
                "records": (
                    prov["files"]["mal_est_cases"]["accepted_records"] if disease == "Malaria"
                    else "existing GHO TB incidence extract (957 rows, 197 countries); not refetched"
                    if disease == "Tuberculosis"
                    else "existing GHO PLHIV count extract; not refetched in this round"),
                "official_absolute_indicator_not_used": (
                    "TB_e_inc_num excluded because it contains no India records"
                    if disease == "Tuberculosis" else "not applicable"),
            },
            "comparison_denominator": {
                "indicator": lcfg["indicator"], "unit": lcfg["unit"],
                "role": ("sensitivity only, no longer a primary result"
                         if disease == "Malaria" else
                         "identical to primary; denominator unchanged"),
                "reproduces_old_derived_table": True,
            },
            "before_total_population": {
                "n_countries": m_old["n"], "n_burden_countries": m_old["n_burden"],
                "M": round(m_old["M"], 4), "D": round(m_old["D"], 4),
                "C": round(m_old["C"], 4), "R25": round(m_old["R25"], 4),
                "top25pct_burden_share": round(m_old["top_b"], 4),
                "top25pct_supply_share": round(m_old["top_s"], 4),
            },
            "after_official_cases": {
                "n_countries": m_new["n"], "n_burden_countries": m_new["n_burden"],
                "M": round(m_new["M"], 4), "D": round(m_new["D"], 4),
                "C": round(m_new["C"], 4), "R25": round(m_new["R25"], 4),
                "M_ci95": list(m_new["ci"]),
                "top25pct_burden_share": round(m_new["top_b"], 4),
                "top25pct_supply_share": round(m_new["top_s"], 4),
                "top_quartile_n_countries": m_new["k"],
            },
            "delta": {
                key: round(m_new[key] - m_old[key], 4)
                for key in ("M", "D", "C", "R25", "top_b", "top_s")
            },
        }
        print(f"  {disease}: 主口径 n={m_new['n']} (负担 {m_new['n_burden']}) "
              f"M={m_new['M']:.4f} C={m_new['C']:.4f} R25={m_new['R25']:.4f} "
              f"前25% b={100*m_new['top_b']:.2f}% s={100*m_new['top_s']:.2f}% "
              f"负担年 {ymin}–{ymax}")

    write(f"res_B_burden_primary_{STAMP}.csv",
          ["disease", "burden_source_indicator", "burden_unit",
           "burden_year_min", "burden_year_max", "burden_year_median",
           "supply_denominator_rows", "n_supply_countries_active",
           "n_countries", "n_burden_countries",
           "M_sum_abs_diff", "D_normalised", "ci95_lo_M", "ci95_hi_M",
           "burden_weighted_supply_coverage_C", "top25_coverage_ratio_R25",
           "top25pct_burden_share_of_b", "top25pct_burden_share_of_s",
           "top_quartile_n_countries", "comparable_across_diseases", "method_note"],
          primary_rows)
    write(f"res_B_burden_sensitivity_{STAMP}.csv",
          ["disease", "calibre", "burden_source_indicator",
           "n_countries", "n_burden_countries", "M_sum_abs_diff", "D_normalised",
           "burden_weighted_supply_coverage_C", "top25_coverage_ratio_R25",
           "top25pct_burden_share_of_b", "top25pct_burden_share_of_s", "note"],
          sens_rows)
    write(f"res_B_country_set_reconciliation_{STAMP}.csv",
          ["disease", "calibre", "burden_observed_countries", "all_29_holder_countries",
           "overlap_burden_and_holder", "holder_without_burden",
           "disease_specific_active_holder_countries", "active_holder_without_burden",
           "union_n", "missing_burden_handling", "b_positive_criterion", "note"],
          recon_rows)
    write(f"res_B_burden_by_country_{STAMP}.csv",
          ["disease", "iso3", "iso2_holder", "burden_year",
           "supply_share_s_disease_specific", "burden_share_b_primary_official_cases",
           "burden_share_b_legacy_total_population", "abs_s_minus_b_primary",
           "pq_product_rows_in_area"],
          by_country_rows)
    with open(os.path.join(PROC, f"res_B_denominator_change_audit_{STAMP}.json"),
              "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print("VERDICT = RECOMPUTE OK (对照口径已复现旧值；仅新增文件)")
    return audit


if __name__ == "__main__":
    main()
