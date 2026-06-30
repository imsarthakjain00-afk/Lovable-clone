# Autonomous Multi-Agent AI Software Development System

This system acts like a real software engineering company, translating high-level user descriptions of **what** they want into functional, production-ready codebases of **any** technology stack. 

It divides the engineering process into three distinct, autonomous AI agents that communicate solely via a shared workspace and run sequentially through an orchestrator.

---

## 🏗️ Project Architecture

```
ai-development-system/
├── README.md
├── agents/                      # Agent Persona, Prompt, and Workflow Definitions
│   ├── research-agent/          # Phase 1: Gathers exhaustive tech data, APIs, and libraries
│   ├── solution-architect/      # Phase 2: Designs schemas, APIs, code guidelines, and plans
│   └── implementation-engineer/ # Phase 3: Implements robust, DRY, clean code
├── orchestrator/                # Orchestration state engine and trigger rules
├── shared_workspace/            # Shared data plane (Artifacts folder)
│   ├── research/
│   ├── architecture/
│   └── implementation/
├── memory/                      # Long-term cross-project knowledge repository
└── templates/                   # Standardized markdown structure files
```

---

## 🤖 The Autonomous Agents

### 1. Research & Intelligence Agent
* **Role**: Technical Researcher.
* **Mission**: Eliminate unknowns, compare tech stacks, discover hidden edge cases, and inspect API/SDK limits.
* **Rule**: Never write implementation/production code.

### 2. Solution Architect
* **Role**: Principal Systems Architect.
* **Mission**: Build the engineering blueprint, database schemas, routing, directory structures, and milestone tasks.
* **Rule**: Read research artifacts; output only blueprints and schemas; never write code.

### 3. Implementation Engineer
* **Role**: Senior Staff Software Engineer.
* **Mission**: Translate architecture blueprints into production codebases following SOLID, Clean Architecture, and DRY patterns.
* **Rule**: No independent architectural decisions; follow the architect's implementation blueprint exactly.

---

## ⚙️ How it Works (Orchestrator Pipeline)

1. **User Input**: A natural language description of the target software.
2. **Phase 1 (Research)**: Research Agent is initialized, searches for packages/competitors/SDK limits, and populates `shared_workspace/research/`.
3. **Phase 1 Validation**: Automated checks verify all necessary research artifacts are complete.
4. **Phase 2 (Architecture)**: Solution Architect consumes the research packages and builds structural design specs in `shared_workspace/architecture/`.
5. **Phase 2 Validation**: Blueprint schema check validates dependencies and schema readiness.
6. **Phase 3 (Implementation)**: Implementation Engineer consumes both research and design blueprints to write clean code, outputting logs to `shared_workspace/implementation/`.

---

## 🏃 Running the Pipeline

You can run the fully autonomous pipeline script from the system root:

1. **Bootstrap the Pipeline**:
   Ensure you have dependencies installed (using the virtual environment or your python environment):
   ```bash
   pip install google-genai
   ```

2. **Trigger the Orchestrator**:
   Provide the system description as a command-line argument:
   ```bash
   python run_pipeline.py "Create a lightweight Python CLI utility that parses CSV files and exports clean JSON models"
   ```

3. **Check the Workspace**:
   As the pipeline runs, it writes outputs to the shared workspace:
   * **Research logs**: `shared_workspace/research/research_package.md`
   * **Design blueprints**: `shared_workspace/architecture/architecture.md`
   * **Code implementation**: `shared_workspace/implementation/implementation_notes.md`
