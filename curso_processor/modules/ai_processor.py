"""
AI Processor module for Curso Processor
Supports both Claude (Anthropic) and ChatGPT (OpenAI) for processing transcriptions
"""

import os
import re
import time
import json
import yaml
import logging
import datetime
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from utils import file_manager, ui_components
from config import settings, credentials

# Configure logging
logger = logging.getLogger("ai_processor")

# Constants
CLAUDE_MODELS = {
    "claude-3-5-sonnet-20241022": {
        "name": "Claude 3.5 Sonnet",
        "context_window": 200000,
        "input_cost_per_1m_tokens": 3.00,
        "output_cost_per_1m_tokens": 15.00
    },
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "context_window": 200000,
        "input_cost_per_1m_tokens": 15.00,
        "output_cost_per_1m_tokens": 75.00
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet",
        "context_window": 200000,
        "input_cost_per_1m_tokens": 3.00,
        "output_cost_per_1m_tokens": 15.00
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "context_window": 200000,
        "input_cost_per_1m_tokens": 0.25,
        "output_cost_per_1m_tokens": 1.25
    }
}

OPENAI_MODELS = {
    "gpt-4-turbo-preview": {
        "name": "GPT-4 Turbo",
        "context_window": 128000,
        "input_cost_per_1m_tokens": 10.00,
        "output_cost_per_1m_tokens": 30.00
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "context_window": 128000,
        "input_cost_per_1m_tokens": 5.00,
        "output_cost_per_1m_tokens": 15.00
    },
    "gpt-4": {
        "name": "GPT-4",
        "context_window": 8192,
        "input_cost_per_1m_tokens": 30.00,
        "output_cost_per_1m_tokens": 60.00
    },
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "context_window": 16385,
        "input_cost_per_1m_tokens": 0.50,
        "output_cost_per_1m_tokens": 1.50
    }
}

DEFAULT_CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_OPENAI_MODEL = "gpt-4-turbo-preview"

# Control tokens for conversation management
CONTINUE_TOKEN = "[CONTINUA]"
CONTINUE_COMMAND = "[CONTINUAR]"
END_TOKEN = "[FIM]"

