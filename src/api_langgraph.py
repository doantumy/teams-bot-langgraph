"""
Microsoft Teams Bot API Server with LangGraph Integration

This module sets up the HTTP API server that handles incoming webhook requests
from Microsoft Teams using our LangGraph-powered bot implementation.

The API server:
- Listens for POST requests to /api/messages (Teams webhook endpoint)
- Routes incoming activities to the LangGraph bot application for processing
- Handles errors gracefully with middleware
- Returns appropriate HTTP responses to Teams

Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from http import HTTPStatus

from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware

# Import the configured LangGraph bot application
from bot_langgraph import app

# Define HTTP routes for the web server
routes = web.RouteTableDef()


@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    """
    Handle incoming messages from Microsoft Teams using LangGraph.
    
    This endpoint receives webhook requests from Microsoft Teams containing
    user messages, system events, and other bot activities. It processes
    these through our LangGraph-powered bot framework.
    
    Args:
        req: The incoming HTTP request from Teams containing the activity
        
    Returns:
        web.Response: HTTP response to send back to Teams
    """
    # Process the incoming request through the LangGraph bot framework
    res = await app.process(req)

    # If the bot returned a specific response, use it
    if res is not None:
        return res

    # Otherwise, return a standard OK response
    return web.Response(status=HTTPStatus.OK)


# Create the web application with error handling middleware
api = web.Application(middlewares=[aiohttp_error_middleware])

# Register our routes with the application
api.add_routes(routes)