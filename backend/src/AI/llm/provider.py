"""
LLM Provider Abstraction Layer
==============================
Selects the active LLM provider based on the LLM_PROVIDER env variable.
Supports: "gemini" | "groq"

Usage:
    from src.AI.llm.provider import get_llm_provider
    llm = get_llm_provider()
    
    # Non-streaming
    text = await llm.complete(messages, max_tokens=8000)
    
    # Streaming (yields str chunks)
    async for chunk in llm.stream(messages, max_tokens=8000):
        ...
"""

import logging
from typing import AsyncIterator, List, Dict, Any
from src.utils.settings import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Base class. Subclasses implement complete() and stream()."""

    async def complete(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> str:
        raise NotImplementedError

    async def stream(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> AsyncIterator[str]:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini provider via google-generativeai SDK."""

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        logger.info(f"[LLM] Using Gemini provider — model: {self.model_name}")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple[str, list]:
        """Convert OpenAI-style messages to Gemini format."""
        system_prompt = ""
        history = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_prompt = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        return system_prompt, history

    async def complete(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> str:
        import asyncio
        system_prompt, history = self._convert_messages(messages)
        
        model = self._genai.GenerativeModel(
            self.model_name,
            system_instruction=system_prompt if system_prompt else None,
        )
        
        # Gemini's Python SDK is sync — run in thread pool
        def _sync_call():
            chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
            last_user_msg = history[-1]["parts"][0] if history else ""
            response = chat.send_message(
                last_user_msg,
                generation_config=self._genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                )
            )
            return response.text

        return await asyncio.get_running_loop().run_in_executor(None, _sync_call)

    async def stream(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> AsyncIterator[str]:
        import asyncio
        import queue as queue_module

        system_prompt, history = self._convert_messages(messages)

        model = self._genai.GenerativeModel(
            self.model_name,
            system_instruction=system_prompt if system_prompt else None,
        )

        # Use a queue to bridge the sync Gemini SDK streaming with async
        chunk_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        _SENTINEL = object()

        def _sync_stream_all():
            """Run in thread pool — streams ALL chunks and puts them on the queue."""
            try:
                chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
                last_user_msg = history[-1]["parts"][0] if history else ""
                response = chat.send_message(
                    last_user_msg,
                    stream=True,
                    generation_config=self._genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    )
                )
                for chunk in response:
                    if chunk.text:
                        loop.call_soon_threadsafe(chunk_queue.put_nowait, chunk.text)
            except Exception as e:
                loop.call_soon_threadsafe(chunk_queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(chunk_queue.put_nowait, _SENTINEL)

        # Start streaming in background thread — does NOT block the event loop
        loop.run_in_executor(None, _sync_stream_all)

        # Yield chunks as they arrive from the queue
        while True:
            item = await chunk_queue.get()
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                raise item
            yield item



class GroqProvider(LLMProvider):
    """Groq provider via groq SDK."""

    def __init__(self):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model_name = "llama-3.3-70b-versatile"
        logger.info(f"[LLM] Using Groq provider — model: {self.model_name}")

    async def complete(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def stream(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.7) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


def get_llm_provider() -> LLMProvider:
    """Factory: returns the active LLM provider based on LLM_PROVIDER env var."""
    provider_name = (settings.LLM_PROVIDER or "groq").lower().strip()

    if provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("[LLM] GEMINI_API_KEY not set — falling back to Groq")
            return GroqProvider()
        return GeminiProvider()
    
    elif provider_name == "groq":
        if not settings.GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER=groq but GROQ_API_KEY is not set.")
        return GroqProvider()
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider_name}'. Expected 'gemini' or 'groq'.")
