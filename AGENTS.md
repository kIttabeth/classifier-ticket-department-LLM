# AGENTS Instructions

## Coding Style

- Use `snake_case` for variable names, function names, file names, and other identifiers whenever applicable.
- Always use `BaseModel` for data models and DTOs.
- Use direct imports from the actual module path, and do not rely on package `__init__` re-exports. Example: `from app.services.extract import extract_text_from_upload`
- Add a concise comment in every module explaining what the module is responsible for.
- Add a concise comment for every function explaining what the function does.

## Dependency Management

- Use `uv add <package>` for every package installation.
- Do not use `pip install`, `poetry add`, or other package installation commands unless the user explicitly requests an exception.

## Communication

- Every time you create, modify, or generate something, explain what was created or changed and how it works.
- Keep explanations concise, but always include enough detail for the user to understand the implementation.

## Rules

- Don't Read .env file

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
