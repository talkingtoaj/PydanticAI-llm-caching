from typing import Any, Protocol, Dict, List, TypeVar
from pydantic_ai.messages import ModelMessage, TextPart, ModelRequest, UserPromptPart, ModelResponse, SystemPromptPart

MessageType = Any

class MessageConverter(Protocol):
    def __call__(self, messages: list[Any]) -> List[MessageType]: ...

class ExpenseRecorder(Protocol):
    async def __call__(self, model: str, task_name: str, cost: float) -> None: ...

async def noop_expense_recorder(model: str, task_name: str, cost: float) -> None: ...

def default_message_converter(messages: list[Any]) -> List[MessageType]: ... 