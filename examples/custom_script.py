"""
Example custom script for Synda.

This script demonstrates how to create a custom processing function
that can be used in a Synda pipeline.
"""

import re
from typing import Dict, Any, Optional


def process_text(
    text: str,
    node_id: Optional[int] = None,
    parent_node_id: Optional[int] = None,
    min_length: int = 0,
    max_length: int = 1000,
    language: str = "english",
    **kwargs
) -> str:
    """
    Process text by cleaning, filtering, and transforming it.
    
    Args:
        text: The input text to process
        node_id: The ID of the current node (optional)
        parent_node_id: The ID of the parent node (optional)
        min_length: Minimum length of text to keep
        max_length: Maximum length of text to keep
        language: Language for processing
        **kwargs: Additional parameters
        
    Returns:
        The processed text
    """
    # Print some debug info
    print(f"Processing node {node_id} (parent: {parent_node_id})")
    print(f"Parameters: min_length={min_length}, max_length={max_length}, language={language}")
    
    # Clean the text
    processed_text = text.strip()
    
    # Remove extra whitespace
    processed_text = re.sub(r'\s+', ' ', processed_text)
    
    # Check length constraints
    if len(processed_text) < min_length:
        return f"[TOO SHORT] {processed_text}"
    
    if len(processed_text) > max_length:
        processed_text = processed_text[:max_length] + "..."
    
    # Add language tag if not English
    if language.lower() != "english":
        processed_text = f"[{language.upper()}] {processed_text}"
    
    return processed_text


async def process_text_async(
    text: str,
    node_id: Optional[int] = None,
    parent_node_id: Optional[int] = None,
    min_length: int = 0,
    max_length: int = 1000,
    language: str = "english",
    **kwargs
) -> str:
    """
    Asynchronous version of process_text.
    
    This function has the same behavior as process_text but can be used
    in async pipelines.
    """
    # For this example, we'll just call the synchronous function
    # In a real implementation, you might want to use async operations
    return process_text(
        text, 
        node_id, 
        parent_node_id, 
        min_length, 
        max_length, 
        language, 
        **kwargs
    )