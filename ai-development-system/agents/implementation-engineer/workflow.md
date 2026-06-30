# Workflow: Implementation Engineer

The Implementation Engineer Agent runs as the final implementation stage in the pipeline:

```mermaid
graph TD
    Start[Read shared_workspace/research/ & architecture/] --> Scaffold[Scaffold Folder Hierarchy]
    Scaffold --> WriteCode[Write DB Models, Repositories, Services, Routers]
    WriteCode --> WriteTests[Write Unit/Integration Tests]
    WriteTests --> WriteLog[Update shared_workspace/implementation/ generated_files.md]
    WriteLog --> End[Complete Production Codebase]
```

## Step 1: Read Workspace
* Retrieve all research and design instructions.

## Step 2: Set Up File System Structure
* Execute directory shell setup.

## Step 3: Implement Database & Models
* Write data structure scripts.

## Step 4: Implement Service layer
* Write services, utilities, and helper functions.

## Step 5: Implement Routing & Controllers
* Write the API routers, security checks, and controllers.

## Step 6: Log Execution
* Update the files in `shared_workspace/implementation/` following templates exactly.
