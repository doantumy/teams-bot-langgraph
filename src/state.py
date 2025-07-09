"""
Application State Management for Microsoft Teams Bot

This module defines the state management classes that handle data persistence
across bot conversations. It provides a structured way to store and retrieve
conversation history, user preferences, and temporary data.

State Management Architecture:
- ConversationState: Data shared across all participants in a conversation
- UserState: Data specific to individual users across all conversations
- TempState: Temporary data that exists only for the current turn
- TurnState: Combines all state types for a single conversation turn

The state system enables the bot to:
- Remember conversation context and history
- Maintain user preferences and settings
- Track temporary data during processing
- Persist data across bot restarts (when using persistent storage)

Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from typing import List, Optional

from botbuilder.core import Storage, TurnContext
from teams.state import ConversationState, TempState, TurnState, UserState

from message import Message


class AppConversationState(ConversationState):
    """
    Application-specific conversation state that persists across the entire conversation.
    
    This class extends the base ConversationState to include bot-specific data
    that should be shared among all participants in a Teams conversation.
    
    Conversation state is scoped to the conversation ID and persists until
    the conversation ends or is explicitly cleared.
    
    Attributes:
        lights_on: Boolean flag tracking whether the lights are currently on
                  This demonstrates stateful bot behavior - the bot remembers
                  the light status across multiple messages
        history: List of all messages in the conversation including system,
                user, assistant, and tool messages. This enables the AI to
                maintain context across the entire conversation
    
    Use Cases:
        - Tracking device states (lights, temperature, etc.)
        - Maintaining conversation history for AI context
        - Storing shared settings for all conversation participants
        - Keeping track of ongoing tasks or workflows
    """
    
    # Bot-specific state variables
    lights_on: bool = False           # Tracks the current light status
    history: List[Message] = []       # Complete conversation history for AI context

    @classmethod
    async def load(
        cls, context: TurnContext, storage: Optional[Storage] = None
    ) -> "AppConversationState":
        """
        Load conversation state from storage and return an AppConversationState instance.
        
        This method handles the deserialization of conversation state data from
        the configured storage backend (memory, Azure Storage, etc.) and creates
        a properly typed instance of our custom conversation state.
        
        Args:
            context: The turn context containing conversation and channel information
            storage: Optional storage backend (uses default from context if None)
            
        Returns:
            AppConversationState: A loaded instance with current conversation data
            
        Note:
            This method is called automatically by the framework when processing
            each incoming message to restore the conversation state.
        """
        # Load the base state data from storage
        state = await super().load(context, storage)
        # Create a new instance with the loaded data
        return cls(**state)


class AppTurnState(TurnState[AppConversationState, UserState, TempState]):
    """
    Complete application state for a single conversation turn.
    
    This class combines all types of state (conversation, user, and temporary)
    into a single object that represents the complete state context for
    processing one message or bot interaction.
    
    The TurnState pattern provides a clean way to access different scopes of data:
    - Conversation: Shared data for all participants in this conversation
    - User: Data specific to the individual user across all conversations
    - Temp: Temporary data that only exists during this turn's processing
    
    Type Parameters:
        AppConversationState: Our custom conversation state class
        UserState: Framework-provided user state class
        TempState: Framework-provided temporary state class
    
    Attributes:
        conversation: Instance of AppConversationState with conversation-scoped data
        user: Instance of UserState with user-scoped data (inherited)
        temp: Instance of TempState with turn-scoped data (inherited)
    
    Usage:
        This class is instantiated for every incoming message and provides
        the complete state context to all bot handlers and AI planning logic.
    """
    
    # Explicitly type the conversation state for better IDE support and clarity
    conversation: AppConversationState

    @classmethod
    async def load(cls, context: TurnContext, storage: Optional[Storage] = None) -> "AppTurnState":
        """
        Load and combine all state types into a complete turn state instance.
        
        This factory method creates a new AppTurnState by loading each type of
        state from the storage backend and combining them into a single object.
        The method ensures that all state scopes are properly initialized and
        ready for use during message processing.
        
        Args:
            context: The turn context containing conversation and user information
            storage: Optional storage backend (uses default from context if None)
            
        Returns:
            AppTurnState: A complete state instance with all scopes loaded
            
        Loading Process:
            1. Load conversation state (shared across conversation participants)
            2. Load user state (specific to the individual user)
            3. Load temp state (temporary data for this turn only)
            4. Combine all into a single TurnState instance
            
        Note:
            This method is called by the turn state factory registered in bot.py
            for every incoming message to ensure fresh state is available.
        """
        return cls(
            # Load our custom conversation state with lights and history
            conversation=await AppConversationState.load(context, storage),
            # Load framework-provided user state
            user=await UserState.load(context, storage),
            # Load framework-provided temporary state
            temp=await TempState.load(context, storage),
        )