class AIProcessor:
    """Class for processing transcriptions using AI models"""
    
    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        claude_model: str = DEFAULT_CLAUDE_MODEL,
        openai_model: str = DEFAULT_OPENAI_MODEL,
        temperature: float = 0.7,
        console: Optional[Console] = None
    ):
        """
        Initialize AIProcessor
        
        Args:
            claude_api_key: Anthropic API key (if None, will try to get from credentials)
            openai_api_key: OpenAI API key (if None, will try to get from credentials)
            claude_model: Claude model to use
            openai_model: OpenAI model to use
            temperature: Sampling temperature (0.0 to 1.0)
            console: Rich console for output
        """
        self.claude_api_key = claude_api_key or credentials.get_anthropic_api_key()
        self.openai_api_key = openai_api_key or credentials.get_openai_api_key()
        self.claude_model = claude_model
        self.openai_model = openai_model
        self.temperature = temperature
        self.console = console or Console()
        
        # Initialize clients if API keys are available
        self.claude_client = None
        if self.claude_api_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
            except ImportError:
                logger.warning("Anthropic package not installed. Claude processing will not be available.")
        
        self.openai_client = None
        if self.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. ChatGPT processing will not be available.")
        
        # Prompts directory
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Cache for processed content
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / "processed"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup directory
        self.backup_dir = Path(__file__).parent.parent / "data" / "backups" / "processed"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def process_with_claude(
        self,
        transcription: str,
        prompt_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process transcription using Claude
        
        Args:
            transcription: Transcription text to process
            prompt_path: Path to prompt file (if None, will use default prompt)
            output_path: Path to save processed content
            metadata: Additional metadata for template variables
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and processed content
        """
        if not self.claude_api_key or not self.claude_client:
            error_message = "Claude API key not available"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description="Loading prompt...")
        
        # Load prompt
        prompt_text, prompt_file = self.load_custom_prompt(prompt_path)
        if not prompt_text:
            error_message = f"Failed to load prompt from {prompt_path}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Apply template variables
        prompt_text = self.apply_template_variables(prompt_text, transcription, metadata)
        
        # Validate prompt size
        if not self.validate_prompt_size(prompt_text, "claude"):
            error_message = f"Prompt size exceeds Claude model context window"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description="Processing with Claude...")
        
        # Process with Claude
        try:
            # Estimate tokens and cost
            input_tokens = self.estimate_tokens(prompt_text, "claude")
            
            # Start time for tracking
            start_time = time.time()
            
            # Process with Claude using conversation management
            processed_content = self.manage_conversation(
                prompt_text, 
                provider="claude",
                progress=progress,
                task_id=task_id
            )
            
            # End time for tracking
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Estimate output tokens and cost
            output_tokens = self.estimate_tokens(processed_content, "claude")
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = self.calculate_cost(input_tokens, output_tokens, "claude")
            
            # Create result
            result = {
                "content": processed_content,
                "model": self.claude_model,
                "prompt_file": prompt_file,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
                "processing_time": processing_time,
                "processed_at": datetime.datetime.now().isoformat()
            }
            
            # Save processed content if output_path is provided
            if output_path:
                self.save_processed_content(result, output_path, metadata)
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
            
            return True, result
        
        except Exception as e:
            error_message = f"Error processing with Claude: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    def process_with_chatgpt(
        self,
        transcription: str,
        prompt_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process transcription using ChatGPT
        
        Args:
            transcription: Transcription text to process
            prompt_path: Path to prompt file (if None, will use default prompt)
            output_path: Path to save processed content
            metadata: Additional metadata for template variables
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and processed content
        """
        if not self.openai_api_key or not self.openai_client:
            error_message = "OpenAI API key not available"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description="Loading prompt...")
        
        # Load prompt
        prompt_text, prompt_file = self.load_custom_prompt(prompt_path)
        if not prompt_text:
            error_message = f"Failed to load prompt from {prompt_path}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Apply template variables
        prompt_text = self.apply_template_variables(prompt_text, transcription, metadata)
        
        # Validate prompt size
        if not self.validate_prompt_size(prompt_text, "openai"):
            error_message = f"Prompt size exceeds OpenAI model context window"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description="Processing with ChatGPT...")
        
        # Process with ChatGPT
        try:
            # Estimate tokens and cost
            input_tokens = self.estimate_tokens(prompt_text, "openai")
            
            # Start time for tracking
            start_time = time.time()
            
            # Process with ChatGPT using conversation management
            processed_content = self.manage_conversation(
                prompt_text, 
                provider="openai",
                progress=progress,
                task_id=task_id
            )
            
            # End time for tracking
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Estimate output tokens and cost
            output_tokens = self.estimate_tokens(processed_content, "openai")
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = self.calculate_cost(input_tokens, output_tokens, "openai")
            
            # Create result
            result = {
                "content": processed_content,
                "model": self.openai_model,
                "prompt_file": prompt_file,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
                "processing_time": processing_time,
                "processed_at": datetime.datetime.now().isoformat()
            }
            
            # Save processed content if output_path is provided
            if output_path:
                self.save_processed_content(result, output_path, metadata)
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
            
            return True, result
        
        except Exception as e:
            error_message = f"Error processing with ChatGPT: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    def batch_process_transcriptions(
        self,
        transcription_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        provider: str = "claude",
        prompt_path: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        create_summary: bool = True,
        console: Optional[Console] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process multiple transcriptions
        
        Args:
            transcription_paths: List of transcription file paths
            output_dir: Directory to save processed content
            provider: AI provider ("claude" or "openai")
            prompt_path: Path to prompt file (if None, will use default prompt)
            metadata: Additional metadata for template variables
            create_summary: Whether to create a summary of all processed content
            console: Rich console for output
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and results
        """
        # Convert paths to Path objects
        transcription_paths = [Path(p) for p in transcription_paths]
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided console or instance console
        console = console or self.console
        
        # Create progress bar
        progress = ui_components.create_progress_bar("Processando transcrições")
        
        results = {
            "success": True,
            "processed": [],
            "failed": [],
            "total": len(transcription_paths),
            "provider": provider,
            "total_tokens": 0,
            "total_cost": 0.0
        }
        
        with progress:
            # Add task
            task = progress.add_task("Iniciando processamento...", total=len(transcription_paths))
            
            # Process each transcription
            for transcription_path in transcription_paths:
                # Update progress
                progress.update(task, description=f"Processando {transcription_path.name}")
                
                try:
                    # Read transcription
                    with open(transcription_path, "r", encoding="utf-8") as f:
                        transcription = f.read()
                    
                    # Extract metadata from transcription file
                    file_metadata = self._extract_metadata_from_file(transcription_path)
                    
                    # Merge with provided metadata
                    if metadata:
                        file_metadata.update(metadata)
                    
                    # Set output path
                    output_path = output_dir / f"{transcription_path.stem}_processed.md"
                    
                    # Process transcription
                    if provider == "claude":
                        success, result = self.process_with_claude(
                            transcription=transcription,
                            prompt_path=prompt_path,
                            output_path=output_path,
                            metadata=file_metadata,
                            progress=progress,
                            task_id=task
                        )
                    elif provider == "openai":
                        success, result = self.process_with_chatgpt(
                            transcription=transcription,
                            prompt_path=prompt_path,
                            output_path=output_path,
                            metadata=file_metadata,
                            progress=progress,
                            task_id=task
                        )
                    else:
                        error_message = f"Invalid provider: {provider}"
                        logger.error(error_message)
                        return False, {"error": error_message}
                    
                    # Store result
                    if success:
                        results["processed"].append({
                            "transcription_path": str(transcription_path),
                            "output_path": str(output_path),
                            "tokens": result.get("total_tokens", 0),
                            "cost": result.get("cost_usd", 0.0)
                        })
                        
                        # Update totals
                        results["total_tokens"] += result.get("total_tokens", 0)
                        results["total_cost"] += result.get("cost_usd", 0.0)
                    else:
                        results["failed"].append({
                            "transcription_path": str(transcription_path),
                            "error": result.get("error", "Unknown error")
                        })
                        results["success"] = False
                
                except Exception as e:
                    error_message = f"Error processing {transcription_path}: {str(e)}"
                    logger.error(error_message)
                    
                    results["failed"].append({
                        "transcription_path": str(transcription_path),
                        "error": error_message
                    })
                    results["success"] = False
        
        # Create summary if requested
        if create_summary and results["processed"]:
            try:
                # Create summary file
                summary_path = output_dir / "Resumo_Completo.md"
                
                # Create summary content
                summary_content = self._create_summary(
                    [Path(item["output_path"]) for item in results["processed"]],
                    provider=provider
                )
                
                # Save summary
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary_content)
                
                results["summary_path"] = str(summary_path)
                
                console.print(f"[green]Resumo completo criado: {summary_path}[/green]")
            
            except Exception as e:
                error_message = f"Error creating summary: {str(e)}"
                logger.error(error_message)
                results["summary_error"] = error_message
        
        # Print summary
        successful = len(results["processed"])
        console.print(f"[green]Processamento concluído: {successful}/{len(transcription_paths)} arquivos processados com sucesso[/green]")
        console.print(f"[cyan]Total de tokens: {results['total_tokens']}[/cyan]")
        console.print(f"[cyan]Custo total: ${results['total_cost']:.2f} USD[/cyan]")
        
        if results["failed"]:
            console.print(f"[red]Falhas: {len(results['failed'])} arquivos[/red]")
            
            # Print failed files
            for item in results["failed"]:
                console.print(f"[red]  {Path(item['transcription_path']).name}: {item['error']}[/red]")
        
        return results["success"], results
    
    def manage_conversation(
        self,
        prompt: str,
        provider: str = "claude",
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> str:
        """
        Manage conversation with AI model
        
        Args:
            prompt: Initial prompt
            provider: AI provider ("claude" or "openai")
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            str: Full processed content
        """
        full_response = ""
        message = prompt
        conversation_turn = 1
        
        # Retry parameters
        max_retries = 5
        retry_delay = 1  # Initial delay in seconds
        
        while True:
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description=f"Processando (turno {conversation_turn})...")
            
            # Send message to AI with retry logic
            for attempt in range(max_retries):
                try:
                    if provider == "claude":
                        response = self._send_to_claude(message, conversation_turn > 1)
                    elif provider == "openai":
                        response = self._send_to_openai(message, conversation_turn > 1)
                    else:
                        raise ValueError(f"Invalid provider: {provider}")
                    
                    # Break retry loop if successful
                    break
                
                except Exception as e:
                    logger.warning(f"API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                    
                    # Update progress if provided
                    if progress and task_id is not None:
                        progress.update(task_id, description=f"API error, retrying... ({attempt+1}/{max_retries})")
                    
                    # Exponential backoff with jitter
                    sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep_time)
                    
                    # If this is the last attempt, re-raise the exception
                    if attempt == max_retries - 1:
                        raise
            
            # Check for end or continue tokens
            if END_TOKEN in response:
                # Remove end token and add to full response
                full_response += response.replace(END_TOKEN, "")
                break
            elif CONTINUE_TOKEN in response:
                # Remove continue token and add to full response
                full_response += response.replace(CONTINUE_TOKEN, "")
                # Set next message to continue command
                message = CONTINUE_COMMAND
                conversation_turn += 1
            else:
                # No control tokens, add response and break
                full_response += response
                break
        
        # Clean response
        cleaned_response = self.clean_ai_response(full_response)
        
        # Format for Obsidian
        formatted_response = self.format_for_obsidian(cleaned_response)
        
        return formatted_response
    
    def _send_to_claude(self, message: str, is_continuation: bool = False) -> str:
        """
        Send message to Claude
        
        Args:
            message: Message to send
            is_continuation: Whether this is a continuation of a previous message
            
        Returns:
            str: Claude's response
        """
        if not self.claude_client:
            raise ValueError("Claude client not initialized")
        
        # For continuation messages, use a simpler system prompt
        system_prompt = "You are a helpful AI assistant that processes course transcriptions."
        if is_continuation:
            system_prompt = "Continue from where you left off."
        
        # Send message to Claude
        response = self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=4000,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        
        # Extract response text
        return response.content[0].text
    
    def _send_to_openai(self, message: str, is_continuation: bool = False) -> str:
        """
        Send message to OpenAI
        
        Args:
            message: Message to send
            is_continuation: Whether this is a continuation of a previous message
            
        Returns:
            str: OpenAI's response
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        # For continuation messages, use a simpler system prompt
        system_prompt = "You are a helpful AI assistant that processes course transcriptions."
        if is_continuation:
            system_prompt = "Continue from where you left off."
        
        # Send message to OpenAI
        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        
        # Extract response text
        return response.choices[0].message.content
    
    def load_custom_prompt(
        self,
        prompt_path: Optional[Union[str, Path]] = None
    ) -> Tuple[str, str]:
        """
        Load custom prompt from file
        
        Args:
            prompt_path: Path to prompt file (if None, will use default prompt)
            
        Returns:
            Tuple[str, str]: Prompt text and prompt file name
        """
        # If no prompt path provided, use default prompt
        if not prompt_path:
            default_prompt_path = self.prompts_dir / "default_prompt.txt"
            prompt_path = default_prompt_path
        else:
            prompt_path = Path(prompt_path)
            
            # If prompt path is just a filename, look in prompts directory
            if not prompt_path.is_absolute():
                prompt_path = self.prompts_dir / prompt_path
        
        # Check if prompt file exists
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            return "", ""
        
        # Read prompt file
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
            
            return prompt_text, prompt_path.name
        
        except Exception as e:
            logger.error(f"Error reading prompt file: {str(e)}")
            return "", ""
    
    def apply_template_variables(
        self,
        prompt_text: str,
        transcription: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Apply template variables to prompt
        
        Args:
            prompt_text: Prompt text with template variables
            transcription: Transcription text
            metadata: Additional metadata for template variables
            
        Returns:
            str: Prompt text with variables replaced
        """
        # Create variables dictionary
        variables = {
            "TRANSCRIPTION": transcription,
            "COURSE_NAME": "Curso",
            "FILE_NAME": "transcription.txt",
            "DURATION": "00:00:00"
        }
        
        # Update with metadata if provided
        if metadata:
            for key, value in metadata.items():
                variables[key.upper()] = value
        
        # Replace variables in prompt
        for key, value in variables.items():
            prompt_text = prompt_text.replace(f"{{{{{key}}}}}", str(value))
        
        return prompt_text
    
    def validate_prompt_size(self, prompt_text: str, provider: str) -> bool:
        """
        Validate prompt size against model context window
        
        Args:
            prompt_text: Prompt text
            provider: AI provider ("claude" or "openai")
            
        Returns:
            bool: True if prompt size is valid, False otherwise
        """
        # Estimate tokens
        tokens = self.estimate_tokens(prompt_text, provider)
        
        # Get context window size
        if provider == "claude":
            context_window = CLAUDE_MODELS.get(self.claude_model, {}).get("context_window", 100000)
        elif provider == "openai":
            context_window = OPENAI_MODELS.get(self.openai_model, {}).get("context_window", 8192)
        else:
            raise ValueError(f"Invalid provider: {provider}")
        
        # Check if tokens exceed context window
        # Leave room for response (about 25% of context window)
        max_input_tokens = int(context_window * 0.75)
        
        return tokens <= max_input_tokens
    
    def estimate_tokens(self, text: str, provider: str) -> int:
        """
        Estimate number of tokens in text
        
        Args:
            text: Text to estimate tokens for
            provider: AI provider ("claude" or "openai")
            
        Returns:
            int: Estimated number of tokens
        """
        # Simple estimation based on words and characters
        # This is a rough estimate, actual token count may vary
        
        # Count words and characters
        words = len(text.split())
        chars = len(text)
        
        # Estimate tokens based on provider
        if provider == "claude":
            # Claude uses about 5 characters per token on average
            return int(chars / 5)
        elif provider == "openai":
            # GPT models use about 4 characters per token on average
            return int(chars / 4)
        else:
            raise ValueError(f"Invalid provider: {provider}")
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: str
    ) -> float:
        """
        Calculate cost of API usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: AI provider ("claude" or "openai")
            
        Returns:
            float: Estimated cost in USD
        """
        if provider == "claude":
            model_info = CLAUDE_MODELS.get(self.claude_model, {})
            input_cost_per_token = model_info.get("input_cost_per_1m_tokens", 0) / 1000000
            output_cost_per_token = model_info.get("output_cost_per_1m_tokens", 0) / 1000000
        elif provider == "openai":
            model_info = OPENAI_MODELS.get(self.openai_model, {})
            input_cost_per_token = model_info.get("input_cost_per_1m_tokens", 0) / 1000000
            output_cost_per_token = model_info.get("output_cost_per_1m_tokens", 0) / 1000000
        else:
            raise ValueError(f"Invalid provider: {provider}")
        
        # Calculate cost
        input_cost = input_tokens * input_cost_per_token
        output_cost = output_tokens * output_cost_per_token
        total_cost = input_cost + output_cost
        
        return round(total_cost, 4)
    
    def clean_ai_response(self, response: str) -> str:
        """
        Clean AI response by removing control tokens and other artifacts
        
        Args:
            response: AI response
            
        Returns:
            str: Cleaned response
        """
        # Remove control tokens
        response = response.replace(CONTINUE_TOKEN, "")
        response = response.replace(CONTINUE_COMMAND, "")
        response = response.replace(END_TOKEN, "")
        
        # Remove any markdown code block markers for the entire content
        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        return response
    
    def format_for_obsidian(self, content: str) -> str:
        """
        Format content for Obsidian/Markdown
        
        Args:
            content: Content to format
            
        Returns:
            str: Formatted content
        """
        # Ensure proper heading levels
        # Replace any level 1 headings (# ) with level 2 headings (## )
        content = re.sub(r'^# (.+)$', r'## \1', content, flags=re.MULTILINE)
        
        # Ensure proper list formatting
        # Add empty line before lists if not already present
        content = re.sub(r'([^\n])\n([\*\-\+]|\d+\.) ', r'\1\n\n\2 ', content)
        
        # Ensure proper code block formatting
        # Add empty line before and after code blocks if not already present
        content = re.sub(r'([^\n])\n```', r'\1\n\n```', content)
        content = re.sub(r'```\n([^\n])', r'```\n\n\1', content)
        
        # Ensure proper blockquote formatting
        # Add empty line before blockquotes if not already present
        content = re.sub(r'([^\n])\n> ', r'\1\n\n> ', content)
        
        return content
    
    def save_processed_content(
        self,
        result: Dict[str, Any],
        output_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save processed content to file
        
        Args:
            result: Processing result
            output_path: Path to save processed content
            metadata: Additional metadata for YAML header
            
        Returns:
            Path: Path to saved file
        """
        # Convert output_path to Path object
        output_path = Path(output_path)
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create YAML header
        yaml_header = {
            "processed": True,
            "ai_model": result.get("model", "unknown"),
            "prompt_used": result.get("prompt_file", "unknown"),
            "tokens_used": result.get("total_tokens", 0),
            "cost_usd": result.get("cost_usd", 0),
            "processing_date": result.get("processed_at", datetime.datetime.now().isoformat()),
            "version": "v1"
        }
        
        # Update with metadata if provided
        if metadata:
            yaml_header.update(metadata)
        
        # Get content
        content = result.get("content", "")
        
        # Create backup if file exists
        if output_path.exists():
            self._create_backup(output_path)
        
        # Write file with YAML header
        file_manager.write_yaml_header(output_path, yaml_header, content)
        
        return output_path
    
    def _create_backup(self, file_path: Path) -> Path:
        """
        Create backup of file
        
        Args:
            file_path: Path to file
            
        Returns:
            Path: Path to backup file
        """
        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup filename
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_filename
        
        # Copy file to backup
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return file_path
    
    def _extract_metadata_from_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict[str, Any]: Metadata
        """
        metadata = {
            "FILE_NAME": file_path.name,
            "COURSE_NAME": file_path.parent.name
        }
        
        # Try to extract YAML header
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check if file has YAML header
            if content.startswith("---"):
                # Extract YAML header
                yaml_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
                if yaml_match:
                    yaml_text = yaml_match.group(1)
                    yaml_data = yaml.safe_load(yaml_text)
                    
                    # Add relevant metadata
                    if "duration" in yaml_data:
                        metadata["DURATION"] = yaml_data["duration"]
                    if "source_file" in yaml_data:
                        metadata["SOURCE_FILE"] = yaml_data["source_file"]
                    if "language" in yaml_data:
                        metadata["LANGUAGE"] = yaml_data["language"]
        
        except Exception as e:
            logger.warning(f"Error extracting metadata from file: {str(e)}")
        
        return metadata
    
    def _create_summary(
        self,
        processed_files: List[Path],
        provider: str = "claude"
    ) -> str:
        """
        Create summary of all processed content
        
        Args:
            processed_files: List of processed file paths
            provider: AI provider used for processing
            
        Returns:
            str: Summary content
        """
        # Sort files by name
        processed_files.sort()
        
        # Initialize summary content
        summary_content = ""
        
        # Create YAML header
        yaml_header = {
            "processed": True,
            "summary_type": "concatenation",
            "files_included": len(processed_files),
            "created_at": datetime.datetime.now().isoformat(),
            "version": "v1"
        }
        
        # Add provider-specific info
        if provider == "claude":
            yaml_header["ai_model"] = self.claude_model
        elif provider == "openai":
            yaml_header["ai_model"] = self.openai_model
        
        # Create summary content
        summary_text = "# Resumo Completo do Curso\n\n"
        
        # Add each processed file
        for file_path in processed_files:
            try:
                # Read file
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extract content without YAML header
                if content.startswith("---"):
                    yaml_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
                    if yaml_match:
                        content = content[yaml_match.end():]
                
                # Add file name as heading
                summary_text += f"## {file_path.stem}\n\n"
                
                # Add content
                summary_text += content.strip() + "\n\n"
                summary_text += "---\n\n"  # Add separator
            
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
                summary_text += f"## {file_path.stem}\n\n"
                summary_text += f"*Error reading file: {str(e)}*\n\n"
                summary_text += "---\n\n"  # Add separator
        
        # Write file with YAML header
        summary_content = file_manager.format_yaml_header(yaml_header) + "\n" + summary_text
        
        return summary_content


def process_transcription(
    transcription_path: Union[str, Path],
    output_path: Union[str, Path],
    provider: str = "claude",
    model: Optional[str] = None,
    prompt_path: Optional[Union[str, Path]] = None,
    temperature: float = 0.7,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Process a single transcription
    
    Args:
        transcription_path: Path to transcription file
        output_path: Path to save processed content
        provider: AI provider ("claude" or "openai")
        model: Model to use (if None, will use default model)
        prompt_path: Path to prompt file (if None, will use default prompt)
        temperature: Sampling temperature (0.0 to 1.0)
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and processing result
    """
    # Convert paths to Path objects
    transcription_path = Path(transcription_path)
    output_path = Path(output_path)
    
    # Read transcription
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription = f.read()
    except Exception as e:
        error_message = f"Error reading transcription file: {str(e)}"
        logger.error(error_message)
        return False, {"error": error_message}
    
    # Extract metadata from transcription file
    metadata = {
        "FILE_NAME": transcription_path.name,
        "COURSE_NAME": transcription_path.parent.name
    }
    
    # Initialize processor
    processor = AIProcessor(
        claude_model=model if provider == "claude" else DEFAULT_CLAUDE_MODEL,
        openai_model=model if provider == "openai" else DEFAULT_OPENAI_MODEL,
        temperature=temperature,
        console=console
    )
    
    # Process transcription
    if provider == "claude":
        return processor.process_with_claude(
            transcription=transcription,
            prompt_path=prompt_path,
            output_path=output_path,
            metadata=metadata
        )
    elif provider == "openai":
        return processor.process_with_chatgpt(
            transcription=transcription,
            prompt_path=prompt_path,
            output_path=output_path,
            metadata=metadata
        )
    else:
        error_message = f"Invalid provider: {provider}"
        logger.error(error_message)
        return False, {"error": error_message}


def batch_process_transcriptions(
    transcription_dir: Union[str, Path],
    output_dir: Union[str, Path],
    provider: str = "claude",
    model: Optional[str] = None,
    prompt_path: Optional[Union[str, Path]] = None,
    temperature: float = 0.7,
    create_summary: bool = True,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Process all transcriptions in a directory
    
    Args:
        transcription_dir: Directory containing transcription files
        output_dir: Directory to save processed content
        provider: AI provider ("claude" or "openai")
        model: Model to use (if None, will use default model)
        prompt_path: Path to prompt file (if None, will use default prompt)
        temperature: Sampling temperature (0.0 to 1.0)
        create_summary: Whether to create a summary of all processed content
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and processing results
    """
    # Convert paths to Path objects
    transcription_dir = Path(transcription_dir)
    output_dir = Path(output_dir)
    
    # Find all transcription files
    transcription_files = list(transcription_dir.glob("**/*.txt"))
    
    # Initialize processor
    processor = AIProcessor(
        claude_model=model if provider == "claude" else DEFAULT_CLAUDE_MODEL,
        openai_model=model if provider == "openai" else DEFAULT_OPENAI_MODEL,
        temperature=temperature,
        console=console
    )
    
    # Process transcriptions
    return processor.batch_process_transcriptions(
        transcription_paths=transcription_files,
        output_dir=output_dir,
        provider=provider,
        prompt_path=prompt_path,
        create_summary=create_summary
    )


def estimate_processing_cost(
    transcription_paths: List[Union[str, Path]],
    provider: str = "claude",
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Estimate cost of processing transcriptions
    
    Args:
        transcription_paths: List of transcription file paths
        provider: AI provider ("claude" or "openai")
        model: Model to use (if None, will use default model)
        
    Returns:
        Dict[str, Any]: Cost estimate
    """
    # Convert paths to Path objects
    transcription_paths = [Path(p) for p in transcription_paths]
    
    # Initialize processor
    processor = AIProcessor(
        claude_model=model if provider == "claude" else DEFAULT_CLAUDE_MODEL,
        openai_model=model if provider == "openai" else DEFAULT_OPENAI_MODEL
    )
    
    # Calculate total input tokens
    total_input_tokens = 0
    for path in transcription_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Estimate tokens
            tokens = processor.estimate_tokens(content, provider)
            total_input_tokens += tokens
        
        except Exception as e:
            logger.warning(f"Error estimating tokens for {path}: {str(e)}")
    
    # Estimate output tokens (typically about 50% of input for summaries)
    total_output_tokens = int(total_input_tokens * 0.5)
    
    # Calculate cost
    cost = processor.calculate_cost(total_input_tokens, total_output_tokens, provider)
    
    # Create result
    result = {
        "total_files": len(transcription_paths),
        "total_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "estimated_cost_usd": cost,
        "provider": provider
    }
    
    # Add model info
    if provider == "claude":
        result["model"] = model or DEFAULT_CLAUDE_MODEL
    elif provider == "openai":
        result["model"] = model or DEFAULT_OPENAI_MODEL
    
    return result