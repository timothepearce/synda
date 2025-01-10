# Nebula

A simple synthetic data generator pipeline.

## Pipeline file

```yaml
source:
  type: csv
  properties:
    path: "path/to/source.csv"
    target_column: "content"

steps:
  - type: split
    method: chunk
    parameters:
      size: 500
      template: |
        Here is some text:
        content: {chunk}
        
        Instructions :
        1. Ask a question regarding the content
        2. Use english only
  
  - type: generation
    parameters:
      provider: openai
      model: gpt-4o-mini

  - type: ablation
    method: llm
    parameters:
      model: gpt-4o-mini
      instructions:
        - "Checks text for consistency"
        - "Check that the text is only in English"
```
