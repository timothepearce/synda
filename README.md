# Synda

> [!WARNING]
> This project is in its very early stages of development and should not be used in production environments.

> [!NOTE]
> PR are more than welcome. Check the roadmap if you want to contribute or create discussion to submit a use-case.

Synda (*synthetic data*) is a package that allows you to create synthetic data generation pipelines. 
It is opinionated and fast by design, with plans to become highly configurable in the future.


## Installation

Synda requires Python 3.10 or higher.

You can install Synda using pip:

```bash
pip install synda
```

## Usage

1. Create a YAML configuration file (e.g., `config.yaml`) that defines your pipeline:

```yaml
input:
  type: csv
  properties:
    path: source.csv  # relative path to your source file
    target_column: content
    separator: "\t"

pipeline:
  - type: split
    method: chunk
    parameters:
      size: 500

  - type: generation
    method: llm
    parameters:
      provider: openai
      model: gpt-4o-mini
      template: |
        Ask a question regarding the content.
        content: {chunk}

        Instructions :
        1. Use english only
        2. Keep it short

        question:

  - type: ablation
    method: llm-judge-binary
    parameters:
      provider: openai
      model: gpt-4o-mini
      consensus: all
      criteria:
        - Is the text written in english?
        - Is the text consistent?

output:
  type: csv
  properties:
    path: tests/stubs/simple_pipeline/output.csv
    separator: "\t"
```

2. Add a model provider:

```bash
synda provider add openai --api-key [YOUR_API_KEY]
```

3. Generate some synthetic data:

```bash
synda generate config.yaml
```

## Pipeline Structure

The Nebula pipeline consists of three main parts:

- **Input**: Data source configuration
- **Pipeline**: Sequence of transformation and generation steps
- **Output**: Configuration for the generated data output

### Available Steps

- **split**: Breaks down data into chunks of defined size
- **generation**: Generates content using LLM models
- **ablation**: Filters data based on defined criteria

## Roadmap

The following features are planned for future releases:

- [x] Implement a Proof of Concept
- [x] Implement a common interface (Node) for input and output of each step
- [x] Add SQLite support
- [x] Add setter command for provider variable (openai, etc.)
- [ ] Store each execution and step in DB
- [ ] Allow pausing and resuming pipelines
- [ ] Enable caching of each step's output
- [ ] Trace each synthetic data with his historic
- [ ] Design other step & methods
- [ ] Implement custom scriptable step for developer
- [ ] Add Ollama, VLLM and transformers provider
- [ ] Add a programmatic API
- [ ] Use Ray for large workload

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.