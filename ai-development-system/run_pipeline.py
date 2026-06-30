import os
import sys
import json
from google import genai
from google.genai import types

# Load API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # Optional fallback for local development context if they specifically want to reuse the same key
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(parent_dir, "backend", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        # Reusing the clone key as fallback
                        GEMINI_API_KEY = line.split("=")[1].strip()
                        break
    except Exception:
        pass

# Initialize client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.0-flash"
    print("Orchestrator initialized using API key.")
else:
    client = None
    MODEL_NAME = None
    print("No GEMINI_API_KEY environment variable set. Running in SIMULATION MODE.")
    print("To use real AI generation, set the environment variable:")
    print("   Windows (Cmd):  set GEMINI_API_KEY=your_api_key")
    print("   Windows (PS):   $env:GEMINI_API_KEY=\"your_api_key\"")
    print("   Linux/macOS:    export GEMINI_API_KEY=\"your_api_key\"\n")


def query_llm(system_prompt: str, user_prompt: str) -> str:
    """Helper to query the Gemini model with system instructions."""
    if not client:
        # Return a simulation response based on which agent is running
        if "Research & Intelligence Agent" in system_prompt:
            return "Simulation Research: Verified Python 3.11, click, and pandas are standard for CLI parsing. Competitors use simple argparse. No significant risks identified."
        elif "Solution Architect" in system_prompt:
            return "Simulation Architecture: Blueprint specifies config/, src/main.py, and setup.py. Model schemas defined."
        else:
            return "Simulation Code: print('Sample Output Generated')"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
        )
        return response.text
    except Exception as e:
        print(f"Error querying Gemini: {e}")
        return f"Error: {e}"


def load_agent_file(agent_name: str, file_name: str) -> str:
    """Reads a configuration or instruction markdown file for an agent."""
    path = os.path.join("agents", agent_name, file_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def write_shared_file(stage: str, file_name: str, content: str):
    """Writes output artifacts into the shared workspace."""
    dir_path = os.path.join("shared_workspace", stage)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, file_name), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py \"Describe the project you want to build\"")
        sys.exit(1)

    project_description = sys.argv[1]
    print(f"\n🚀 Starting Autonomous Multi-Agent Pipeline for Project:\n\"{project_description}\"\n")

    # ─── PHASE 1: RESEARCH ──────────────────────────────────────────────────────
    print("🧠 [Phase 1] Invoking Research & Intelligence Agent...")
    research_prompt = load_agent_file("research-agent", "prompt.md")
    research_instructions = load_agent_file("research-agent", "instructions.md")
    research_constraints = load_agent_file("research-agent", "constraints.md")

    full_research_system = f"{research_prompt}\n\n{research_instructions}\n\n{research_constraints}"
    
    # Query research
    research_output = query_llm(
        system_prompt=full_research_system,
        user_prompt=f"Generate the full research package for this project: {project_description}. Provide sections matching research_package.md, competitors.md, database_analysis.md, etc."
    )
    
    # Write output to shared workspace
    write_shared_file("research", "research_package.md", research_output)
    print("✅ Research package saved to: shared_workspace/research/research_package.md")

    # ─── PHASE 2: ARCHITECTURE ──────────────────────────────────────────────────
    print("\n📐 [Phase 2] Invoking Solution Architect...")
    architect_prompt = load_agent_file("solution-architect", "prompt.md")
    architect_instructions = load_agent_file("solution-architect", "instructions.md")
    architect_constraints = load_agent_file("solution-architect", "constraints.md")

    full_architect_system = f"{architect_prompt}\n\n{architect_instructions}\n\n{architect_constraints}"
    
    architect_output = query_llm(
        system_prompt=full_architect_system,
        user_prompt=f"Read this research: {research_output[:10000]}. Design the architecture. Provide folder structures, models, API schemas, and milestones matching folder_structure.md, api_design.md, database_schema.md."
    )
    
    write_shared_file("architecture", "architecture.md", architect_output)
    print("✅ System design specs saved to: shared_workspace/architecture/architecture.md")

    # ─── PHASE 3: IMPLEMENTATION ────────────────────────────────────────────────
    print("\n💻 [Phase 3] Invoking Implementation Engineer...")
    engineer_prompt = load_agent_file("implementation-engineer", "prompt.md")
    engineer_instructions = load_agent_file("implementation-engineer", "instructions.md")
    engineer_constraints = load_agent_file("implementation-engineer", "constraints.md")

    full_engineer_system = f"{engineer_prompt}\n\n{engineer_instructions}\n\n{engineer_constraints}"
    
    engineer_output = query_llm(
        system_prompt=full_engineer_system,
        user_prompt=f"Based on Research: {research_output[:5000]} and Architecture: {architect_output[:5000]}. Generate code. Provide files to create, write class files matching coding_guidelines.md, and generated_files.md logs."
    )
    
    write_shared_file("implementation", "implementation_notes.md", engineer_output)
    print("✅ Implementation notes and code output logged to: shared_workspace/implementation/implementation_notes.md")
    print("\n🎉 Autonomous Agent Pipeline Finished successfully!\n")


if __name__ == "__main__":
    main()
