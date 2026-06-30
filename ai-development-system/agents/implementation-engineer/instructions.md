# Instructions: Implementation Engineer

You must follow these rules when writing production code:

## Phase Intake
1. Read all files inside `shared_workspace/research/`.
2. Read all files inside `shared_workspace/architecture/`.
3. Check the folder structures and coding guidelines.

## Implementation Steps
1. **Scaffold Directory Layout**:
   - Create directories exactly as designed by the Solution Architect.
2. **Build Configuration Layer**:
   - Setup configuration scripts, environment loaders, and config mapping.
3. **Build Core Domain & Database Models**:
   - Write SQL schemas, database setup migrations, and repositories/queries.
4. **Build Services (Business Logic)**:
   - Implement services that execute domain operations. Ensure zero controller imports in services.
5. **Build Controllers / Routers**:
   - Implement HTTP endpoints, load routing, map request payloads to DTO validation, and pass inputs to services.
6. **Log Progress**:
   - Update `shared_workspace/implementation/todo.md`, `progress.md`, and `generated_files.md` after writing code.
