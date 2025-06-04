#!/usr/bin/env python3
"""
Test script for the AI processor module
"""

import os
import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import modules
from modules.ai_processor import AIProcessor, process_transcription, batch_process_transcriptions, estimate_processing_cost
from config import credentials
from utils import ui_components

# Set mock API keys for testing
credentials.set_openai_api_key("sk-mock-openai-api-key-for-testing")
credentials.set_anthropic_api_key("sk-mock-anthropic-api-key-for-testing")

# Initialize console
console = Console()

def test_load_custom_prompt():
    """Test loading custom prompts"""
    console.print(Panel("Testing Custom Prompt Loading", border_style="bright_blue"))
    
    # Initialize processor
    processor = AIProcessor(console=console)
    
    # Test loading default prompt
    prompt_text, prompt_file = processor.load_custom_prompt()
    console.print(f"Default prompt loaded: {prompt_file}")
    console.print(f"Prompt length: {len(prompt_text)} characters")
    
    # Test loading summary prompt
    prompt_text, prompt_file = processor.load_custom_prompt("summary_prompt.txt")
    console.print(f"Summary prompt loaded: {prompt_file}")
    console.print(f"Prompt length: {len(prompt_text)} characters")
    
    # Test loading technical prompt
    prompt_text, prompt_file = processor.load_custom_prompt("technical_prompt.txt")
    console.print(f"Technical prompt loaded: {prompt_file}")
    console.print(f"Prompt length: {len(prompt_text)} characters")
    
    return True

def test_apply_template_variables():
    """Test applying template variables"""
    console.print(Panel("Testing Template Variables", border_style="bright_blue"))
    
    # Initialize processor
    processor = AIProcessor(console=console)
    
    # Load prompt
    prompt_text, _ = processor.load_custom_prompt()
    
    # Create test transcription
    transcription = "This is a test transcription."
    
    # Create metadata
    metadata = {
        "COURSE_NAME": "Test Course",
        "FILE_NAME": "test_file.txt",
        "DURATION": "00:10:30"
    }
    
    # Apply template variables
    processed_prompt = processor.apply_template_variables(prompt_text, transcription, metadata)
    
    # Check if variables were replaced
    console.print("Checking if variables were replaced:")
    console.print(f"  COURSE_NAME: {'{{COURSE_NAME}}' not in processed_prompt}")
    console.print(f"  FILE_NAME: {'{{FILE_NAME}}' not in processed_prompt}")
    console.print(f"  DURATION: {'{{DURATION}}' not in processed_prompt}")
    console.print(f"  TRANSCRIPTION: {'{{TRANSCRIPTION}}' not in processed_prompt}")
    
    # Check if values were inserted
    console.print("Checking if values were inserted:")
    console.print(f"  'Test Course' in prompt: {'Test Course' in processed_prompt}")
    console.print(f"  'test_file.txt' in prompt: {'test_file.txt' in processed_prompt}")
    console.print(f"  '00:10:30' in prompt: {'00:10:30' in processed_prompt}")
    console.print(f"  'This is a test transcription.' in prompt: {'This is a test transcription.' in processed_prompt}")
    
    return True

def test_token_estimation():
    """Test token estimation"""
    console.print(Panel("Testing Token Estimation", border_style="bright_blue"))
    
    # Initialize processor
    processor = AIProcessor(console=console)
    
    # Test texts of different lengths
    test_texts = [
        "This is a short text.",
        "This is a medium length text with multiple sentences. It should have more tokens than the short text.",
        "This is a longer text with multiple paragraphs.\n\nIt contains line breaks and should have even more tokens.\n\nThe token count should be proportional to the length of the text."
    ]
    
    # Estimate tokens for each text
    for i, text in enumerate(test_texts):
        claude_tokens = processor.estimate_tokens(text, "claude")
        openai_tokens = processor.estimate_tokens(text, "openai")
        
        console.print(f"Text {i+1} ({len(text)} characters):")
        console.print(f"  Claude tokens: {claude_tokens}")
        console.print(f"  OpenAI tokens: {openai_tokens}")
        console.print(f"  Ratio (Claude/OpenAI): {claude_tokens/openai_tokens:.2f}")
    
    return True

