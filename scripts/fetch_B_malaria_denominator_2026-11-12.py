# -*- coding: utf-8 -*-
"""B① 返修 · WHO 官方疟疾分母原始提取（2026-11-12）

目的
----
把疟疾疾病负担的主分母从「发病率 × 世界银行总人口」换成 WHO 官方
估计病例数（绝对数），并落盘可复跑的原始提取与来源登记。

取数纪律
--------
1. 指标码不凭记忆写死：先实读 WHO GHO 官方指标目录，确认指标存在并取得
   官方英文名，再按该目录中的 IndicatorCode 请求数据。
2. 客户端只保留 SpatialDimType == COUNTRY 的 ISO3 国家行，排除区域／全球
   聚合行；Dim1/Dim2/Dim3 非空的行一律排除（避免把年龄／性别／虫种子层
   当成国家级数值）。
3. 同一 (iso3, year) 只允许一条；重复计入 skipped 并如实登记。
4. 只新增文件，不改动任何既有 raw / processed / 稿件文件。

三个指标的角色
--------------
- MALARIA_EST_CASES     : 主分母，WHO 估计疟疾病例数（绝对数）
- MALARIA_EST_INCIDENCE : 既有提取的同源发病率，用于核对数据源一致性，
                          并反推出 WHO 隐含的高危人口，量化旧乘子偏倚
- TB_e_inc_num          : 结核估计发病病例数，作为结核「率 × 总人口」口径
                          的外部效标（校验旧链路对结核是否成立）

来源：WHO Global Health Observatory OData API https://ghoapi.azureedge.net/api/
"""
import collections
import csv
import datetime
import hashlib
import json
import os
import ssl
import urllib.request

BASE = "https://ghoapi.azureedge.net/api"
CTX = ssl.create_default_context()
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "raw"))
STAMP = "2026-11-12"

TARGETS = {
    "mal_est_cases": "MALARIA_EST_CASES",
    "mal_est_incidence": "MALARIA_EST_INCIDENCE",
    "tb_est_cases": "TB_e_inc_num",
}

OUT = {
    "mal_est_cases": f"gho_mal_est_cases_{STAMP}.csv",
    "mal_est_incidence": f"gho_mal_est_incidence_{STAMP}.csv",
    "tb_est_cases": f"gho_tb_est_cases_{STAMP}.csv",
}


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def official_names():
    d = http_json(BASE + "/Indicator")
    vals = d["value"]
    names = {x["IndicatorCode"]: x["IndicatorName"] for x in vals}
    for key, code in TARGETS.items():
        assert code in names, f"指标目录中不存在 {code}，禁止凭记忆取数"
    return names, len(vals)


def fetch_all(code):
    url = f"{BASE}/{code}"
    rows, pages, first_url = [], 0, url
    while url:
        d = http_json(url)
        rows.extend(d.get("value", []))
        pages += 1
        nxt = d.get("@odata.nextLink")
        if nxt and not nxt.startswith("http"):
            nxt = BASE + "/" + nxt.lstrip("/")
        url = nxt
        assert pages <= 300, "分页异常，终止以防失控"
    return rows, pages, first_url


def clean(rows):
    out, skipped = {}, collections.Counter()
    for r in rows:
        if r.get("SpatialDimType") != "COUNTRY":
            skipped["non_country_aggregate"] += 1
            continue
        iso = (r.get("SpatialDim") or "").strip().upper()
        if len(iso) != 3 or not iso.isalpha():
            skipped["invalid_iso3"] += 1
            continue
        if any(r.get(k) not in (None, "") for k in ("Dim1", "Dim2", "Dim3")):
            skipped["extra_dimension"] += 1
            continue
        try:
            year = int(r.get("TimeDim"))
        except (TypeError, ValueError):
            skipped["non_year_time"] += 1
            continue
        v = r.get("NumericValue")
        if v is None:
            skipped["null_numeric"] += 1
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            skipped["non_numeric"] += 1
            continue
        key = (iso, year)
        if key in out:
            skipped["duplicate_iso3_year"] += 1
            continue
        out[key] = {
            "iso3": iso,
            "year": year,
            "value": v,
            "low": r.get("Low"),
            "high": r.get("High"),
            "value_raw": r.get("Value"),
            "source_date": r.get("Date"),
        }
    return out, dict(skipped)


