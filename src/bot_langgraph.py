"""
Microsoft Teams Bot with LangGraph Integration

This module initializes and configures a Microsoft Teams bot that uses LangGraph
for AI planning and conversation management. This is a simplified version that
focuses on general conversation without tool calling.

Features:
- LangGraph-powered AI responses
- Simple conversation handling
- Error handling and logging
- Azure OpenAI integration
"""

# Import required libraries and modules
import os
import sys
import traceback

# Bot Framework imports for Teams integration
from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.actions import ActionTurnContext, ActionTypes
from teams.ai.prompts import PromptManager, PromptManagerOptions
from teams.state import todict

# Local imports
from config import Config
from langgraph_planner import LangGraphPlanner
from state import AppTurnState

# Load configuration settings
config = Config()

# Validate required environment variables
if config.AZURE_OPENAI_API_KEY is None:
    raise RuntimeError(
        "Missing environment variables - please check that AZURE_OPENAI_API_KEY is set."
    )

# Set up Azure OpenAI environment variables for LangGraph
os.environ["AZURE_OPENAI_API_KEY"] = config.AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["AZURE_OPENAI_API_VERSION"] = config.AZURE_OPENAI_API_VERSION

# Initialize prompt manager to load system prompts
print("Initializing prompt manager...")
prompts = PromptManager(
    PromptManagerOptions(prompts_folder=f"{os.path.dirname(os.path.abspath(__file__))}/prompts")
)

# Initialize in-memory storage for conversation state
storage = MemoryStorage()

# Create the main Teams application with LangGraph AI capabilities
app = Application[AppTurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,           # Microsoft App ID for the bot
        storage=storage,                    # Storage for conversation state
        adapter=TeamsAdapter(config),       # Teams-specific adapter
        ai=AIOptions(
            planner=LangGraphPlanner(       # Our custom LangGraph-based planner
                prompts=prompts,            # Prompt manager loads system prompts
                default_prompt="tools"      # Loads our updated conversation prompt
            )
        ),
    )
)

# =============================================================================
# EVENT HANDLERS AND FACTORY FUNCTIONS
# =============================================================================

@app.turn_state_factory
async def turn_state_factory(context: TurnContext):
    """
    Factory function to create and load turn state for each conversation turn.
    
    Args:
        context: The turn context containing message and bot information
        
    Returns:
        AppTurnState: The loaded or new turn state for this conversation
    """
    return await AppTurnState.load(context, storage)


# =============================================================================
# AI ACTION HANDLERS
# =============================================================================

@app.ai.action(ActionTypes.SAY_COMMAND)
async def on_say(
    context: ActionTurnContext,
    _state: AppTurnState,
):
    """
    Handle the SAY command from the AI planner.
    
    This is called when the AI wants to send a text response. We'll explicitly
    send the response to ensure it gets displayed.
    
    Args:
        context: Action context containing the response to send
        _state: Application state (unused)
        
    Returns:
        str: Empty string
    """
    # Get the response content from the action context
    if hasattr(context, 'data') and hasattr(context.data, 'response'):
        response = context.data.response
        if hasattr(response, 'content'):
            await context.send_activity(response.content)
    
    return ""


# =============================================================================
# ERROR HANDLING
# =============================================================================

@app.error
async def on_error(context: TurnContext, error: Exception):
    """
    Global error handler for the bot application.
    
    Args:
        context: Turn context for sending error messages to the user
        error: The exception that occurred
    """
    # Log error details to console for debugging
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    print(todict(error))

    # Send a user-friendly error message
    await context.send_activity("The bot encountered an error or bug.")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("LangGraph Teams Bot is ready!")
    print("The bot will use LangGraph for conversation management.")
    print("Start the bot with: python bot_langgraph.py")