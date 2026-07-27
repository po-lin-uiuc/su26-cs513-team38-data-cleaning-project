# CS 513 — Phase-II Report (scaffold)  [Team]

**Team 38** — Charlene Khun (ckhun2@illinois.edu), Madalyn Killian (killian7@illinois.edu),
Po Lin (pohungl2@illinois.edu)

**Dataset:** NYPL *"What's on the Menu?"*

> Section headings follow the Phase-II rubric exactly. Fill each section as the work lands;
> do not restructure. Export to `deliverables/phase2/CS513-Team38-Phase2-Report.pdf`.

## 1. Description of data cleaning performed

### 1.1 High-level cleaning steps (20 pts)  [PoLin] [CharleneKhun] [MadalynKillian]

_Identify and describe every high-level step actually performed._

### 1.2 Rationale per step (20 pts)  [PoLin] [CharleneKhun] [MadalynKillian]

_For each step: was it really required to support U1? If not, why was it still useful?_
Trace each step back to a problem ID (`P1`…`P10`) in
[data-quality-problems.md](data-quality-problems.md).

## 2. Document data quality changes

### 2.1 Summary table of changes (10 pts)  [CharleneKhun] [PoLin]

_Which columns changed? How many cells per column? Source: `cleaning_log.csv`._

| Table | Column | Cells changed | Rows flagged | Rows excluded | Problem ID |
| --- | --- | --- | --- | --- | --- |

### 2.2 IC-violation report, before vs. after (10 pts)  [CharleneKhun] [MadalynKillian] [PoLin]

_Denial-constraint answers on D and on D′. Source:
`validation_ic_results.csv`, `validation_ind_results.csv`, `validation_fd_results.csv`._

| Constraint | Type | Violations in D | Violations in D′ |
| --- | --- | --- | --- |

Also report Q_U1 before/after (queries in [use-cases.md](use-cases.md)): running Q on D must
give an incorrect/misleading answer, and on D′ a correct one.

## 3. Workflow model

### 3.1 Outer workflow W1 (10 pts)  [Team]

_Key inputs, outputs, steps, and dependencies; explain the design and tool choices._
Artifacts in [../workflow/](../workflow/). Tool selection is also documented in
[Appendix A](#appendix-a--tool-use-and-ai-assistance).

### 3.2 Inner cleaning workflow W2 (10 pts)  [PoLin]

_Detailed view — e.g. OR2YW over the OpenRefine history._

## 4. Conclusions & summary (10 pts)  [Team]

_Summary, lessons learned, problems encountered, next steps for implementing U1._

### Contributions

| Member | Contribution |
| --- | --- |
| Madalyn Killian | |
| Po Lin | |
| Charlene Khun | |

### Plan vs. actual

_Compare against [phase2-plan.md](phase2-plan.md): which steps executed as planned, what
changed, and why._

## 5. Supplementary materials (10 pts)  [Team]

See [deliverables-checklist.md](deliverables-checklist.md).

---

## Appendix A — Tool use and AI assistance  [Team]

The project instructions require this. On tools beyond those used in class, they state:

> "Or maybe you find a new way to use an LLM (e.g., ChatGPT). In all these cases your report
> will have to include sufficient documentation about how you used these tools."

Our Phase-I plan also anticipated "AI-assisted code generation where appropriate and permitted
by course guidelines" (S3) and listed ChatGPT among the S2 profiling tools, so this appendix
covers both the repository setup and any AI use during the cleaning work itself.

### A.1 Repository scaffolding

**Tool:** Claude Code (Anthropic Claude Opus), July 2026.

**What we asked it to do.** After Phase-I was submitted, we asked it to read the course
project instructions and our Phase-I report and lay out a repository structure for Phase-II.
It produced:

- the directory layout (`data/`, `src/`, `sql/`, `openrefine/`, `workflow/`, `docs/`,
  `deliverables/`) with a README in each explaining what belongs there, plus `.gitignore` and
  `requirements.txt`;
- our own Phase-I report content reorganized from the submitted document into per-topic
  markdown files (dataset description, use cases, data quality problems, Phase-II plan), so it
  could be revised during Phase-II rather than re-edited as one document. The data quality
  problems were given stable IDs (P1–P10) so cleaning rules and validation queries could cite
  them;
- our Phase-II task-division checklist split into one file per team member, with a search
  token (`[PoLin]`, `[CharleneKhun]`, `[MadalynKillian]`, `[Team]`) placed wherever a file
  needs someone's attention;
- empty templates for artifacts our checklist required but had no home for — the cleaning-rule
  catalog, the data dictionary, and the iteration log;
- comment-only stub files for each SQL script and Python module, stating the owner, the step,
  what the file must contain, and known pitfalls of the chosen tools.

**What it did not do.** No cleaning logic, SQL queries, profiling, cleaning rules, or analysis.
Every stub is comments and a `TODO` marker. Where it had begun drafting validation queries and
a profiling script, we had it remove them so the work would be ours; the same applied to
several design decisions it had filled in (the data dictionary field definitions, the
loop-stopping criteria, and the U1 query set), which we reset to blank for us to decide.

Two things it flagged that changed our plan, both recorded in
[Plan vs. actual](#plan-vs-actual):

1. Our Phase-I plan named MySQL, but our Phase-II task division assigned SQLite. We confirmed
   SQLite.
2. Our Phase-I task split assigned whole steps S1–S5 per member, while the Phase-II division
   splits by workflow step and tool, so all three of us work across S3–S5.

### A.2 AI assistance during the cleaning work  [Team]

_Record any LLM use during Steps 2–10 here: which tool, for what task, what it produced, and
how the output was checked before being used. Be specific — "used ChatGPT to help write a
regex for parsing `Menu.date`, then verified it against N sample values" is documentation; "used
AI for help" is not._

| Step | Tool | Used for | How the output was verified |
| --- | --- | --- | --- |

### A.3 Other tools

_Anything outside the course toolset (RegEx, OpenRefine, Datalog/Logica, SQL, Python) —
e.g. OR2YW, YesWorkflow, diagramming tools — with a note on how each was used._
