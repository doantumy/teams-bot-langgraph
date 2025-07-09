"""
Microsoft Teams Bot Application Entry Point with LangGraph

This is the main entry point for the Microsoft Teams bot application
using LangGraph for AI conversation management.

It sets up and runs the web server that hosts the bot API endpoints,
enabling the bot to receive and respond to messages from Microsoft Teams
using our LangGraph-powered conversation system.

Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from aiohttp import web

# Import the configured LangGraph API application
from api_langgraph import api
from config import Config

if __name__ == "__main__":
    """
    Main application entry point for LangGraph Teams Bot.
    
    This starts the aiohttp web server that hosts our LangGraph-powered
    Teams bot, making it available to receive webhooks from Microsoft Teams.
    
    The server will:
    1. Listen for incoming HTTP requests from Teams
    2. Route requests to the LangGraph bot's message handlers
    3. Process conversations using our SimpleLangGraphAgent
    4. Send AI-generated replies back to Teams
    """
    print("=" * 60)
    print("Starting LangGraph Teams Bot...")
    print("=" * 60)
    print(f"Server will start on: http://localhost:{Config.PORT}")
    print(f"Teams webhook endpoint: http://localhost:{Config.PORT}/api/messages")
    print("Using LangGraph for conversation management")
    print("Ready to chat with users in Microsoft Teams!")
    print("=" * 60)
    
    # Start the web server
    web.run_app(api, host="localhost", port=Config.PORT)