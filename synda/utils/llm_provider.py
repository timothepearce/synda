from litellm import completion


class LLMProvider:
    @staticmethod
    def call(provider: str, model: str, api_key: str, prompt: str) -> str:
        response = completion(
            model=f"{provider}/{model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=api_key,
        )

        return response["choices"][0]["message"]["content"]
