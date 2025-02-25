# Synda

> [!WARNING]
> This project is in its very early stages of development and should not be used in production environments.

> [!NOTE]
> PR are more than welcome. Check the roadmap if you want to contribute or create discussion to submit a use-case.

Synda (*synthetic data*) is a package that allows you to create synthetic data generation pipelines. 
It is opinionated and fast by design, with plans to become highly configurable in the future.


## Installation

Synda requires Python 3.10 or higher.

You can install Synda using pipx:

```bash
pipx install synda
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
    name: chunk_faq
    parameters:
      size: 500
      # overlap: 20

  - type: split
    method: separator
    name: sentence_chunk_faq
    parameters:
      separator: .
      keep_separator: true

  - type: generation
    method: llm
    parameters:
      provider: openai
      model: gpt-4o-mini
      template: |
        Ask a question regarding the sentence about the content.
        content: {chunk_faq}
        sentence: {sentence_chunk_faq}

        Instructions :
        1. Use english only
        2. Keep it short

        question:

  - type: clean
    method: deduplicate-tf-idf
    parameters:
      strategy: fuzzy
      similarity_threshold: 0.9
      keep: first 

  - type: ablation
    method: llm-judge-binary
    parameters:
      provider: openai
      model: gpt-4o-mini
      consensus: all # any, majority
      criteria:
        - Is the question written in english?
        - Is the question consistent?

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

### Available Pipeline Steps

Currently, Synda supports four pipeline steps (as shown in the example above):

- **split**: Breaks down data (`method: chunk` or `method: split`)
- **generation**: Generates content using LLMs (`method: llm`)
- **clean**: Delete the duplicated data (`method: deduplicate-tf-idf`)
- **ablation**: Filters data based on defined criteria (`method: llm-judge-binary`)
- **metadata**: Add metadata to text (`method: word-position`)

More steps will be added in future releases.

## Roadmap

The following features are planned for future releases.

### Core
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
- [x] Add Ollama with structured generation output
- [x] Retry a failed run
- [ ] Add asynchronous behaviour for any CLI
- [ ] Add vLLM with structured generation output
- [ ] Batch processing logic (via param.) for LLMs steps
- [ ] Move input into pipeline (step type: 'load')
- [ ] Move output into pipeline (step type: 'export')
- [ ] Allow pausing and resuming pipelines
- [ ] Trace each synthetic data with his historic
- [ ] Enable caching of each step's output
- [ ] Implement custom scriptable step for developer
- [ ] Use Ray for large workload
- [ ] Add a programmatic API

### Steps
- [x] input/output: .xls format
- [ ] input/output: Hugging Face datasets
- [ ] chunk: Semantic chunks
- [ ] clean: embedding deduplication
- [ ] ablation: LLMs as a juries
- [ ] masking: NER (GliNER)
- [ ] masking: Regexp
- [ ] masking: PII
- [ ] metadata: Word position
- [ ] metadata: Regexp

### Ideas
- [ ] translations (SeamlessM4T)
- [ ] speech-to-text
- [ ] text-to-speech
- [ ] metadata extraction
- [ ] tSNE / PCA
- [ ] custom steps?

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
