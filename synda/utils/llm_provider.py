from litellm import completion
from pydantic import BaseModel


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
    ) -> str:
        provider = LLMProvider._resolve_provider(provider)
        response = completion(
            model=f"{provider}/{model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=api_key,
            api_base=url,
            response_format=response_format,
            format=format,
        )

        return response["choices"][0]["message"]["content"]

    @staticmethod
    def _resolve_provider(provider: str):
        if provider == "ollama":
            return "ollama_chat"
        return provider
