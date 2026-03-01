
import logging
from typing import List, Dict, Any, Optional
from src.storage.memory import memory

def remember_insight(content: str, tags: List[str], importance: int = 3) -> str:
    """
    Save a valuable insight, rule, or fact to long-term memory.
    
    Args:
        content: The knowledge to save.
        tags: Keywords to help categorization (e.g., ['python', 'error-handling']).
        importance: 1-5 scale (5 is critical).
        
    Returns:
        Success message.
    """
    metadata = {
        "type": "fact",
        "tags": tags,
        "importance": importance,
        "source": "agent_tool"
    }
    
    success = memory.add_knowledge(content, metadata)
    if success:
        return f"Successfully saved insight to memory: {content[:50]}..."
    return "Failed to save insight."

def recall_knowledge(query: str, n_results: int = 5) -> str:
    """
    Search long-term memory for relevant knowledge.
    
    Args:
        query: The search query.
        n_results: Number of results to return.
        
    Returns:
        Formatted string of retrieved memories.
    """
    memories = memory.retrieve(query, n_results=n_results, collection_name="knowledge")
    
    if not memories:
        return "No relevant memories found."
        
    return "\n---\n".join([f"- {m}" for m in memories])
