"""Check the YesWorkflow annotations for faults YesWorkflow does not report.

    python -m src.lint_workflow

YesWorkflow exits successfully on several mistakes that produce a wrong graph:

* an output name that no input consumes, because of a typo -- the graph renders
  as disconnected subgraphs with no warning;
* a parameter naming a constant that does not exist;
* a file reference pointing at nothing;
* one of its keywords appearing in ordinary prose, which opens a real block and
  breaks the pairing. This one cost a debugging cycle, so it is checked here.

Run this before regenerating workflow/W2.gv. Owner: Po Lin  [PoLin].
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from src import config

# File order matters to YesWorkflow itself; see workflow/README.md. The frame
# file opens the workflow and run_pipeline.py closes it.
SOURCES: tuple[str, ...] = (
    "workflow/W2_frame.yw",
    "src/clean_menu.py",
    "src/clean_menu_page.py",
    "src/clean_dish.py",
    "src/clean_menu_item.py",
    "src/run_pipeline.py",
)

# A real annotation is a keyword directly after the comment marker. Anything
# else on the line means the keyword is embedded in prose.
ANNOTATION = re.compile(r"^\s*(?:#|//)\s*@(begin|end|in|out|param)\b\s*(\S+)?")
PROSE_KEYWORD = re.compile(r"@(begin|end)\b")

# Names ending like this are legitimately un-consumed: they leave the workflow.
TERMINAL_SUFFIXES = ("_cleaned", "_omitted", "cleaning_log")
SOURCE_SUFFIXES = ("_or",)


def lint() -> list[str]:
    problems: list[str] = []
    produced: dict[str, list[str]] = defaultdict(list)
    consumed: dict[str, list[str]] = defaultdict(list)
    params: dict[str, list[str]] = defaultdict(list)
    uris: dict[str, str] = {}
    stack: list[tuple[str, str]] = []
    blocks = 0

    for relative in SOURCES:
        path = config.PROJECT_ROOT / relative
        if not path.exists():
            problems.append(f"{relative}: listed in SOURCES but missing")
            continue

        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            where = f"{relative}:{number}"
            match = ANNOTATION.match(line)

            if not match:
                # A keyword outside a real annotation is a trap, not a comment.
                if PROSE_KEYWORD.search(line):
                    problems.append(
                        f"{where}: YesWorkflow keyword in prose -- it will be parsed "
                        f"as an annotation and open a duplicate block"
                    )
                continue

            kind, name = match.group(1), match.group(2)
            if name is None:
                problems.append(f"{where}: @{kind} with no name")
                continue

            if kind == "begin":
                blocks += 1
                stack.append((name, where))
            elif kind == "end":
                if not stack:
                    problems.append(f"{where}: @end {name} with no open @begin")
                elif stack[-1][0] != name:
                    problems.append(
                        f"{where}: @end {name} closes @begin {stack[-1][0]} "
                        f"(opened at {stack[-1][1]})"
                    )
                    stack.pop()
                else:
                    stack.pop()
            else:
                {"in": consumed, "out": produced, "param": params}[kind][name].append(where)
                if reference := re.search(r"@uri\s+file:(\S+)", line):
                    uris.setdefault(name, reference.group(1))

    for name, where in stack:
        problems.append(f"{where}: @begin {name} never closed")

    for name in consumed:
        if name not in produced and not name.endswith(SOURCE_SUFFIXES):
            problems.append(f"@in {name} has no producing @out and is not a workflow input")

    for name in produced:
        if name not in consumed and not name.endswith(TERMINAL_SUFFIXES):
            problems.append(f"@out {name} is consumed by nothing and is not a workflow output")

    for name in params:
        known = (
            hasattr(config, name)
            or hasattr(config.Reason, name)
            or hasattr(config.Operation, name)
            or hasattr(config.PriceSource, name)
        )
        if not known:
            problems.append(f"@param {name} is not defined in src/config.py")

    for name, reference in uris.items():
        if not (config.PROJECT_ROOT / reference).exists():
            problems.append(f"@uri for {name} points at a missing path: {reference}")

    print(f"{blocks} blocks · {len(produced)} outputs · {len(consumed)} inputs · "
          f"{len(params)} parameters · {len(uris)} file references")
    return problems


def main() -> int:
    problems = lint()
    if not problems:
        print("No problems found.")
        return 0

    print(f"\n{len(problems)} problem(s):")
    for problem in problems:
        print(f"  {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
