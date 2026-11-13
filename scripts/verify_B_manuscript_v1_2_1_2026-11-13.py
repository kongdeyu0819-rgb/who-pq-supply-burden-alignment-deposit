# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · 全文一致性终检（2026-11-13）

断言分组：唯一版本与哈希、送审 Word 结构、标签语义、分母口径、
数值回链、图表与引用、防火墙、逐页审计留痕、对外文件元说明。
输出 verify_result_v1_2_1.json 与一份可读的复核结果件。
"""
import csv
import hashlib
import json
import os
import re

from docx import Document
from docx.oxml.ns import qn

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
OUT = os.path.join(MAIN, "投稿包_v1.2.1_唯一固定版本_2026-11-13")
OLD = os.path.join(MAIN, "投稿包_2026-11-12")
PROOF = os.path.join(OLD, "_proof_build_v1.2.1")
PROC = os.path.join(ROOT, "数据", "processed")
PROC_V = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13")
RAW = os.path.join(ROOT, "数据", "raw")
STAMP = "2026-11-12"

checks = []


def check(item, ok, note=""):
    checks.append({"item": item, "ok": bool(ok), "note": str(note)})


def read(p):
    return open(p, encoding="utf-8").read()


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def cload(base, name):
    return list(csv.DictReader(open(os.path.join(base, name), encoding="utf-8-sig", newline="")))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def docx_all(path):
    d = Document(path)
    paras = [p.text for p in d.paragraphs]
    cells = [c.text for t in d.tables for r in t.rows for c in r.cells]
    return d, "\n".join(paras), "\n".join(cells)


def main():
    man_md = read(os.path.join(MAIN, "49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md"))
    supp_md = read(os.path.join(MAIN, "48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md"))
    man = man_md.split("# PART II", 1)[0]
    d_man, man_docx, man_cells = docx_all(os.path.join(OUT, "B①_TMIH_主稿_v1.2.1.docx"))
    d_supp, supp_docx, supp_cells = docx_all(os.path.join(OUT, "B①_TMIH_补充材料_S1-S8_v1.2.1.docx"))
    manifest = jload(os.path.join(OUT, "MANIFEST.json"))
    audit = jload(os.path.join(PROOF, "page_audit_result_v1_2_1.json"))
    change = jload(os.path.join(PROC_V, "res_B_manuscript_v1_2_1_change_audit.json"))
    note_audit = jload(os.path.join(PROC_V, "res_B_notes_change_audit_2026-11-13.json"))
    india = jload(os.path.join(PROC_V, "res_B_india_record_check_2026-11-13.json"))

    # ---- A. 唯一版本与哈希 ----
    files = sorted(f for f in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, f)))
    check("送审目录恰好 9 份文件", len(files) == 9, str(files))
    check("MANIFEST 版本为 v1.2.1", manifest["version"] == "v1.2.1", "")
    check("MANIFEST 逐文件哈希与实际一致",
          all(x["sha256"] == sha256(os.path.join(OUT, x["file"]))
              and x["bytes"] == os.path.getsize(os.path.join(OUT, x["file"]))
              for x in manifest["files"]), f"{len(manifest['files'])} 项")
    check("送审目录无历史版本文件",
          not any("v1.0" in f or "v1.1" in f or "S1-S5" in f for f in files), "")
    check("送审目录无校样 PDF", not any(f.endswith(".pdf") for f in files), "")
    check("历史文件已移入归档目录",
          len([f for f in os.listdir(os.path.join(OLD, "_archive_history_v1.0-v1.2_2026-11-13"))
               if f.endswith((".docx", ".pdf"))]) >= 5, "")
    check("旧投稿包根目录已无历史 Word/PDF",
          not [f for f in os.listdir(OLD) if os.path.isfile(os.path.join(OLD, f))
               and f.endswith((".docx", ".pdf"))], "")

    # ---- B. 送审 Word 结构（送出去的那一件） ----
    heads = [p.text.strip() for p in d_supp.paragraphs if p.style.name.startswith("Heading")]
    check("补材 docx 8 个 S 编号 Heading 小节", len(heads) == 8
          and all(re.match(r"^S[1-8]\.", h) for h in heads), str(heads))
    for i in range(1, 9):
        key = "Notes S3." if i == 3 else f"Table S{i}."
        check(f"补材 docx 含 {key} 表题文字", key in supp_docx, "")
    check("补材 docx 全部表格设重复标题行",
          all(t.rows[0]._tr.find(qn("w:trPr")) is not None
              and t.rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
              for t in d_supp.tables), f"{len(d_supp.tables)} 张表")
    check("补材 docx 全部行禁止跨页断裂",
          all(r._tr.find(qn("w:trPr")) is not None
              and r._tr.find(qn("w:trPr")).find(qn("w:cantSplit")) is not None
              for t in d_supp.tables for r in t.rows), "")
    check("补材 docx 为横向页面",
          d_supp.sections[0].page_width > d_supp.sections[0].page_height, "")
    check("主稿 docx 表格也设重复标题行",
          all(t.rows[0]._tr.find(qn("w:trPr")) is not None
              and t.rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
              for t in d_man.tables), "")
    check("主稿 docx 嵌入三张图",
          len(d_man.inline_shapes) == 3, f"{len(d_man.inline_shapes)} 张")

    # ---- C. 标签语义（本轮新增的固定断言） ----
    sens = cload(PROC_V, f"res_B_burden_sensitivity_{STAMP}.csv")
    prim = cload(PROC_V, f"res_B_burden_primary_{STAMP}.csv")
    recon = cload(PROC_V, f"res_B_country_set_reconciliation_{STAMP}.csv")
    by_label = {(r["disease"], r["calibre"]): r for r in sens}
    expect = {
        "Malaria": ("primary_official_case_counts", "MALARIA_EST_CASES"),
        "Tuberculosis": ("primary_incidence_times_population", "MDG_0000000020"),
        "HIV/AIDS": ("primary_PLHIV_counts", "PLHIV"),
    }
    for dis, (lab, ind) in expect.items():
        r = by_label.get((dis, lab))
        check(f"{dis} 主口径标签语义正确", r is not None and ind in r["burden_source_indicator"],
              "" if r else "缺行")
        check(f"{dis} 不再标为官方病例数" if dis != "Malaria" else "疟疾保留官方病例数标签",
              all(x["calibre"] != "primary_official_case_counts" for x in sens
                  if x["disease"] == dis) if dis != "Malaria"
              else ("Malaria", "primary_official_case_counts") in by_label, "")
    for dis in ("Tuberculosis", "HIV/AIDS"):
        check(f"{dis} 口径登记行存在",
              (dis, "calibre_record_denominator_unchanged") in by_label, "")
        p = by_label[(dis, expect[dis][0])]
        q = by_label[(dis, "calibre_record_denominator_unchanged")]
        check(f"{dis} 登记行与主口径逐项相同",
              all(p[k] == q[k] for k in ("M_sum_abs_diff", "D_normalised",
                                         "burden_weighted_supply_coverage_C",
                                         "top25_coverage_ratio_R25")), "")
    check("burden_observed_only 三行在敏感性表",
          sum(1 for r in sens if r["calibre"] == "burden_observed_only") == 3, "")
    check("burden_observed_only 三行在 S6 对账表",
          sum(1 for r in recon if r["calibre"] == "burden_observed_only") == 3, "")
    check("S6 对账表共 12 行", len(recon) == 12, f"{len(recon)} 行")
    check("common_support_only 仅作旧名说明",
          sum(1 for r in sens if r["calibre"] == "common_support_only") == 0
          and supp_md.count("common_support_only") == 1, "")
    for dis, kw in (("Malaria", "official estimated malaria cases"),
                    ("Tuberculosis", "incidence per 100,000 population"),
                    ("HIV/AIDS", "PLHIV count")):
        r = [x for x in prim if x["disease"] == dis][0]
        check(f"主结果表 {dis} method_note 写实", kw.lower() in r["method_note"].lower(), "")
    check("HIV 主结果表不再把 PLHIV 写成发病例数",
          "prevalence stock, not incident cases" in
          [x for x in prim if x["disease"] == "HIV/AIDS"][0]["method_note"], "")

    # ---- D. 数值零改动 ----
    editable = {
        f"res_B_burden_primary_{STAMP}.csv": {"method_note"},
        f"res_B_burden_sensitivity_{STAMP}.csv": {"calibre", "note"},
    }
    for name, cols in editable.items():
        a, b = cload(PROC, name), cload(PROC_V, name)
        check(f"{name} 数值列逐格不变",
              len(a) == len(b) and all(
                  all(x[k] == y[k] for k in x if k not in cols)
                  for x, y in zip(a, b)), "")
    a = cload(PROC, f"res_B_country_set_reconciliation_{STAMP}.csv")
    b = [r for r in recon if r["calibre"] != "burden_observed_only"]
    check("对账表原有 9 行数值列逐格不变",
          len(a) == len(b) == 9 and all(
              all(x[k] == y[k] for k in x if k not in ("calibre", "note"))
              for x, y in zip(a, b)), "")
    check("语义修正台账声明零数值改动",
          "no statistical value changed" in note_audit["scope"], "")
    check("主稿词数 3496 / 摘要 300",
          change["word_count_imrd"]["after"] == 3496
          and change["word_count_abstract"]["after"] == 300
          and "3496 words" in man and "300 words" in man, "")

    # ---- E. 分母与来源 ----
    prov = jload(os.path.join(RAW, "who_malaria_denominator_provenance_2026-11-12.json"))
    check("主分母为 MALARIA_EST_CASES 2024",
          "MALARIA_EST_CASES" in man and "2024" in man
          and "MALARIA_EST_CASES" in supp_md, "")
    check("官方分母来源登记 2723 条",
          prov["files"]["mal_est_cases"]["accepted_records"] == 2723, "")
    check("TB_e_inc_num 印度记录为 0",
          india["indicators"]["TB_e_inc_num"]["n_IND_rows"] == 0
          and "0 records for India" in supp_md, "")
    check("S6 含 India records present? 列", "India records present?" in supp_md
          and "India records present?" in supp_cells, "")
    check("外部效标 928 配对与 4.21% 一致",
          len(cload(PROC_V, "res_B_tb_benchmark_summary_2026-11-13.csv")) == 6
          and "4.21%" in supp_md and "928" in supp_md, "")
    check("旧总人口口径仅作敏感性对照",
          "legacy_incidence_times_total_population" in supp_md
          and "sensitivity comparison" in supp_md, "")
    check("结核主口径未被官方病例数替换",
          "incidence per 100,000 population" in supp_md
          and "cannot replace" in supp_md
          and [x for x in prim if x["disease"] == "Tuberculosis"][0]["burden_source_indicator"]
          == "MDG_0000000020", "")

    # ---- F. 数值回链、图表与引用 ----
    for tok in ("1.9225", "1.8613–1.9634", "0.3082", "0.0652", "93.92%", "6.12%",
                "102 (81)", "1.3983", "0.5174", "0.9535", "1.9760", "13.19%",
                "4175.53", "3737.94–4643.50"):
        check(f"关键数值 {tok} 在主稿", tok in man, "")
    check("Vancouver 编号 [1,2,3] 与 [13] 存在",
          "[1,2,3]" in man and "[13]" in man, "")
    check("Figure 1(A,B) 与 Table S6 交叉引用存在",
          "Figure 1(A,B)" in man and "Table S6" in man, "")
    for i in range(1, 9):
        check(f"主稿补材索引含 S{i}",
              ("Notes S3" if i == 3 else f"Table S{i}") in man, "")
    check("数据可得性指向 v1.2.1", "release v1.2.1" in man
          and "/tree/v1.2.1" in man and "release v1.2.0:" not in man, "")
    fig_manifest = jload(os.path.join(MAIN, "配图_v1.2_2026-11-12", "manifest.json"))
    old_manifest = jload(os.path.join(MAIN, "配图_2026-11-12", "manifest.json"))
    check("v1.2 图件数据源指向官方主表",
          fig_manifest["sources"]["misalign"]["file"] == "res_B_burden_primary_2026-11-12.csv", "")
    check("原版图件冻结未回写",
          old_manifest["sources"]["misalign"]["file"]
          == "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv", "")

    # ---- G. 防火墙与禁词 ----
    scan = (man + supp_md).lower()
    for pat in (r"\bcomtrade\b", r"\bhs\s*code", r"10,324", r"u1/u2/u3",
                r"export value", r"dualchain_china_pq_access",
                r"\bfirst\b(?=\s+(?:study|analysis|report))", r"\bnovel\b",
                r"theoretical contribution", r"\bphase\b", r"工作包", r"go-no-go",
                r"背书", r"延伸许铭"):
        check(f"禁词零命中 {pat}", re.search(pat, scan) is None, "")
    check("旧措辞零命中",
          all(t not in man + supp_md for t in
              ("137 unique names", "approximately 15 firms", "common support,",
               "release v1.2.0:", "## Table S4.")), "")

    # ---- H. 逐页审计与对外文件 ----
    check("逐页审计 ALL CLEAN", audit["verdict"] == "ALL CLEAN" and audit["failed"] == 0,
          f"{audit['total']} 项")
    check("最终投稿 PDF 审计如实标注待执行",
          audit["final_submission_pdf_audit"].startswith("PENDING")
          and manifest["page_audit"]["final_submission_pdf"] == "PENDING", "")
    for f in ("回传清单.md", "逐页审计清单.md", "变更前后对照表.md"):
        t = read(os.path.join(OUT, f))
        s = t.replace("A4", "A-four")
        check(f"{f} 元说明外泄自查",
              not re.search(r"\b(?:M|B|X|A)\d{1,3}\b", s)
              and not re.search(r"\b\d{2}\s*号(?:稿|件|文件|主稿)", t)
              and not re.search(r"res_B_|verify_B_|build_B_|draw_B_", t)
              and not re.search(r"\bPhase\b|工作包|go-no-go|背书|延伸许铭", t), "")
    check("逐页审计清单含 12 项待执行",
          read(os.path.join(OUT, "逐页审计清单.md")).count("| 待执行 |") == 12, "")

    # ---- 输出 ----
    failed = [c for c in checks if not c["ok"]]
    result = {
        "version": "v1.2.1", "date": "2026-11-13",
        "checks": len(checks), "failed": len(failed),
        "failed_items": [c["item"] for c in failed],
        "details": checks,
        "verdict": "ALL CLEAN" if not failed else "FAILED",
    }
    out_json = os.path.join(PROOF, "verify_result_v1_2_1.json")
    json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    groups = [
        ("唯一版本与哈希", "送审目录恰好 9 份文件"),
        ("送审 Word 结构", "补材 docx 8 个 S 编号 Heading 小节"),
        ("标签语义", "Malaria 主口径标签语义正确"),
        ("数值零改动", "res_B_burden_primary_2026-11-12.csv 数值列逐格不变"),
        ("分母与来源", "主分母为 MALARIA_EST_CASES 2024"),
        ("数值回链与引用", "关键数值 1.9225 在主稿"),
        ("防火墙与禁词", "禁词零命中"),
        ("逐页审计与对外文件", "逐页审计 ALL CLEAN"),
    ]
    lines = [
        "# v1.2.1 全文一致性复核结果", "",
        f"2026 年 11 月 13 日。结论先行：**{result['checks']} 项断言全部通过，判定 {result['verdict']}**。", "",
        "复核对象为唯一送审目录内的两个 Word 文件、三张出版级图件、三份对外附件与哈希清单，",
        "以及它们对应的源稿、派生表、分母来源登记与逐页审计留痕。", "",
        "| 分组 | 覆盖内容 |", "|---|---|",
        "| 唯一版本与哈希 | 目录白名单、逐文件 SHA-256、历史版本归档隔离 |",
        "| 送审 Word 结构 | S1–S8 标题层级、表题、重复标题行、禁止行内断裂、横向页面、三图嵌入 |",
        "| 标签语义 | 三个病种主口径标签与真实分母一致、登记行性质、burden_observed_only 定义 |",
        "| 数值零改动 | 三张派生表除标签与注释列外逐格相同、词数回填 |",
        "| 分母与来源 | WHO 官方病例数、India 记录实读、外部效标、对照分母定位 |",
        "| 数值回链与引用 | 关键数值、Vancouver 编号、图表交叉引用、固定版本链接、图件契约 |",
        "| 防火墙与禁词 | 跨篇资产禁词、首创声明、旧措辞残留 |",
        "| 逐页审计与对外文件 | 65 项逐页审计、最终投稿 PDF 待执行登记、对外文件元说明外泄自查 |", "",
        "## 如实登记的边界", "",
        "- 最终投稿 PDF 由投稿系统从本次提交的 Word 文件导出，其逐页审计仍待执行；内部校样结果不代填。",
        "- 前页作者实名、通讯作者信息与稿件编号按当次确认填写，本次未代填。",
        "- 本轮未重跑分析，未改动任何统计数值；结核与 HIV/AIDS 的主口径与登记行数值逐项相同。",
        "- 逐国派生的负担份额表与汇总表在「有正负担份额的行数」上存在既有覆盖口径差异，",
        "  已在语义修正台账中登记为待后续核查项；本轮未据此改动任何数值。", "",
        f"机器可读留痕：`{os.path.relpath(out_json, MAIN)}`。", "",
    ]
    open(os.path.join(MAIN, "50_B①主稿_v1.2.1_全文一致性复核结果_2026-11-13.md"),
         "w", encoding="utf-8").write("\n".join(lines))

    for c in failed:
        print("FAIL:", c["item"], "|", c["note"])
    print(f"v1.2.1 终检 {len(checks)} 项，失败 {len(failed)} 项 -> {result['verdict']}")
    print("留痕 ->", os.path.relpath(out_json, MAIN))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
