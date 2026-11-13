# Data Accessibility Statement

The WHO prequalification CSV extracts (https://extranet.who.int/prequal/; listing
snapshot 15 September 2026), the WHO Global Health Observatory burden indicators
and the World Bank World Development Indicators are publicly available from their
issuing institutions. Copies of the extracts used in this analysis, the reviewed
applicant-to-country mapping, all derived tables, the three figure files and the
scripts that reproduce every reported quantity are deposited in a public
repository at https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit (release v1.2.1: https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit/tree/v1.2.1). All derived tables and the
scripts that reproduce them are supplied as supplementary material; the raw
extracts and the applicant-to-country mapping are retained alongside the analysis
code so that every reported quantity can be recomputed. No proprietary or
individual-level data were used.

Repository contents are listed with SHA-256 checksums in `MANIFEST.json`, and the
execution order is documented in `REPRODUCE.md`. Version v1.2.1 is the single fixed version cited in the manuscript and is aligned with the submission package. Relative to v1.2.0 it corrects denominator-calibre labels so that only malaria is labelled as WHO official estimated case counts (tuberculosis uses incidence per 100,000 population x total population; HIV/AIDS uses people living with HIV prevalence counts), renames the burden-observed-only calibre, adds a calibre-label dictionary, a country-set reconciliation with an India-record check and a grouped tuberculosis external magnitude benchmark, and records the label and wording changes in two machine-readable audit files. No statistical value was changed. The primary malaria denominator remains MALARIA_EST_CASES (2024 estimates); the earlier incidence-times-total-population construction is retained only as a sensitivity comparison. Releases v1.0.0 and v1.2.0 are retained unchanged as historical versions.

Code is released under MIT and
data under CC BY 4.0.
