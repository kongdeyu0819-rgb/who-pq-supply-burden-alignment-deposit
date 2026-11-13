# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · 送审目录装配与历史版本归档（2026-11-13）

送审目录只保留唯一版本：主稿 docx、补材 docx、三张出版级图件、
哈希清单、回传清单、逐页审计清单与变更前后对照表。
历史版本的 docx/PDF 从旧投稿包移入归档子目录（只移动，不删除、不改名内容）。
校样 PDF 与页面渲染图留在内部校样目录，不随送审包提交。
"""
import hashlib
import json
import os
import re
import shutil

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
OLD = os.path.join(MAIN, "投稿包_2026-11-12")
ARCHIVE = os.path.join(OLD, "_archive_history_v1.0-v1.2_2026-11-13")
OUT = os.path.join(MAIN, "投稿包_v1.2.1_唯一固定版本_2026-11-13")
FIG = os.path.join(MAIN, "配图_v1.2_2026-11-12")
PROC_V = os.path.join(ROOT, "数据", "processed_v1.2.1_2026-11-13")

MAN_DOCX = "B①_TMIH_主稿_v1.2.1.docx"
SUPP_DOCX = "B①_TMIH_补充材料_S1-S8_v1.2.1.docx"
FIGS = ["Figure1.tif", "Figure2.tif", "Figure3.tif"]
DOCS = ["回传清单.md", "逐页审计清单.md", "变更前后对照表.md"]
AUDIT_SRC = os.path.join(OLD, "_proof_build_v1.2.1", "page_audit_result_v1_2_1.json")
CHANGE_SRC = os.path.join(PROC_V, "res_B_manuscript_v1_2_1_change_audit.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)

    # ---- 1) 唯一版本文件就位 ----
    for name in (MAN_DOCX, SUPP_DOCX):
        src = os.path.join(OUT, name)
        assert os.path.isfile(src), f"缺送审 Word 文件：{src}"
    for name in FIGS:
        src = os.path.join(FIG, name)
        assert os.path.isfile(src), f"缺出版级图件：{src}"
        shutil.copyfile(src, os.path.join(OUT, name))

    audit = json.load(open(AUDIT_SRC, encoding="utf-8"))
    change = json.load(open(CHANGE_SRC, encoding="utf-8"))
    assert audit["verdict"] == "ALL CLEAN" and audit["failed"] == 0

    # ---- 2) 对外回传清单 ----
    checklist = """# 返修回传清单

本次提交的**唯一固定版本为 v1.2.1**。历史主稿、历史补充材料及其校样文件已移入归档目录，不随本次提交；内部校样 PDF 与页面渲染图亦不随包提交。请只以本目录内的两个 Word 文件与三张图件为准。

| 文件 | 用途 |
|---|---|
| 主稿 Word 文件 | 正文、前页、Tables 1–3、Figure 1–3 图注、Declarations 与 References |
| 补充材料 Word 文件 | S1–S8 全部小节、表格与表注 |
| Figure 1–3 图件（TIFF） | 出版级图件，供投稿系统单独上传 |
| MANIFEST.json | 逐文件 SHA-256 校验和与文件大小 |
| 逐页审计清单 | 最终投稿 PDF 导出后须逐项执行的复核底稿 |
| 变更前后对照表 | 本轮逐项修改的位置与修改前后文本 |

补充材料 v1.2.1 已完成以下修订：S1–S8 均建立以 S 编号起首的独立小节并套用 Word 标题样式；口径标签按各病种实际分母写实，派生表注释同步订正；`burden_observed_only` 口径在 Table S6 增列并给出定义；Table S7 明确 136 个非空唯一名称加 1 行空白缺失、`n_products` 合计 649；Table S6 增加 India 记录可核查列与结核外部量级效标分组表；所有表格设置跨页重复标题行与禁止行内跨页断裂，宽表改为横向页面。

结核与 HIV/AIDS 的主口径和登记行数值仍逐项相同，未作改动；本轮没有重跑分析，没有改动任何统计数值，结论方向不变。数据可得性声明中的固定版本已指向 v1.2.1。

前页作者实名、通讯作者信息与稿件编号按当次确认填写，本次未代填。最终投稿 PDF 由投稿系统从本目录的 Word 文件导出后，须按《逐页审计清单》再逐页复核一次；内部校样结果不代填该次审计。

