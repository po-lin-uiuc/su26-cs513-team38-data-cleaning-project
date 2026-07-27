# Iteration log  [MadalynKillian]

Owner: **Madalyn Killian** (Step 8). One entry per pass through Steps 5–7. This log is the
evidence that the cleaning loop converged, and it supplies the stopping rationale the rubric
asks for.

## Stopping criteria  [MadalynKillian] [Team]

**Define these before iterating.** Without them the loop either runs indefinitely or stops
arbitrarily, and "it looked good enough" is not a defensible rationale — the checklist asks
for an explicit stopping criterion and the report has to state it.

Agree them as a team and record them here:

- [ ]
- [ ]
- [ ]

## Iteration entries

Copy this block per iteration.

### Iteration N — YYYY-MM-DD

**Inputs:** cleaned CSVs produced by _(rule set / commit)_
**Ran:** Steps 5 → 6 → 7

| Metric | Count |
| --- | --- |
| IC violations | |
| IND violations | |
| FD violations | |
| Domain violations | |
| Rows repaired | |
| Rows newly warned | |
| Rows newly excluded | |
| Violations remaining | |
| New rules added | |
| Rules modified | |
| Schema changes | |
| U1-eligible menus | |
| U1-eligible items | |
| Change in U1-eligible records vs. prior | |

**Violation dispositions**

| Rule ID | Category | Count | Cause | Disposition | Routed to |
| --- | --- | --- | --- | --- | --- |
| | | | dirty raw data / incomplete rule / incorrect rule / staging-load problem / unavoidable ambiguity | repair / warning / exclusion / accepted limitation | Po / Charlene / Madalyn |

**Another iteration performed?** Yes / No — _reason_

**Artifacts:** `data/reports/validation_*_results_iterN.csv`

---

## Schema revision log  [MadalynKillian]

Step 5 requires recording every staging schema change.

| Iteration | Table | Change | Why | Made by |
| --- | --- | --- | --- | --- |

## Unresolved limitations  [Team]

Carried into the Phase-II conclusions. Anything here must be stated in the report, not quietly
dropped.

| Limitation | Affected records | Why unresolvable | Impact on U1 |
| --- | --- | --- | --- |
