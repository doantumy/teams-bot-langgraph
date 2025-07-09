"""
LangGraph Planner for Microsoft Teams AI Framework

This module provides a planner implementation that integrates our LangGraph agent
with the Microsoft Teams AI framework.
"""

import sys
from logging import DEBUG, Logger, StreamHandler
from typing import Awaitable, Callable, Union

from botbuilder.core import TurnContext
from teams.ai.planners import Plan, Planner, PredictedSayCommand
from teams.ai.prompts import PromptManager, PromptTemplate
from teams.ai.tokenizers import GPTTokenizer, Tokenizer

from langgraph_agent import SimpleLangGraphAgent
from message import Message
from state import AppTurnState

# Type alias for a factory function that creates PromptTemplate instances
LangGraphPlannerPromptFactory = Callable[
    [TurnContext, AppTurnState, "LangGraphPlanner"], Awaitable[PromptTemplate]
]


class LangGraphPlanner(Planner[AppTurnState]):
    """
    A planner implementation that integrates LangGraph agents with Teams AI framework.
    
    This planner uses our SimpleLangGraphAgent to generate responses in a simpler,
    more reliable way compared to the streaming LangChain approach.
    
    Attributes:
        agent: The LangGraph agent used for generating responses
        prompts: Manager for handling prompt templates
        tokenizer: Tokenizer for counting and managing tokens
        _prompt_factory: Factory function for creating prompt templates
        _logger: Logger instance for debugging and monitoring
    """
    
    # Core components for the planner
    agent: SimpleLangGraphAgent         # Our LangGraph agent
    prompts: PromptManager              # Manages prompt templates and their loading
    tokenizer: Tokenizer                # Handles token counting and text processing
    
    # Private attributes
    _prompt_factory: LangGraphPlannerPromptFactory  # Creates prompt templates dynamically
    _logger: Logger                     # For logging debug information and monitoring

    def __init__(
        self,
        *,
        prompts: PromptManager,
        tokenizer: Tokenizer = GPTTokenizer(),
        default_prompt: Union[str, LangGraphPlannerPromptFactory] = "tools",
        logger: Logger = Logger("langgraph:planner", DEBUG),
    ) -> None:
        """
        Initialize the LangGraph planner.
        
        Args:
            prompts: Manager for handling prompt templates
            tokenizer: Tokenizer for counting tokens (defaults to GPTTokenizer)
            default_prompt: Either a string name of a prompt or a factory function
                          (defaults to "tools" which loads the tools prompt template)
            logger: Logger instance for debugging (defaults to a new logger)
        """
        # Store the core components
        self.prompts = prompts
        self.tokenizer = tokenizer
        self._logger = logger
        self.agent = None  # Will be initialized after loading prompt

        # Configure logger to output to stdout for debugging
        logger.addHandler(StreamHandler(sys.stdout))

        # Set up the prompt factory based on the input type
        if isinstance(default_prompt, str):
            # If it's a string, create a factory that loads the named prompt
            self._prompt_factory = self._default_prompt_factory(default_prompt)
        else:
            # If it's already a factory function, use it directly
            self._prompt_factory = default_prompt

    async def _ensure_agent_initialized(self, context: TurnContext, state: AppTurnState) -> None:
        """Ensure the agent is initialized with the current prompt."""
        if self.agent is None:
            # Load the prompt template
            template = await self._prompt_factory(context, state, self)
            
            # Render the prompt template to get the text
            rendered_prompt = await template.prompt.render_as_text(
                context,
                state,
                self.prompts,
                self.tokenizer,
                template.config.completion.max_input_tokens,
            )
            
            # Extract the system prompt from the rendered result
            system_prompt = rendered_prompt.output
            
            # Create the agent with the system prompt
            self.agent = SimpleLangGraphAgent(system_prompt=system_prompt)
            
            self._logger.debug(f"Initialized agent with system prompt: {system_prompt[:100]}...")

    async def begin_task(self, context: TurnContext, state: AppTurnState) -> Plan:
        """
        Begin a new conversation task.
        
        This method is called when starting a new conversation or when there's no
        existing conversation history. For LangGraph, we treat this the same as
        continuing a task since the agent handles conversation state internally.
        
        Args:
            context: The turn context containing the current message and bot state
            state: The application state including conversation history
            
        Returns:
            A Plan containing the commands to execute in response to the user's message
        """
        # Ensure the agent is initialized with the current prompt
        await self._ensure_agent_initialized(context, state)
        
        # Log the input message for debugging
        self._logger.debug(
            "begin_task - input => %s", context.activity.text
        )
        
        # Add the user's current message to the conversation history
        state.conversation.history.append(Message(role="user", content=context.activity.text))
        
        # Generate response using our LangGraph agent
        return await self._generate_response(context, state)

    async def continue_task(self, context: TurnContext, state: AppTurnState) -> Plan:
        """
        Continue an existing conversation task.
        
        For LangGraph, we use the same approach as begin_task since the agent
        manages conversation context internally.
        
        Args:
            context: The turn context containing the current message and bot state
            state: The application state including conversation history
            
        Returns:
            A Plan containing the commands to execute in response
        """
        # Ensure the agent is initialized with the current prompt
        await self._ensure_agent_initialized(context, state)
        
        # Log the input message for debugging
        self._logger.debug(
            "continue_task - input => %s", context.activity.text
        )
        
        # Add the user's current message to the conversation history
        state.conversation.history.append(Message(role="user", content=context.activity.text))
        
        # Generate response using our LangGraph agent
        return await self._generate_response(context, state)

    async def _generate_response(self, context: TurnContext, state: AppTurnState) -> Plan:
        """
        Generate a response using the LangGraph agent.
        
        Args:
            context: The turn context for sending messages
            state: The application state with conversation history
            
        Returns:
            A Plan containing the SAY command with the agent's response
        """
        # Get the user's message
        user_message = context.activity.text
        
        # Get conversation history (excluding the current message we just added)
        conversation_history = state.conversation.history[:-1] if len(state.conversation.history) > 0 else []
        
        # Call our LangGraph agent with conversation history
        try:
            agent_response = await self.agent.chat(user_message, conversation_history)
            
            # Log the response for debugging
            self._logger.debug(
                "agent response (with history) => %s", agent_response
            )
            self._logger.debug(
                "conversation history length => %d", len(conversation_history)
            )
            
            # Create a plan with the agent's response
            plan = Plan()
            plan.commands.append(
                PredictedSayCommand(response=Message(role="assistant", content=agent_response))
            )
            
            # Add the assistant's response to conversation history
            state.conversation.history.append(Message(role="assistant", content=agent_response))
            
            return plan
            
        except Exception as e:
            self._logger.error(f"Error generating response: {e}")
            
            # Return a plan with an error message
            plan = Plan()
            plan.commands.append(
                PredictedSayCommand(
                    response=Message(
                        role="assistant", 
                        content="I apologize, but I encountered an error while processing your request. Please try again."
                    )
                )
            )
            return plan

    def _default_prompt_factory(self, name: str) -> LangGraphPlannerPromptFactory:
        """
        Create a default prompt factory that loads a named prompt template.
        
        Note: For LangGraph, we don't use prompt templates in the same way as LangChain,
        but we keep this for compatibility with the Teams AI framework.
        
        Args:
            name: The name of the prompt template to load
            
        Returns:
            A factory function that loads the specified prompt template
        """
        async def __factory__(
            _context: TurnContext, _state: AppTurnState, _planner: "LangGraphPlanner"
        ) -> PromptTemplate:
            """
            Factory function that loads a prompt template by name.
            
            Args:
                _context: Turn context (unused in LangGraph implementation)
                _state: Application state (unused in LangGraph implementation)  
                _planner: The planner instance (unused in LangGraph implementation)
                
            Returns:
                The loaded prompt template
            """
            return await self.prompts.get_prompt(name)

        return __factory__