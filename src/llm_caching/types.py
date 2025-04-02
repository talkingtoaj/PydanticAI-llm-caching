"""Type definitions for the llm-caching package."""

from typing import Any, Protocol, Dict
from pydantic_ai.messages import ModelMessage, TextPart

class MessageConverter(Protocol):
    """Protocol for message conversion functions."""
    def __call__(self, messages: list[Any]) -> list[ModelMessage]: ...

class ExpenseRecorder(Protocol):
    """Protocol for expense recording functions."""
    async def __call__(self, model: str, task_name: str, cost: float) -> None: ...

async def noop_expense_recorder(model: str, task_name: str, cost: float) -> None:
    """Default do-nothing expense recorder."""
    pass

def default_message_converter(messages: list[Any]) -> list[ModelMessage]:
    """Convert messages to ModelMessage format.
    
    Args:
        messages: List of messages to convert. Each message can be:
            - A dict with 'role' and 'content' keys
            - A ModelMessage object
            - A string (treated as user message)
            
    Returns:
        List of ModelMessage objects
        
    Raises:
        ValueError: If a message is in an unrecognized format.
    """
    if not messages:
        return []
        
    converted = []
    for i, msg in enumerate(messages):
        # Check for dict and str first
        if isinstance(msg, dict):
            role = msg.get('role')
            content = msg.get('content')
            if role and isinstance(role, str) and content and isinstance(content, str):
                converted.append(ModelMessage(
                    role=role,
                    parts=[TextPart(content=content)]
                ))
            else:
                # Raise error for invalid dictionary format
                raise ValueError(f"Invalid message format at index {i}: Dictionary must have string 'role' and 'content'. Got: {msg}")
        elif isinstance(msg, str):
            converted.append(ModelMessage(
                role='user',
                parts=[TextPart(content=msg)]
            ))
        # If not dict or str, try passing it through. 
        # Assume it might be a valid ModelMessage or similar object.
        # This avoids the problematic isinstance(msg, ModelMessage) which causes TypeError.
        # Let pydantic-ai handle potential downstream errors if the object is truly invalid.
        elif msg is not None: 
             converted.append(msg) # Pass it through
        else:
             # Only raise error for None or other completely unexpected scenarios
             raise ValueError(f"Invalid message format at index {i}: Unexpected None value.")
            
    return converted 