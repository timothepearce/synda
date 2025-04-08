import os
from synda.utils.llm_provider import LLMProvider

# Test OpenRouter provider
provider = "openrouter"
model = "openai/gpt-3.5-turbo"  # Example model
api_key = "your_openrouter_api_key"  # Replace with your actual API key
prompt = "Hello, how are you?"

try:
    response = LLMProvider.call(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=prompt,
        temperature=0.7,
    )
    print(f"Response from OpenRouter: {response}")
    print("OpenRouter integration successful!")
except Exception as e:
    print(f"Error testing OpenRouter: {e}")