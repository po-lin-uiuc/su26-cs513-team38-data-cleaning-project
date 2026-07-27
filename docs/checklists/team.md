# Team-effort checklist  [Team]

Items requiring all three members. Individual work is tracked in [po-lin.md](po-lin.md),
[charlene-khun.md](charlene-khun.md), and [madalyn-killian.md](madalyn-killian.md).

## Step 1 — Repository setup  [Team]

- [ ] All members confirm access
- [x] Raw data remains unchanged
- [x] Folder and naming conventions are finalized — see [README.md](README.md#where-artifacts-go)
- [ ] Raw row/column counts are recorded
- [x] Shared source-row provenance convention is finalized — `source_file`, `source_row_num`

## Step 7 — Combined validation  [Team] [CharleneKhun] [MadalynKillian] [PoLin]

- [ ] Charlene submits IC/domain checks
- [ ] Madalyn submits IND checks
- [ ] Po submits FD checks
- [ ] All rules have IDs and plain-English descriptions
- [ ] All queries are included in `queries.txt`
- [ ] All violation files include source identifiers
- [ ] Before/after counts are consolidated
- [ ] Remaining violations are explained
- [ ] Validation results demonstrate that D′ is cleaner than D

## Step 10 — Final exports and supplementary materials  [Team]

Final data/output files:

- [ ] `final_menu.csv`
- [ ] `final_item.csv`
- [ ] `cleaning_log.csv`
- [ ] `excluded_records.csv`
- [ ] `validation_report.csv`

Cleaned source files:

- [ ] `Menu_cleaned.csv`
- [ ] `MenuPage_cleaned.csv`
- [ ] `MenuItem_cleaned.csv`
- [ ] `Dish_cleaned.csv`

Validation files:

- [ ] `validation_ic_results.csv`
- [ ] `validation_ind_results.csv`
- [ ] `validation_fd_results.csv`

Supplementary materials:

- [ ] Workflow W1 source file
- [ ] Workflow W1 PDF
- [ ] Workflow W2 source file
- [ ] Workflow W2 PDF or equivalent visual
- [ ] `OpenRefineHistory.json`
- [ ] Python scripts/notebooks
- [ ] SQLite DDL and load scripts
- [ ] Validation SQL
- [ ] `queries.txt`
- [ ] Provenance and iteration logs
- [ ] `DataLinks.txt`

Raw and cleaned datasets go in a shared Box folder referenced through `DataLinks.txt`,
**not** in the ZIP.

## Final report integration  [Team]

- [ ] Describe all actual high-level cleaning steps
- [ ] Explain the rationale for every step
- [ ] Explain each step's relevance to U1
- [ ] Compare the actual workflow with the Phase-I plan
- [ ] Quantify rows and cells changed
- [ ] Provide before/after validation results
- [ ] Demonstrate that U1 is now supportable
- [ ] Explain W1 design and tool selection
- [ ] Explain W2 design
- [ ] Summarize problems encountered
- [ ] Summarize lessons learned
- [ ] State unresolved limitations
- [ ] Summarize each member's contribution
- [ ] Document tools used beyond the course toolset, including any LLM use — required by the
      project instructions; drafted in Appendix A of [../phase2-report.md](../phase2-report.md)
- [ ] Verify every report figure and table matches the final output files
- [ ] Have every team member review the complete submission before the single final submission

### Plan-vs-actual differences to report

The rubric asks what changed from Phase I. Already known:

| Change | Phase-I plan | Phase-II actual | Why |
| --- | --- | --- | --- |
| SQL engine | MySQL | SQLite | _record the team's reason_ |
| Task split | Whole S-steps per member (S1/S2 MK, S3/S4 P, S5 CK) | Split by workflow step and tool; all members span S3–S5 | Validation work (Step 7) naturally divides into IC / IND / FD, which no single member owned under the original split |

Add rows as further deviations occur — this table feeds §4 "Plan vs. actual" of
[../phase2-report.md](../phase2-report.md).
