# Copyright 2025 Ashwin Raj
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import logging
import warnings
import streamlit as st
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.planners import BuiltInPlanner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

from mcp import StdioServerParameters

from .config import MODEL_TEMPERATURE, MODEL_MAX_TOKENS, MODEL_THINKING_BUDGET
from .prompts import DRIVE_AGENT_SYSTEM_INSTRUCTIONS

load_dotenv()
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")


MODEL_DRIVE_AGENT: str = "gemini-2.5-flash"

CURRENT_DIR = os.getcwd()
SERVER_PATH = os.path.join(
    CURRENT_DIR, "src", "mcp_server", "google_drive", "server.py"
)

CREDENTIALS_DIR = os.path.join(CURRENT_DIR, ".credentials")
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

CREDENTIALS_PATH = os.path.join(CREDENTIALS_DIR, "credentials.json")
creds = json.loads(st.secrets["GCP_OAUTH_CLIENT"])
with open(CREDENTIALS_PATH, "w") as f:
    json.dump(creds, f)

SAFETY_CONFIGURATIONS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

def before_agent_callback(
    callback_context: CallbackContext
) -> Optional[types.Content]:
    state = callback_context.state

    if "current_date" not in state:
        state["current_date"] = datetime.now().strftime("%B %d, %Y (%I:%M %p)")

    if "current_timezone" not in state:
        state["current_timezone"] = st.context.timezone or "unavailable"
    
    if "users_locale" not in state:
        state["users_locale"] = st.context.locale or "en-US"

    return None

google_drive_mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uv',
            args=[
                "--directory",
                CURRENT_DIR,
                "run",
                SERVER_PATH,
                "--credentials",
                CREDENTIALS_PATH
            ],
        ),
    ),
)

drive_agent = LlmAgent(
    model=MODEL_DRIVE_AGENT,
    name='drive_agent',
    description='An agent to assist with Google Drive related tasks.',
    instruction=DRIVE_AGENT_SYSTEM_INSTRUCTIONS,
    generate_content_config=types.GenerateContentConfig(
        temperature=MODEL_TEMPERATURE,
        max_output_tokens=MODEL_MAX_TOKENS,
        safety_settings=SAFETY_CONFIGURATIONS,
    ),
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=MODEL_THINKING_BUDGET,
        )
    ),
    include_contents="default",
    tools=[
        google_drive_mcp_toolset
    ],
    disallow_transfer_to_peers=False,
    disallow_transfer_to_parent=False,   
    before_agent_callback=before_agent_callback
)
