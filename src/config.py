"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import os

from dotenv import load_dotenv

# load_dotenv()
load_dotenv("env/.env")



class Config:
    """Bot Configuration"""

    PORT = 3978
    APP_ID = os.getenv("BOT_ID")
    APP_PASSWORD = os.getenv("BOT_PASSWORD")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME= os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "")