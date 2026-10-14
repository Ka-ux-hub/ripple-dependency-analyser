# Ripple — Dependency Impact Analyser

Ripple is a small Python command-line tool that models task dependencies, reports downstream impact when a task changes, detects circular dependencies, and calculates a valid dependency-first execution order.

It was built as a learning project to practise Python functions, dictionaries and sets, graph traversal, JSON file handling, command-line arguments, error handling, and automated tests.

## Requirements

- Python 3.10 or newer
- No third-party packages required

## Run it

From this folder, run:

```bash
python main.py
```

To see what would be affected if `design` changed:

```bash
python main.py --changed design
```

Use a different JSON file like this:

```bash
python main.py tasks.json --changed api
```

## Input format

The JSON object maps each task to a list of tasks it depends on. For example:

```json
{
  "design": [],
  "api": ["design"],
  "tests": ["api"]
}
```

Dependencies must refer to task names that exist in the same file. Ripple reports malformed input and unknown dependencies clearly. If a cycle exists, `execution_order` is `null` and the `cycles` field explains the circular path.

## Run the tests

```bash
python -m unittest -v
```

The tests cover downstream impact, dependency ordering, circular dependencies, JSON loading, and invalid input.

## Design notes

- The input is kept simple and readable so a new Python learner can explain it.
- The reverse dependency graph makes it possible to walk from a changed task to all tasks that rely on it.
- A breadth-first traversal discovers downstream impact; a dependency-first ordering checks whether the plan can be executed without circular dependencies.
- The project uses only Python's standard library.

## Current limitations

This is a local demonstration tool, not a production scheduler. It does not read a real project repository, infer dependencies automatically, or execute tasks. The input dependencies must be entered by the user.

## Learning and authorship

Use this project as a learning base: read the functions, run the tests, change the sample task graph, and make improvements you can explain in your own words. In an interview, be transparent about any tutorials or AI assistance used while developing it.

## Example output

Running `python main.py --changed design` reports the number of tasks and dependencies, any cycles, a valid execution order, and the tasks downstream of `design`.