2026 年 11 月 13 日
"""
    open(os.path.join(OUT, DOCS[0]), "w", encoding="utf-8").write(checklist)

    # ---- 3) 逐页审计清单（如实标注边界） ----
    page_items = [
        "由本次提交的 Word 文件导出，页数与页码连续、无空白页",
        "全篇无替换符、方框、问号乱码；中文参考文献条目汉字正常",
        "题目、短标题、结构化摘要四段、关键词与 Word count 与定稿一致",
        "Methods 主分母为 WHO 官方估计疟疾病例数，总人口版本仅作敏感性对照",
        "Results 稳健性一句结论的最低下界 13.19% 未被回退",
        "Results 疟疾数值 93.92%／6.12%／1.9225／0.3082／0.0652 与 Table 1「102 (81)」一致",
        "Table 1 九行、Table 2 四行、Table 3 六行完整，无串表、无裁切",
        "Figure 1–3 三图完整、图内文字无重叠超框、图注未被压住",
        "正文对 Figure 1–3、Table 1–3 的交叉引用齐全，补材索引按 S1–S8 顺序",
        "参考文献编号连续、DOI 与页码完整",
        "补材 S1–S8 小节标题与表题齐全，Table S6 宽表列不叠印、跨页保留表头",
        "数据可得性声明中的仓库地址与 v1.2.1 固定版本地址可匿名访问且未被截断",
    ]
    lines = [
        "# 最终投稿 PDF 逐页审计清单", "",
        "本清单用于投稿系统从本次提交的 Word 文件导出最终 PDF 之后逐页复核。",
        "**当前状态：全部待执行。** 内部校样 PDF 的程序化核查与逐页目视已完成并通过，",
        "但内部校样的分页与排版不等于投稿 PDF，不得以校样结果代填下表。", "",
        "| 检查项 | 状态 |", "|---|---|",
    ]
    lines += [f"| {i}. {x} | 待执行 |" for i, x in enumerate(page_items, 1)]
    lines += [
        "", "## 已在本次交付中完成的前置核对", "",
        f"- 内部校样程序化逐页核查：{audit['total']} 项全部通过（主稿 {audit['manuscript_pages']} 页、补材 {audit['supplement_pages']} 页）。",
        "- 逐页目视检视：发现并修复了分母来源宽表的列挤压，拆为两张窄表后重新渲染通过。",
        "- 送审 Word 结构核对：补材 S1–S8 共 8 个 Word 标题层级小节；全部表格已设跨页重复标题行与禁止行内断裂；补材为 A4 横向。",
        "- 上述核对的对象是本次提交的 Word 文件与内部校样，不是最终投稿 PDF。", "",
    ]
    open(os.path.join(OUT, DOCS[1]), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ---- 4) 变更前后对照表（对外，零内部编号） ----
    rows = [
        ("口径标签与派生表注释", "Table S2、Table S6、敏感性派生表、主结果表注释",
         "三个病种主口径一律标为官方估计病例数，注释按同一模板复制",
         "疟疾为官方估计病例数、结核为发病率乘总人口、HIV/AIDS 为 PLHIV 现患数；标签与注释按病种分别写实"),
        ("结核与 HIV/AIDS 的登记行", "Table S2、Table S6",
         "标为旧总人口乘子口径，易被读作敏感性对照",
         "标为「分母未替换的口径登记行」，数值与主口径逐项相同，说明不构成敏感性对照"),
        ("仅保留有负担观测国家的口径", "Table S2、Table S6、Notes S3",
         "名为 common_support_only，易被读成供应集与负担集的交集；对账表未列该口径",
         "改名为 burden_observed_only，Table S6 增列三行并给出定义；说明结核该口径与主口径相同、无增量信息"),
        ("补充材料小节结构", "补充材料 Word 文件",
         "S4–S8 只有表题，Word 标题未套用标题样式",
         "S1–S8 均建立以 S 编号起首的独立小节、套用 Word 标题样式，并保留 Table/Notes 表题文字"),
        ("申请人映射计数", "Notes S3、Table S7 表注、主稿 Methods／Results／Discussion",
         "写作 137 个唯一名称；正文把名称变体数与约 15 家企业并列",
         "改为 136 个非空唯一名称加 1 行空白缺失；表注给出 n_products 合计 649；正文不再与家数并列"),
        ("印度记录与外部量级效标", "Table S6、Notes S3",
         "缺印度只在文字中说明，928 对国家—年与 4.21% 未列表",
         "来源表增加 India records present? 列（数值由存入的原始提取实读）；新增按时期分组的外部量级效标表"),
        ("表格跨页与宽表排版", "补充材料 Word 文件",
         "表头跨页不重复、行内文字可跨页断裂、十列宽表挤压",
         "全部表格设置跨页重复标题行与禁止行内断裂；补材改为 A4 横向；宽表拆为两张窄表"),
        ("版本唯一性", "投稿包",
         "历史主稿与历史补充材料与当前版本同目录并存",
         "历史文件移入归档目录；本次只提交一个固定版本目录，附 MANIFEST 与逐文件哈希"),
        ("数据可得性声明", "主稿 Declarations",
         "固定版本指向 v1.2.0",
         "固定版本指向 v1.2.1，两个旧版本登记为历史版本"),
    ]
    ct = [
        "# 变更前后对照表", "",
        "本轮全部为标签、定义、措辞、留痕与排版修订；没有重跑分析，没有改动任何统计数值，结论方向不变。", "",
        "| 意见主题 | 修改位置 | 修改前 | 修改后 |", "|---|---|---|---|",
    ]
    ct += ["| " + " | ".join(r) + " |" for r in rows]
    ct += [
        "", "## 未在本次改动的两项", "",
        "- 结核主口径行与口径登记行数值逐项相同（M = 1.3983、D = 0.6991、C = 0.5174、R25 = 0.9535、前四分位负担份额 = 0.9489），M 单元格不空白，故保留「相同」的表述，未按意见改写为「存在小差异」。意见引用的 0.5147 与 0.9499 未在本次提交的任何文件中出现，请贵方按本目录文件复核。",
        "- 主稿 Results 与摘要已写最低下界 13.19%，Figure 1(B) 图注不含具体下界数值；补材 Table S1 中的 13.22 是 HAC lag 3 的真实结果，与 lag 4 的 13.19 并存，不是版本不同步。", "",
        "2026 年 11 月 13 日", "",
    ]
    open(os.path.join(OUT, DOCS[2]), "w", encoding="utf-8").write("\n".join(ct) + "\n")

    # ---- 5) 历史版本归档（只移动，不删除） ----
    os.makedirs(ARCHIVE, exist_ok=True)
    moved = []
    for f in sorted(os.listdir(OLD)):
        p = os.path.join(OLD, f)
        if os.path.isfile(p) and (f.endswith(".docx") or f.endswith(".pdf")):
            dst = os.path.join(ARCHIVE, f)
            if os.path.abspath(p) != os.path.abspath(dst):
                shutil.move(p, dst)
                moved.append(f)
    # 幂等：首次运行移动，复跑时确认归档目录内已有历史文件
    archived = sorted(f for f in os.listdir(ARCHIVE)
                      if os.path.isfile(os.path.join(ARCHIVE, f))
                      and (f.endswith(".docx") or f.endswith(".pdf")))
    assert archived, "归档目录内没有历史 Word/PDF 文件"
    remaining = [f for f in os.listdir(OLD)
                 if os.path.isfile(os.path.join(OLD, f))
                 and (f.endswith(".docx") or f.endswith(".pdf"))]
    assert not remaining, f"旧投稿包仍残留历史文件：{remaining}"
    moved = moved or archived

    # ---- 6) MANIFEST ----
    deliverables = [MAN_DOCX, SUPP_DOCX] + FIGS + DOCS
    items = []
    for f in deliverables:
        p = os.path.join(OUT, f)
        assert os.path.isfile(p), f"送审文件缺失：{f}"
        items.append({"file": f, "bytes": os.path.getsize(p), "sha256": sha256(p)})
    manifest = {
        "version": "v1.2.1",
        "date": "2026-11-13",
        "statement": "This directory is the single fixed version submitted for review. "
                     "Historical manuscript and supplementary files have been moved to a separate "
                     "archive directory and are not part of this submission.",
        "source_manuscript": "49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md",
        "source_supplement": "48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md",
        "word_count": {"manuscript_text": change["word_count_imrd"]["after"],
                       "abstract": change["word_count_abstract"]["after"]},
        "page_audit": {"proof_checks": audit["total"], "proof_failed": audit["failed"],
                       "final_submission_pdf": "PENDING"},
        "total_files": len(items) + 1,
        "total_bytes": sum(x["bytes"] for x in items),
        "files": items,
    }
    json.dump(manifest, open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # ---- 7) 唯一性断言 ----
    actual = sorted(f for f in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, f)))
    expected = sorted(deliverables + ["MANIFEST.json"])
    assert actual == expected, f"送审目录出现非白名单文件：{set(actual) ^ set(expected)}"
    for f in actual:
        if f.endswith((".md", ".json")):
            t = open(os.path.join(OUT, f), encoding="utf-8").read()
            # A4 是纸张规格，不是内部编号，先排除再扫自造编号
            scan = t.replace("A4", "A-four")
            assert not re.search(r"\b(?:M|B|X|A)\d{1,3}\b", scan), f"{f} 含自造编号"
            assert not re.search(r"\b\d{2}\s*号(?:稿|件|文件|主稿)", t), f"{f} 含内部稿号"
            assert not re.search(r"res_B_|verify_B_|build_B_|draw_B_", t), f"{f} 含工序代号"
    assert not any(f.endswith(".pdf") for f in actual), "送审目录不应含校样 PDF"
    assert not any("v1.0" in f or "v1.1" in f for f in actual), "送审目录混入历史版本"

    print("唯一固定版本目录：", os.path.relpath(OUT, MAIN))
    print(f"  交付文件 {len(actual)} 份 / {manifest['total_bytes']:,} B（不含 MANIFEST 自身）")
    print(f"  历史文件归档 {len(moved)} 份 -> {os.path.relpath(ARCHIVE, MAIN)}")
    for f in moved:
        print("    ARCHIVED", f)
    print(f"  逐页审计留痕 {audit['total']} 项 ALL CLEAN；最终投稿 PDF 审计如实标注待执行")
    print("VERDICT = UNIQUE VERSION V1.2.1 OK")


if __name__ == "__main__":
    main()
