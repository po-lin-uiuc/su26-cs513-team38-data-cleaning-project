# Submission Checklist  [Team]

**Each artifact may be submitted ONCE.** Phase-I report, Phase-II report, and the
supplementary ZIP are manually graded and cannot be resubmitted — only upload final versions.

## Phase-I

- [ ] Single PDF, narrative form → `deliverables/phase1/CS513-Team38-Phase1-Report.pdf`
- [ ] Header lists Team-ID (38) and each member's name + Illinois email
- [ ] §1 ER diagram / ontology / detailed schema **and** narrative description
- [ ] §2 U1, U0, U2
- [ ] §3 DQ problems with evidence (snippets/screenshots) + why cleaning is necessary for U1
- [ ] §4 Plan S1–S5 with **who does what** and a **timeline**

## Phase-II

### Report → `deliverables/phase2/CS513-Team38-Phase2-Report.pdf`

- [ ] Actual workflow W performed, compared against the Phase-I plan (what changed, why)
- [ ] Narrative tying steps to the U1 motivation and tool rationale
- [ ] Before/after query evidence: Q_U1(D) vs Q_U1(D′)
- [ ] Summary of data changes ΔD
- [ ] Findings, problems encountered, lessons learned, next steps
- [ ] Per-member contributions
- [ ] **Documentation of tools used beyond the course toolset, including any LLM use** — the
      instructions require this explicitly. See Appendix A of
      [phase2-report.md](phase2-report.md).

### Supplementary ZIP → `deliverables/phase2/supplementary/`

- [ ] **Workflow model** — `Workflow.yw` + `Workflow.gv` (YesWorkflow), or a source file
      (e.g. PPTX) + `Workflow.pdf` for other diagramming tools
- [ ] **`OpenRefineHistory.json`** — OpenRefine operation history, copy-pasted
- [ ] **`OtherToolHistory.json`** — history/provenance for other tools, plus Python scripts
      and notebooks
- [ ] **`queries.txt`** — all SQL/Datalog profiling and integrity-constraint queries
- [ ] **`DataLinks.txt`** — Box link to raw and cleaned datasets
- [ ] **Datasets are NOT in the ZIP** — Box only

## Assembly command

```powershell
Compress-Archive -Path deliverables\phase2\supplementary\* `
                 -DestinationPath deliverables\phase2\CS513-Team38-Supplementary.zip
```
