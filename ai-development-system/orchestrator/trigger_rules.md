# Trigger Rules: Agent Workflows

The state engine operates based on the presence and verification status of workspace files.

---

## ⚡ Automated Trigger Schema

### Rule 1: User Prompt Intake
* **Condition**: User provides input configuration block and execution runs.
* **Action**: Launch `research-agent`. Create folders in `shared_workspace/research/`.

### Rule 2: Research Completion to Architect Trigger
* **Condition**: Check all `shared_workspace/research/*.md` files exist and exceed minimum content constraints (file sizes > 100 bytes, sections populated).
* **Action**: Execute validation scripts. If validation passes, launch `solution-architect`.

### Rule 3: Architecture Completion to Engineer Trigger
* **Condition**: Check `shared_workspace/architecture/*.md` are valid and the folder structure tree is complete.
* **Action**: Verify coding styles and milestones checklist. Launch `implementation-engineer`.

### Rule 4: Exception & Loopback Rule
* **Condition**: Validation checks fail on Architecture layout (e.g. references non-existent SDKs or libraries).
* **Action**: Increment `iteration_count`. Route validation logs back to `research-agent` (loopback) to re-evaluate options.
