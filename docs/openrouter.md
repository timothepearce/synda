# Using OpenRouter with Synda

Synda supports [OpenRouter](https://openrouter.ai/) as a provider for LLM generation steps. OpenRouter gives you access to a wide range of models from different providers through a single API.

## Setup

1. Sign up for an account at [OpenRouter](https://openrouter.ai/) and get your API key.

2. Add OpenRouter as a provider in Synda:

```bash
synda provider add openrouter --api-key YOUR_OPENROUTER_API_KEY
```

## Usage in Configuration

In your YAML configuration file, specify `openrouter` as the provider and use the appropriate model name:

```yaml
- type: generation
  method: llm
  parameters:
    provider: openrouter
    model: openai/gpt-3.5-turbo  # Format: provider/model-name
    template: |
      Your prompt template here
    temperature: 0.7
```

## Available Models

OpenRouter supports a wide range of models from different providers. The model name format is typically `provider/model-name`. Some examples include:

- `openai/gpt-3.5-turbo`
- `openai/gpt-4`
- `anthropic/claude-2`
- `anthropic/claude-instant-v1`
- `google/palm-2-chat-bison`
- `meta-llama/llama-2-70b-chat`

For a complete and up-to-date list of available models, visit the [OpenRouter models page](https://openrouter.ai/models).

## Example

See the complete example configuration in the `examples/openrouter_example.yaml` file.