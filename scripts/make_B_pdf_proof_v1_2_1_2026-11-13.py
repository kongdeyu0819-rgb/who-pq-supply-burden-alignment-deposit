# -*- coding: utf-8 -*-
"""派生并运行 v1.2.1 逐页审计用校样 PDF 脚本。

校样 PDF 只放内部校样目录，不随唯一送审版本提交；它用于字符、表格、
图注、URL 与编号引用的逐页核查，不能替代由投稿系统导出的最终 PDF 审计。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "build_B_pdf_proof_v1_2_2026-11-12.py")
DST = os.path.join(HERE, "build_B_pdf_proof_v1_2_1_2026-11-13.py")
code = open(SRC, encoding="utf-8").read()


def rep(old, new, n=1):
    global code
    assert code.count(old) == n, f"锚点命中 {code.count(old)} 次（应为 {n}）：{old[:90]!r}"
    code = code.replace(old, new)


rep("B① 主稿 · v1.2 逐页审计用校样 PDF 装配，2026-11-12",
    "B① 唯一固定版本 · v1.2.1 逐页审计用校样 PDF 装配，2026-11-13")
rep("  排版软件中由 v1.2 docx 导出，并按同一逐页清单再核一遍。",
    "  排版软件中由 v1.2.1 docx 导出，并按同一逐页清单再核一遍。"
    "  v1.2.1 校样 PDF 只放内部校样目录，不随唯一送审版本提交。")
rep("输入：39 号 v1.2 主稿 PART I、40 号补材全文、配图_v1.2_2026-11-12/Figure1–3.png",
    "输入：49 号 v1.2.1 主稿 PART I、48 号补材全文、配图_v1.2_2026-11-12/Figure1–3.png")
rep("SRC_MAN = os.path.join(MAIN, \"39_B①主稿_v1.2_分母重算定稿_2026-11-12.md\")",
    "SRC_MAN = os.path.join(MAIN, \"49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md\")")
rep("SRC_SUPP = os.path.join(MAIN, \"40_B①主稿_补充材料_v1.2_S1-S8_2026-11-12.md\")",
    "SRC_SUPP = os.path.join(MAIN, \"48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md\")")
rep('BUILD = os.path.join(OUTDIR, "_proof_build_v1.2")',
    'BUILD = os.path.join(OUTDIR, "_proof_build_v1.2.1")')
rep('PDF_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.2_校样PDF_2026-11-12.pdf")',
    'PDF_MAN = os.path.join(BUILD, "B①_TMIH_主稿_v1.2.1_校样PDF.pdf")')
rep('PDF_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_v1.2_S1-S8_校样PDF_2026-11-12.pdf")',
    'PDF_SUPP = os.path.join(BUILD, "B①_TMIH_补充材料_v1.2.1_S1-S8_校样PDF.pdf")')
rep('    assert "## Table S8." in supp',
    '    assert "## S8." in supp and "burden_observed_only" in supp')
rep('    p1 = build_pdf("manuscript_v1.2.md", inject_figures(man), PDF_MAN, "主稿校样")\n'
    '    p2 = build_pdf("supplement_v1.2.md", supp, PDF_SUPP, "补材校样",',
    '    p1 = build_pdf("manuscript_v1.2.1.md", inject_figures(man), PDF_MAN, "主稿校样")\n'
    '    p2 = build_pdf("supplement_v1.2.1.md", supp, PDF_SUPP, "补材校样",')
rep('        "engine": "pandoc + XeLaTeX from the same Markdown sources as the v1.2 docx",',
    '        "engine": "pandoc + XeLaTeX from the same Markdown sources as the v1.2.1 docx",')
rep('        "limitation": "pagination/typography differ from the submission docx; final PDF must be exported from docx and re-audited",',
    '        "limitation": "internal proof only, NOT shipped with the single fixed version; pagination/typography differ from the submission docx; final PDF must be exported from docx and re-audited",')
rep('    shutil.copyfile(built, pdf_path)',
    '    if os.path.abspath(built) != os.path.abspath(pdf_path):\n'
    '        shutil.copyfile(built, pdf_path)')
rep('    print("VERDICT = PDF PROOF V1.2 OK")',
    '    print("VERDICT = PDF PROOF V1.2.1 OK")')

open(DST, "w", encoding="utf-8").write(code)
print("已派生", os.path.basename(DST))
r = subprocess.run([sys.executable, DST], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip())
if r.returncode:
    print(r.stderr.strip()[-2500:])
    sys.exit(r.returncode)
