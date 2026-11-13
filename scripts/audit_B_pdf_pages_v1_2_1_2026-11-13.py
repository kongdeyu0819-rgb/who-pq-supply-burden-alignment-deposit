# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · 校样 PDF 逐页审计（2026-11-13）

边界：被审计对象是内部校样 PDF（pandoc + XeLaTeX），不是投稿 PDF。
最终投稿 PDF 由投稿系统从 v1.2.1 docx 导出后，须按同一清单再逐页核一遍；
本脚本结果不得代填最终 PDF 审计。
"""
import json
import os
import re
import shutil
import subprocess

from pypdf import PdfReader

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
BUILD = os.path.join(MAIN, "投稿包_2026-11-12", "_proof_build_v1.2.1")
PDF_MAN = os.path.join(BUILD, "B①_TMIH_主稿_v1.2.1_校样PDF.pdf")
PDF_SUPP = os.path.join(BUILD, "B①_TMIH_补充材料_v1.2.1_S1-S8_校样PDF.pdf")
PAGES = os.path.join(BUILD, "pages_v1.2.1")
RESULT = os.path.join(BUILD, "page_audit_result_v1_2_1.json")

PDFFOPPM = shutil.which("pdftoppm")
PDFTOTEXT = shutil.which("pdftotext")
MAGICK = shutil.which("magick")
checks = []


def check(item, ok, note=""):
    checks.append({"item": item, "ok": bool(ok), "note": str(note)})


def pdf_text(path):
    """Poppler 提取的文本保留词间空格；pypdf 只用于页数与回退。
    XeLaTeX 校样经 pypdf 提取会吞掉部分英文词间空格，属提取器差异而非排版缺陷。"""
    r = PdfReader(path)
    n = len(r.pages)
    if PDFTOTEXT:
        out = subprocess.run([PDFTOTEXT, "-layout", path, "-"],
                             capture_output=True, text=True, errors="ignore").stdout
        pages = out.split("\f")
    else:
        pages = [p.extract_text() or "" for p in r.pages]
    return pages, n


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def render(pdf, prefix):
    if not PDFFOPPM:
        return []
    os.makedirs(PAGES, exist_ok=True)
    subprocess.run([PDFFOPPM, "-png", "-r", "80", pdf,
                    os.path.join(PAGES, prefix)], capture_output=True, timeout=300)
    return sorted(f for f in os.listdir(PAGES) if f.startswith(prefix) and f.endswith(".png"))


def main():
    assert os.path.isfile(PDF_MAN) and os.path.isfile(PDF_SUPP), "校样 PDF 缺失"
    man_pages, n_man = pdf_text(PDF_MAN)
    supp_pages, n_supp = pdf_text(PDF_SUPP)
    man_n = norm("\n".join(man_pages))
    supp_n = norm("\n".join(supp_pages))
    all_n = man_n + " " + supp_n

    check("主稿校样页数 >= 10", n_man >= 10, f"{n_man} 页")
    check("补材校样页数 >= 10", n_supp >= 10, f"{n_supp} 页")
    check("无替换符 U+FFFD", "\ufffd" not in man_n + supp_n, "")
    check("无裸 Unicode 转义残留", not re.search(r"\\u[0-9a-fA-F]{4}", all_n), "")
    real_pages = man_pages[:n_man] + supp_pages[:n_supp]
    check("无空白页", all(len(p.strip()) > 40 for p in real_pages),
          f"最短页 {min(len(p.strip()) for p in real_pages)} 字符")

    # 逐页审计清单（43 号第五部分 12 项）中可由文本层核验的部分
    check("题目含 certificate-holder countries", "certificate-holder countries" in man_n, "")
    check("结构化摘要四段标题齐全",
          all(k in man_n for k in ("objectives", "methods", "results", "conclusions")), "")
    check("Word count 与定稿一致", "3496 words" in man_n and "300 words" in man_n, "")
    check("Methods 主分母为 WHO 官方估计病例数", "malaria_est_cases" in man_n, "")
    check("Results 3.2 最低下界 13.19%", "13.19%" in man_n, "")
    for tok in ("93.92%", "6.12%", "1.9225", "0.3082", "0.0652", "102 (81)"):
        check(f"Results 3.4 数值 {tok} 存在", tok in man_n, "")
    check("Figure 1–3 图注齐全",
          all(f"figure {i} " in man_n for i in (1, 2, 3)), "")
    check("Table 1–3 正文交叉引用齐全",
          all(f"table {i}" in man_n for i in (1, 2, 3)), "")
    sec = man_n.rsplit("supplementary material", 1)[-1]
    pos = [sec.find("notes s3" if i == 3 else f"table s{i}") for i in range(1, 9)]
    check("补材索引 S1–S8 顺序", all(p >= 0 for p in pos) and pos == sorted(pos), str(pos))
    check("参考文献编号 1–13 连续",
          all(re.search(rf"\b{i}\.\s", man_n) for i in range(1, 14)), "")
    check("数据可得性指向 v1.2.1 固定版本",
          "release v1.2.1" in man_n and "tree/v1.2.1" in man_n, "")
    check("旧固定版本链接不再作为当前版本", "release v1.2.0:" not in man_n, "")

    # 补材结构与本轮修订
    for i in range(1, 9):
        check(f"补材含 S{i}. 独立小节标题",
              re.search(rf"\bs{i}\.\s", supp_n) is not None, "")
    for i in range(1, 9):
        check(f"补材含 Table/Notes S{i} 表题",
              f"table s{i}." in supp_n or (i == 3 and "notes s3." in supp_n), "")
    for tok in ("primary_official_case_counts", "primary_incidence_times_population",
                "primary_plhiv_counts", "calibre_record_denominator_unchanged",
                "burden_observed_only", "legacy_incidence_times_total_population"):
        check(f"补材含新标签 {tok}", tok in supp_n, "")
    check("补材不再把结核/HIV 主口径写成官方病例数标签",
          supp_n.count("primary_official_case_counts") <= 3, "仅疟疾主口径与字典说明允许")
    check("common_support_only 仅作为旧名说明出现",
          supp_n.count("common_support_only") == 1, "")
    check("S6 含 India records present? 列",
          "india records" in supp_n and "present?" in supp_n, "表头跨行，分词核对")
    check("S6 含外部效标分组表",
          "paired country" in supp_n and "all years" in supp_n and "median (%)" in supp_n, "")
    check("S7 计数为 136 非空唯一名称 + 1 空白", "136 unique non-blank" in supp_n, "")
    check("S7 n_products 合计 649", "n_products totals 649" in supp_n, "")
    check("S3 登记标签字典与语义审计",
          "res_b_calibre_dictionary" in supp_n and "res_b_notes_change_audit" in supp_n, "")
    check("补材含 13.19% 与 1.9225", "13.19%" in supp_n and "1.9225" in supp_n, "")

    # 专家指出的排版症状：文本层零命中
    for tok in ("diseasedisease", "calibrecalibre", "nn mm", "primary_official_case\n_counts"):
        check(f"排版症状 {tok} 零命中", tok not in all_n, "")
    check("标签无断裂 token（文本层）",
          "primary_official_case_\n_counts" not in supp_n
          and "total_population_\nmultiplier" not in supp_n, "")

    # docx 结构断言（送出去的那一件）
    from docx import Document
    from docx.oxml.ns import qn
    supp_docx = os.path.join(MAIN, "投稿包_v1.2.1_唯一固定版本_2026-11-13",
                             "B①_TMIH_补充材料_S1-S8_v1.2.1.docx")
    d = Document(supp_docx)
    heads = [p.text.strip() for p in d.paragraphs if p.style.name.startswith("Heading")]
    check("送审补材 docx 有 8 个 Heading 层级小节", len(heads) == 8
          and all(re.match(r"^S[1-8]\.", h) for h in heads), str(heads))
    celltxt = " ".join(c.text for t in d.tables for r in t.rows for c in r.cells)
    check("送审补材 docx 表格含新标签",
          "primary_incidence_times_population" in celltxt
          and "burden_observed_only" in celltxt, "")
    check("送审补材 docx 标签完整无断裂",
          all(k in celltxt for k in ("primary_official_case_counts",
                                     "primary_incidence_times_population",
                                     "primary_PLHIV_counts",
                                     "calibre_record_denominator_unchanged"))
          and "\n_counts" not in celltxt and "case_ counts" not in celltxt, "")
    check("送审补材 docx 全部表格已设重复标题行",
          all(t.rows[0]._tr.find(qn("w:trPr")) is not None
              and t.rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
              for t in d.tables), f"{len(d.tables)} 张表")
    check("送审补材 docx 全部行禁止跨页断裂",
          all(r._tr.find(qn("w:trPr")) is not None
              and r._tr.find(qn("w:trPr")).find(qn("w:cantSplit")) is not None
              for t in d.tables for r in t.rows), "")
    check("送审补材 docx 为 A4 横向",
          d.sections[0].page_width > d.sections[0].page_height, "")

    # 渲染页面供人工目视
    pm = render(PDF_MAN, "main--")
    ps = render(PDF_SUPP, "supp--")
    check("主稿页面渲染完成", len(pm) == n_man, f"{len(pm)} 张")
    check("补材页面渲染完成", len(ps) == n_supp, f"{len(ps)} 张")
    if MAGICK and pm:
        subprocess.run([MAGICK, "montage"] + [os.path.join(PAGES, f) for f in pm] +
                       ["-tile", "4x", "-geometry", "200x+4+4",
                        os.path.join(BUILD, "contact_main_v1.2.1.png")],
                       capture_output=True, timeout=300)
    if MAGICK and ps:
        subprocess.run([MAGICK, "montage"] + [os.path.join(PAGES, f) for f in ps] +
                       ["-tile", "4x", "-geometry", "200x+4+4",
                        os.path.join(BUILD, "contact_supp_v1.2.1.png")],
                       capture_output=True, timeout=300)

    failed = [c for c in checks if not c["ok"]]
    result = {
        "version": "v1.2.1",
        "object": "internal proof PDF + submission docx structure; NOT the final submission PDF",
        "manuscript_pages": n_man, "supplement_pages": n_supp,
        "checks": checks, "total": len(checks), "failed": len(failed),
        "failed_items": [c["item"] for c in failed],
        "final_submission_pdf_audit": "PENDING — must be exported from v1.2.1 docx and re-audited page by page",
        "verdict": "ALL CLEAN" if not failed else "FAILED",
    }
    json.dump(result, open(RESULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for c in failed:
        print("FAIL:", c["item"], "|", c["note"])
    print(f"逐页审计 {len(checks)} 项，失败 {len(failed)} 项 -> {result['verdict']}")
    print("留痕 ->", os.path.relpath(RESULT, MAIN))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
