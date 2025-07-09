"""
Simple LangGraph Agent with Azure OpenAI Chat Model

This module provides a basic LangGraph implementation that connects to Azure OpenAI
for answering general questions. This is step 1 of the RAG implementation plan.
"""

import os
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, add_messages, START, END
from langgraph.graph.message import add_messages

from config import Config


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[list[BaseMessage], add_messages]


class SimpleLangGraphAgent:
    """A simple LangGraph agent that uses Azure OpenAI for general questions."""
    
    def __init__(self, system_prompt: str = None):
        """Initialize the agent with Azure OpenAI configuration."""
        self.config = Config()
        
        # Set up Azure OpenAI environment variables
        os.environ["AZURE_OPENAI_API_KEY"] = self.config.AZURE_OPENAI_API_KEY
        os.environ["AZURE_OPENAI_ENDPOINT"] = self.config.AZURE_OPENAI_ENDPOINT
        os.environ["AZURE_OPENAI_API_VERSION"] = self.config.AZURE_OPENAI_API_VERSION
        
        # Store the system prompt
        self.system_prompt = system_prompt or "You are a helpful AI assistant powered by Azure OpenAI and LangGraph."
        
        # Initialize the Azure OpenAI model
        self.llm = AzureChatOpenAI(
            api_version=self.config.AZURE_OPENAI_API_VERSION,
            azure_deployment=self.config.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
            temperature=0.1,
            max_tokens=1000
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add the chat node
        workflow.add_node("chat", self._chat_node)
        
        # Set entry point
        workflow.add_edge(START, "chat")
        workflow.add_edge("chat", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _chat_node(self, state: AgentState) -> dict:
        """Chat node that processes user messages with Azure OpenAI."""
        messages = state["messages"]
        
        # Add system message if this is the first message
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            from langchain_core.messages import SystemMessage
            system_message = SystemMessage(content=self.system_prompt)
            messages = [system_message] + messages
        
        # Call the Azure OpenAI model
        response = await self.llm.ainvoke(messages)
        
        # Return the new state with the assistant's response
        return {"messages": [response]}
    
    async def chat(self, message: str, conversation_history: list = None) -> str:
        """
        Chat interface for the agent with conversation history support.
        
        Args:
            message: User's current message
            conversation_history: List of previous messages for context
            
        Returns:
            Agent's response
        """
        # Convert conversation history to LangChain messages
        messages = []
        
        if conversation_history:
            for msg in conversation_history:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        messages.append(AIMessage(content=msg.content))
                    # Skip system messages for now to keep it simple
        
        # Add the current user message
        messages.append(HumanMessage(content=message))
        
        # Create initial state with full conversation
        initial_state = {
            "messages": messages
        }
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        # Extract the last message (assistant's response)
        last_message = result["messages"][-1]
        return last_message.content


# Test function
async def test_simple_agent():
    """Test the simple LangGraph agent."""
    print("Initializing SimpleLangGraphAgent...")
    agent = SimpleLangGraphAgent()
    
    print("Testing with a simple question...")
    response = await agent.chat("Hello! What is the capital of Norway?")
    print(f"Agent response: {response}")
    
    print("\nTesting with another question...")
    response = await agent.chat("Can you explain what artificial intelligence is?")
    print(f"Agent response: {response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_agent())