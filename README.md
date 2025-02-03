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

  - type: clean
    method: deduplicate
    parameters:
      strategy: fuzzy
      similarity_threshold: 0.9
      keep: first 

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
    path: output.csv
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

### Available Pipeline Steps

Currently, Synda supports three pipeline steps (as shown in the example above):

- **split**: Breaks down data into chunks of defined size (`method: chunk` or `method: split`)
- **generation**: Generates content using LLM models (`method: llm`)
- **ablation**: Filters data based on defined criteria (`method: llm-judge-binary`)

More steps will be added in future releases.

## Roadmap

The following features are planned for future releases:

- [x] Implement a Proof of Concept
- [x] Implement a common interface (Node) for input and output of each step
- [x] Add SQLite support
- [x] Add setter command for provider variable (openai, etc.)
- [x] Store each execution and step in DB
- [x] Add "split" -> "separator" step
- [x] Add named step
- [x] Store each Node in DB
- [x] Add "clean" -> "deduplicate" step
- [x] Allow injecting params from distant step into prompt
- [ ] Retry logic for LLM steps
- [ ] Allow pausing and resuming pipelines
- [ ] Trace each synthetic data with his historic
- [ ] Enable caching of each step's output
- [ ] Implement custom scriptable step for developer
- [ ] Add Ollama, VLLM and transformers provider
- [ ] Use Ray for large workload
- [ ] Batch processing logic (via param.) for LLMs steps
- [ ] Add a programmatic API
- [ ] More steps...

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
