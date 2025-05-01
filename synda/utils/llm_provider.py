from litellm import completion, embedding
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
        temperature: float = 1.0,
    ) -> str:
        provider = LLMProvider._resolve_provider(provider)
        params = {
            "model": f"{provider}/{model}",
            "messages": [{"content": prompt, "role": "user"}],
            "api_key": api_key,
            "api_base": url,
            "response_format": response_format,
            "temperature": temperature,
        }
        if format:
            params["format"] = format

        response = completion(**params)
        return response["choices"][0]["message"]["content"]
    
    @staticmethod
    def embedding(
        provider: str,
        model: str,
        api_key: str,
        texts: list[str],
        url: str | None = None,
    ) -> list[list[float]]:
        provider = LLMProvider._resolve_provider(provider)
        params = {
            "model": f"{provider}/{model}",
            "input": texts,
            "api_key": api_key,
            "api_base": url,
        }
        response = embedding(**params)
        return [d["embedding"] for d in response["data"]]

    @staticmethod
    def embedding(
        provider: str,
        model: str,
        api_key: str,
        texts: list[str],
        url: str | None = None,
    ) -> list[list[float]]:
        provider = LLMProvider._resolve_provider(provider)
        params = {
            "model": f"{provider}/{model}",
            "input": texts,
            "api_key": api_key,
            "api_base": url,
        }
        response = embedding(**params)
        return [d["embedding"] for d in response["data"]]

    @staticmethod
    def _resolve_provider(provider: str):
        if provider == "ollama":
            return "ollama_chat"
        return provider
