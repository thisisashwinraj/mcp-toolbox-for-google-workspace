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
import time
import asyncio
from dotenv import load_dotenv

from google import genai
from google.genai import types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


GEMINI_MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.7

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

google_calendar_mcp_server_params = StdioServerParameters(
    command="uv",
    args=[
        "run",
        "src/mcp_server/google_calendar/server.py",
        "--credentials",
        ".credentials/credentials.json"
    ],
)


def clean_schema(schema):
    if isinstance(schema, dict):
        schema_copy = schema.copy()

        if "additionalProperties" in schema_copy:
            del schema_copy["additionalProperties"]
        if "$schema" in schema_copy:
            del schema_copy["$schema"]

        for key, value in schema_copy.items():
            if isinstance(value, (dict, list)):
                schema_copy[key] = clean_schema(value)

        return schema_copy

    elif isinstance(schema, list):
        return [clean_schema(item) for item in schema]

    else:
        return schema


def generate_response(contents, tools=None, retries=3, backoff=60):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    tools=[tools] if tools else None,
                ),
            )
            return response

        except Exception as error:
            if "RESOURCE_EXHAUSTED" in str(error):
                wait_time = backoff * (attempt + 1)

                print(
                    f"... Gemini quota hit. Waiting {wait_time}s before retry."
                    f" (Attempt {attempt + 1}/3)"
                )
                time.sleep(wait_time)

    raise RuntimeError(">>> Failed after max retries due to quota limits.")


async def google_calendar_client():
    try:
        async with stdio_client(google_calendar_mcp_server_params) as (
            google_calendar_read,
            google_calendar_write,
        ):
            async with ClientSession(
                google_calendar_read, google_calendar_write
            ) as mcp_session:
                await mcp_session.initialize()

                google_calendar_mcp_tools = await mcp_session.list_tools()

                google_calendar_tools = types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": clean_schema(tool.inputSchema),
                        }
                        for tool in google_calendar_mcp_tools.tools
                    ]
                )

                contents = []

                while True:
                    prompt = str(input(
                        "\n>>> Enter your query (or type 'exit' to quit): "))

                    if prompt.lower() in ["exit", "quit"]:
                        print("... Exiting. Goodbye!\n")
                        break

                    contents.append(
                        types.Content(
                            role="user", parts=[types.Part(text=prompt)]
                        )
                    )

                    response = generate_response(
                        contents, google_calendar_tools)

                    for part in response.candidates[0].content.parts:
                        if (
                            hasattr(part, "function_call")
                            and part.function_call is not None
                        ):
                            function = part.function_call

                            if hasattr(function, "name") and function.name:
                                print(
                                    f"\n... Detected function call: "
                                    f"{function.name} with args: "
                                    f"{function.args}"
                                )

                                if function.name in [
                                    tool.name 
                                    for tool in google_calendar_mcp_tools.tools
                                ]:
                                    result = await mcp_session.call_tool(
                                        function.name, function.args
                                    )

                                    print(
                                        f"... Executed function: "
                                        f"{function.name} "
                                        f"with args: {function.args}\n"
                                    )

                                    function_response_part = (
                                        types.Part.from_function_response(
                                            name=function.name,
                                            response={"result": result},
                                        )
                                    )

                                    contents.append(
                                        response.candidates[0].content)

                                    contents.append(
                                        types.Content(
                                            role="user", 
                                            parts=[function_response_part]
                                        )
                                    )

                                    response = generate_response(
                                        contents, google_calendar_tools
                                    )

                    print(f">>> Response:\n{response.text}")
                    contents.append(response.candidates[0].content)

    except* Exception as eg:
        for error in eg.exceptions:
            print(">>> Sub-exception:", repr(error))
            raise error


if __name__ == "__main__":
    asyncio.run(google_calendar_client())

    """
    EXAMPLE USAGE:
    ---
    >>> Enter your query: List the upcoming events from my primary calendar.
    ---
    >>> Response:
    Here are the upcoming events from your primary calendar:

    *   **Train to NEW DELHI (NDLS) from MUMBAI (MMCT)**
        *   Start: September 1, 2025, 4:12 PM IST
        *   End: September 2, 2025, 12:30 PM IST

    *   **TechTalk: AI in Retail**
        *   Start: September 12, 2025, 1:00 PM KST
        *   End: September 12, 2025, 2:30 PM KST
        *   Recurrence: Monthly, on the 3rd Wednesday
    """
