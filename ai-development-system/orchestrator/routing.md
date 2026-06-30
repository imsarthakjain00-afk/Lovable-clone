# Orchestrator Routing Logic

Routing dictates which prompt templates and config schemas are loaded into the target LLM run depending on context.

---

## 🔀 Input & Context Parameters
```json
{
  "project_type": "saas | api | website | ml_pipeline | extension | mobile",
  "priority": "standard | fast | deep",
  "memory_depth": "full | partial | none"
}
```

## 🛤️ Context-Based Routing Configurations

### 1. SaaS / Multi-Layer Applications
* **Routing Weight**: High complexity.
* **Agent Context Added**: Focus on DB migrations, OAuth2 validation, caching queues, and CORS setup.
* **LLM Temperature Override**: Set to `0.1` on solution-architect to enforce rigid standard MVC patterns.

### 2. Machine Learning / Data Engineering Pipelines
* **Routing Weight**: Medium complexity, high latency.
* **Agent Context Added**: Focus on data storage formats (Parquet vs JSON), execution memory profiles, thread locking, and dataset validation checks (Great Expectations style).
* **LLM Temperature Override**: Set to `0.2` on research-agent to discover novel libraries.
