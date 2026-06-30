# Orchestrator: Multi-Agent Coordination Engine

The orchestrator controls the state transitions and validation gates of the development pipeline. It executes without human intervention to enforce architectural and research integrity before code generation.

---

## 🔄 State Machine Lifecycle

```
[ Idle ] ──(User Request)──> [ Researching ] ──(Valid?)──> [ Designing ] ──(Valid?)──> [ Implementing ] ──> [ Complete ]
                                  │                            │
                            (Needs Retried)              (Needs Retried)
```

## 🚥 Phase Validation Gates

### Gate 1: Research Validator
Before triggering the Solution Architect, the orchestrator verifies:
* All 14 files in `shared_workspace/research/` contain valid data.
* No section has empty markdown tables or "TBD" comments.
* At least three package options have been scored.
* Rate limits are declared for any selected APIs.

### Gate 2: Architecture Validator
Before triggering the Implementation Engineer, the orchestrator verifies:
* The folder structures in `folder_structure.md` contain at least root, routing, and repository/model definitions.
* Database models match all requirements defined in Research.
* APIs specify path, method, headers, request schema, and response schema.
* No implementation logic or functional code blocks are present.
