import json
from typing import Any, Dict, List, Optional, Union
import asyncio
from pydantic import BaseModel

from vllm import LLM, SamplingParams


class VLLMProvider:
    """Provider for vLLM inference."""
    
    _instances = {}
    
    @classmethod
    def get_instance(cls, model_name: str, **kwargs) -> "LLM":
        """Get or create a vLLM instance for the specified model."""
        if model_name not in cls._instances:
            cls._instances[model_name] = LLM(model=model_name, **kwargs)
        return cls._instances[model_name]
    
    @staticmethod
    def _prepare_prompt(prompt: str) -> str:
        """Prepare the prompt for vLLM."""
        return prompt
    
    @staticmethod
    def _prepare_messages(messages: List[Dict[str, str]]) -> str:
        """Convert messages format to a prompt string."""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
            else:
                prompt += f"{role.capitalize()}: {content}\n\n"
                
        prompt += "Assistant: "
        return prompt
    
    @classmethod
    async def call_async(
        cls,
        model: str,
        prompt: str,
        response_format: Optional[BaseModel] = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        **kwargs
    ) -> str:
        """Call vLLM asynchronously with the given prompt."""
        llm = cls.get_instance(model)
        
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        prepared_prompt = cls._prepare_prompt(prompt)
        outputs = await llm.generate([prepared_prompt], sampling_params)
        
        generated_text = outputs[0].outputs[0].text
        
        # Handle structured output if response_format is provided
        if response_format is not None:
            try:
                # Try to extract JSON from the response
                json_start = generated_text.find('{')
                json_end = generated_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = generated_text[json_start:json_end]
                    # Validate against the response format
                    parsed = json.loads(json_str)
                    return json.dumps(parsed)
                
                return generated_text
            except (json.JSONDecodeError, ValueError):
                return generated_text
        
        return generated_text
    
    @classmethod
    def call(
        cls,
        model: str,
        prompt: str,
        response_format: Optional[BaseModel] = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        **kwargs
    ) -> str:
        """Synchronous wrapper for the async call method."""
        return asyncio.run(
            cls.call_async(
                model, prompt, response_format, temperature, max_tokens, **kwargs
            )
        )
    
    @classmethod
    async def batch_call_async(
        cls,
        model: str,
        prompts: List[str],
        response_format: Optional[BaseModel] = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        **kwargs
    ) -> List[str]:
        """Call vLLM with multiple prompts in a batch."""
        llm = cls.get_instance(model)
        
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        prepared_prompts = [cls._prepare_prompt(prompt) for prompt in prompts]
        outputs = await llm.generate(prepared_prompts, sampling_params)
        
        results = []
        for output in outputs:
            generated_text = output.outputs[0].text
            
            # Handle structured output if response_format is provided
            if response_format is not None:
                try:
                    # Try to extract JSON from the response
                    json_start = generated_text.find('{')
                    json_end = generated_text.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = generated_text[json_start:json_end]
                        # Validate against the response format
                        parsed = json.loads(json_str)
                        results.append(json.dumps(parsed))
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
            
            results.append(generated_text)
        
        return results
    
    @classmethod
    def batch_call(
        cls,
        model: str,
        prompts: List[str],
        response_format: Optional[BaseModel] = None,
        temperature: float = 1.0,
        max_tokens: int = 512,
        **kwargs
    ) -> List[str]:
        """Synchronous wrapper for the async batch call method."""
        return asyncio.run(
            cls.batch_call_async(
                model, prompts, response_format, temperature, max_tokens, **kwargs
            )
        )