"""Type definitions for the pyai-caching package."""

from typing import Any, Protocol, Dict, List
from pydantic_ai.messages import ModelMessage, TextPart, ModelRequest, UserPromptPart, ModelResponse, SystemPromptPart
import logging

log = logging.getLogger(__name__)

# Define a broader type hint for the message list
MessageType = Any # Could refine with Union[ModelRequest, ModelResponse, ...] if needed

class MessageConverter(Protocol):
    """Protocol for message conversion functions."""
    def __call__(self, messages: list[Any]) -> List[MessageType]: ... # Use broader return type

class ExpenseRecorder(Protocol):
    """Protocol for expense recording functions."""
    async def __call__(self, model: str, task_name: str, cost: float) -> None: ...

async def noop_expense_recorder(model: str, task_name: str, cost: float) -> None:
    """Default do-nothing expense recorder."""
    pass

def default_message_converter(messages: list[Any]) -> List[MessageType]: # Use broader return type
    """Convert messages to specific PydanticAI message types.
    
    Args:
        messages: List of messages to convert. Each message can be:
            - A dict with 'role' and 'content' keys
            - A ModelMessage object
            - A string (treated as user message)
            
    Returns:
        List of specific PydanticAI message types
        
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
                # Convert based on role
                if role == 'user':
                    converted.append(ModelRequest(
                        parts=[UserPromptPart(content=content)]
                    ))
                elif role == 'assistant': # Assuming 'assistant' role for ModelResponse
                    converted.append(ModelResponse(
                        parts=[TextPart(content=content)] 
                        # Note: ModelResponse usually includes model_name etc., 
                        # which we don't have here. This might be incomplete.
                    ))
                elif role == 'system':
                     converted.append(ModelRequest(
                        parts=[SystemPromptPart(content=content)]
                     ))
                else:
                     # Keep generic ModelMessage for other roles? Or raise error?
                     # For now, let's raise an error for unhandled roles.
                     raise ValueError(f"Unhandled role '{role}' in message at index {i}: {msg}")
            else:
                # Raise error for invalid dictionary format
                raise ValueError(f"Invalid message format at index {i}: Dictionary must have string 'role' and 'content'. Got: {msg}")
        elif isinstance(msg, str):
            # Treat string as user prompt
            converted.append(ModelRequest(
                parts=[UserPromptPart(content=msg)]
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