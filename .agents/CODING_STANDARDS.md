# Coding Standards — Lovable Clone

Read this before writing any code in this project.

---

## Naming

- **Variables**: `camelCase` in JS/JSX, `snake_case` in Python. Name after what the value holds, not its type.
  - Good: `allProjects`, `activeProject`, `currentUser`
  - Bad: `data`, `result`, `arr`, `temp`, `obj`

- **Functions**: Name after the action they perform.
  - Good: `loadAllProjects`, `handleSendPrompt`, `deleteProject`, `create_project_for_user`
  - Bad: `doStuff`, `process`, `handleAction`, `fn`

- **Components (React)**: PascalCase, named after the page or feature.
  - Good: `AuthPage`, `Dashboard`, `Templates`, `LandingPage`

- **Classes / Models (Python)**: PascalCase with the layer as a suffix.
  - Good: `UserModel`, `ProjectModel`, `ChatMessageModel`

- **CSS Classes**: `kebab-case`, prefixed with the component name.
  - Good: `dashboard-sidebar`, `chat-message-bubble`, `auth-submit-button`
  - Bad: `.container`, `.wrapper`, `.box`

---

## Comments

- No comments that restate what the code already says.
  - Bad: `# Get user by ID` above `get_user_by_id(user_id, db)`
  - Bad: `// increment counter` above `counter++`

- Write a comment only if the *why* is not obvious from the code itself.
  - Good: `// Optimistically add the user's message before the server confirms`
  - Good: `# Falls back to simulation mode when no API key is configured`

- Section separators in long files are allowed to aid navigation.
  - Use: `// ── Section Name ──────────`

- No docstrings for functions whose name already explains everything.
  - A brief docstring is okay if the function has non-obvious side effects or complex logic.

---

## Code Structure

- **One responsibility per function.** If a function does two unrelated things, split it.
- **No deeply nested logic.** Use early returns to handle error/edge cases at the top.
- **No magic numbers or strings.** Pull them into a named constant or config.
- **DRY**: If the same logic appears twice, extract it into a shared helper.

---

## Python Backend

- Layer structure: `routers.py` → `controller.py` → `services.py` → `db_queries.py`
- Routers only handle request/response — no business logic.
- Services own all business logic and raise `HTTPException` for failures.
- `db_queries.py` contains raw SQLAlchemy queries only — no business logic.
- DTOs (`dtos.py`) are Pydantic models for request and response shapes.
- Settings come from `src/utils/settings.py` — never hardcode secrets or config values.

---

## React Frontend

- State lives as close to where it is used as possible.
- API calls go through `src/api.js` — never write raw `fetch` or `axios` calls inline in components.
- Keep JSX clean — move complex conditions into named variables before the return statement.
- CSS goes in a per-page `.css` file with the same name as the component.
- No inline styles except for truly dynamic values (e.g., `animationDelay`).

---

## Formatting

- **Python**: 4-space indentation, max ~100 chars per line.
- **JS/JSX**: 2-space indentation.
- Trailing commas where the language allows.
- Blank line between logical blocks of code — not between every single line.
