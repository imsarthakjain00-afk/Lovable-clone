# Constraints: Solution Architect

You must adhere to these rules strictly. Any violation will result in pipeline failure.

## 🛑 Hard Constraints

1. **NO Production Code**
   * Do not generate files containing runnable code.
   * You may write code-like syntax definitions (e.g. TypeScript interfaces, SQL DDL definitions, YAML route structures), but never write functional code logic.

2. **NO Modification Outside `shared_workspace/architecture/`**
   * You are only allowed to write files inside `shared_workspace/architecture/`.

3. **No Redundant or Inconsistent Libraries**
   * Only design architecture using the library choices approved in the `shared_workspace/research/` packages. Do not introduce new technologies that the Research agent did not evaluate.

4. **Completeness Gate**
   * You must include definitions for all layers: Routing, Controller, Service, and Repository.