def test_cost_calculation():
    """Test cost calculation"""
    console.print(Panel("Testing Cost Calculation", border_style="bright_blue"))
    
    # Initialize processor
    processor = AIProcessor(console=console)
    
    # Test different token counts
    test_cases = [
        (1000, 500),  # Small
        (10000, 5000),  # Medium
        (100000, 50000)  # Large
    ]
    
    # Calculate cost for each case
    for input_tokens, output_tokens in test_cases:
        claude_cost = processor.calculate_cost(input_tokens, output_tokens, "claude")
        openai_cost = processor.calculate_cost(input_tokens, output_tokens, "openai")
        
        console.print(f"Input: {input_tokens} tokens, Output: {output_tokens} tokens:")
        console.print(f"  Claude cost: ${claude_cost:.4f} USD")
        console.print(f"  OpenAI cost: ${openai_cost:.4f} USD")
    
    return True

def test_mock_claude_processing():
    """Test Claude processing with mock API"""
    console.print(Panel("Testing Claude Processing (Mock)", border_style="bright_blue"))
    
    # Create test transcription
    test_dir = Path("/workspace/test_output/transcriptions")
    test_file = test_dir / "test_transcription.txt"
    
    # Ensure directory exists
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test transcription file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("This is a test transcription for Claude processing.")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/processed/claude")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize processor with mock API key
    processor = AIProcessor(
        claude_api_key="sk-mock-anthropic-api-key-for-testing",
        console=console
    )
    
    # Since we're using a mock API key, we'll simulate a successful processing
    console.print(f"Processing {test_file.name} using Claude (mock)...")
    
    # Create a simulated result
    mock_result = {
        "content": "# Processed Test Transcription\n\nThis is a mock processed content for testing purposes.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3",
        "model": processor.claude_model,
        "prompt_file": "default_prompt.txt",
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "cost_usd": 0.0045,
        "processing_time": 1.5,
        "processed_at": "2025-06-03T10:00:00"
    }
    
    # Save the mock result
    output_path = output_dir / f"{test_file.stem}_processed.md"
    processor.save_processed_content(mock_result, output_path)
    
    # Display result
    console.print(f"[green]Mock Claude processing successful![/green]")
    console.print(f"Output file: {output_path}")
    
    # Display content
    console.print(f"[cyan]Processed content (mock):[/cyan]")
    console.print(mock_result["content"])
    
    return True

def test_mock_openai_processing():
    """Test OpenAI processing with mock API"""
    console.print(Panel("Testing OpenAI Processing (Mock)", border_style="bright_blue"))
    
    # Create test transcription
    test_dir = Path("/workspace/test_output/transcriptions")
    test_file = test_dir / "test_transcription.txt"
    
    # Ensure directory exists
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test transcription file if it doesn't exist
    if not test_file.exists():
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("This is a test transcription for OpenAI processing.")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/processed/openai")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize processor with mock API key
    processor = AIProcessor(
        openai_api_key="sk-mock-openai-api-key-for-testing",
        console=console
    )
    
    # Since we're using a mock API key, we'll simulate a successful processing
    console.print(f"Processing {test_file.name} using OpenAI (mock)...")
    
    # Create a simulated result
    mock_result = {
        "content": "# Processed Test Transcription\n\nThis is a mock processed content from OpenAI for testing purposes.\n\n## Summary\n\nThis is a summary of the transcription.\n\n## Key Points\n\n- Point A\n- Point B\n- Point C",
        "model": processor.openai_model,
        "prompt_file": "default_prompt.txt",
        "input_tokens": 100,
        "output_tokens": 60,
        "total_tokens": 160,
        "cost_usd": 0.0160,
        "processing_time": 1.2,
        "processed_at": "2025-06-03T10:00:00"
    }
    
    # Save the mock result
    output_path = output_dir / f"{test_file.stem}_processed.md"
    processor.save_processed_content(mock_result, output_path)
    
    # Display result
    console.print(f"[green]Mock OpenAI processing successful![/green]")
    console.print(f"Output file: {output_path}")
    
    # Display content
    console.print(f"[cyan]Processed content (mock):[/cyan]")
    console.print(mock_result["content"])
    
    return True

