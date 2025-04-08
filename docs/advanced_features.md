# Advanced Features in Synda

This document describes the advanced features available in Synda for creating more powerful and efficient synthetic data generation pipelines.

## Asynchronous Execution

Synda now supports asynchronous execution for improved performance, especially when working with LLMs and large datasets.

To use asynchronous execution, add the `--async` flag when running the pipeline:

```bash
synda generate config.yaml --async
```

You can also enable asynchronous execution for specific steps in your pipeline by adding `use_async: true` to the step parameters:

```yaml
- type: generation
  method: llm
  parameters:
    provider: openai
    model: gpt-3.5-turbo
    use_async: true
    # other parameters...
```

## Batch Processing

For improved throughput when working with LLMs, Synda now supports batch processing. You can specify a batch size for the entire pipeline or for individual steps:

```bash
synda generate config.yaml --batch-size 10
```

Or in the configuration:

```yaml
- type: generation
  method: llm
  parameters:
    provider: openai
    model: gpt-3.5-turbo
    batch_size: 10
    # other parameters...
```

## vLLM Integration

Synda now supports [vLLM](https://github.com/vllm-project/vllm) for high-throughput LLM inference. To use vLLM:

```yaml
- type: generation
  method: llm
  parameters:
    provider: vllm
    model: meta-llama/Llama-2-7b-chat-hf
    # other parameters...
```

## Caching

Synda now includes a caching system that can significantly speed up pipeline execution by reusing results from previous runs. Caching is enabled by default but can be disabled:

```bash
synda generate config.yaml --no-cache
```

You can manage the cache using the new `cache` command:

```bash
# Clear the entire cache
synda cache clear

# Clear cache for a specific step
synda cache clear --step 123

# View cache information
synda cache info
```

## Distributed Processing with Ray

For large workloads, Synda now integrates with [Ray](https://ray.io/) for distributed processing:

```bash
synda generate config.yaml --ray
```

## Pausing and Resuming Pipelines

You can now pause a pipeline after a specific step and resume it later:

```bash
# Pause after step 3
synda generate config.yaml --pause-after 3

# Resume from where you left off
synda generate --resume RUN_ID
```

## Input and Output as Pipeline Steps

You can now include input and output operations as steps in your pipeline, which allows for more complex data flows:

```yaml
pipeline:
  # Input step
  - type: input
    method: csv
    parameters:
      path: input.csv
      target_column: content
      separator: "\t"
  
  # Processing steps...
  
  # Output step
  - type: output
    method: csv
    parameters:
      path: output.csv
      separator: "\t"
```

## Custom Scriptable Steps

You can now create custom processing steps using Python scripts:

```yaml
- type: custom
  method: script
  parameters:
    script_path: "/path/to/script.py"
    function_name: "process_text"
    script_params:
      param1: value1
      param2: value2
```

Your script should define a function with the specified name that takes a text input and returns processed text:

```python
def process_text(text, node_id=None, parent_node_id=None, **kwargs):
    # Process the text
    return processed_text
```

## API Server

Synda now includes an API server for programmatic access:

```bash
# Start the API server
synda server --port 8000
```

You can then interact with the API using HTTP requests or the provided Python client:

```python
from synda.api.client import SyndaClient

client = SyndaClient("http://localhost:8000")

# Run a pipeline
result = client.run_pipeline_from_file("config.yaml")
run_id = result["run_id"]

# Check status
status = client.get_pipeline_status(run_id)

# Wait for completion
final_status = client.wait_for_completion(run_id)
```

## Example Advanced Pipeline

See the `examples/advanced_pipeline.yaml` file for a complete example that demonstrates these advanced features.