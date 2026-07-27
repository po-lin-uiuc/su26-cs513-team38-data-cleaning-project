# Phase-II checklists

Working checklists for Phase-II execution. Tick boxes here as work lands — this is the team's
tracking surface, and the Phase-II report is assembled from what it records.

| Owner | Token | Checklist | Steps owned |
| --- | --- | --- | --- |
| Po Lin | `[PoLin]` | [po-lin.md](po-lin.md) | 1 (group), 4 (Python/pandas cleaning), 7 FD checks, 9 final tables, 10 (portion) |
| Charlene Khun | `[CharleneKhun]` | [charlene-khun.md](charlene-khun.md) | 1 (group), 2 (OpenRefine profiling), 3 (cleaning rules), 7 IC/domain checks, 10 (portion) |
| Madalyn Killian | `[MadalynKillian]` | [madalyn-killian.md](madalyn-killian.md) | 1 (group), 5 (SQLite staging), 6 (load), 7 IND checks, 8 (violations & iteration), 10 (portion) |
| Team | `[Team]` | [team.md](team.md) | 1, 7 consolidation, 10, report integration |

Step numbers refer to the S3 workflow in [../phase2-plan.md](../phase2-plan.md).

## Ownership changed from Phase-I

Phase-I assigned whole S-steps (S1/S2 → MK, S3/S4 → P, S5 → CK). Phase-II splits by **workflow
step and tool** instead, so all three members contribute across S3–S5. **This is a difference
from the Phase-I plan and must be recorded in the report** — the rubric asks explicitly what
changed and why.

The other recorded change: **the SQL layer is SQLite, not MySQL.** See
[../phase2-plan.md](../phase2-plan.md#tooling-changes-from-phase-i).

## Shared responsibilities

Every member completes these for each assigned step:

- [ ] Describe what was actually performed.
- [ ] Explain why the step was necessary.
- [ ] Explain how the step supports U1.
- [ ] Identify the inputs and outputs.
- [ ] Identify the tool, script, query, or operation history used.
- [ ] Record any difference from the Phase-I plan.
- [ ] Explain why the plan changed, if applicable.
- [ ] Record counts and measurements that support S4 and S5.
- [ ] Preserve screenshots, queries, scripts, logs, or output files as evidence.
- [ ] Add the step's inputs, outputs, and dependencies to the workflow model.
- [ ] Document problems encountered and decisions made.
- [ ] Preserve enough information for another team member to reproduce the work.
- [ ] Place final artifacts in the agreed repository location.
- [ ] Contribute a short summary of personal contributions for the final report.

## Where artifacts go

The "agreed repository location" referenced above:

| Artifact | Location |
| --- | --- |
| Raw data (never modified) | `data/raw/` |
| Cleaned CSVs, cleaning log | `data/interim/` |
| `final_menu.csv`, `final_item.csv` | `data/final/` |
| Validation outputs, violation exports, excluded records | `data/reports/` |
| Python scripts | `src/` |
| Notebooks | `notebooks/` |
| SQLite DDL / load / validation scripts | `sql/` |
| SQLite database file | `data/cs513_team38.sqlite` (git-ignored) |
| OpenRefine history and profiling notes | `openrefine/` |
| Workflow W1/W2 sources and renders | `workflow/` |
| Report figures and screenshots | `docs/figures/` |
| Cleaning-rule catalog | [../cleaning-rules.md](../cleaning-rules.md) |
| Data dictionary for generated fields | [../data-dictionary.md](../data-dictionary.md) |
| Iteration log and stopping rationale | [../iteration-log.md](../iteration-log.md) |
| Report drafts | [../phase2-report.md](../phase2-report.md) |
| Final submission artifacts | `deliverables/phase2/` |

## Naming conventions

- Violation exports: `validation_<type>_results_iter<N>.csv` in `data/reports/`; the final
  iteration is also copied without the suffix (`validation_ic_results.csv`) for submission.
- Figures: `fig-<section>-<n>-<slug>.png` (see [../figures/README.md](../figures/README.md)).
- OpenRefine histories: one file per session in `openrefine/history/`, concatenated into
  `OpenRefineHistory.json` at submission.
- Rule IDs: `IC-n`, `IND-n`, `FD-n` for validation; `R-n` for cleaning rules in the catalog.
