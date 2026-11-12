# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.2 逐页审计用校样 PDF 装配，2026-11-12

用途与边界（务必如实向审稿人说明）：
  - 本机无 Microsoft Word / LibreOffice，无法从投稿 docx 直接导出投稿用 PDF。
  - 本脚本用 pandoc + XeLaTeX 把**同一份 Markdown 源**排成校样 PDF，供逐页
    核查字符、表格、图注、URL、参考文献与图表编号引用。
  - 校样 PDF 的行距、字体大小与分页**不等同**于投稿 docx；正式投稿 PDF 仍需在
    排版软件中由 v1.2 docx 导出，并按同一逐页清单再核一遍。
  - 不重写 prose、不改数值；只在 Figure 1–3 图注前插入对应 PNG。

输入：39 号 v1.2 主稿 PART I、40 号补材全文、配图_v1.2_2026-11-12/Figure1–3.png
输出：投稿包_2026-11-12/B①_TMIH_主稿_v1.2_校样PDF_2026-11-12.pdf
      投稿包_2026-11-12/B①_TMIH_补充材料_v1.2_S1-S8_校样PDF_2026-11-12.pdf
      投稿包_2026-11-12/_proof_build_v1.2/ （中间 md、图片副本、页数台账）

运行：python build_B_pdf_proof_v1_2_2026-11-12.py
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
SRC_MAN = os.path.join(MAIN, "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md")
SRC_SUPP = os.path.join(MAIN, "40_B①主稿_补充材料_v1.2_S1-S8_2026-11-12.md")
FIGDIR = os.path.join(MAIN, "配图_v1.2_2026-11-12")
OUTDIR = os.path.join(MAIN, "投稿包_2026-11-12")
BUILD = os.path.join(OUTDIR, "_proof_build_v1.2")
PDF_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.2_校样PDF_2026-11-12.pdf")
PDF_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_v1.2_S1-S8_校样PDF_2026-11-12.pdf")

PANDOC = shutil.which("pandoc")
assert PANDOC, "未找到 pandoc，无法生成校样 PDF"


def manuscript_part1():
    t = open(SRC_MAN, encoding="utf-8").read()
    return t.split("# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0].strip()


def inject_figures(text):
    """仅在三条图注前插入对应 PNG；图注文字本身保持逐字不变。"""
    out, hits = [], []
    for line in text.splitlines():
        m = re.match(r"^(Figure [123])\s", line)
        if m:
            n = int(m.group(1).split()[-1])
            out.append(f"![](Figure{n}.png){{width=16cm}}")
            out.append("")
            hits.append(n)
        out.append(line)
    assert hits == [1, 2, 3], f"图注插入顺序异常：{hits}"
    return "\n".join(out)


def build_pdf(md_name, md_text, pdf_path, label, landscape=False, fontsize="11pt"):
    md_path = os.path.join(BUILD, md_name)
    open(md_path, "w", encoding="utf-8").write(md_text)
    # 补材含 10 列国家集合对账表与 137 行映射表，纵向 A4 会挤列；
    # 校样改用横向 + 小号字，保证宽表可读。这是校样排版选择，不改任何数值。
    geom = "geometry:margin=1.6cm,landscape" if landscape else "geometry:margin=2.4cm"
    cmd = [
        PANDOC, md_name, "-o", os.path.basename(pdf_path),
        "--pdf-engine=xelatex",
        "-V", "CJKmainfont=SimSun",
        "-V", "mainfont=Times New Roman",
        "-V", f"fontsize={fontsize}",
        "-V", geom,
        "--wrap=none",
    ]
    r = subprocess.run(cmd, cwd=BUILD, capture_output=True, text=True, timeout=300)
    built = os.path.join(BUILD, os.path.basename(pdf_path))
    assert r.returncode == 0 and os.path.isfile(built), (
        f"{label} pandoc 失败：{r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
    )
    shutil.copyfile(built, pdf_path)
    pages = len(PdfReader(pdf_path).pages)
    assert pages >= 3 and os.path.getsize(pdf_path) > 20000, f"{label} PDF 疑似空白"
    print(f"{label}: {pages} 页, {os.path.getsize(pdf_path)//1024} KB")
    return pages


def main():
    os.makedirs(BUILD, exist_ok=True)
    for n in (1, 2, 3):
        src = os.path.join(FIGDIR, f"Figure{n}.png")
        assert os.path.isfile(src), f"缺图件：{src}"
        shutil.copyfile(src, os.path.join(BUILD, f"Figure{n}.png"))

    man = manuscript_part1()
    assert "MALARIA_EST_CASES" in man and "13.19%" in man
    supp = open(SRC_SUPP, encoding="utf-8").read().strip()
    assert "## Table S8." in supp

    p1 = build_pdf("manuscript_v1.2.md", inject_figures(man), PDF_MAN, "主稿校样")
    p2 = build_pdf("supplement_v1.2.md", supp, PDF_SUPP, "补材校样",
                   landscape=True, fontsize="9pt")

    ledger = {
        "purpose": "page-by-page audit proof; NOT the submission PDF",
        "engine": "pandoc + XeLaTeX from the same Markdown sources as the v1.2 docx",
        "limitation": "pagination/typography differ from the submission docx; final PDF must be exported from docx and re-audited",
        "manuscript_pdf": os.path.basename(PDF_MAN),
        "manuscript_pages": p1,
        "supplement_pdf": os.path.basename(PDF_SUPP),
        "supplement_pages": p2,
        "figures_embedded": ["Figure1.png", "Figure2.png", "Figure3.png"],
    }
    with open(os.path.join(BUILD, "proof_ledger.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print("VERDICT = PDF PROOF V1.2 OK")


if __name__ == "__main__":
    main()
