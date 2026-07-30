# Workflow models

Phase-II rubric item 3 (20 pts). Two models are required.

## W1 — outer workflow (10 pts)  [Team]

The end-to-end project: data profiling → loading → cleaning → IC violation checks → final
dataset. Must identify key **inputs, outputs, steps, and dependencies**, and the report must
explain the design and why each tool was chosen.

Using YesWorkflow, annotate the pipeline source and generate the graph:

```powershell
yw graph src\run_pipeline.py > workflow\Workflow.gv
dot -Tpdf workflow\Workflow.gv -o workflow\Workflow.pdf
```

Deliver `Workflow.yw` (annotations) **and** `Workflow.gv` (Graphviz). With another diagramming
tool, deliver the source file (e.g. PPTX) **and** `Workflow.pdf`.

## W2 — inner cleaning workflow (10 pts)  [PoLin]

The detailed view of the Python/pandas cleaning. The annotations live in the pipeline source, so
the graph is generated from the code that actually runs and cannot drift from it.

### Prerequisites

- **Java** (any recent JRE) — `java -version`
- **The YesWorkflow jar**, not on PATH by default:
  ```powershell
  Invoke-WebRequest `
    'https://github.com/yesworkflow-org/yw-prototypes/releases/download/v0.2.1.2/yesworkflow-0.2.1.2-jar-with-dependencies.jar' `
    -OutFile yesworkflow.jar
  ```
- **Graphviz** for `dot`, only needed to render a PDF:
  `winget install Graphviz.Graphviz`. The installer does **not** add itself to PATH
  non-interactively, so either tick that option in the GUI installer or call `dot.exe` by full
  path.

### Rendering

```powershell
$src = 'workflow/W2_frame.yw',
       'src/clean_menu.py','src/clean_menu_page.py','src/clean_dish.py','src/clean_menu_item.py',
       'src/run_pipeline.py'

# top-level: the four table chains plus the cleaning-log rollup
java -jar yesworkflow.jar graph @src -c "extract.comment=#" -c graph.view=combined > workflow\W2.gv

# stage detail for one table (qualified name is required)
java -jar yesworkflow.jar graph @src -c "extract.comment=#" -c graph.view=combined `
  -c "graph.subworkflow=cleaning_workflow_W2.clean_menu" > workflow\W2_clean_menu.gv

dot -Tpdf workflow\W2.gv -o workflow\W2.pdf
```

### Three things that will silently produce a wrong graph

1. **`-c "extract.comment=#"` is mandatory.** Without it YesWorkflow treats Python *docstrings*
   as the comment syntax and finds no annotations — it exits successfully having produced nothing.
2. **File order matters.** YesWorkflow concatenates its arguments into one stream, so
   `W2_frame.yw` must come first (it opens the workflow) and `run_pipeline.py` last (it closes
   it). Getting this wrong yielded a 6-node graph containing none of the cleaning chains, with no
   error reported.
3. **Never write the YesWorkflow begin/end keywords in prose**, in comments or docstrings.
   They are matched loosely, so a keyword inside an ordinary sentence opens a real block and
   breaks the pairing. This is why the explanation in `W2_frame.yw` describes them indirectly.

## Files

| File | Purpose |
| --- | --- |
| `Workflow.yw` | YesWorkflow annotations for W1 (pending) |
| `Workflow.gv` | Generated Graphviz source for W1 (pending) |
| `Workflow.pdf` | Rendered W1 (also acceptable as the deliverable for non-YW tools) |
| `W2_frame.yw` | W2 outer frame — opens the workflow and declares its external ports |
| `W2.gv` | W2 top level: four table chains + the cleaning-log rollup (21 nodes, 24 edges) |
| `W2_clean_menu.gv` | Menu's four stages in detail |
| `W2_clean_menu_page.gv` | MenuPage's single stage |
| `W2_clean_dish.gv` | Dish's three stages |
| `W2_clean_menu_item.gv` | MenuItem's three stages, including the omit split |
| `W2*.pdf` | Rendered views (produced by `dot`, not yet generated) |

The per-table graphs are what show the asymmetry the model exists to demonstrate: Menu runs four
stages, MenuPage one, because each table is cleaned according to the column types it has.

Keep both the source and the render — the graders ask for the source file, and the render is
what goes in the report.
