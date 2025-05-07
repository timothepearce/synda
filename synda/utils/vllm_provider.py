import logging
import requests

import vllm


logging.getLogger("vllm").setLevel(logging.CRITICAL)

class VLLMProvider:
    @classmethod
    def call(
        cls,
        provider: str,
        model: str,
        api_url: str,
        prompts: list[str],
        temperature: float = 1.0,
        max_tokens: int | None = None
    ) -> list[str]:
        if "hosted_vllm" in provider:
            if "v1/chat/completions" in api_url:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt} for prompt in prompts
                    ],
                    "temperature": temperature,
                    **({"max_tokens": max_tokens} if max_tokens is not None else {})
                }
            elif "v1/completions" in api_url:
                payload = {
                    "model": model,
                    "prompt": prompts,
                    "temperature": temperature,
                    **({"max_tokens": max_tokens} if max_tokens is not None else {})
                }
            else:
                raise ValueError("vLLM API endpoint not recognized in synda")
            return cls._invoke_vllm_rest_api(api_url=api_url, payload=payload)
        elif "vllm" in provider:
            return cls._invoke_vllm_programmatic_api(prompts=prompts, model=model, temperature=temperature)
        raise ValueError(
            "To use vLLM for inference, the provider name should contains 'vllm' in its name to use vLLM"
            "programmatic API or 'hosted_vllm' to request a vLLM server"
        )


    @staticmethod
    def _invoke_vllm_rest_api(api_url: str, payload: dict[str, str | list | dict]) -> list[str]:
        llm_answers = requests.post(url=api_url, json=payload).json()
        return [response["text"] for response in llm_answers["choices"]]

    @staticmethod
    def _invoke_vllm_programmatic_api(
            prompts: list[str], model: str, temperature: float, max_tokens: int | None = None
    ) -> list[str]:
        llm = vllm.LLM(model=model)
        sampling_params = vllm.SamplingParams(temperature=temperature, max_tokens=max_tokens)
        llm_answers = llm.generate(prompts=prompts, sampling_params=sampling_params)
        return [response.outputs[0].text for response in llm_answers]
