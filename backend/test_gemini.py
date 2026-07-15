from dotenv import load_dotenv
load_dotenv()
import asyncio
from src.AI.llm.provider import get_llm_provider

async def test():
    try:
        llm = get_llm_provider()
        print(f"Using provider: {type(llm).__name__}")
        resp = await llm.complete([{"role": "user", "content": "hello"}], max_tokens=10)
        print("Success:", resp)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
