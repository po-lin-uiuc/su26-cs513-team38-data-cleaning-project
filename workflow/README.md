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

The detailed view of the cleaning itself. If it is derived from the OpenRefine history, render
it with [OR2YW](https://github.com/idaks/OR2YWTool):

```powershell
or2yw -i ..\openrefine\history\OpenRefineHistory.json -o workflow\W2.gv -t GV
```

## Files

| File | Purpose |
| --- | --- |
| `Workflow.yw` | YesWorkflow annotations for W1 |
| `Workflow.gv` | Generated Graphviz source for W1 |
| `Workflow.pdf` | Rendered W1 (also acceptable as the deliverable for non-YW tools) |
| `W2.gv` / `W2.pdf` | Inner cleaning workflow |

Keep both the source and the render — the graders ask for the source file, and the render is
what goes in the report.
