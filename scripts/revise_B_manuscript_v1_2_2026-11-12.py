# -*- coding: utf-8 -*-
"""B① 返修 · v1.1 → v1.2 全文级修订（2026-11-12）

唯一改动来源：WHO 官方疟疾估计病例数成为主分母后，正文、表格、图注、
摘要与补材索引中的对应数值与表述同步更新；同时兑现回信中承诺的确定表述
（概念降调、时间趋势全文一致、稳健区间披露、术语改名、非洲计数、映射口径）。

替换纪律
--------
- 每条替换断言在原文中唯一命中；失败即中止，不静默跳过。
- 长段按「行前缀」定位后整行替换，短句按精确子串替换。
- 旧稿 v1.1 与 v1.0 冻结件一律不回写。
- 自动生成逐条变更前后对照台账（供回传审稿人）。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAIN = os.path.join(ROOT, "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）")
PROC = os.path.join(ROOT, "数据", "processed")
STAMP = "2026-11-12"
SRC = os.path.join(MAIN, "34_B①主稿_v1.1_数据可得性定稿_2026-11-12.md")
OUT = os.path.join(MAIN, "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md")
AUDIT_MD = os.path.join(MAIN, "41_B①主稿_v1.2_变更前后对照_2026-11-12.md")

CHANGELOG = []


def replace_line(text, prefix, new_line, label, note=""):
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, f"[{label}] 行前缀命中 {len(idx)} 次：{prefix[:60]}"
    old = lines[idx[0]]
    lines[idx[0]] = new_line
    CHANGELOG.append((label, note, old, new_line))
    return "\n".join(lines)


def replace_exact(text, old, new, label, note=""):
    c = text.count(old)
    assert c == 1, f"[{label}] 精确片段命中 {c} 次：{old[:70]}"
    CHANGELOG.append((label, note, old, new))
    return text.replace(old, new, 1)


def append_line(text, prefix, extra, label, note=""):
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, f"[{label}] 行前缀命中 {len(idx)} 次"
    old = lines[idx[0]]
    lines[idx[0]] = old + extra
    CHANGELOG.append((label, note, old, lines[idx[0]]))
    return "\n".join(lines)


def prose_words(block):
    """与 polish_B_manuscript_2026-11-12.py 完全相同的纯 prose 计数口径。"""
    body = "\n".join(l for l in block.splitlines()
                     if not re.match(r"^\s{0,3}#{1,6}\s", l))
    return len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body))


def prose_counts(part1):
    abstract = prose_words(part1.split("## Abstract", 1)[1].split("---", 1)[0])
    imrd = prose_words(part1.split("## 1 Introduction", 1)[1]
                       .split("## Declarations", 1)[0])
    return imrd, abstract


def compress_line(text, prefix, new_line, label):
    """定稿篇幅压缩：整行替换，并把 CHANGELOG 中该位置的「变更后」更新为最终文本，
    使对照台账始终显示 v1.1 原文 → v1.2 最终文本，不出现中间态。"""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, f"[压缩/{label}] 行前缀命中 {len(idx)} 次：{prefix[:60]}"
    lines[idx[0]] = new_line
    for k, (lb, note, old, _) in enumerate(CHANGELOG):
        if lb == label:
            CHANGELOG[k] = (lb, note + "；定稿时压缩篇幅", old, new_line)
            break
    else:
        raise AssertionError(f"CHANGELOG 中未找到 {label}")
    return "\n".join(lines)


def main():
    raw = open(SRC, encoding="utf-8").read()
    a = re.search(r"^# PART I — Manuscript text\s*$", raw, flags=re.M)
    b = re.search(r"^# PART II", raw, flags=re.M)
    assert a and b
    head, part1, part2 = raw[:a.end()], raw[a.end():b.start()], raw[b.start():]
    old_imrd, old_abs = prose_counts(part1)
    t = part1

    # ---------- 前页与摘要 ----------
    t = replace_line(t, "# Geographic alignment between",
        "# Geographic alignment between certificate-holder countries of WHO-prequalified medicines and malaria, tuberculosis and HIV/AIDS burden in low- and middle-income countries, 2002–2026",
        "题目", "medicine supply → certificate-holder countries")
    t = replace_line(t, "**Short title:**",
        "**Short title:** Certificate-holder countries and disease burden",
        "短标题", "同步概念降调")
    t = replace_line(t, "Objectives: To characterise",
        "Objectives: To characterise the WHO-prequalified finished pharmaceutical product listing retained on 15 September 2026 by year of prequalification (2002–2026), the distribution of certificate-holder countries and the alignment of listing-row shares of those countries with country-level malaria and tuberculosis burden in low- and middle-income countries; HIV/AIDS alignment is supplementary because the available burden extract ends in 2006.",
        "摘要 Objectives", "去掉 trajectory；明确单时点快照；HIV 明确仅补材")
    t = replace_line(t, "Methods: We conducted",
        "Methods: We conducted a descriptive ecological analysis of publicly available aggregate databases: WHO Prequalification of Medicines Programme CSV exports (a single dated snapshot, 15 September 2026, excluding products withdrawn earlier), the WHO Global Health Observatory indicator catalogue and World Bank World Development Indicators. Countries were the unit of analysis. Holder countries came from a reviewed applicant-to-country mapping with explicit code conversion, and listing-row shares were rebuilt within each therapeutic area. Malaria burden shares used the WHO official estimated malaria case counts (MALARIA_EST_CASES, 2024 estimates); the earlier incidence-times-total-population construction was retained only as a sensitivity comparison. A single-slope log-linear fit summarised the retained stock by prequalification year. Model-based and bootstrap intervals quantified uncertainty in concentration, finite-list proportions and alignment.",
        "摘要 Methods", "写入主分母及对照分母；快照边界前置")
    t = replace_line(t, "Results: Of 649",
        "Results: Of 649 finished pharmaceutical product rows, 558 carried a parseable prequalification date and 648 mapped to 29 holder countries. The retained 2026 stock by prequalification year followed a log-linear slope of 19.11% per year (conventional 95% CI 17.67–20.57; autocorrelation-robust intervals were wider, with the lowest lower bound 13.19% per year). The product-row Herfindahl–Hirschman Index was 4175.53 (95% CI 3737.94–4643.50), with India holding 413 of 648 products (63.73%, 95% CI 60.03–67.44). Chinese-held products represented 24 of 98 malaria products (24.49%, descriptive 95% CI 16.36–34.21) and 1 of 126 tuberculosis products (0.79%, 95% CI 0.02–4.34). Using WHO official estimated case counts, the heaviest-burden quartile held 93.92% of malaria burden against 6.12% of malaria products (n = 102; burden year 2024), versus 94.89% and 90.48% for tuberculosis (n = 193); the total-population sensitivity gave the same direction.",
        "摘要 Results", "grew → retained stock slope；疟疾新数值；稳健区间精确下界 13.19%")
    t = replace_line(t, "**Keywords:**",
        "**Keywords:** WHO prequalification; certificate-holder geography; prequalification listing; malaria; tuberculosis; HIV/AIDS; low- and middle-income countries",
        "关键词", "medicine access → certificate-holder geography")

    # ---------- 引言 ----------
    t = replace_line(t, "We aimed to describe",
        "We aimed to describe the retained 15 September 2026 WHO-prequalified FPP listing by year of prequalification (2002–2026), the concentration of its certificate-holder countries and the alignment between listing-row shares of those countries and country-level disease burden, using a descriptive ecological analysis of WHO prequalification CSV exports, WHO Global Health Observatory (GHO) burden indicators and World Bank World Development Indicators, with the country as the spatial unit. The analysis sets out what a quality-assured listing records and gives a baseline for monitoring how the geography of the listing changes across updates.",
        "引言研究目的", "去掉 trajectory；单时点快照")

    # ---------- Methods ----------
    t = replace_line(t, "We used publicly available aggregate databases.",
        "We used publicly available aggregate databases. Supply-side data came from the WHO Prequalification of Medicines Programme CSV exports (https://extranet.who.int/prequal/), downloaded on 15 September 2026. The finished pharmaceutical products (FPP) list was the master file (649 rows). Burden-side data came from the WHO Global Health Observatory (GHO) OData indicator catalogue (https://ghoapi.azureedge.net/api/), read on 12 November 2026, and from World Bank World Development Indicators for population. The primary malaria denominator was MALARIA_EST_CASES (estimated number of malaria cases), whose records carry the WHO data stamp 19 December 2025 and cover 110 countries over 2000–2024; 2,723 country-year records were retrieved. The earlier sparse extract of MALARIA_EST_INCIDENCE (estimated malaria incidence per 1,000 population at risk) was retained solely for the sensitivity comparison. Tuberculosis used MDG_0000000020 (incidence per 100,000 population) multiplied by total population; TB_e_inc_num (number of incident tuberculosis cases, WHO data stamp 11 November 2026) served as an external magnitude check only. HIV/AIDS used HIV_0000000001 (people living with HIV, count). The observation window was 2002–2026 (25 years, inclusive), bounded by the earliest and latest prequalification dates; 2026 was a partial year of a single dated stock snapshot that excludes products withdrawn before 15 September 2026. Cumulative counts denote products still listed on that date grouped by their year of prequalification; they are not historical year-end stocks.",
        "Methods 2.1 数据来源", "主分母指标码/取值版本/覆盖；删除未使用的 GDP 与卫生支出；修正历史 stock 表述")
    t = replace_line(t, "### 2.2 Study design and calibre",
        "### 2.2 Study design and reporting framework",
        "Methods 2.2 标题", "calibre → reporting framework")
    t = replace_line(t, "Country attribution was defined",
        "Country attribution was defined at certificate-holder level from the free-text Applicant field. Names were normalised by rule, graded for confidence and reviewed where ambiguous; the reviewed mapping contains 137 applicant rows with 137 unique names covering all 649 product rows, of which 110 assignments were graded high, 26 medium and one remained unresolved and was retained as missing rather than assigned. Sixteen Chinese applicant-name variants resolved to approximately 15 firms. The column named iso3 in the reviewed concentration table holds ISO 3166-1 alpha-2 codes, whereas the GHO and World Bank extracts use alpha-3 codes; an explicit 29-country conversion table was applied to every merge so that listing and burden shares refer to the same country set. Disease-specific listing-row shares were reconstructed by joining Therapeutic Area × Applicant to that mapping and normalising within each area by product rows (denominators 98, 126 and 255). All joins were complete (98/98, 126/126 and 255/255). The mapping table with confidence grades and the 29-country conversion table are supplied as Tables S7 and S8.",
        "Methods 2.3 映射", "删除 seven unresolved assigned outside China；137/137 实读口径；补表引用")
    t = replace_line(t, "The outcomes were prequalification year,",
        "The outcomes were prequalification year, therapeutic area, certificate-holder country share and the geographic alignment between listing-row shares and country-level disease burden, all measured at listing level. Burden shares were constructed as a country's estimated number of affected people divided by the sum over countries in the analysis set. For malaria the numerator was the WHO official estimated number of cases (MALARIA_EST_CASES, 2024 estimates for every included country), so no population multiplier was applied. For tuberculosis the WHO incidence per 100,000 population (MDG_0000000020) was multiplied by total population because the indicator's own denominator is total population. For HIV/AIDS the PLHIV count was used directly. The earlier malaria construction — estimated incidence per 1,000 population at risk multiplied by total population — is retained only as a sensitivity comparison (Table S2); multiplying a rate defined on the at-risk population by total population does not recover case counts, because the at-risk fraction varies between countries. WHO GHO publishes no absolute population-at-risk indicator. The official tuberculosis case-count indicator TB_e_inc_num was used as an external magnitude check but not as a denominator, because it contains no records for India. Burden years were 2024 for malaria, 2004–2024 for tuberculosis and 2005–2006 for HIV/AIDS. Malaria and tuberculosis were the primary disease strata; HIV/AIDS, whose GHO extract ends in 2006, is reported in Table S2 as supplementary only.",
        "Methods 2.4 分母定义（核心）", "官方病例数为主分母；总人口版本降为敏感性；删除 constant cancels 与 GDP/CHE")
    t = replace_line(t, "Four measures were defined",
        "Four measures were defined on the union of all 29 holder countries and the countries with a positive burden observation; holder countries without a burden observation remain in the union with b_i = 0. With s_i the disease-specific listing-row share and b_i the burden share, M = Σ|s_i − b_i| (L1 distance, 0–2), D = 0.5·M (0–1), C = Σ b_i·1[s_i > 0] (the burden share located in countries with any listed holder; not procurement coverage), and R25 (the top-quartile supply-to-burden ratio, i.e. supply share divided by burden share among the quartile with the heaviest burden). C, R25 and the quartile shares carry the substantive interpretation. Product rows are equally weighted, so a holder with many listed presentations counts more than a holder with one; these are listing-row indices, not market concentration measures. M approaches its upper bound when the two supports barely overlap — 11 disease-specific active holder countries against 81 malaria and 193 tuberculosis burden countries — and quantifies the geographic narrowness of the listing rather than a shortfall in supplied volumes. Each M is interpreted within its own disease stratum: country sets (n = 102, 193, 151), burden units and burden-year ranges differ across diseases. The criterion b_i > 0 is applied identically in the country-level and summary tables; Table S6 reconciles the country sets for every calibre.",
        "Methods 2.4 指标定义", "union 供给侧写明 29 国；b>0 判据统一；C/R25 改名；产品行等权；M 分病种解释")
    t = replace_line(t, "Trend was summarised",
        "Trend was summarised by a single-slope log-linear model, log(retained stock by prequalification year) = a + b·year, fitted by ordinary least squares over 25 annual observations; the average annual percent change (AAPC) was 100·(exp(b) − 1), estimating the average annual change of that retained stock. The primary 95% interval was the ordinary t interval of the same fit (df = 23, t = 2.0687). Residual first-order autocorrelation was 0.68–0.88 and Durbin–Watson statistics were 0.215–0.496, so two sensitivity intervals were computed for each series: an autocorrelation-consistent interval at lag 3 and a residual moving-block bootstrap (block length 3, 5,000 replicates). The t interval was prespecified as primary. Extending the autocorrelation-consistent lag from 1 to 4, reporting lag-1 to lag-4 residual autocorrelations and refitting after excluding the partial 2026 observation are reported in Table S1; the lag was set by convention and no small-sample degrees-of-freedom correction was applied. All sensitivity intervals are tabulated with their diagnostics in Table S1.",
        "Methods 2.5 趋势", "DW/ACF/lag 1–4/去 2026 均为实算后写入")
    t = replace_exact(t, "Concentration was measured by the Herfindahl–Hirschman Index (HHI)",
        "Concentration was measured by a product-row Herfindahl–Hirschman Index (HHI)",
        "Methods 2.5 集中度", "HHI 明确为 product-row")
    t = replace_exact(t,
        "A country-level scheme, common-support and second-latest-burden-year variants were computed as sensitivities;",
        "A country-level scheme, common-support, second-latest-burden-year and total-population-denominator variants were computed as sensitivities;",
        "Methods 2.5 敏感性", "纳入总人口对照")
    t = append_line(t, "Ethical approval was not required",
        " The GHO indicator catalogue was read on 12 November 2026 and its data stamps are recorded in the provenance file accompanying the derived tables.",
        "Methods 2.7 可复现性", "登记指标目录读取日")
    t = replace_exact(t,
        "Prequalification status carries no information about quantities procured, shipments, national registration, price or patient use.",
        "Prequalification status carries no information about quantities procured, shipments, national registration, price or patient use, and every listing-side index weights product rows equally.",
        "Discussion 4.4 产品行等权", "补充等权边界")

    # ---------- Results ----------
    t = replace_exact(t, "all values denote stock.",
        "all values denote products still listed on the snapshot date grouped by prequalification year.",
        "Results 3.1 存量口径", "消除历史 stock 歧义")
    t = replace_line(t, "On the burden side,",
        "On the burden side, the WHO official malaria case-count extract contained 2,723 country-year observations from 110 countries (2000–2024), with 2024 available for 109 of them. The earlier sparse incidence extract contained 952 observations from 109 countries; the tuberculosis extract contained 957 from 197 countries (2000–2024) and the HIV/AIDS extract 957 from 142 countries (2000–2006). Forty-two regional aggregate codes were excluded. After country-code conversion and matching, the primary analysis comprised 102 countries for malaria (81 with a burden observation, all dated 2024) and 193 for tuberculosis (all with a burden observation); the HIV/AIDS set comprised 151 countries and is reported in Table S2 as supplementary only (burden snapshot ends in 2006). The union of burden countries and all 29 holder countries, with missing burden set to zero, is reconciled for every calibre in Table S6. The denominator chain is summarised in Table 1.",
        "Results 3.1 国家集合", "n 100→102、79→81；负担年统一 2024；对账表")
    t = replace_line(t, "The cumulative FPP stock grew",
        "The retained 2026 stock by prequalification year followed a log-linear slope of 19.11% per year (conventional 95% CI 17.67–20.57) over 2002–2026, with R² = 0.9745 and residual first-order autocorrelation of 0.8779. The slope was steepest for malaria at 24.85% per year (95% CI 21.54–28.25; R² = 0.9268), followed by tuberculosis at 18.28% per year (95% CI 15.49–21.14; R² = 0.9021) and HIV/AIDS at 14.75% per year (95% CI 13.74–15.77; R² = 0.9782). Autocorrelation-robust intervals were wider: across the prespecified and extended schemes the lowest lower bound was 13.19% per year, so a positive slope holds in every series under every interval scheme; excluding the partial 2026 observation gave an all-FPP slope of 19.70% per year (95% CI 18.32–21.10). The full intervals and diagnostics are tabulated in Table S1 and the primary t intervals were used throughout. These slopes describe the retained stock grouped by prequalification year, not annual approval flows. Cumulative trajectories and average annual percentage changes are shown in Figure 1(A,B).",
        "Results 3.2 趋势", "全文级去 growth；稳健区间与去 2026 结果实写")
    t = replace_exact(t, "The HHI was 4175.53",
        "The product-row HHI was 4175.53",
        "Results 3.3 HHI", "术语同步")
    t = replace_exact(t,
        "Three African countries appeared among the holder countries, with 2 rows for Nigeria and 1 each for Uganda and South Africa.",
        "Four African countries appeared among the holder countries: Egypt with 3 rows, Nigeria with 2, and Uganda and South Africa with 1 each.",
        "Results 3.3 非洲计数", "定一种，不留选择项")
    t = replace_exact(t,
        "India held 53.06% of malaria products and 84.92% of tuberculosis products, against 63.73% across all areas",
        "India held 52 of 98 malaria products (53.06%) and 107 of 126 tuberculosis products (84.92%), against 413 of 648 (63.73%) across all areas",
        "Results 3.3 份额分母", "写成 n/N")
    t = replace_exact(t, "and the remaining 19 holder countries are listed in Table S5.",
        "and all 29 holder countries are listed in Table S5.",
        "Results 3.3 补材表引用", "S5 实列 29 国")
    t = replace_line(t, "The heaviest-burden quartile accounted",
        "Using WHO official estimated case counts, the heaviest-burden quartile accounted for 93.92% of estimated malaria burden and 6.12% of disease-specific malaria products, giving a top-quartile supply-to-burden ratio R25 = 0.0652 and a burden share in countries with any listed holder C = 0.3082 across 102 countries (81 with a burden observation, 11 active holder countries). For tuberculosis, the corresponding quartile accounted for 94.89% of burden and 90.48% of products, with R25 = 0.9535 and C = 0.5174 across 193 countries (all with a burden observation, 11 active holder countries). The tuberculosis pattern is consistent with the concentration of tuberculosis products among Indian holders (107 of 126 products). The malaria result was directionally unchanged when the earlier incidence-times-total-population denominator was used (91.44% of burden, R25 = 0.0670, C = 0.3184, n = 100); that construction is reported only in Table S2.",
        "Results 3.4 主结果（核心）", "疟疾全部对齐数值按官方病例数重算；总人口版本降为对照")
    t = replace_line(t, "On the union of holder and burden countries,",
        "On the union of holder and burden countries, M was 1.9225 (bootstrap 95% CI 1.8613–1.9634) with D = 0.9613 for malaria, and 1.3983 (1.3354–1.4539) with D = 0.6991 for tuberculosis. As an L1 distance between two distributions whose supports barely overlap, M quantifies the geographic narrowness of the listing; its magnitude depends on the size of the two supports and on the number of countries with a zero share on one side, which is why C, R25 and the quartile shares carry the substantive interpretation. Each M is interpreted within its own disease stratum, since country sets (n = 102, 193), burden units and burden-year ranges differ. Country-level bootstrap intervals, common-support, second-latest-burden-year, total-population-denominator estimates, and the supplementary HIV/AIDS stratum are tabulated in Table S2. Quartile burden and listing-row shares, and the coverage indices, are compared in Figure 3(A,B).",
        "Results 3.4 L1 距离", "M/CI/D 新值；M 解释分病种")

    # ---------- Discussion ----------
    t = replace_line(t, "Across 2002–2026 the stock",
        "Across 2002–2026 the retained stock of prequalified finished pharmaceutical products, grouped by prequalification year, followed a log-linear slope of 19.11% per year, while the certificate-holder-country distribution remained concentrated and the disease-specific listing-row distribution differed from the geographic distribution of malaria and tuberculosis burden. What the measure records sets the bounds on this reading. The WHO prequalification list is a single stock snapshot taken on 15 September 2026: it contains products still listed on that date and excludes products withdrawn earlier, so the cumulative series describes the size of the retained stock by prequalification year rather than the flow of annual approvals. Prequalification breadth is a product-holder-level quality signal within that listing; registration in destination countries, procurement, delivery and patient access lie outside what the list records. Country attribution comes from certificate-holder names, so the holder country is an applicant-country proxy rather than a manufacturing location or a sales destination. The alignment discussed below is therefore a comparison between listing-row shares and a country-level burden distribution; these bounds apply to every estimate that follows.",
        "Discussion 4.1 主要发现", "expanded → retained stock slope；单时点快照前置")
    t = replace_exact(t, "so the growth rates describe changes in the size of the retained stock rather than approval rates",
        "so the slopes describe changes in the size of the retained stock rather than approval rates",
        "Discussion 4.1 趋势措辞", "去 growth")
    t = replace_exact(t, "The 649 applicants were mapped in 137 rows with graded confidence",
        "The 649 product rows were mapped through 137 applicant rows (137 unique names, 110 high-confidence, 26 medium, one unresolved retained as missing)",
        "Discussion 4.4 映射口径", "与复核表实读一致")
    t = replace_line(t, "Several features of the listing",
        "Several features of the listing offer candidate interpretations of these patterns. India held 413 of 648 mapped products (63.73%), 52 of 98 malaria products (53.06%) and 107 of 126 tuberculosis products (84.92%), which is consistent with the concentration of prequalified generic manufacturing among a small number of holder countries. The heaviest-burden quartile accounted for 93.92% of estimated malaria burden against 6.12% of disease-specific malaria products, whereas the corresponding figures for tuberculosis were 94.89% and 90.48%; the latter pattern may be consistent with the position of India as both the dominant holder country for tuberculosis products and a high-burden country. The two disease strata rest on different country sets, units and reference years, and the tuberculosis estimate is sensitive to the choice of supply denominator. China held 24 of 98 malaria products and 1 of 126 tuberculosis products, a difference that may be consistent with the historical concentration of Chinese applicants in antimalarial products; the listing contains no information on applications, manufacturing capacity or commercial decisions with which to evaluate that possibility. M was 1.9225 for malaria and 1.9760 for the supplementary HIV/AIDS stratum, both close to the upper bound of 2, and 1.3983 for tuberculosis. Because M depends on support size and on the number of zero-share countries, it is reported by disease rather than as a single cross-disease statement; C, R25 and the quartile shares carry the substantive interpretation. Replacing the malaria denominator with WHO official estimated case counts did not change the direction of these findings. Distinguishing among these candidates requires procurement, registration and utilisation data; the interpretation here therefore stays at the level of listing structure.",
        "Discussion 4.3 解释", "删除 all three strata 概括；M 分病种；新数值；说明分母替换未改方向")
    t = replace_line(t, "Burden indicators were matched",
        "Burden indicators were matched at the latest Global Health Observatory value available for each country. Malaria burden is now measured directly from WHO estimated case counts for 2024, so the earlier mismatch between an incidence defined per 1,000 population at risk and a total-population multiplier no longer applies; that earlier construction is retained as a sensitivity comparison and gave the same direction of alignment (91.44% of burden in the heaviest quartile, versus 93.92% under the official case counts). WHO GHO publishes no absolute population-at-risk indicator, so the at-risk fraction could only be recovered diagnostically. Tuberculosis burden still relies on incidence per 100,000 population multiplied by total population; against the WHO official case-count indicator the median absolute relative difference was 4.21% over 928 paired country-years, and that official indicator contains no records for India and therefore cannot replace the denominator. Burden years span 2024 for malaria, 2004–2024 for tuberculosis and 2005–2006 for HIV/AIDS, while the supply side is a 2026 snapshot; cross-country comparisons within a disease stratum therefore retain some year heterogeneity. The HIV/AIDS stratum is reported in Table S2 as supplementary only, and the burden shares should be compared within rather than across disease strata.",
        "Discussion 4.4 分母局限（核心）", "旧 at-risk 高估表述改为已修正；登记结核外部效标与印度缺口")
    t = replace_exact(t, "a common reporting calibre would let",
        "a common reporting standard would let",
        "Discussion 4.5 用词", "calibre → standard")
    t = replace_exact(t, "and the same calibre applied to other product classes.",
        "and the same standard applied to other product classes.",
        "Discussion 4.5 用词", "calibre → standard")
    t = replace_exact(t, "Expanding the number of prequalified products alone is unlikely to change the geographic distribution",
        "Expanding the number of prequalified products alone may not by itself change the geographic distribution",
        "Discussion 4.5 推测措辞", "去掉强断言")
    t = replace_exact(t, "The expansion of the quality-assured listing and its concentrated, unevenly aligned geography are separate findings.",
        "The size of the retained listing and its concentrated, unevenly aligned geography are separate findings.",
        "Discussion 4.5 趋势措辞", "去 expansion")
    t = replace_line(t, "The WHO-prequalified finished pharmaceutical product listing expanded",
        "Grouped by year of prequalification, the WHO-prequalified finished pharmaceutical products still listed on 15 September 2026 span 2002–2026, while certificate holders remained concentrated and disease-specific listing-row shares differed from the geography of malaria and tuberculosis burden.",
        "Conclusions 首段", "去 expanded；单时点快照；术语统一")
    t = replace_exact(t, "so the same calibre can serve as a monitoring baseline.",
        "so the same standard can serve as a monitoring baseline.",
        "Conclusions 用词", "calibre → standard")

    # ---------- 表格、图注、补材索引 ----------
    t = replace_line(t, "**Table 1.**",
        "**Table 1.** Denominator chain and composition of the WHO prequalification listing, snapshot 15 September 2026. FPP, finished pharmaceutical product. All values are counts; no estimate in this table is plotted as a text label in Figures 1–3. The retained stock by prequalification year and its average annual percentage change are shown in Figure 1; their exact values are reported in Results 3.2 and Table S1. Malaria burden in the alignment analysis uses WHO official estimated case counts for 2024 (MALARIA_EST_CASES); the earlier incidence-times-total-population construction is a sensitivity comparison in Table S2. HIV/AIDS burden alignment is supplementary because the local GHO PLHIV extract ends in 2006. All quantities are reproducible from the derivation described in Methods 2.1–2.4 and the derived tables supplied with the submission.",
        "Table 1 表注", "去 trajectory；写明主分母")
    t = replace_line(t, "| 7 | Countries in alignment analysis — malaria (with burden observation) |",
        "| 7 | Countries in alignment analysis — malaria (with burden observation) | 102 (81) |",
        "Table 1 第 7 行", "100 (79) → 102 (81)")
    t = replace_line(t, "**Table 2.**",
        "**Table 2.** Concentration of certificate-holder countries, 15 September 2026 listing snapshot (648 reviewed FPP rows, 29 holder countries). The HHI is a product-row index computed from equally weighted listing rows; it is not a market-share concentration measure. Intervals are descriptive product-row bootstrap intervals for the composition of a finite listing, not sampling error from a superpopulation. Individual country shares and their intervals are plotted in Figure 2(A) and listed in Table S5; they are not repeated as text values here. CR1, CR4, CR8, concentration ratios; FPP, finished pharmaceutical product.",
        "Table 2 表注", "product-row HHI 与等权边界")
    t = replace_line(t, "Figure 1 Cumulative number",
        "Figure 1 WHO-prequalified finished pharmaceutical products (FPPs) still listed on 15 September 2026, grouped by year of prequalification, 2002–2026. (A) Cumulative counts of currently listed FPPs by prequalification year for all FPPs and for malaria, HIV/AIDS and tuberculosis products, from the single dated 15 September 2026 snapshot (n = 25 annual observations); products withdrawn before that date are absent, so these are not historical year-end stocks. (B) Average annual percentage change (AAPC, % per year) with 95% confidence intervals from a single log-linear ordinary least-squares fit to each retained-stock series; intervals shown are the primary t intervals, and the HAC and residual block-bootstrap intervals are wider (Table S1). HIV/AIDS appears in the retained-stock series only; burden alignment is reported for malaria and tuberculosis. Source: WHO prequalification listing, snapshot 15 September 2026",
        "Figure 1 图注与轴口径", "全文级时间趋势一致；稳健区间披露")
    t = replace_exact(t, "the remaining 19 holder countries are tabulated in the supplementary material",
        "all 29 holder countries are tabulated in Table S5",
        "Figure 2 图注", "S5 实列 29 国")
    t = replace_line(t, "Figure 3 Alignment between",
        "Figure 3 Alignment between country-level disease burden and disease-specific listing-row shares. (A) Share of burden and of prequalified supply (%) accounted for by the top quartile of countries ranked by descending burden share, for malaria (26 of 102 countries; WHO official estimated case counts, burden year 2024) and tuberculosis (49 of 193 countries; burden years 2004–2024). (B) Burden share located in countries with any listed holder (C) and the top-quartile supply-to-burden ratio (R25) on a 0–1 index for the same two diseases; the dotted line marks a value of one. Malaria burden is measured from WHO GHO MALARIA_EST_CASES; tuberculosis burden from WHO GHO incidence per 100,000 population multiplied by total population. The two diseases differ in burden unit, country count and year range, so their misalignment indices are not compared with one another. C, burden share in countries with any listed holder (not procurement coverage); R25, ratio of supply to burden share among the top quartile",
        "Figure 3 图注", "新 n/年份/四分位国家数；C 与 R25 改名")
    t = replace_line(t, "| Table S1 |",
        "| Table S1 | Average annual percentage change under primary t, HAC lag 1–4 and residual block-bootstrap interval schemes, with Durbin–Watson statistics, residual autocorrelations and the 2002–2025 refit |",
        "补材索引 S1", "登记实算内容")
    t = replace_line(t, "| Table S2 |",
        "| Table S2 | Alignment sensitivity estimates (country-level bootstrap, common support, second-latest burden year, total-population malaria denominator; supplementary HIV/AIDS stratum) |",
        "补材索引 S2", "纳入总人口对照")
    t = replace_line(t, "| Table S5 |",
        "| Table S5 | All 29 certificate-holder countries: product rows, share, descriptive 95% CI and applicant-name variants |\n| Table S6 | Country-set reconciliation for every calibre, including the WHO official malaria denominator and its total-population sensitivity |\n| Table S7 | Reviewed applicant-to-country mapping with confidence grades (137 rows) |\n| Table S8 | Explicit 29-country ISO 3166-1 alpha-2 to alpha-3 conversion table |",
        "补材索引 S5", "列名订正；S6–S8 按编号顺序接在 S5 之后")
    t = replace_exact(t,
        "| Notes S3 | Method notes carried over from the main text |",
        "| Notes S3 | Method notes on the primary and comparison malaria denominators, interval schemes, ISO code conversion, country-set reconciliation and the limits of listing-row indices |",
        "补材索引 S3", "S3 为方法注释而非表格，描述与 v1.2 实际内容对齐")
    t = replace_exact(t,
        "Tables S1–S3 are reproduced from the Methods–Results manuscript; Tables S4 and S5 are assembled\nfrom the same authoritative derived CSVs as Tables 1–3. The full supplementary file is supplied\nseparately at submission.",
        "Tables S1–S8 are assembled from the authoritative derived CSVs named in each table note. The full supplementary file is supplied separately at submission.",
        "补材索引尾段", "覆盖新增 S6–S8")
    t = replace_line(t, "**Availability of data and materials.**",
        "**Availability of data and materials.** The WHO prequalification CSV extracts (https://extranet.who.int/prequal/; listing snapshot 15 September 2026), the WHO Global Health Observatory burden indicators and the World Bank World Development Indicators are publicly available from their issuing institutions. Copies of the extracts used in this analysis, the WHO official estimated malaria case-count extract and its provenance record, the reviewed applicant-to-country mapping, all derived tables, the three regenerated figure files and the scripts that reproduce every reported quantity are deposited in a public repository at https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit (release v1.2.0: https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit/tree/v1.2.0). Release v1.0.0 is retained unchanged as the historical version of the earlier denominator. All derived tables and the scripts that reproduce them are supplied as supplementary material; MANIFEST.json lists the repository contents with SHA-256 checksums and REPRODUCE.md gives the execution order, so that every reported quantity can be recomputed. No proprietary or individual-level data were used.",
        "Declarations 数据可得性", "固定版本改指 v1.2.0；登记官方分母与 v1.0.0 历史版本")

    # ---------- 定稿篇幅压缩 ----------
    # 新增的方法学细节保留在补材与派生表中；正文只留结论、口径与关键边界，
    # 使纯 prose 词数回到 TMIH Research Article 的 3,500 词上限以内。
    t = compress_line(t, "Methods: We conducted",
        "Methods: We conducted a descriptive ecological analysis of publicly available aggregate databases: WHO Prequalification of Medicines Programme CSV exports (a single dated snapshot, 15 September 2026, excluding products withdrawn earlier), the WHO Global Health Observatory indicator catalogue and World Bank population indicators. Holder countries came from a reviewed applicant-to-country mapping with explicit code conversion, and listing-row shares were rebuilt within each therapeutic area. Malaria burden shares used WHO official estimated case counts (MALARIA_EST_CASES, 2024); the earlier incidence-times-total-population construction was retained only as a sensitivity comparison. A single-slope log-linear fit summarised the retained stock by prequalification year. Model-based and bootstrap intervals quantified uncertainty.",
        "摘要 Methods")
    t = compress_line(t, "We used publicly available aggregate databases.",
        "We used publicly available aggregate databases. Supply-side data came from the WHO Prequalification of Medicines Programme CSV exports (https://extranet.who.int/prequal/), downloaded on 15 September 2026; the finished pharmaceutical products (FPP) list was the master file (649 rows). Burden-side data came from the WHO Global Health Observatory (GHO) OData indicator catalogue, read on 12 November 2026, and World Bank population indicators. The primary malaria denominator was the WHO official estimated number of malaria cases (MALARIA_EST_CASES, 2024 estimates); the earlier incidence-per-1,000-at-risk extract was retained only for sensitivity comparison. Tuberculosis used GHO incidence per 100,000 population multiplied by total population, and HIV/AIDS used the GHO PLHIV count; indicator codes, WHO data stamps and coverage are listed in Table S6. The observation window was 2002–2026 (25 years, inclusive), bounded by the earliest and latest prequalification dates; 2026 was a partial year of a single dated stock snapshot that excludes products withdrawn before 15 September 2026. Cumulative counts denote products still listed on that date grouped by their year of prequalification; they are not historical year-end stocks.",
        "Methods 2.1 数据来源")
    t = compress_line(t, "The outcomes were prequalification year,",
        "The outcomes were prequalification year, therapeutic area, certificate-holder country share and the alignment between listing-row shares and country-level disease burden, all measured at listing level. Burden shares were each country's estimated number of affected people divided by the analysis-set total. Malaria used WHO official estimated case counts (MALARIA_EST_CASES, 2024) with no population multiplier; tuberculosis used incidence per 100,000 population multiplied by total population because that indicator's own denominator is total population; HIV/AIDS used PLHIV counts directly. The earlier malaria construction — incidence per 1,000 population at risk multiplied by total population — is retained only as a sensitivity comparison (Table S2), because the at-risk fraction varies between countries and WHO GHO publishes no absolute population-at-risk indicator. The WHO tuberculosis case-count indicator served as an external magnitude check only, as it contains no records for India. Burden years were 2024 for malaria, 2004–2024 for tuberculosis and 2005–2006 for HIV/AIDS. Malaria and tuberculosis were the primary strata; HIV/AIDS is supplementary (Table S2).",
        "Methods 2.4 分母定义（核心）")
    t = compress_line(t, "Four measures were defined",
        "Four measures were defined on the union of all 29 holder countries and countries with a positive burden observation; holder countries without a burden observation remain in the union with b_i = 0. With s_i the disease-specific listing-row share and b_i the burden share, M = Σ|s_i − b_i| (0–2), D = 0.5·M (0–1), C = Σ b_i·1[s_i > 0] (the burden share in countries with any listed holder, not procurement coverage), and R25 (the top-quartile supply-to-burden ratio). C, R25 and the quartile shares carry the substantive interpretation; product rows are equally weighted, so these are listing-row indices rather than market concentration measures, and M depends on support size and the number of zero-share countries. Each M is interpreted within its own disease stratum, since country sets (n = 102, 193, 151), burden units and burden-year ranges differ. The criterion b_i > 0 is applied identically in country-level and summary tables, and Table S6 reconciles every country set.",
        "Methods 2.4 指标定义")
    t = compress_line(t, "Trend was summarised",
        "Trend was summarised by a single-slope log-linear model, log(retained stock by prequalification year) = a + b·year, fitted by ordinary least squares over 25 annual observations; AAPC was 100·(exp(b) − 1). The primary 95% interval was the ordinary t interval of the same fit (df = 23, t = 2.0687). Residual first-order autocorrelation was 0.68–0.88 and Durbin–Watson statistics were 0.215–0.496, so an autocorrelation-consistent interval at lag 3 and a residual moving-block bootstrap (block length 3, 5,000 replicates) were computed for each series; the t interval was prespecified as primary. HAC lags 1–4, lag-1 to lag-4 residual autocorrelations and a refit excluding the partial 2026 observation are reported in Table S1. The lag was set by convention and no small-sample degrees-of-freedom correction was applied.",
        "Methods 2.5 趋势")
    t = compress_line(t, "On the burden side,",
        "On the burden side, the WHO official malaria case-count extract contained 2,723 country-year observations from 110 countries (2000–2024), with 2024 available for 109; the earlier sparse incidence extract contained 952 observations from 109 countries, the tuberculosis extract 957 from 197 countries (2000–2024) and the HIV/AIDS extract 957 from 142 countries (2000–2006). Forty-two regional aggregate codes were excluded. After code conversion and matching, the primary analysis comprised 102 countries for malaria (81 with a burden observation, all dated 2024) and 193 for tuberculosis (all with a burden observation); the HIV/AIDS set comprised 151 countries and is supplementary (Table S2). Country sets for every calibre are reconciled in Table S6, and the denominator chain is summarised in Table 1.",
        "Results 3.1 国家集合")
    t = compress_line(t, "The retained 2026 stock",
        "The retained 2026 stock by prequalification year followed a log-linear slope of 19.11% per year (conventional 95% CI 17.67–20.57) over 2002–2026, with R² = 0.9745 and residual first-order autocorrelation of 0.8779. The slope was steepest for malaria at 24.85% per year (95% CI 21.54–28.25; R² = 0.9268), followed by tuberculosis at 18.28% (15.49–21.14; R² = 0.9021) and HIV/AIDS at 14.75% (13.74–15.77; R² = 0.9782). Autocorrelation-robust intervals were wider, with the lowest lower bound 13.19% per year across the prespecified and extended schemes; excluding the partial 2026 observation gave an all-FPP slope of 19.70% (95% CI 18.32–21.10). Full intervals and diagnostics are in Table S1 and the primary t intervals were used throughout. These slopes describe the retained stock by prequalification year, not annual approval flows (Figure 1(A,B)).",
        "Results 3.2 趋势")
    t = compress_line(t, "Using WHO official estimated case counts,",
        "Using WHO official estimated case counts, the heaviest-burden quartile accounted for 93.92% of estimated malaria burden and 6.12% of disease-specific malaria products, giving R25 = 0.0652 and C = 0.3082 across 102 countries (81 with a burden observation, 11 active holder countries). For tuberculosis, the quartile accounted for 94.89% of burden and 90.48% of products, with R25 = 0.9535 and C = 0.5174 across 193 countries (all with a burden observation, 11 active holder countries), consistent with the concentration of tuberculosis products among Indian holders (107 of 126). Under the earlier incidence-times-total-population denominator the malaria result was directionally unchanged (91.44%, R25 = 0.0670, C = 0.3184, n = 100); that construction appears only in Table S2.",
        "Results 3.4 主结果（核心）")
    t = compress_line(t, "On the union of holder and burden countries,",
        "On the union of holder and burden countries, M was 1.9225 (bootstrap 95% CI 1.8613–1.9634) with D = 0.9613 for malaria, and 1.3983 (1.3354–1.4539) with D = 0.6991 for tuberculosis. M quantifies the geographic narrowness of the listing and depends on support size and the number of zero-share countries, so C, R25 and the quartile shares carry the substantive interpretation. Each M is interpreted within its own disease stratum, since country sets (n = 102, 193), burden units and burden-year ranges differ. Country-level bootstrap, common-support, second-latest-burden-year and total-population-denominator estimates, and the supplementary HIV/AIDS stratum, are in Table S2. Quartile shares and coverage indices are compared in Figure 3(A,B).",
        "Results 3.4 L1 距离")
    t = compress_line(t, "Across 2002–2026 the retained stock",
        "Across 2002–2026 the retained stock of prequalified finished pharmaceutical products, grouped by prequalification year, followed a log-linear slope of 19.11% per year, while certificate-holder countries remained concentrated and disease-specific listing-row shares differed from the geography of malaria and tuberculosis burden. The WHO prequalification list is a single stock snapshot taken on 15 September 2026 containing products still listed on that date; the cumulative series therefore describes the retained stock by prequalification year rather than annual approvals. Prequalification breadth is a product-holder-level quality signal; registration, procurement, delivery and patient access lie outside what the list records. Country attribution comes from certificate-holder names, so holder country is an applicant-country proxy rather than a manufacturing location or sales destination. The alignment below compares listing-row shares with a country-level burden distribution; these bounds apply to every estimate.",
        "Discussion 4.1 主要发现")
    t = replace_line(t, "The framing of prequalification as a global quality signal",
        "The framing of prequalification as a global quality signal is consistent with earlier accounts of WHO prequalification and of reliance-based regulatory convergence [11]. Concentration among a small set of holder countries is in line with descriptive accounts of how manufacturers seek and maintain prequalification status [12]. Earlier work has generally described the institutional architecture, national regulators' experience, or manufacturers from a single country. Placing certificate-holder country, therapeutic area and disease burden on a common country scale complements that literature: the geographic structure of the listing can be compared directly with that of burden [13], giving a stratification that can be recomputed as the listing is updated.",
        "Discussion 4.2 压缩", "按审稿建议压缩篇幅，保留全部引文编号")
    t = compress_line(t, "Several features of the listing",
        "Several features of the listing offer candidate interpretations. India held 413 of 648 mapped products (63.73%), 52 of 98 malaria products (53.06%) and 107 of 126 tuberculosis products (84.92%), consistent with concentrated prequalified generic manufacturing. The heaviest-burden quartile accounted for 93.92% of estimated malaria burden against 6.12% of malaria products, versus 94.89% and 90.48% for tuberculosis; the latter may be consistent with India's position as both dominant tuberculosis holder and a high-burden country. The two strata rest on different country sets, units and reference years. China held 24 of 98 malaria products and 1 of 126 tuberculosis products, a difference that may be consistent with the historical concentration of Chinese applicants in antimalarials; the listing contains no information on applications, capacity or commercial decisions with which to evaluate this. M was 1.9225 for malaria and 1.9760 for the supplementary HIV/AIDS stratum, both close to the upper bound of 2, and 1.3983 for tuberculosis; because M depends on support size and zero-share countries, it is reported by disease rather than as a cross-disease statement, and C, R25 and the quartile shares carry the substantive interpretation. Replacing the malaria denominator with WHO official case counts did not change the direction of these findings. Distinguishing among these candidates requires procurement, registration and utilisation data.",
        "Discussion 4.3 解释")
    t = compress_line(t, "Burden indicators were matched",
        "Burden indicators were matched at the latest GHO value available for each country. Malaria burden is now measured directly from WHO estimated case counts for 2024, so the earlier mismatch between an incidence defined per 1,000 population at risk and a total-population multiplier no longer applies; that construction remains a sensitivity comparison and gave the same direction (91.44% of burden in the heaviest quartile, versus 93.92% under official case counts). WHO GHO publishes no absolute population-at-risk indicator. Tuberculosis still uses incidence per 100,000 population multiplied by total population; against the WHO official case-count indicator the median absolute relative difference was 4.21% over 928 paired country-years, and that indicator contains no records for India and cannot replace the denominator. Burden years span 2024 for malaria, 2004–2024 for tuberculosis and 2005–2006 for HIV/AIDS, while supply is a 2026 snapshot, so within-stratum comparisons retain some year heterogeneity. HIV/AIDS is supplementary (Table S2), and burden shares should be compared within rather than across strata.",
        "Discussion 4.4 分母局限（核心）")
    t = compress_line(t, "Grouped by year of prequalification,",
        "Grouped by year of prequalification, the WHO-prequalified finished pharmaceutical products still listed on 15 September 2026 span 2002–2026, while certificate holders remained concentrated and listing-row shares differed from the geography of malaria and tuberculosis burden.",
        "Conclusions 首段")

    t = compress_line(t, "Results: Of 649",
        "Results: Of 649 finished pharmaceutical product rows, 558 carried a parseable prequalification date and 648 mapped to 29 holder countries. The retained 2026 stock by prequalification year followed a log-linear slope of 19.11% per year (conventional 95% CI 17.67–20.57; autocorrelation-robust intervals were wider, with the lowest lower bound 13.19% per year). The product-row HHI was 4175.53 (3737.94–4643.50), with India holding 413 of 648 products (63.73%, 60.03–67.44). Chinese-held products represented 24 of 98 malaria products (24.49%, 16.36–34.21) and 1 of 126 tuberculosis products (0.79%, 0.02–4.34). Using WHO official estimated case counts, the heaviest-burden quartile held 93.92% of malaria burden against 6.12% of malaria products (n = 102; 2024), versus 94.89% and 90.48% for tuberculosis (n = 193); the total-population sensitivity gave the same direction.",
        "摘要 Results")
    t = replace_line(t, "The size of a quality-assured listing",
        "A product count and the geographic composition of a listing are separate questions. Holder country, therapeutic area and disease burden are recorded in different data systems and must be placed on a common country scale before their alignment can be measured. The distinction matters for monitoring: later prequalification-year cohorts can contain more listed products while the set of holder countries stays narrow, and reading either pattern requires keeping the listing separate from downstream availability.",
        "引言概念段压缩", "按篇幅上限压缩，保留概念边界")
    t = replace_line(t, "Existing accounts of prequalification",
        "Existing accounts of prequalification have largely described its institutional architecture, the experience of individual national regulators, the assessment and inspection process, or manufacturers from a single country [9,10]. Most aggregate at the programme, product or institution level, leaving little room to describe geographic heterogeneity in who holds certificates. Placing holder country, therapeutic area and disease burden on a common country scale gives a stratification that can be recomputed as the listing is updated.",
        "引言文献段压缩", "保留原有引文编号")
    t = replace_line(t, "This descriptive ecological analysis linked",
        "This descriptive ecological analysis linked a complete stock listing to country-level burden indicators. Point estimates are exact for that listing; the intervals below quantify model uncertainty, compositional variation and sensitivity to definitional choices (reference models in 2.5). The denominator chain ran from 649 FPP rows to 558 dated rows for the 25-year series and 648 mapped rows for concentration, with the single blank applicant retained as missing. Therapeutic-area denominators were malaria 98, tuberculosis 126 and HIV/AIDS 255; forty-two regional aggregate codes were removed by ISO 3166-1 validation. Prequalification breadth is a product-holder-level quality signal, bounded by the distinction between listing status and downstream procurement, delivery or patient access.",
        "Methods 2.2 压缩", "按篇幅上限压缩")
    t = replace_line(t, "The 52 Chinese-held products",
        "The 52 Chinese-held products represented 8.02% (95% CI 6.02–10.19) of the 648 mapped FPP rows, and their distribution across therapeutic areas was uneven. China held 24 of 98 malaria products (24.49%, descriptive 95% CI 16.36–34.21), 16 of 255 HIV/AIDS products (6.27%, 3.63–9.99) and 1 of 126 tuberculosis products (0.79%, 0.02–4.34); the smaller areas and Wilson comparison intervals are tabulated in Table 3 and Table S4, where the wide intervals reflect small denominators. These counts measure China-sourced breadth within the quality-assured listing.",
        "Results 3.5 压缩", "细目已在 Table 3／Table S4，正文不重复")

    # ---------- 词数复算 ----------
    new_imrd, new_abs = prose_counts(t)
    assert new_imrd <= 3500, f"正文 {new_imrd} 词，超过 TMIH 3,500 词上限，需继续压缩"
    t = replace_line(t, "**Word count:**",
        f"**Word count:** {new_imrd} words of manuscript text (Introduction–Conclusions), {new_abs} words in the structured abstract; tables, references and declarations excluded.",
        "Word count", f"同一口径复算：v1.1 {old_imrd}/{old_abs} → v1.2 {new_imrd}/{new_abs}")
    print(f"词数（统一纯 prose 口径）：v1.1 IMRD={old_imrd} Abstract={old_abs} → "
          f"v1.2 IMRD={new_imrd} Abstract={new_abs}")

    # ---------- 输出 ----------
    ledger = "\n\n## 十、v1.2 分母重算全文修订台账\n\n" \
             f"本轮共 {len(CHANGELOG)} 条替换，每条在 v1.1 PART I 唯一命中；" \
             "冻结件 `32`／`34` 与 v1.0、v1.1 docx 未回写。\n\n" \
             "| 位置 | 变更要点 | 变更前（摘要） | 变更后（摘要） |\n|---|---|---|---|\n"
    for label, note, old, new in CHANGELOG:
        def brief(s):
            s = re.sub(r"\s+", " ", s).strip()
            return (s[:90] + "…") if len(s) > 90 else s
        ledger += f"| {label} | {note} | {brief(old)} | {brief(new)} |\n"
    out_text = head + "\n" + t.rstrip() + "\n\n---\n\n" + part2.rstrip() + "\n" + ledger
    open(OUT, "w", encoding="utf-8").write(out_text)

    md = ["# B① 主稿 v1.2 · 变更前后对照", "",
          f"2026 年 11 月 12 日。共 {len(CHANGELOG)} 处替换；旧稿 `34` 号 v1.1 冻结不回写。", "",
          "## 主分母与数值变化", "",
          "| 量 | 变更前（率 × 总人口） | 变更后（WHO 官方估计病例数） |",
          "|---|---|---|",
          "| 疟疾负担分母 | MALARIA_EST_INCIDENCE × 世界银行总人口 | MALARIA_EST_CASES（WHO，2024 估计） |",
          "| 疟疾负担年 | 2006–2024（各国最新可得） | 2024（全部纳入国） |",
          "| 疟疾国家集合 n（有负担观测） | 100 (79) | 102 (81) |",
          "| 前四分位疟疾负担份额 | 91.44% | 93.92% |",
          "| 前四分位疟疾供应份额 | 6.12% | 6.12% |",
          "| M（L1）及其 95% CI | 1.9118 (1.8505–1.9527) | 1.9225 (1.8613–1.9634) |",
          "| D | 0.9559 | 0.9613 |",
          "| C | 0.3184 | 0.3082 |",
          "| R25 | 0.0670 | 0.0652 |",
          "| 结核 M / C / R25 | 1.3983 / 0.5174 / 0.9535 | 不变（分母未改） |",
          "| HIV/AIDS M / C / R25 | 1.9760 / 0.2062 / 0.0084 | 不变（分母未改） |",
          "", "结论方向未改变；原总人口版本仅作 Table S2 敏感性对照。", "",
          "## 逐处替换", "",
          "| 位置 | 变更要点 | 变更前 | 变更后 |", "|---|---|---|---|"]
    for label, note, old, new in CHANGELOG:
        def brief(s):
            s = re.sub(r"\s+", " ", s).strip().replace("|", "\\|")
            return (s[:110] + "…") if len(s) > 110 else s
        md.append(f"| {label} | {note} | {brief(old)} | {brief(new)} |")
    open(AUDIT_MD, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"替换 {len(CHANGELOG)} 条 → {os.path.basename(OUT)}")
    print(f"对照台账 → {os.path.basename(AUDIT_MD)}")
    print("VERDICT = REVISE OK")


if __name__ == "__main__":
    main()
