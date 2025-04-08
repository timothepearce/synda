import asyncio
import os
from typing import List, Dict, Any, Optional, Union
import json

from litellm import completion, acompletion
from pydantic import BaseModel

from synda.utils.vllm_provider import VLLMProvider


class LLMProvider:
    @staticmethod
    def call(
        provider: str,
        model: str,
        api_key: str,
        prompt: str,
        response_format: BaseModel | None = None,
        url: str | None = None,
        format: str | None = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
    ) -> str:
        """Call an LLM provider with the given prompt."""
        # Use vLLM if specified
        if provider == "vllm":
            return VLLMProvider.call(
                model=model,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                format=format,
            )
        
        # Use LiteLLM for other providers
        provider = LLMProvider._resolve_provider(provider)
        response = completion(
            model=f"{provider}/{model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=api_key,
            api_base=url,
            response_format=response_format,
            format=format,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response["choices"][0]["message"]["content"]
    
    @staticmethod
    async def call_async(
        provider: str,
        model: str,
        api_key: str,
        prompt: str,
        response_format: BaseModel | None = None,
        url: str | None = None,
        format: str | None = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
    ) -> str:
        """Call an LLM provider asynchronously with the given prompt."""
        # Use vLLM if specified
        if provider == "vllm":
            return await VLLMProvider.call_async(
                model=model,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                format=format,
            )
        
        # Use LiteLLM for other providers
        provider = LLMProvider._resolve_provider(provider)
        response = await acompletion(
            model=f"{provider}/{model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=api_key,
            api_base=url,
            response_format=response_format,
            format=format,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response["choices"][0]["message"]["content"]
    
    @staticmethod
    async def batch_call_async(
        provider: str,
        model: str,
        api_key: str,
        prompts: List[str],
        response_format: BaseModel | None = None,
        url: str | None = None,
        format: str | None = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        batch_size: int = 10,
    ) -> List[str]:
        """Call an LLM provider with multiple prompts in batches."""
        # Use vLLM if specified (which has native batching)
        if provider == "vllm":
            return await VLLMProvider.batch_call_async(
                model=model,
                prompts=prompts,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                format=format,
            )
        
        # For other providers, process in batches
        results = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            tasks = [
                LLMProvider.call_async(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    prompt=prompt,
                    response_format=response_format,
                    url=url,
                    format=format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                for prompt in batch
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def batch_call(
        provider: str,
        model: str,
        api_key: str,
        prompts: List[str],
        response_format: BaseModel | None = None,
        url: str | None = None,
        format: str | None = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        batch_size: int = 10,
    ) -> List[str]:
        """Synchronous wrapper for the async batch call method."""
        return asyncio.run(
            LLMProvider.batch_call_async(
                provider=provider,
                model=model,
                api_key=api_key,
                prompts=prompts,
                response_format=response_format,
                url=url,
                format=format,
                temperature=temperature,
                max_tokens=max_tokens,
                batch_size=batch_size,
            )
        )

    @staticmethod
    def _resolve_provider(provider: str):
        if provider == "ollama":
            return "ollama_chat"
        elif provider == "openrouter":
            return "openrouter"
        return provider
