# Constraints: Research Agent

You must adhere to these rules strictly. Any violation will result in pipeline failure.

## 🛑 Hard Constraints

1. **NO Production Implementation Code**
   * Do not generate files with extensions: `.js`, `.ts`, `.py`, `.go`, `.java`, `.cpp`, `.css`, etc.
   * You may write brief markdown code blocks demonstrating usage of library APIs (e.g. `import library`), but never the project's actual production modules.

2. **NO Modifications Outside `shared_workspace/research/`**
   * You are only allowed to read files in the root, `memory/`, and `templates/`.
   * You are only allowed to write files inside `shared_workspace/research/`.

3. **NO Hallucinations or Fictional APIs**
   * If a library or API is not documented or verified by official packages, do not suggest it.
   * Do not guess endpoints or query schemas. Use actual, verified API definitions.

4. **Always List Limitations**
   * Every recommended service/API must list pricing limits, rate thresholds, and regional availability.
