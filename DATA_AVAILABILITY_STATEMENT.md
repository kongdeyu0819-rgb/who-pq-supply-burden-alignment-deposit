# Data Accessibility Statement

The WHO prequalification CSV extracts (https://extranet.who.int/prequal/; listing
snapshot 15 September 2026), the WHO Global Health Observatory burden indicators
and the World Bank World Development Indicators are publicly available from their
issuing institutions. Copies of the extracts used in this analysis, the reviewed
applicant-to-country mapping, all derived tables, the three figure files and the
scripts that reproduce every reported quantity are deposited in a public
repository at https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit (release v1.2.0: https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit/tree/v1.2.0). All derived tables and the
scripts that reproduce them are supplied as supplementary material; the raw
extracts and the applicant-to-country mapping are retained alongside the analysis
code so that every reported quantity can be recomputed. No proprietary or
individual-level data were used.

Repository contents are listed with SHA-256 checksums in `MANIFEST.json`, and the
execution order is documented in `REPRODUCE.md`. Version v1.2.0 adds the WHO official estimated malaria case-count extract (MALARIA_EST_CASES, 2024 estimates), the recomputed burden and alignment tables, extended AAPC robustness results, country-set reconciliation, regenerated figures and the scripts that reproduce them. The earlier incidence-times-total-population construction is retained only as a sensitivity comparison. Release v1.0.0 remains available as the historical version.

Code is released under MIT and
data under CC BY 4.0.
