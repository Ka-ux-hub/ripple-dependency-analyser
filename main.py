"""Ripple: a small dependency impact analyser for task plans."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


def load_tasks(path: str | Path) -> dict[str, list[str]]:
    """Load a JSON object mapping each task to the tasks it depends on."""
    try:
        raw: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON from {path}: {exc}") from exc
    if not isinstance(raw, dict) or not raw:
        raise ValueError("Input must be a non-empty JSON object of task: [dependencies].")
    tasks: dict[str, list[str]] = {}
    for task, dependencies in raw.items():
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Task names must be non-empty strings.")
        if not isinstance(dependencies, list) or any(not isinstance(d, str) for d in dependencies):
            raise ValueError(f"Dependencies for '{task}' must be a list of task names.")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"Task '{task}' lists a dependency more than once.")
        tasks[task] = dependencies
    unknown = sorted({dep for deps in tasks.values() for dep in deps if dep not in tasks})
    if unknown:
        raise ValueError("Unknown dependencies: " + ", ".join(unknown))
    return tasks


def find_cycles(tasks: dict[str, list[str]]) -> list[list[str]]:
    """Return cycle paths using depth-first search (each path closes at its start)."""
    state: dict[str, int] = {}  # 0/unseen, 1/active, 2/finished
    stack: list[str] = []
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dep in tasks[node]:
            if state.get(dep, 0) == 0:
                visit(dep)
            elif state.get(dep) == 1:
                start = stack.index(dep)
                cycle = stack[start:] + [dep]
                core = cycle[:-1]
                # Canonical rotation avoids reporting the same cycle from another entry point.
                rotations = [tuple(core[i:] + core[:i]) for i in range(len(core))]
                canonical = min(rotations)
                if canonical not in seen:
                    seen.add(canonical)
                    cycles.append(list(canonical) + [canonical[0]])
        stack.pop()
        state[node] = 2

    for task in tasks:
        if state.get(task, 0) == 0:
            visit(task)
    return cycles


def downstream_impact(tasks: dict[str, list[str]], changed_task: str) -> list[str]:
    """List tasks that directly or indirectly depend on changed_task, in stable order."""
    if changed_task not in tasks:
        raise ValueError(f"Unknown task: {changed_task}")
    dependents: dict[str, list[str]] = defaultdict(list)
    for task, deps in tasks.items():
        for dep in deps:
            dependents[dep].append(task)
    found: set[str] = set()
    queue = deque(sorted(dependents[changed_task]))
    while queue:
        current = queue.popleft()
        if current in found or current == changed_task:
            continue
        found.add(current)
        queue.extend(sorted(dependents[current]))
    return sorted(found)


def topological_order(tasks: dict[str, list[str]]) -> list[str] | None:
    """Return a valid dependency-first order, or None if the graph contains a cycle."""
    if find_cycles(tasks):
        return None
    remaining = {task: set(deps) for task, deps in tasks.items()}
    order: list[str] = []
    while remaining:
        ready = sorted(task for task, deps in remaining.items() if not deps)
        if not ready:
            return None
        for task in ready:
            order.append(task)
            del remaining[task]
        for deps in remaining.values():
            deps.difference_update(ready)
    return order


def analyse(tasks: dict[str, list[str]], changed_task: str | None = None) -> dict[str, Any]:
    cycles = find_cycles(tasks)
    result: dict[str, Any] = {
        "task_count": len(tasks),
        "dependency_count": sum(map(len, tasks.values())),
        "cycles": cycles,
        "execution_order": topological_order(tasks),
    }
    if changed_task is not None:
        result["changed_task"] = changed_task
        result["downstream_impact"] = downstream_impact(tasks, changed_task)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse task dependencies and downstream impact.")
    parser.add_argument("file", nargs="?", default="tasks.json", help="Path to task JSON (default: tasks.json)")
    parser.add_argument("--changed", metavar="TASK", help="Show tasks affected by a change to TASK")
    args = parser.parse_args()
    try:
        tasks = load_tasks(args.file)
        report = analyse(tasks, args.changed)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 0 if not report["cycles"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
