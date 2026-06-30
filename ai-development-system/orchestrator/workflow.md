# Orchestrator Execution Workflow

Here is the operational workflow step-by-step:

## Step 1: Pre-Execution Setup
* Create directories if they do not exist.
* Pull reusable components from `memory/reusable_components/` if project parameters match tags.

## Step 2: Gating Pipeline execution
* Invoke agent models via pipeline runs.
* Write logs to memory folders upon successful phase exit.

## Step 3: Deployment & Code Bundling
* Once the Implementation Engineer signals completion, bundle the final directory output, verify file counts, and verify syntax using compiler scripts.
