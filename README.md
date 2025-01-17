# Synda

> [!WARNING]
> This project is in its very early stages of development and should not be used in production environments.

> [!NOTE]
> PR are more than welcome. Check the roadmap if you want to contribute or create discussion to submit a use-case.

Synda (*synthetic data*) is a package that allows you to create synthetic data generation pipelines. 
It is opinionated and fast by design, with plans to become highly configurable in the future.


## Installation

```bash
pip install nebula
```

## Usage

1. Create a YAML configuration file (e.g., `config.yaml`) that defines your pipeline:

```yaml
input:
  type: csv
  properties:
    path: tests/stubs/simple_pipeline/source.csv
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

2. Run the following command:

```bash
poetry run nebula -i config.yaml
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
- [ ] Implement a common interface (Node) for input and output of each step
- [ ] Trace each synthetic data with his historic
- [ ] Add SQLite support
- [ ] Store each execution and step in DB
- [ ] Allow pausing and resuming pipelines
- [ ] Enable caching of each step's output
- [ ] Implement scriptable step for developer
- [ ] Design other step & methods

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.