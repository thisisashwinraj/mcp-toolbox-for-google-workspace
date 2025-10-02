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

from .config import MODEL_TEMPERATURE, MODEL_MAX_TOKENS, MODEL_THINKING_BUDGET
from .prompts import GLOBAL_INSTRUCTIONS, ROOT_AGENT_SYSTEM_INSTRUCTIONS

from .sub_agents.drive_agent.agent import drive_agent
from .sub_agents.calendar_agent.agent import calendar_agent
from .sub_agents.gmail_agent.agent import gmail_agent
from .sub_agents.tasks_agent.agent import tasks_agent

load_dotenv()
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")


MODEL_ROOT_AGENT: str = "gemini-2.5-flash"

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

root_agent = LlmAgent(
    model=MODEL_ROOT_AGENT,
    name="root_agent",
    description="An agent to assist with Google Workspace related tasks.",
    instruction=ROOT_AGENT_SYSTEM_INSTRUCTIONS,
    global_instruction=GLOBAL_INSTRUCTIONS,
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
    sub_agents=[
        drive_agent,
        calendar_agent,
        gmail_agent,
        tasks_agent
    ],
    disallow_transfer_to_peers=False,
    disallow_transfer_to_parent=False,   
    before_agent_callback=before_agent_callback
)
