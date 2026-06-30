# Coding Guidelines & Best Practices

Detailed coding rules for the Implementation phase.

---

## 📜 Development Standards

* **General**:
  - Keep modules self-contained.
  - Never share mutable state variables globally.
  - Apply defensive checks at method inputs.

* **Exception Strategy**:
  - Catch specific exceptions (e.g. `FileNotFoundError`) instead of catching base `Exception`.
  - Use custom exception classes to distinguish validation errors from system failures.

* **Linting / Formatting**:
  - Python: Follow PEP 8 guidelines. Use type annotations on public functions.
  - JavaScript: Use strict mode, standard ES6 import syntax, and camelCase for variable names.
