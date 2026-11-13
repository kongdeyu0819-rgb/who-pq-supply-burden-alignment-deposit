# Reproducing the numerical chain

Snapshot: 15 September 2026. Observation window: 2002–2026 (25 years, inclusive).

1. Set `ROOT` in each script under `scripts/` to the absolute path of this
   deposit's `data/` directory. No other code change is required.
2. `python scripts/compute_B_uncertainty_2026-11-11.py`
   produces the eight `res_B_uncertainty_*` files in `data/processed/`.
   It reads `res_B_china_pq_breadth_input.csv` for the China numerator; this is a
   byte-identical, neutral-named copy of the local PQ-side projection.
3. `python scripts/verify_B_uncertainty_calibre_2026-11-11.py`
   reproduces the anchor AAPCs (19.1100 / 24.8499 / 14.7495 / 18.2837),
   the China breadth denominators (24/98, 16/255, 1/126) and the reviewed
   concentration denominator of 648 mapped rows.
4. `python scripts/verify_B_disease_specific_supply_2026-11-11.py`
   reproduces the Therapeutic Area x Applicant supply-share reconstruction
   (98/98, 255/255, 126/126 matched rows).
5. `python scripts/draw_B_figures_2026-11-12.py` regenerates
   `figures/Figure1–3.png`; `python scripts/verify_B_figures_2026-11-12.py`
   checks the drawn values against the whitelisted CSVs.

Scripts whose names contain `manuscript`, `polish`, `finalize` or `docx`
assemble or verify the manuscript text and additionally read the author's local
Markdown chapters; they are included as a process record, not as standalone
reproducers of the numerical chain.

Random seed: 20261111. Bootstrap draws: 10,000 (country-share / concentration),
5,000 (moving-block). Primary AAPC intervals are OLS t intervals; HAC(3) and
residual moving-block intervals are sensitivity schemes tabulated in the
manuscript's supplementary material.


## v1.2 denominator recomputation (12 November 2026)

6. `python scripts/fetch_B_malaria_denominator_2026-11-12.py` reads the WHO GHO indicator catalogue and writes the official case-count extract plus provenance.
7. `python scripts/recompute_B_burden_denominator_2026-11-12.py` recomputes burden shares, M/D/C/R25, quartile shares, country-set reconciliation and the TB external benchmark; it asserts that the legacy denominator reproduces the published v1.0 values exactly and that TB/HIV values are unchanged.
8. `python scripts/extend_B_aapc_robustness_2026-11-12.py` produces HAC lags 1-4, Durbin-Watson, residual ACF1-4 and the 2002-2025 refit.
9. `python scripts/make_B_figures_v1_2_2026-11-12.py` regenerates `figures_v1_2/`; `python scripts/build_B_supplement_v1_2_2026-11-12.py` rebuilds supplementary tables S1-S8.
10. `python scripts/audit_B_pdf_pages_v1_2_2026-11-12.py` and `python scripts/verify_B_manuscript_v1_2_2026-11-12.py` run the page-level and full-manuscript consistency checks.


## v1.2.1 single fixed version (13 November 2026)

11. `python scripts/revise_B_derived_notes_v1_2_1_2026-11-13.py` rewrites calibre labels, method notes and reconciliation rows, writes the calibre dictionary, the India-record check and the grouped external benchmark, and asserts that every numeric cell outside the editable columns is unchanged.
12. `python scripts/make_B_supplement_v1_2_1_2026-11-13.py` and `python scripts/revise_B_manuscript_v1_2_1_2026-11-13.py` rebuild the S1-S8 supplementary source and the manuscript; both are wording-only revisions.
13. `python scripts/build_B_docx_v1_2_1_2026-11-13.py` and `python scripts/build_B_unique_version_v1_2_1_2026-11-13.py` assemble the two submission Word files, archive historical versions and write the submission MANIFEST with SHA-256 checksums.
14. `python scripts/audit_B_pdf_pages_v1_2_1_2026-11-13.py` and `python scripts/verify_B_manuscript_v1_2_1_2026-11-13.py` run the 65 page-level checks and the 99 full-manuscript consistency checks. The page audit is performed on an internal proof PDF; the final submission PDF exported by the journal system still requires its own page-level audit.
