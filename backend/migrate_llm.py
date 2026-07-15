"""
Migrate all remaining AI files from hardcoded Groq to the LLM provider abstraction.
Run from the backend directory: python migrate_llm.py
"""
import re
import os

files_to_patch = [
    "src/AI/catalog/adaptation.py",
    "src/AI/memory/extraction.py",
    "src/AI/workflow/analysis.py",
    "src/AI/catalog/parser.py",
    "src/AI/pipelines/planning.py",
    "src/AI/pipelines/blueprint.py",
    "src/AI/catalog/ranking.py",
    "src/AI/catalog/refinement.py",
]

def patch_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    
    # Replace import
    content = re.sub(
        r'from groq import AsyncGroq\n',
        'from src.AI.llm.provider import get_llm_provider\n',
        content
    )
    # Remove settings import if only used for GROQ_API_KEY (keep if other settings used)
    # We only remove the groq API key guard checks
    content = re.sub(
        r"if not settings\.GROQ_API_KEY.*?:\n.*?return.*?\n",
        "",
        content
    )
    
    # Replace: client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    content = re.sub(
        r'client = AsyncGroq\(api_key=settings\.GROQ_API_KEY\)',
        'llm = get_llm_provider()',
        content
    )
    
    # Replace: await client.chat.completions.create(
    #              model="...",
    #              messages=messages,
    #              response_format={"type": "json_object"},
    #              temperature=0.x
    #          )
    # with: await llm.complete(messages=messages, ...)
    
    # Pattern for non-streaming, json_object format calls
    content = re.sub(
        r'await client\.chat\.completions\.create\(\s*\n\s*model="[^"]+",\s*\n\s*messages=(\w+),\s*\n\s*response_format=\{"type":\s*"json_object"\},\s*\n\s*temperature=([\d.]+)\s*\n\s*\)',
        lambda m: f'await llm.complete({m.group(1)}, temperature={m.group(2)})',
        content
    )
    
    # Pattern for non-streaming calls without json_object
    content = re.sub(
        r'await client\.chat\.completions\.create\(\s*\n\s*model="[^"]+",\s*\n\s*messages=(\w+),\s*\n\s*temperature=([\d.]+)\s*\n\s*\)',
        lambda m: f'await llm.complete({m.group(1)}, temperature={m.group(2)})',
        content
    )
    
    # Replace response.choices[0].message.content
    content = content.replace(
        "response.choices[0].message.content",
        "response"  # llm.complete() already returns the text
    )
    
    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Patched: {path}")
    else:
        print(f"⚠️  No changes in: {path}")

for fpath in files_to_patch:
    if os.path.exists(fpath):
        patch_file(fpath)
    else:
        print(f"❌ File not found: {fpath}")

print("\nDone. Review each patched file to ensure correctness.")
