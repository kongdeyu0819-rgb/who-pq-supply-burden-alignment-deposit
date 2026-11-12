# WHO prequalification supply–burden alignment: data and code deposit

Public data and code deposit supporting the manuscript *"WHO-prequalified
medicines, 2002–2026: supply concentration and country-level alignment with
malaria and tuberculosis burden"* (submitted to *Tropical Medicine &
International Health*).

## What this deposit contains

| Directory | Contents |
|---|---|
| `data/raw/` | 11 public aggregate extracts downloaded on 15 September 2026: four WHO Prequalification CSV exports (finished pharmaceutical products, APIs, vaccines, IVDs), four WHO Global Health Observatory indicators (malaria incidence, PLHIV, tuberculosis incidence, UHC service coverage) and three World Bank World Development Indicators (population, GDP per capita, health expenditure per capita). |
| `data/processed/` | 13 authoritative derived tables (2 anchor series, 3 reviewed country/concentration mappings, 8 uncertainty estimates incl. the two `_revised` alignment files and the summary JSON) plus `res_B_china_pq_breadth_input.csv`, a 52-row PQ-side projection used as the numerator for China's prequalification breadth. |
| `figures/` | The three 600-dpi main figures, their English captions, the drawing contract and the provenance manifest. |
| `scripts/` | 15 reproducible Python scripts: uncertainty estimation, calibre checks, disease-specific supply reconstruction, figure drawing and verification, manuscript assembly, language revision, Vancouver numbering and DOCX assembly. |

`MANIFEST.json` lists every file with its byte size, SHA-256 and local source.
`REPRODUCE.md` gives the execution order. `DATA_AVAILABILITY_STATEMENT.md` holds the
statement printed in the manuscript.

## Provenance and interpretation

- The WHO prequalification FPP list is a **complete stock snapshot** as of
  15 September 2026. It is not a flow of registration events and excludes products
  withdrawn before that date; 2026 is a partial year.
- Prequalification breadth is a **product-holder-level quality signal within the
  WHO listing**. It is not national registration, procurement, delivery or patient
  access.
- `Applicant` is a proxy for the holder's country, not a hard field; the reviewed
  applicant-to-country mapping is supplied in `data/processed/`.
- The analysis is descriptive. All intervals quantify model uncertainty,
  compositional variation or sensitivity to definitional choices, not sampling
  error from a superpopulation.

## Firewall statement

This deposit contains **only** publicly available aggregate institutional data
and derived results for the supply-side / burden-side analysis. It contains no
bilateral trade-flow or tariff-line data, no single-procurement shipment records,
no individually linked regulatory-event data, no individual-level observations,
and no credentials of any kind. Bridge artefacts belonging to companion analyses
are deliberately excluded; the single PQ-side input needed by the estimation
script is supplied here under a neutral filename, byte-identical to its local
source. Deprecated v1 alignment estimates (computed with an all-area supply
share) are excluded from the manuscript; the `_revised` disease-specific
estimates are the authoritative results. Two legacy rows retained inside the
derived CSVs are explicitly flagged as deprecated and serve only as provenance
of the 2026-11-11 calibre revision.

## Re-running the scripts

Script `ROOT` constants point to the author's local workspace. Redirect `ROOT`
to this deposit's `data/` directory (see `REPRODUCE.md`) before execution.
Dependencies: Python 3.13, numpy, scipy, matplotlib, Pillow, python-docx.
Manuscript-assembly and verification scripts additionally read the author's local
manuscript Markdown files; the numerical chain (raw extracts → derived tables →
figures) is fully reproducible from this deposit alone.

## Licence

Code: MIT. Data: CC BY 4.0. Reuse requires attribution to this deposit and to the
originating institutions (WHO Prequalification of Medicines Programme, WHO Global
Health Observatory, World Bank World Development Indicators).

## Version

Release `v1.0.0` is the version cited in the manuscript's data accessibility
statement. Generated 2026-11-12.


## Version v1.2.0 (12 November 2026)

The primary malaria burden denominator is now the WHO official estimated number of malaria cases (`MALARIA_EST_CASES`, 2024 estimates). The previous incidence-per-1,000-at-risk-times-total-population construction is retained only as a sensitivity comparison. Additional contents: four raw GHO extracts and their provenance record, eight recomputed derived tables, `figures_v1_2/` (the three regenerated main figures with captions, drawing contract and manifest), and twelve reproducible v1.2 scripts. Country sets are reconciled in `data/processed/res_B_country_set_reconciliation_2026-11-12.csv`; the WHO tuberculosis case-count indicator is used only as an external magnitude check because it contains no India records. Release v1.0.0 is retained unchanged.
