# Workflow: Solution Architect

The Solution Architect Agent runs as the second stage in the pipeline:

```mermaid
graph TD
    Start[Read shared_workspace/research/] --> ReadMemory[Fetch Reusable Design Patterns]
    ReadMemory --> FolderDesign[Build Directory & Module Blueprint]
    FolderDesign --> APIDesign[Build API & Database Schemas]
    APIDesign --> WriteDocs[Write blueprints to shared_workspace/architecture/]
    WriteDocs --> Validate[Self-Validate Architecture Completeness]
    Validate --> End[Complete Phase 2]
```

## Step 1: Read Research Package
* Read all research documents to identify the technologies chosen and constraints noted.

## Step 2: Directory & Modularity Definition
* Build the directory blueprint.
* Map files to specific framework architectures.

## Step 3: Schema & Endpoint Specification
* Output database DDL statements or Document definitions.
* Define all API endpoints.

## Step 4: Write Architecture Workspace
* Populate files in `shared_workspace/architecture/` following templates exactly.

## Step 5: Transition Gate
* Ensure all files contain robust architectural descriptions.
* Emit pipeline token to signal Implementation Engineer.
