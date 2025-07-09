"""
Message Bridge Between Teams AI Framework and LangChain

This module provides a Message class that acts as a bridge between the Microsoft
Teams AI framework and LangChain message formats. It allows seamless conversion
between the two message systems while supporting tool calls and various message roles.

The Message class extends the Teams AI Message class and adds LangChain compatibility,
enabling the bot to work with both frameworks simultaneously.
"""

from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from teams.ai.prompts import Message as TeamsAIMessage


@dataclass_json
@dataclass
class Message(TeamsAIMessage[str]):
    """
    Enhanced message class that bridges Teams AI and LangChain message formats.
    
    This class extends the Teams AI Message class to include LangChain-specific
    features like tool calls while maintaining compatibility with both frameworks.
    
    Attributes:
        tool_calls: List of tool/function calls made by the AI assistant
        tool_call_id: ID of the tool call when this message is a tool response
        
    Inherited Attributes:
        role: The role of the message sender ("system", "user", "assistant", "tool")
        content: The text content of the message
    """

    # LangChain-specific attributes for tool calling functionality
    tool_calls: Optional[List[ToolCall]] = None    # Tools the AI wants to call
    tool_call_id: Optional[str] = None             # ID when responding to a tool call

    def to_langchain(self) -> BaseMessage:
        """
        Convert this message to a LangChain BaseMessage format.
        
        This method transforms the Teams AI message format into the corresponding
        LangChain message type, preserving all relevant information including
        tool calls and IDs.
        
        Returns:
            BaseMessage: The equivalent LangChain message object
            
        Raises:
            RuntimeError: If the message role is not recognized
        """
        # Ensure content is a string, default to empty if None
        content = self.content if self.content is not None else ""

        # Convert based on message role
        if self.role == "system":
            return SystemMessage(content)
        elif self.role == "user":
            return HumanMessage(content)
        elif self.role == "assistant":
            # Assistant messages can include tool calls
            return AIMessage(content, tool_calls=self.tool_calls)
        elif self.role == "tool":
            # Tool messages include the ID of the tool call they're responding to
            return ToolMessage(content, tool_call_id=self.tool_call_id)

        raise RuntimeError(f"invalid message role {self.role}")

    @classmethod
    def from_langchain(cls, message: BaseMessage) -> "Message":
        """
        Create a Message instance from a LangChain BaseMessage.
        
        This class method converts LangChain message objects back into our
        enhanced Message format, preserving tool calls and other metadata.
        
        Args:
            message: The LangChain message to convert
            
        Returns:
            Message: A new Message instance with equivalent data
            
        Raises:
            RuntimeError: If the LangChain message type is not recognized
        """
        # Extract content as string, handle cases where content might not be string
        content = message.content if isinstance(message.content, str) else ""

        # Convert based on LangChain message type
        if isinstance(message, SystemMessage):
            return cls(role="system", content=content)
        elif isinstance(message, HumanMessage):
            return cls(role="user", content=content)
        elif isinstance(message, AIMessage):
            # AI messages may include tool calls
            return cls(role="assistant", content=content, tool_calls=message.tool_calls)
        elif isinstance(message, ToolMessage):
            # Tool messages include the tool call ID
            return cls(role="tool", content=content, tool_call_id=message.tool_call_id)

        raise RuntimeError(f"invalid message type {message.__class__}")