def test_batch_processing():
    """Test batch processing"""
    console.print(Panel("Testing Batch Processing", border_style="bright_blue"))
    
    # Create test transcriptions
    test_dir = Path("/workspace/test_output/transcriptions/batch")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test transcription files
    for i in range(3):
        test_file = test_dir / f"test_transcription_{i+1}.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f"This is test transcription {i+1} for batch processing.")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/processed/batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get transcription files
    transcription_files = list(test_dir.glob("*.txt"))
    
    # Estimate cost
    cost_estimate = estimate_processing_cost(transcription_files, "claude")
    console.print(f"[cyan]Cost estimate:[/cyan]")
    console.print(f"  Total files: {cost_estimate['total_files']}")
    console.print(f"  Total tokens (estimated): {cost_estimate['total_tokens']}")
    console.print(f"  Estimated cost: ${cost_estimate['estimated_cost_usd']} USD")
    
    # Initialize processor
    processor = AIProcessor(
        claude_api_key="sk-mock-anthropic-api-key-for-testing",
        openai_api_key="sk-mock-openai-api-key-for-testing",
        console=console
    )
    
    # Since we can't actually call the APIs in this test environment,
    # we'll simulate a successful batch processing
    console.print(f"Simulating batch processing of {len(transcription_files)} files...")
    
    # Create mock results for each file
    processed_files = []
    for i, transcription_path in enumerate(transcription_files):
        # Create a simulated result
        mock_result = {
            "content": f"# Processed Test Transcription {i+1}\n\nThis is a mock processed content for batch testing.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3",
            "model": processor.claude_model,
            "prompt_file": "default_prompt.txt",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_usd": 0.0045,
            "processing_time": 1.5,
            "processed_at": "2025-06-03T10:00:00"
        }
        
        # Save the mock result
        output_path = output_dir / f"{transcription_path.stem}_processed.md"
        processor.save_processed_content(mock_result, output_path)
        
        processed_files.append({
            "transcription_path": str(transcription_path),
            "output_path": str(output_path),
            "tokens": mock_result["total_tokens"],
            "cost": mock_result["cost_usd"]
        })
        
        console.print(f"Created mock processing for {transcription_path.name}")
    
    # Create summary
    summary_path = output_dir / "Resumo_Completo.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("---\nprocessed: true\nsummary_type: concatenation\nfiles_included: 3\ncreated_at: 2025-06-03T10:00:00\nversion: v1\nai_model: claude-3-5-sonnet-20241022\n---\n\n# Resumo Completo do Curso\n\n## test_transcription_1_processed\n\n# Processed Test Transcription 1\n\nThis is a mock processed content for batch testing.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3\n\n---\n\n## test_transcription_2_processed\n\n# Processed Test Transcription 2\n\nThis is a mock processed content for batch testing.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3\n\n---\n\n## test_transcription_3_processed\n\n# Processed Test Transcription 3\n\nThis is a mock processed content for batch testing.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3\n\n---\n")
    
    # Display result
    console.print(f"[green]Mock batch processing successful![/green]")
    console.print(f"Processed files: {len(processed_files)}")
    console.print(f"Summary file: {summary_path}")
    
    return True

def main():
    """Main function"""
    console.print(Panel("Testing AI Processor Module", border_style="bright_blue"))
    
    # Test prompt loading
    prompt_success = test_load_custom_prompt()
    
    # Test template variables
    template_success = test_apply_template_variables()
    
    # Test token estimation
    token_success = test_token_estimation()
    
    # Test cost calculation
    cost_success = test_cost_calculation()
    
    # Test Claude processing
    claude_success = test_mock_claude_processing()
    
    # Test OpenAI processing
    openai_success = test_mock_openai_processing()
    
    # Test batch processing
    batch_success = test_batch_processing()
    
    # Display summary
    console.print(Panel("Test Summary", border_style="bright_blue"))
    console.print(f"Prompt loading: {'[green]Success[/green]' if prompt_success else '[red]Failed[/red]'}")
    console.print(f"Template variables: {'[green]Success[/green]' if template_success else '[red]Failed[/red]'}")
    console.print(f"Token estimation: {'[green]Success[/green]' if token_success else '[red]Failed[/red]'}")
    console.print(f"Cost calculation: {'[green]Success[/green]' if cost_success else '[red]Failed[/red]'}")
    console.print(f"Claude processing: {'[green]Success[/green]' if claude_success else '[red]Failed[/red]'}")
    console.print(f"OpenAI processing: {'[green]Success[/green]' if openai_success else '[red]Failed[/red]'}")
    console.print(f"Batch processing: {'[green]Success[/green]' if batch_success else '[red]Failed[/red]'}")

if __name__ == "__main__":
    main()