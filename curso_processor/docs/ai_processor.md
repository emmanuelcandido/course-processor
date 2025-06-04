# AI Processor Module

The AI Processor module provides functionality for processing text with AI models like Claude and ChatGPT.

## Features

- Process text with Claude (Anthropic) or ChatGPT (OpenAI)
- Support for multiple models and parameters
- Batch processing of text files
- Template-based prompts with variable substitution
- Token estimation and cost calculation
- Conversation management with continuation tokens

## Usage

### Basic Usage

```python
from modules.ai_processor import AIProcessor
from rich.console import Console

console = Console()

# Initialize AI processor with Claude
processor = AIProcessor(
    api_key="your-anthropic-api-key",
    model="claude-3-opus-20240229",
    provider="claude",
    console=console
)

# Process text
success, result = processor.process_text(
    text="Summarize the following text: ...",
    output_path="/path/to/output.md"
)

if success:
    print(f"Text processed successfully: {result}")
else:
    print(f"Failed to process text: {result}")
```

### Using ChatGPT

```python
# Initialize AI processor with ChatGPT
processor = AIProcessor(
    api_key="your-openai-api-key",
    model="gpt-4",
    provider="chatgpt",
    console=console
)

# Process text
success, result = processor.process_text(
    text="Explain the following concept: ...",
    output_path="/path/to/output.md"
)

if success:
    print(f"Text processed successfully: {result}")
else:
    print(f"Failed to process text: {result}")
```

### Using Templates

```python
# Load a template
success, template = processor.load_template("/path/to/template.txt")

if success:
    # Replace variables in template
    variables = {
        "course_name": "Python Programming",
        "module_name": "Data Structures",
        "content": "..."
    }
    
    prompt = processor.replace_template_variables(template, variables)
    
    # Process with template
    success, result = processor.process_text(
        text=prompt,
        output_path="/path/to/output.md"
    )
    
    if success:
        print(f"Text processed successfully with template: {result}")
    else:
        print(f"Failed to process text: {result}")
else:
    print(f"Failed to load template: {template}")
```

### Batch Processing

```python
# Process multiple text files
text_files = [
    "/path/to/text1.txt",
    "/path/to/text2.txt",
    "/path/to/text3.txt"
]

output_dir = "/path/to/output_directory"

success, results = processor.batch_process(
    text_files=text_files,
    output_dir=output_dir,
    template_path="/path/to/template.txt",
    variables={
        "course_name": "Python Programming"
    }
)

if success:
    print(f"Batch processing completed successfully")
    for text_file, output_file in results.items():
        print(f"{text_file} -> {output_file}")
else:
    print(f"Failed to process batch: {results}")
```

### Conversation Management

```python
# Process text with conversation management
text = """
This is the first part of a long text that needs to be processed.
...
[CONTINUA]
"""

success, result = processor.process_text(
    text=text,
    output_path="/path/to/output.md",
    manage_conversation=True
)

if success:
    print(f"First part processed successfully: {result}")
    
    # Continue the conversation
    text = """
    This is the second part of the text.
    ...
    [CONTINUA]
    """
    
    success, result = processor.continue_conversation(
        text=text,
        output_path="/path/to/output_part2.md"
    )
    
    if success:
        print(f"Second part processed successfully: {result}")
    else:
        print(f"Failed to process second part: {result}")
else:
    print(f"Failed to process first part: {result}")
```

## Class Reference

### AIProcessor

The main class for processing text with AI models.

#### Methods

- `process_text`: Process text with AI
- `batch_process`: Process multiple text files
- `load_template`: Load a template from a file
- `replace_template_variables`: Replace variables in a template
- `estimate_tokens`: Estimate the number of tokens in a text
- `calculate_cost`: Calculate the cost of processing a text
- `continue_conversation`: Continue a conversation
- `set_api_key`: Set the API key
- `set_model`: Set the AI model
- `set_provider`: Set the AI provider (claude or chatgpt)

## Dependencies

- anthropic
- openai
- rich (for console output)
- tiktoken (for token estimation)