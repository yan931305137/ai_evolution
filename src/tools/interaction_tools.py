
import logging
from typing import List, Optional

def ask_user(question: str, options: Optional[List[str]] = None) -> str:
    """
    Ask the user a question and get their input.
    Useful when the agent needs clarification, confirmation, or preferences.
    
    Args:
        question: The question to ask the user.
        options: Optional list of valid choices.
        
    Returns:
        The user's response string.
    """
    print(f"\n[Agent Question] {question}")
    
    if options:
        print(f"Options: {', '.join(options)}")
        
    # In a real interactive environment, this would block for input.
    # Since this runs in a headless agent environment often, we simulate 
    # or rely on the orchestrator to handle the input loop.
    # For now, we use standard input.
    try:
        response = input("> ")
        return response.strip()
    except EOFError:
        logging.warning("No user input available (EOF).")
        return ""
