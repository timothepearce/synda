"""
This file overwrite the litellm batch_completion function for vllm provider
This overwriting is due to an error coming from "stream" args set to False by default
and not supported by vllm
"""
from typing import List, Optional

import litellm
from litellm.utils import get_optional_params
from litellm.llms.vllm.completion import handler as vllm_handler

def vllm_batch_completion(
        model: str,
        # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
        messages: Optional[List] = None,
        functions: Optional[List] = None,
        function_call: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stream: Optional[bool] = None,
        stop=None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[dict] = None,
        user: Optional[str] = None,
        deployment_id=None,
        request_timeout: Optional[int] = None,
        timeout: Optional[int] = 600,
        max_workers: Optional[int] = 100,
        # Optional liteLLM function params
        **kwargs,
):
    """
    Batch litellm.completion function for a given model.

    Args:
        model (str): The model to use for generating completions.
        messages (List, optional): List of messages to use as input for generating completions. Defaults to [].
        functions (List, optional): List of functions to use as input for generating completions. Defaults to [].
        function_call (str, optional): The function call to use as input for generating completions. Defaults to "".
        temperature (float, optional): The temperature parameter for generating completions. Defaults to None.
        top_p (float, optional): The top-p parameter for generating completions. Defaults to None.
        n (int, optional): The number of completions to generate. Defaults to None.
        stream (bool, optional): Whether to stream completions or not. Defaults to None.
        stop (optional): The stop parameter for generating completions. Defaults to None.
        max_tokens (float, optional): The maximum number of tokens to generate. Defaults to None.
        presence_penalty (float, optional): The presence penalty for generating completions. Defaults to None.
        frequency_penalty (float, optional): The frequency penalty for generating completions. Defaults to None.
        logit_bias (dict, optional): The logit bias for generating completions. Defaults to {}.
        user (str, optional): The user string for generating completions. Defaults to "".
        deployment_id (optional): The deployment ID for generating completions. Defaults to None.
        request_timeout (int, optional): The request timeout for generating completions. Defaults to None.
        max_workers (int,optional): The maximum number of threads to use for parallel processing.

    Returns:
        list: A list of completion results.
    """
    args = locals()
    if not messages:
        messages = []
    batch_messages = messages
    completions = []
    model = model
    custom_llm_provider = None
    if model.split("/", 1)[0] in litellm.provider_list:
        custom_llm_provider = model.split("/", 1)[0]
        model = model.split("/", 1)[1]

    optional_params = get_optional_params(
        functions=functions,
        function_call=function_call,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
        stop=stop,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        # params to identify the model
        model=model,
        custom_llm_provider=custom_llm_provider,
    )
    results = vllm_handler.batch_completions(
        model=model,
        messages=batch_messages,
        custom_prompt_dict=litellm.custom_prompt_dict,
        optional_params=optional_params,
    )
    return results
