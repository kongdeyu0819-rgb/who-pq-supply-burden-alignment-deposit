# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.2 全文一致性复核（只读终检），2026-11-12

与 v1.0/v1.1 终检的关键差别：首次纳入**分母语义断言**与**外部效标断言**，
不再只做版本链／数值 token／逐字一致的内部一致性核查（见 42 号复盘）。

十组检查：
  1 分母契约与来源版本   2 主／对照分母定位与旧值复现
  3 外部语义效标          4 数值回链（主稿 ↔ 权威派生表）
  5 图件与图注            6 补材 S1–S8 与对账
  7 Vancouver／图表引用   8 版本冻结与四篇防火墙
  9 DAS／公开仓库／docx／PDF 产物
 10 旧核验脚本留痕复跑（策展白名单）

输出：投稿包_2026-11-12/verify_result_v1_2.json；stdout 末行 VERDICT。
运行：python verify_B_manuscript_v1_2_2026-11-12.py
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ROOT = Path(r"D:\D\我的论文\全球卫生新博士课题")
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
PROC = ROOT / "数据" / "processed"
RAW = ROOT / "数据" / "raw"
SCRIPTS = ROOT / "数据" / "scripts"
OUTDIR = MAIN / "投稿包_2026-11-12"
FIG_V12 = MAIN / "配图_v1.2_2026-11-12"
FIG_V10 = MAIN / "配图_2026-11-12"

F39 = MAIN / "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md"
F40 = MAIN / "40_B①主稿_补充材料_v1.2_S1-S8_2026-11-12.md"
F41 = MAIN / "41_B①主稿_v1.2_变更前后对照_2026-11-12.md"
F42 = MAIN / "42_B①主稿_分母错误严肃复盘与分母口径纪律_2026-11-12.md"
F34 = MAIN / "34_B①主稿_v1.1_数据可得性定稿_2026-11-12.md"
PROV = RAW / "who_malaria_denominator_provenance_2026-11-12.json"
AUDIT = PROC / "res_B_denominator_change_audit_2026-11-12.json"
PRIMARY = PROC / "res_B_burden_primary_2026-11-12.csv"
SENS = PROC / "res_B_burden_sensitivity_2026-11-12.csv"
RECON = PROC / "res_B_country_set_reconciliation_2026-11-12.csv"
BENCH = PROC / "res_B_tb_external_benchmark_2026-11-12.csv"
ROBUST = PROC / "res_B_aapc_robustness_2026-11-12.csv"
REPO_V12 = MAIN / "公开仓库_v1.2_2026-11-12"
LINK_V12 = MAIN / "公开仓库_v1.2_真实链接_2026-11-12.json"
PAGE_AUDIT = OUTDIR / "_proof_build_v1.2" / "page_audit_result.json"
DOCX_MAN = OUTDIR / "B①_TMIH_主稿_v1.2_2026-11-12.docx"
DOCX_SUPP = OUTDIR / "B①_TMIH_补充材料_v1.2_S1-S8_2026-11-12.docx"
PDF_MAN = OUTDIR / "B①_TMIH_主稿_v1.2_校样PDF_2026-11-12.pdf"
PDF_SUPP = OUTDIR / "B①_TMIH_补充材料_v1.2_S1-S8_校样PDF_2026-11-12.pdf"

N = 0
FAIL = 0
RESULTS = []


def group(name):
    print(f"\n--- {name} ---")


def check(label, ok, detail=""):
    global N, FAIL
    N += 1
    if not ok:
        FAIL += 1
    RESULTS.append({"group": CUR[0], "item": label, "ok": bool(ok), "detail": str(detail)[:240]})
    if not ok:
        print(f"  FAIL: {label} | {str(detail)[:200]}")


CUR = [""]


def read(p):
    return Path(p).read_text(encoding="utf-8")


def rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def part1(text):
    return text.split("# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0]


def prose(text):
    return re.sub(r"\s+", "", text)


def main():
    man_raw, supp, d41, d42, d34 = (read(x) for x in (F39, F40, F41, F42, F34))
    man = part1(man_raw)
    prov, audit = json.loads(read(PROV)), json.loads(read(AUDIT))
    prim, sens, recon, bench, rob = (rows(x) for x in (PRIMARY, SENS, RECON, BENCH, ROBUST))
    pmap = {r["disease"]: r for r in prim}
    smap = {r["disease"]: r for r in sens}

    # ================================================================ 1
    CUR[0] = "组 1 分母契约与来源版本"
    group(CUR[0])
    cat = prov["files"]
    check("WHO 指标目录实读规模 3092", prov["indicator_catalog_size"] == 3092, prov["indicator_catalog_size"])
    check("主分母官方指标名含 Estimated number of malaria cases",
          "Estimated number of malaria cases" in cat["mal_est_cases"]["official_indicator_name"], "")
    check("对照分母官方指标名含 per 1000 population at risk",
          "per 1000 population at risk" in cat["mal_est_incidence"]["official_indicator_name"], "")
    check("【语义断言】两个疟疾指标的分母人群不同",
          cat["mal_est_cases"]["official_indicator_name"] != cat["mal_est_incidence"]["official_indicator_name"]
          and "at risk" in cat["mal_est_incidence"]["official_indicator_name"]
          and "at risk" not in cat["mal_est_cases"]["official_indicator_name"], "")
    check("主分母 WHO Date stamp 留痕",
          "2025-12-19T14:14:17.45+01:00" in str(cat["mal_est_cases"]["source_date_values"]), "")
    check("主分母 2723 条／110 国／2000–2024",
          (cat["mal_est_cases"]["accepted_records"], cat["mal_est_cases"]["n_countries"],
           cat["mal_est_cases"]["year_min"], cat["mal_est_cases"]["year_max"]) == (2723, 110, 2000, 2024), "")
    for key, v in cat.items():
        f = ROOT / v["local_file"]
        check(f"来源文件 SHA-256 一致 {key}", f.is_file() and sha(f) == v["local_sha256"], "")
    check("既有 MALARIA_EST_INCIDENCE 提取与官方指标零差异",
          prov["consistency_check"]["mismatches_against_MALARIA_EST_INCIDENCE"] == []
          and prov["consistency_check"]["verdict"] == "same WHO indicator", "")
    check("主稿 Methods 2.1 写明主分母与取值版本",
          "MALARIA_EST_CASES, 2024 estimates" in man and "read on 12 November 2026" in man, "")
    check("主稿 Methods 2.4 写明无人口乘子与对照分母定位",
          "with no population multiplier" in man and "retained only as a sensitivity comparison (Table S2)" in man, "")
    check("【基线有效性】旧稿的 constant cancels 推理已删除",
          "constant cancels" not in man and "constant cancels" in d34, "")
    check("42 号复盘含六维度与四项门禁",
          all(k in d42 for k in ("数据来源与口径", "分母定义", "计算链路", "指标对齐", "版本同步", "复核盲区",
                               "分母口径确认", "主分母与对照分母区分", "对齐指标一致性条件", "复核留痕")), "")
    check("用户级分母纪律技能已落盘",
          Path(r"C:\Users\Administrator\.workbuddy\skills\分母口径纪律denominator-discipline\SKILL.md").is_file(), "")

    # ================================================================ 2
    CUR[0] = "组 2 主／对照分母定位与旧值复现"
    group(CUR[0])
    ch = audit["diseases"]["Malaria"]
    check("审计文件登记主／对照两个分母字段",
          "primary_denominator" in ch and "comparison_denominator" in ch, "")
    check("对照分母角色标为 sensitivity only",
          "sensitivity only" in ch["comparison_denominator"]["role"], "")
    check("对照分母可精确复现旧派生态",
          ch["comparison_denominator"]["reproduces_old_derived_table"] is True, "")
    check("旧总人口口径 M/C/R25 = 1.9118/0.3184/0.0670",
          (ch["before_total_population"]["M"], ch["before_total_population"]["C"],
           ch["before_total_population"]["R25"]) == (1.9118, 0.3184, 0.067), "")
    check("新官方口径 M/C/R25 = 1.9225/0.3082/0.0652",
          (ch["after_official_cases"]["M"], ch["after_official_cases"]["C"],
           ch["after_official_cases"]["R25"]) == (1.9225, 0.3082, 0.0652), "")
    check("结核／HIV 分母未改标记",
          audit["diseases"]["Tuberculosis"]["denominator_changed"] is False
          and audit["diseases"]["HIV/AIDS"]["denominator_changed"] is False, "")
    check("结核／HIV delta 全为 0",
          all(v == 0 for d in ("Tuberculosis", "HIV/AIDS")
              for v in audit["diseases"][d]["delta"].values()), "")
    legacy = [r for r in sens if r["disease"] == "Malaria" and "total_population" in r.get("calibre", "")]
    check("敏感性表保留疟疾总人口对照行", len(legacy) >= 1, len(legacy))
    check("主文旧主值 1.9118 零命中", "1.9118" not in man, "")
    for token in ("0.0670", "0.3184"):
        check(f"对照数值 {token} 主文仅 1 处", man.count(token) == 1, man.count(token))
    for zone, text in (("摘要", man.split("## 1 Introduction", 1)[0]),
                       ("Conclusions", man.split("## 5 Conclusions", 1)[1].split("## Declarations", 1)[0]),
                       ("Figure captions", man.split("## Figure captions", 1)[1].split("## Supplementary material", 1)[0])):
        check(f"{zone} 对照数值零命中",
              not any(t in text for t in ("1.9118", "0.0670", "0.3184", "91.44%")), "")
    check("主稿两处对照句均带 Table S2／sensitivity 定位",
          man.count("Table S2") >= 3 and "sensitivity comparison" in man, man.count("Table S2"))
    check("41 号对照登记前后数值变化",
          all(k in d41 for k in ("1.9118", "1.9225", "0.3184", "0.3082", "0.0670", "0.0652", "93.92%")), "")

    # ================================================================ 3
    CUR[0] = "组 3 外部语义效标"
    group(CUR[0])
    ext = audit["external_benchmark"]
    check("外部效标 928 配对国家—年", ext["paired_country_years"] == 928, "")
    check("中位绝对相对差 4.21%", abs(ext["median_abs_relative_error"] - 0.0421) < 1e-9, "")
    check("【关键】官方结核病例数指标无印度记录", ext["india_in_TB_e_inc_num"] is False, "")
    check("外部效标 verdict 明确不可作主分母", "cannot replace" in ext["verdict"], "")
    check("主稿 Methods 2.4 登记印度缺口与效标用途",
          "external magnitude check only" in man and "no records for India" in man, "")
    check("主稿 4.4 登记 4.21%／928 配对", "4.21%" in man and "928 paired country-years" in man, "")
    check("外部效标派生表存在且非空", len(bench) == 928, len(bench))
    check("【语义断言】旧脚本 rate_x_pop 分支未被用于疟疾主结果",
          "rate_x_pop" not in man and "MALARIA_EST_CASES" in str(pmap["Malaria"]), "")

    # ================================================================ 4
    CUR[0] = "组 4 数值回链（主稿 ↔ 权威派生表）"
    group(CUR[0])
    MK = ("M_sum_abs_diff", "burden_weighted_supply_coverage_C", "top25_coverage_ratio_R25")
    m = pmap["Malaria"]
    check("主表疟疾 M/C/R25 与主稿一致",
          all(f"{float(m[k]):.4f}" in man for k in MK), m)
    check("主表疟疾国家数 102／81 与主稿一致",
          m["n_countries"] == "102" and m["n_burden_countries"] == "81" and "102 (81)" in man, "")
    check("前四分位负担份额 93.92% 与主表 0.9392 对链",
          abs(float(m["top25pct_burden_share_of_b"]) - 0.9392) < 1e-9 and "93.92%" in man, "")
    check("前四分位供应份额 6.12% 与主表 0.0612 对链",
          abs(float(m["top25pct_burden_share_of_s"]) - 0.0612) < 1e-9 and "6.12%" in man, "")
    tb = pmap["Tuberculosis"]
    check("结核主表 M/C/R25 与主稿一致",
          all(f"{float(tb[k]):.4f}" in man for k in MK), tb)
    check("M 的 bootstrap CI 1.8613–1.9634 与主稿一致",
          "1.8613–1.9634" in man and "1.3354–1.4539" in man, "")
    rlow = [float(r[k]) for r in rob for k in ("hac1_lo", "hac2_lo", "hac3_lo", "hac4_lo")]
    check("实算 HAC 最低下界 13.19% 与主稿一致",
          abs(min(rlow) - 13.19) < 0.005, min(rlow))
    check("稳健性最低下界 13.19% 在主稿与补材均出现",
          "13.19%" in man and "13.19%" in supp, "")
    check("HHI 4175.53 与 product-row 术语在主稿",
          "4175.53" in man and "product-row Herfindahl" in man, "")
    check("AAPC 19.11% 与常规 CI 17.67–20.57 在主稿",
          "19.11%" in man and "17.67–20.57" in man, "")
    check("Word count 3491／300 且正文 ≤3500",
          "3491 words" in man and "300 words" in man, "")
    check("摘要 300 词口径与主稿 Word count 行一致", "300 words in the structured abstract" in man, "")
    for k in ("102 countries", "193 countries", "26 of 102", "49 of 193"):
        check(f"国家集合锚点 {k} 在主稿或图注", k in man, "")

    # ================================================================ 5
    CUR[0] = "组 5 图件与图注"
    group(CUR[0])
    for n in (1, 2, 3):
        for ext in (".png", ".pdf", ".tif"):
            check(f"v1.2 Figure{n}{ext} 存在", (FIG_V12 / f"Figure{n}{ext}").is_file(), "")
    fig_manifest = json.loads(read(FIG_V12 / "manifest.json"))
    check("Figure 3 数据源指向官方分母主表",
          fig_manifest["sources"]["misalign"]["file"] == "res_B_burden_primary_2026-11-12.csv", "")
    check("Figure 1 画布 ylabel 登记与出图脚本一致",
          "Currently listed FPPs by prequalification year (cumulative n)"
          in fig_manifest["figures"]["Figure1"]["texts_drawn_on_canvas"], "")
    caps = read(FIG_V12 / "figure_captions.md")
    for n in (1, 2, 3):
        line = [l for l in man.splitlines() if l.startswith(f"Figure {n} ")]
        check(f"Figure {n} 图注在主稿唯一", len(line) == 1, len(line))
        if line:
            check(f"Figure {n} 图注与图件清单逐字一致", line[0].strip() in caps, "")
    check("Figure 3 图注写明两病种不可比",
          "not compared with one another" in man, "")
    check("Figure 1 图注写明留存清单口径",
          "grouped by year of prequalification" in man and "still listed on 15 September 2026" in man, "")
    old_manifest = json.loads(read(FIG_V10 / "manifest.json"))
    check("原配图_2026-11-12 未被回写（仍指向旧 CSV）",
          old_manifest["sources"]["misalign"]["file"]
          == "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv", "")

    # ================================================================ 6
    CUR[0] = "组 6 补材 S1–S8 与对账"
    group(CUR[0])
    for k in ("## Table S1.", "## Table S2.", "## Notes S3.", "## Table S4.", "## Table S5.",
              "## Table S6.", "## Table S7.", "## Table S8."):
        check(f"补材小节 {k}", k in supp, "")
    check("S6 对账表 9 行（3 病种 × 3 口径）", len(recon) == 9, len(recon))
    check("S6 疟疾主口径 81/29/8/21/11/6/102",
          any(r["disease"] == "Malaria" and r["calibre"] == "primary_official_case_counts"
              and [r["burden_observed_countries"], r["all_29_holder_countries"],
                   r["overlap_burden_and_holder"], r["holder_without_burden"],
                   r["disease_specific_active_holder_countries"],
                   r["active_holder_without_burden"], r["union_n"]]
              == ["81", "29", "8", "21", "11", "6", "102"] for r in recon), "")
    check("S6 统一 b>0 判据说明", "b > 0" in supp and "identical" in supp, "")
    check("S6 provenance 登记 2723／2680／5013",
          all(x in supp for x in ("2723", "2680", "5013")), "")
    check("补材路径为仓库相对路径（无中文路径）",
          "data/raw/" in supp and "数据/raw/" not in supp, "")
    check("S7 映射 137 行与置信度分级",
          "137 rows" in supp and supp.count("| high |") >= 100 and "| medium |" in supp,
          supp.count("| high |"))
    check("S8 29 国码表完整", "ZA | ZAF" in supp and "IN | IND" in supp, "")
    check("S2 主口径与对照口径同行可对照",
          "primary_official_case_counts" in supp and "total_population_multiplier_legacy" in supp, "")

    # ================================================================ 7
    CUR[0] = "组 7 Vancouver／图表引用"
    group(CUR[0])
    refs = man.split("## References", 1)[1].split("## Tables", 1)[0]
    check("References 13 条编号连续",
          all(re.search(rf"(?m)^{i}\. ", refs) for i in range(1, 14)), "")
    check("正文 Vancouver 编号组 7 组",
          len(re.findall(r"\[\d+(?:,\d+)*\]", man.split("## Declarations", 1)[0])) == 7, "")
    firsts = [int(x) for x in re.findall(r"\[(\d+)", man.split("## Declarations", 1)[0])]
    check("7 组编号首号序列 1,4,6,9,11,12,13",
          firsts == [1, 4, 6, 9, 11, 12, 13], firsts)
    for k in ("Figure 1(A,B)", "Figure 2(A,B)", "Figure 3(A,B)", "Table 1", "Table 2", "Table 3"):
        check(f"正文引用 {k}", k in man, "")
    for k in ("Table S1", "Table S2", "Table S4", "Table S5", "Table S6", "Table S7", "Table S8"):
        check(f"补材表号引用 {k}", k in man, "")
    # S3 在补材中是方法注释（Notes S3），不是表格；索引须按真实体例覆盖 S1–S8。
    check("主稿补材索引覆盖 S1–S8（S3 为 Notes）",
          all(f"Table S{i}" in man for i in (1, 2, 4, 5, 6, 7, 8)) and "Notes S3" in man, "")
    # 技术性用法白名单（与 v1.0 终检一致）：first-order autocorrelation 是统计术语，
    # "listed first" 是排序用语，均非首创声明；剔除后再查首创/贡献类禁词。
    m_ban = re.sub(r"first-order|listed first", "", man, flags=re.I)
    check("禁词零命中（首创声明／Phase／工作包／go-no-go／背书）",
          not any(re.search(p, m_ban, re.I) for p in
                  (r"\bfirst\b", r"\bnovel\b", r"theoretical contribution", r"\bPhase\b",
                   r"工作包", r"go-no-go", r"背书", r"延伸许铭")), "")

    # ================================================================ 8
    CUR[0] = "组 8 版本冻结与四篇防火墙"
    group(CUR[0])
    check("34 号 v1.1 稿未被回写（仍为 v1.0.0 DAS）", "release v1.0.0" in d34, "")
    check("32 号 v1.0 稿仍无仓库 URL（冻结留痕）",
          "github.com" not in read(MAIN / "32_B①主稿_v1.0_定稿稿_2026-11-12.md"), "")
    check("36 号内部台账标记禁止外发",
          "不得对外发送" in read(MAIN / "36_B①主稿_专家评审逐点回应与修改计划_2026-11-12.md"), "")
    check("37 号对外回信零自造编号（M1/B1/X1/A17）",
          not any(x in read(MAIN / "37_B①主稿_致审稿专家回信_2026-11-12.md")
                  for x in ("M1", "B1", "X1", "X7", "A17", "A22")), "")
    firewall = ("Comtrade", "comtrade", "HS code", "10,324", "U1/U2/U3", "export value", "出口额")
    for label, text in (("39 号主稿", man), ("40 号补材", supp), ("41 号对照", d41)):
        check(f"{label} 四篇防火墙禁词零命中", not any(x in text for x in firewall),
              [x for x in firewall if x in text])
    check("主稿无 near-complete mismatch 表述", "near-complete mismatch" not in man, "")
    check("主稿无 medicine supply／medicine access 强表述",
          "medicine supply" not in man and "medicine access" not in man, "")
    check("主稿无 grew／expanded／growth trajectory 时间趋势强表述",
          not any(re.search(p, man, re.I) for p in (r"\bgrew\b", r"\bexpanded\b", r"growth trajectory")), "")

    # ================================================================ 9
    CUR[0] = "组 9 DAS／仓库／docx／PDF 产物"
    group(CUR[0])
    check("主稿 DAS 指向 v1.2.0 固定版本",
          "release v1.2.0" in man and "/tree/v1.2.0" in man, "")
    check("v1.2 真实链接证据文件存在", LINK_V12.is_file(), "")
    if LINK_V12.is_file():
        link = json.loads(read(LINK_V12))
        check("证据 tag = v1.2.0", link.get("tag") == "v1.2.0", link.get("tag"))
        check("证据 owner 与仓库一致", link.get("owner") == "kongdeyu0819-rgb", "")
        check("证据远端 tree 一致性通过", link.get("remote_tree_verified") is True, "")
        check("证据匿名 HTTP 200", link.get("anonymous_http", {}).get("repository") == 200, "")
        check("证据 commit SHA 40 位", bool(re.fullmatch(r"[0-9a-f]{40}", link.get("commit_sha", ""))), "")
        check("v1.0.0 历史证据未回写",
              json.loads(read(MAIN / "公开仓库_真实链接_2026-11-12.json"))["tag"] == "v1.0.0", "")
    if REPO_V12.is_dir():
        mf = json.loads(read(REPO_V12 / "MANIFEST.json"))
        tracked = {x["path"] for x in mf["files"]}
        local = {str(p.relative_to(REPO_V12)).replace("\\", "/")
                 for p in REPO_V12.rglob("*") if p.is_file()}
        local.discard("MANIFEST.json")
        local = {p for p in local if not p.startswith("_")}
        check("MANIFEST 不自登记", "MANIFEST.json" not in tracked, "")
        check("本地文件集合与 MANIFEST 一致", tracked == local,
              f"tracked={len(tracked)} local={len(local)} diff={sorted(tracked ^ local)[:6]}")
        check("MANIFEST 每条 SHA-256 与文件一致",
              all(sha(REPO_V12 / x["path"]) == x["sha256"] for x in mf["files"]), "")
        check("仓库 DAS 指向 v1.2.0", "v1.2.0" in read(REPO_V12 / "DATA_AVAILABILITY_STATEMENT.md"), "")
        check("v1.2 官方分母原始提取已入库",
              (REPO_V12 / "data/raw/gho_mal_est_cases_2026-11-12.csv").is_file(), "")
        check("v1.2 主表已入库",
              (REPO_V12 / "data/processed/res_B_burden_primary_2026-11-12.csv").is_file(), "")
        check("v1.2 图件已入库",
              (REPO_V12 / "figures_v1_2/Figure3.png").is_file(), "")
    for label, p in (("主稿 docx", DOCX_MAN), ("补材 docx", DOCX_SUPP),
                     ("主稿校样 PDF", PDF_MAN), ("补材校样 PDF", PDF_SUPP)):
        check(f"{label} 存在且非空", p.is_file() and p.stat().st_size > 20000, "")
    if DOCX_MAN.is_file():
        dt = "\n".join(x.text for x in Document(DOCX_MAN).paragraphs)
        check("主稿 docx 读回含官方分母与关键数值",
              "MALARIA_EST_CASES" in dt and "1.9225" in dt and "13.19%" in dt, "")
        check("主稿 docx 含 4 张真表与 3 张内嵌图",
              len(Document(DOCX_MAN).tables) == 4
              and len(Document(DOCX_MAN).inline_shapes) == 3, "")
    if DOCX_SUPP.is_file():
        check("补材 docx 含 9 张真表", len(Document(DOCX_SUPP).tables) == 9, "")
    if PAGE_AUDIT.is_file():
        pa = json.loads(read(PAGE_AUDIT))
        check("逐页审计 verdict = ALL CLEAN", pa.get("verdict") == "ALL CLEAN", pa.get("failed"))
        check("逐页审计检查 ≥45 项", len(pa.get("checks", [])) >= 45, len(pa.get("checks", [])))
        check("主稿 14 页／补材 ≥12 页",
              pa.get("manuscript_pages") == 14 and pa.get("supplement_pages") >= 12, "")
    if PDF_MAN.is_file() and PDF_SUPP.is_file():
        check("两份校样 PDF 页数与审计台账一致",
              len(PdfReader(PDF_MAN).pages) == 14
              and len(PdfReader(PDF_SUPP).pages) >= 12, "")

    # ================================================================ 10
    CUR[0] = "组 10 旧核验脚本留痕复跑"
    group(CUR[0])
    olds = []
    for pat in ("verify_B_manuscript_v0_[2-8]_*.py", "verify_B_manuscript_methods_results_*.py",
                "verify_B_figures_*.py", "verify_B_figure_count_and_citations_*.py",
                "audit_B_figure_colour_*.py", "verify_B_manuscript_v1_0_*.py",
                "verify_B_data_availability_*.py"):
        olds += sorted(SCRIPTS.glob(pat))
    olds = sorted(set(p.resolve() for p in olds if p.name != Path(__file__).name))
    print(f"  [INFO] ALL CLEAN 约定核验脚本 {len(olds)} 套")
    for p in olds:
        try:
            r = subprocess.run([sys.executable, str(p)], cwd=str(SCRIPTS),
                               capture_output=True, text=True, timeout=420)
            ok = r.returncode == 0 and "ALL CLEAN" in r.stdout
            check(f"{p.name} 复跑 ALL CLEAN", ok,
                  "" if ok else f"rc={r.returncode} tail={r.stdout[-160:]}{r.stderr[-160:]}")
        except subprocess.TimeoutExpired:
            check(f"{p.name} 复跑 ALL CLEAN", False, "timeout 420s")

    payload = {"version": "v1.2", "checks": N, "failed": FAIL,
               "verdict": "ALL CLEAN" if FAIL == 0 else "FAILED",
               "failed_items": [r["item"] for r in RESULTS if not r["ok"]],
               "details": RESULTS}
    (OUTDIR / "verify_result_v1_2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "=" * 60)
    print(f"CHECKS = {N} | FAIL = {FAIL}")
    print("VERDICT = " + payload["verdict"])
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
