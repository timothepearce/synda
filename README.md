# Synda

> [!WARNING]
> This project is in its very early stages of development and should not be used in production environments.

> [!NOTE]
> PR are more than welcome. Check the roadmap if you want to contribute or create discussion to submit a use-case.

Synda (*synthetic data*) is a package that allows you to create synthetic data generation pipelines. 
It is opinionated and fast by design, with plans to become highly configurable in the future.


## Installation

Synda requires Python 3.10 or higher.

### Using pipx

You can install Synda using pipx:

```bash
pipx install synda
```

### Using uv

You can also install Synda using uv:

```bash
# Install uv if you don't have it
pip install uv

# Install Synda
uv pip install synda
```

### Development Installation

For development, clone the repository and install using uv:

```bash
# Clone the repository
git clone https://github.com/timothepearce/synda.git
cd synda

# Create a virtual environment and install dependencies
make setup
make dev

# Or manually:
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt
uv pip install -e .
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
      provider: openai  # You can also use 'openrouter' here
      model: gpt-4o-mini  # For OpenRouter, use format like 'openai/gpt-3.5-turbo'
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
# For OpenAI
synda provider add openai --api-key [YOUR_API_KEY]

# For OpenRouter
synda provider add openrouter --api-key [YOUR_OPENROUTER_API_KEY]
```

3. Generate some synthetic data:

```bash
synda generate config.yaml
```

## Pipeline Structure

The Synda pipeline consists of three main parts:

- **Input**: Data source configuration
- **Pipeline**: Sequence of transformation and generation steps
- **Output**: Configuration for the generated data output

### Available Pipeline Steps

Synda supports the following pipeline steps:

- **split**: Breaks down data (`method: chunk` or `method: separator`)
- **generation**: Generates content using LLMs (`method: llm`)
- **clean**: Delete the duplicated data (`method: deduplicate-tf-idf`)
- **ablation**: Filters data based on defined criteria (`method: llm-judge-binary`)
- **metadata**: Add metadata to text (`method: word-position`)
- **input**: Load data from various sources (`method: csv` or `method: xls`)
- **output**: Save data to various destinations (`method: csv` or `method: xls`)
- **custom**: Execute custom Python scripts (`method: script`)

## Advanced Features

Synda now includes many advanced features:

- **Asynchronous execution** for improved performance
- **Batch processing** for LLM steps
- **vLLM integration** for high-throughput inference
- **Caching** of step outputs for faster execution
- **Distributed processing** with Ray
- **Pausing and resuming** pipelines
- **Custom scriptable steps** for flexible processing
- **API server** for programmatic access

For more details, see the [Advanced Features](docs/advanced_features.md) documentation.

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
- [x] Add OpenRouter support
- [x] Add asynchronous behaviour for any CLI
- [x] Add vLLM with structured generation output
- [x] Batch processing logic (via param.) for LLMs steps
- [x] Move input into pipeline (step type: 'load')
- [x] Move output into pipeline (step type: 'export')
- [x] Allow pausing and resuming pipelines
- [x] Trace each synthetic data with his historic
- [x] Enable caching of each step's output
- [x] Implement custom scriptable step for developer
- [x] Use Ray for large workload
- [x] Add a programmatic API

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