def write_csv(path, recs):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "year", "value", "low", "high", "value_raw", "source_date"])
        for key in sorted(recs):
            r = recs[key]
            w.writerow([r["iso3"], r["year"], r["value"], r["low"], r["high"],
                        r["value_raw"], r["source_date"]])
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return os.path.getsize(path), h


def main():
    assert os.path.isdir(RAW), f"raw 目录不存在: {RAW}"
    names, n_catalog = official_names()
    fetched_at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"WHO GHO 指标目录实读：{n_catalog} 个指标；目标 3 个指标均存在")

    prov = {
        "fetch_date": STAMP,
        "fetched_at": fetched_at,
        "api_base": BASE,
        "indicator_catalog_url": BASE + "/Indicator",
        "indicator_catalog_size": n_catalog,
        "spatial_filter": "SpatialDimType == COUNTRY, ISO3 alpha-3 only",
        "dimension_filter": "Dim1/Dim2/Dim3 must be empty",
        "deduplication": "one record per (iso3, year); duplicates counted, never silently kept",
        "credential": "none required; public WHO API",
        "files": {},
    }

    for key, code in TARGETS.items():
        rows, pages, url = fetch_all(code)
        recs, skipped = clean(rows)
        path = os.path.join(RAW, OUT[key])
        size, sha = write_csv(path, recs)
        years = sorted({r["year"] for r in recs.values()})
        countries = sorted({r["iso3"] for r in recs.values()})
        dates = collections.Counter(str(r["source_date"]) for r in recs.values())
        prov["files"][key] = {
            "indicator_code": code,
            "official_indicator_name": names[code],
            "request_url": url,
            "api_pages": pages,
            "raw_records": len(rows),
            "accepted_records": len(recs),
            "skipped": skipped,
            "year_min": years[0] if years else None,
            "year_max": years[-1] if years else None,
            "distinct_years": len(years),
            "n_countries": len(countries),
            "value_field": "NumericValue (WHO point estimate)",
            "uncertainty_field": "Low / High (WHO published interval)",
            "source_date_values": dict(dates.most_common(8)),
            "local_file": f"数据/raw/{OUT[key]}",
            "local_bytes": size,
            "local_sha256": sha,
        }
        print(f"  {code}: raw={len(rows)} 保留={len(recs)} 国家={len(countries)} "
              f"年份 {years[0] if years else '-'}–{years[-1] if years else '-'} "
              f"跳过={skipped}")

    # 数据源一致性外部校验：既有 gho_mal_inc.csv 的首行必须来自同一指标
    old = os.path.join(RAW, "gho_mal_inc.csv")
    inc = None
    with open(os.path.join(RAW, OUT["mal_est_incidence"]), encoding="utf-8") as f:
        inc = {(r["iso3"], int(r["year"])): float(r["value"])
               for r in csv.DictReader(f)}
    with open(old, encoding="utf-8-sig") as f:
        old_rows = list(csv.DictReader(f))
    mismatches = []
    for r in old_rows[:40]:
        k = (r["iso3"].strip().upper(), int(r["year"]))
        if k not in inc or abs(inc[k] - float(r["value"])) > 1e-6:
            mismatches.append(k)
    prov["consistency_check"] = {
        "existing_extract": "数据/raw/gho_mal_inc.csv",
        "existing_extract_rows": len(old_rows),
        "compared_head_rows": min(40, len(old_rows)),
        "mismatches_against_MALARIA_EST_INCIDENCE": mismatches,
        "verdict": "same WHO indicator" if not mismatches else "MISMATCH - investigate",
    }
    print(f"  既有提取前 40 行与 MALARIA_EST_INCIDENCE 比对：不一致 {len(mismatches)} 行")

    prov_path = os.path.join(RAW, f"who_malaria_denominator_provenance_{STAMP}.json")
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=2)
    print(f"来源登记已写入：{prov_path}")
    print("VERDICT = FETCH OK (仅新增文件，未改动既有文件)")


if __name__ == "__main__":
    main()
