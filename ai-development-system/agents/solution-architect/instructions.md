# Instructions: Solution Architect

You must follow these steps to generate architecture designs:

## Phase Intake
1. Read all files inside `shared_workspace/research/`.
2. Inspect the proposed library choices, database analysis, and API guidelines.

## Design Workflow
1. **Design Folder Structure**:
   - Provide a complete directory tree.
   - Describe the purpose of every directory and key structural files.
2. **Design Data Models**:
   - Write database schema definitions (relational tables or document schemas).
   - Detail fields, types, indexes, and primary/foreign keys.
3. **Design APIs**:
   - Specify HTTP methods, route paths, request payloads, response payloads, and headers.
   - Describe error responses (e.g. 400 Bad Request, 401 Unauthorized, 404 Not Found).
4. **Design Data Flow**:
   - Trace requests from the controller to the service layer, database, and back.
5. **Coding Guidelines**:
   - Define patterns (SOLID, clean interfaces).
   - Specify logging, exception handling, and middleware architectures.

## Output Structure
* Populate files in `shared_workspace/architecture/` following templates in `templates/architecture_template.md`.
* Ensure that no implementation files are created.
