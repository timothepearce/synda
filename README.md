# Nebula

A simple synthetic data generator pipeline.

## Pipeline file

```yaml
source:
  type: csv
  properties:
    path: "./source.csv"
    target_column: "content"

pipeline:
  - type: split
    method: chunk
    parameters:
      size: 500

  - type: generation
    parameters:
      provider: openai
      model: gpt-4o-mini
      template: |
        Here is some text:
        content: {chunk}

        Instructions :
        1. Ask a question regarding the content
        2. Use english only

  - type: ablation
    method: llm
    parameters:
      model: gpt-4o-mini
      instructions:
        - "Checks text for consistency"
        - "Check that the text is only in English"
```
