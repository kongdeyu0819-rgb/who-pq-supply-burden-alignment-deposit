# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.2 校样 PDF 逐页审计，2026-11-12

检查对象：build_B_pdf_proof_v1_2_2026-11-12.py 产出的两份校样 PDF。
检查内容：每页非空与页序、乱码/替换符/控制字符、3.2 HIV 句、4.3 结核对比句、
Figure 3 图注、Table 2 是否混入 Table 1 行、全部 URL、图表编号引用、
References 页码与 DOI、补材 S1–S8 小节标题与表题。
同时渲染全部页为 PNG 与缩略拼图，供人工逐页目视检视（排版、重叠、截断）。

输出：投稿包_2026-11-12/_proof_build_v1.2/
        page_audit_result.json / page_text.json / pages/*.png / contact_*.png

边界：校样 PDF 由 Markdown 经 pandoc+XeLaTeX 排版，分页与投稿 docx 不同；
正式投稿 PDF 由 v1.2 docx 导出后须按同一清单再核一遍。

运行：python audit_B_pdf_pages_v1_2_2026-11-12.py
"""
import json
import os
import re
import shutil
import subprocess

from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
OUTDIR = os.path.join(MAIN, "投稿包_2026-11-12")
BUILD = os.path.join(OUTDIR, "_proof_build_v1.2")
PAGES = os.path.join(BUILD, "pages")
PDF_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.2_校样PDF_2026-11-12.pdf")
PDF_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_v1.2_S1-S8_校样PDF_2026-11-12.pdf")
PDFFOPPM = shutil.which("pdftoppm")

RESULTS = []


def check(label, ok, detail=""):
    RESULTS.append({"item": label, "ok": bool(ok), "detail": str(detail)[:300]})
    return bool(ok)


def norm(s):
    return re.sub(r"\s+", "", s or "")


def read_pages(path):
    r = PdfReader(path)
    return [p.extract_text() or "" for p in r.pages]


def page_of(pages, token):
    t = norm(token)
    return [i + 1 for i, p in enumerate(pages) if t in norm(p)]


def render(pdf, prefix):
    assert PDFFOPPM, "未找到 pdftoppm，无法渲染页面"
    os.makedirs(PAGES, exist_ok=True)
    for old in os.listdir(PAGES):
        if old.startswith(prefix) and old.endswith(".png"):
            os.remove(os.path.join(PAGES, old))
    cmd = [PDFFOPPM, "-png", "-r", "90", pdf, os.path.join(PAGES, prefix)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"渲染失败：{r.stderr[-800:]}"
    files = sorted(
        os.path.join(PAGES, f) for f in os.listdir(PAGES)
        if f.startswith(prefix) and f.endswith(".png")
    )
    return files


def contact(files, out, cols=5, thumb_w=260):
    imgs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        h = int(im.height * thumb_w / im.width)
        imgs.append(im.resize((thumb_w, h)))
    if not imgs:
        return
    cell_h = max(i.height for i in imgs) + 26
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + 10), rows * (cell_h + 10)), "white")
    d = ImageDraw.Draw(sheet)
    for k, im in enumerate(imgs):
        x = (k % cols) * (thumb_w + 10)
        y = (k // cols) * (cell_h + 10)
        sheet.paste(im, (x, y + 22))
        d.text((x + 4, y + 4), f"p{k+1}", fill="black")
    sheet.save(out)


def main():
    os.makedirs(BUILD, exist_ok=True)
    man_pages = read_pages(PDF_MAN)
    supp_pages = read_pages(PDF_SUPP)
    all_pages = man_pages + supp_pages
    check("主稿校样页数 >= 10", len(man_pages) >= 10, len(man_pages))
    check("补材校样页数 >= 10", len(supp_pages) >= 10, len(supp_pages))
    check("每页文本非空", all(p.strip() for p in all_pages),
          [i + 1 for i, p in enumerate(all_pages) if not p.strip()])

    bad = []
    for i, p in enumerate(all_pages, 1):
        for pat, name in ((r"\ufffd", "replacement char"),
                          (r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "control char"),
                          (r"\u25a1{2,}", "tofu boxes")):
            if re.search(pat, p):
                bad.append((i, name))
    check("全文零替换符／控制字符／方框乱码", not bad, bad)

    man_n = norm("".join(man_pages))
    supp_n = norm("".join(supp_pages))

    # 专家点名的逐项复核
    anchors = [
        ("Results 3.2 HIV/AIDS 趋势句", "HIV/AIDS at 14.75%", True),
        ("Results 3.2 稳健区间一句结论", "lowest lower bound 13.19% per year", True),
        ("Discussion 4.3 结核对比句", "94.89% and 90.48% for tuberculosis", True),
        ("Figure 3 图注：官方疟疾分母", "WHO GHO MALARIA_EST_CASES", True),
        ("Figure 3 图注：四分位国家数", "26 of 102 countries", True),
        ("Figure 3 图注：结核 49 国", "49 of 193 countries", True),
        ("Figure 1 图注：留存清单口径", "grouped by year of prequalification", True),
        ("Table 1 主分母标注", "MALARIA_EST_CASES", True),
        ("Methods 2.4 官方分母定义", "no population multiplier", True),
        ("摘要 稳健区间下界", "lowest lower bound 13.19% per year", True),
        ("作废旧主值 1.9118 不在主稿", "1.9118", False),
        ("作废推理 constant cancels 不在主稿", "constant cancels", False),
    ]
    for label, token, want in anchors:
        got = norm(token) in man_n
        check(label, got == want, f"命中={got}, 期望={want}")

    urls = [
        "https://extranet.who.int/prequal/",
        "https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit",
    ]
    for u in urls:
        check(f"URL 完整：{u[:48]}…", norm(u) in man_n, page_of(man_pages, u))

    # Table 2 不得混入 Table 1 的行标签（按 PDF 全文中的表区块切分）
    i2 = man_n.find(norm("Table 2. Concentration of certificate-holder countries"))
    i3 = man_n.find(norm("Table 3. Chinese-held prequalified"))
    assert i2 >= 0 and i3 > i2, "PDF 全文未定位到 Table 2 / Table 3 表题"
    t2_block = man_n[i2:i3]
    check("Table 2 未混入 Table 1 的 Step／国家集合行",
          norm("Annual observations in the cumulative") not in t2_block
          and norm("Countries in alignment analysis") not in t2_block
          and norm("Certificate-holder countries") not in t2_block,
          f"Table 2 block {i2}:{i3}）")
    check("Table 2 四项指标齐全",
          all(norm(x) in man_n for x in
              ["Herfindahl–Hirschman Index (HHI)", "CR1, largest holder country",
               "CR4, four largest holder countries", "CR8, eight largest holder countries"]), "")

    # 图表编号引用
    for k in ("Figure 1(A,B)", "Figure 2(A,B)", "Figure 3(A,B)",
              "Table 1", "Table 2", "Table 3", "Table S1", "Table S2",
              "Table S4", "Table S5", "Table S6", "Table S7", "Table S8"):
        check(f"引用 {k} 出现在主稿", norm(k) in man_n, page_of(man_pages, k))

    # 参考文献：13 条编号、DOI、中文条目
    ref_pages = "".join(man_pages)
    check("References 13 条编号连续",
          all(re.search(rf"(?m)^{i}\. ", ref_pages) for i in range(1, 14)),
          [i for i in range(1, 14) if not re.search(rf"(?m)^{i}\. ", ref_pages)])
    check("References 含 DOI", "doi:10." in ref_pages, ref_pages.count("doi:10."))
    check("References 中文条目可读", bool(re.search(r"[\u4e00-\u9fff]{4,}", ref_pages)), "")

    # 补材八个小节标题与表题
    for k in ("Table S1.", "Table S2.", "Notes S3.", "Table S4.", "Table S5.",
              "Table S6.", "Table S7.", "Table S8."):
        check(f"补材小节 {k}", norm(k) in supp_n, page_of(supp_pages, k))
    check("补材登记官方分母来源与版本",
          "MALARIA_EST_CASES" in supp_n and "2723" in supp_n, "")
    check("补材含 S6 国家集合对账", norm("Country-set reconciliation") in supp_n, "")
    check("补材含结核外部效标与印度缺口",
          norm("no India records") in supp_n or norm("no records for India") in supp_n, "")

    # 渲染与拼图（人工目视检视用）
    f1 = render(PDF_MAN, "main-")
    f2 = render(PDF_SUPP, "supp-")
    check("渲染页数与 PDF 页数一致", len(f1) == len(man_pages) and len(f2) == len(supp_pages),
          f"{len(f1)}/{len(man_pages)}, {len(f2)}/{len(supp_pages)}")
    contact(f1, os.path.join(BUILD, "contact_main.png"))
    contact(f2, os.path.join(BUILD, "contact_supp.png"))

    with open(os.path.join(BUILD, "page_text.json"), "w", encoding="utf-8") as f:
        json.dump({"manuscript": man_pages, "supplement": supp_pages}, f, ensure_ascii=False, indent=1)
    payload = {
        "manuscript_pages": len(man_pages),
        "supplement_pages": len(supp_pages),
        "checks": RESULTS,
        "failed": [r["item"] for r in RESULTS if not r["ok"]],
        "verdict": "ALL CLEAN" if all(r["ok"] for r in RESULTS) else "FAIL",
        "note": "proof PDF only; final submission PDF must be re-audited from v1.2 docx",
    }
    with open(os.path.join(BUILD, "page_audit_result.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"主稿 {len(man_pages)} 页 / 补材 {len(supp_pages)} 页；检查 {len(RESULTS)} 项")
    for r in RESULTS:
        if not r["ok"]:
            print("  FAIL:", r["item"], r["detail"])
    print("VERDICT =", payload["verdict"])


if __name__ == "__main__":
    main()
