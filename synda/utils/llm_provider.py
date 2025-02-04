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
    ) -> str:
        response = completion(
            model=f"{provider}/{model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=api_key,
            response_format=response_format,
        )

        return response["choices"][0]["message"]["content"]
