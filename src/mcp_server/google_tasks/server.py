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

import asyncio
import logging
from pydantic import Field
from typing import Annotated, Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

import schema
from auth import async_init_google_tasks_service
from utils import handle_google_tasks_exceptions, validate_rfc3339_timestamp

logger = logging.getLogger(__name__)


mcp = FastMCP(
    "Google Tasks MCP Server",
    description="""
    The Google Tasks MCP server provides a suite of tools for managing tasklists 
    and tasks within Google Tasks.""",
    version="0.1.0",
    instructions=schema.GOOGLE_TASKS_MCP_SERVER_INSTRUCTIONS,
    settings={
        "initialization_timeout": 1200.0
    }
)


@mcp.tool(
    title="List Tasklists",
    description=schema.LIST_TASKLISTS_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def list_tasklists(
    max_results: Annotated[
        Optional[int],
        Field(description="Max number of tasklists to return", ge=1, le=1000)
    ] = None
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """
    Tool to fetch a list of tasklists from the user's Google Tasks account.

    This tool interacts with the Tasks API to retrieve the available tasklists, 
    optionally limited by a maximum number of results. It returns the etag, 
    title, last modification time, and a URL pointing to this task list.

    Args:
        max_results (Optional[int]): Maximum number of tasklists to return
            - Must be between 1 and 1000. Defaults to 5, if not provided.
            - Example: 10

    Returns:
        Dict[str, Union[str, List[Dict[str, str]]]]: A dictionary containing:
        - 'status' (str): "success", "not_found", or "error"
            On success:
            - 'tasklists' (List[Dict]): List of tasklist entries with fields:
                - 'etag' (str): ETag of the tasklist resource.
                - 'tasklist_id' (str): Unique identifier of the tasklist.
                - 'title' (str): Title of the tasklist.
                - 'updated' (str): Last modification time of the tasklist.
                - 'self_link' (str): URL pointing to the tasklist.
            If not_found:
            - 'message' (str): Message indicating no tasklists were found.
            On failure:
            - 'message' (str): Description of the error.

    Example:
        Sample Input:
            list_tasklists(max_results=2)

        Expected Output: 
            {
                "status": "success",
                "tasklists": [
                    {
                        "etag": "abc123etag",
                        "id": "ABCdefGHIjkl",
                        "title": "Personal",
                        "updated": "2025-09-25T18:30:00.000Z",
                        "self_link": "https://www.googleapis.com/tasks/v1/u..."
                    },
                    {
                        "etag": "ghi789etag",
                        "id": "YZAbcdEFGhij",
                        "title": "Shopping",
                        "updated": "2025-09-18T09:45:00.000Z",
                        "self_link": "https://www.googleapis.com/tasks/v1/u..."
                    }
                ]
            }
    """
    max_results = max_results or 5

    if not (1 <= max_results <= 1000):
        return {
            "status": "error",
            "message": (f"Invalid max_results value: {max_results}. "
                        "Must be between 1 and 1000.")
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasklists().list(
            maxResults=max_results
        ).execute()
    )

    items = response.get("items", [])

    if not items:
        return {
            "status": "not_found",
            "message": "No tasklists found in the user's Google Tasks account."
        }

    tasklists = [
        {
            "etag": tasklist.get("etag", ""),
            "tasklist_id": tasklist.get("id", ""),
            "title": tasklist.get("title", ""),
            "updated": tasklist.get("updated", ""),
            "self_link": tasklist.get("selfLink", "")
        }
        for tasklist in items
    ]

    return {
        "status": "success",
        "tasklists": tasklists
    }


@mcp.tool(
    title="Create Tasklist",
    description=schema.CREATE_TASKLIST_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def create_tasklist(
    title: Annotated[
        str,
        Field(description="Title of the tasklist to create.", max_length=1024)
    ]
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Tool to create a new tasklist in the user's Google Tasks account.

    This tool interacts with the Google Tasks API to create a new tasklist with 
    the specified title. After creating the tasklist, it returns the etag, 
    title, last modification time, and a URL pointing to this task list.

    Args:
        title (str): Title of the tasklist to create; Max length: 1024 chars.
            - Example: "Project MCP Toolbox"

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: A dictionary containing:
        - 'status' (str): "success" or "error"
            On success:
            - 'tasklist' (Dict): Details of the created tasklist, including:
                - 'etag' (str): ETag of the tasklist resource.
                - 'tasklist_id' (str): Unique identifier of the tasklist.
                - 'title' (str): Title of the tasklist.
                - 'updated' (str): Last modification time of the tasklist.
                - 'self_link' (str): URL pointing to the tasklist.
            On failure:
            - 'message' (str): Description of the error.

    Example:
        Sample Input:
            create_tasklist(title="Project MCP Toolbox")

        Expected Output: 
            {
                "status": "success",
                "tasklist": {
                    "etag": "\"abcd1234etag\"",
                    "id": "tasklistId1234",
                    "title": "Project MCP Toolbox",
                    "updated": "2025-09-26T15:30:00.000Z",
                    "self_link": "https://www.googleapis.com/tasks/v1/users..."
                }
            }
    """
    if not title or not title.strip():
        return {
            "status": "error",
            "message": "Tasklist title cannot be empty."
        }

    if len(title) > 1024:
        return {
            "status": "error",
            "message": "Title exceeds maximum length of 1024 characters."
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasklists().insert(
            body={"title": title.strip()}
        ).execute()
    )

    tasklist = {
        "etag": response.get("etag", ""),
        "tasklist_id": response.get("id", ""),
        "title": response.get("title", title),
        "updated": response.get("updated", ""),
        "self_link": response.get("selfLink", "")
    }

    return {
        "status": "success",
        "tasklist": tasklist
    }


@mcp.tool(
    title="Get Tasklist",
    description=schema.GET_TASKLIST_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def get_tasklist(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist to retrieve.", min_length=1)
    ]
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Tool to fetch a single tasklist from the user's Google Tasks account.

    This tool interacts with the Google Tasks API to retrieve a tasklist by its 
    unique identifier (id). It returns the etag, title, last modification time, 
    and a URL pointing to this task list.

    Args:
        tasklist_id (str): The unique identifier of the tasklist to retrieve.
            - Example: "tasklistId1234"

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: A dictionary containing:
        - 'status' (str): "success", "not_found", or "error"
            On success:
            - 'tasklist' (Dict): Details of the tasklist, including:
                - 'etag' (str): ETag of the tasklist resource.
                - 'tasklist_id' (str): Unique identifier of the tasklist.
                - 'title' (str): Title of the tasklist.
                - 'updated' (str): Last modification time of the tasklist.
                - 'self_link' (str): URL pointing to the tasklist.
            If not_found:
            - 'message' (str): Message indicating no tasklist was found.
            On failure:
            - 'message' (str): Description of the error.

    Example:
        Sample Input:
            get_tasklist(tasklist_id="tasklistId1234")

        Expected Output: 
            {
                "status": "success",
                "tasklist": {
                    "etag": "abcd1234etag",
                    "tasklist_id": "tasklistId1234",
                    "title": "Project Alpha Tasks",
                    "updated": "2025-09-26T15:30:00.000Z",
                    "self_link": "https://www.googleapis.com/tasks/v1/users..."
                }
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist Id cannot be empty."
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasklists().get(
            tasklist=tasklist_id.strip()
        ).execute()
    )

    if not response:
        return {
            "status": "not_found",
            "message": f"No tasklist found with ID: {tasklist_id}"
        }

    tasklist = {
        "etag": response.get("etag", ""),
        "tasklist_id": response.get("id", tasklist_id),
        "title": response.get("title", ""),
        "updated": response.get("updated", ""),
        "self_link": response.get("selfLink", "")
    }

    return {
        "status": "success",
        "tasklist": tasklist
    }


@mcp.tool(
    title="Update Tasklist",
    description=schema.UPDATE_TASKLIST_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def update_tasklist(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist to update.", min_length=1)
    ],
    new_title: Annotated[
        str,
        Field(description="New title for the tasklist.", max_length=1024)
    ]
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Tool to update an existing tasklist in the user's Google Tasks account.

    This tool interacts with Google Tasks API to rename a tasklist identified 
    by its unique ID. It returns the updated tasklist metadata including ETag, 
    ID, title, last updated time, and a URL pointing to this task list.

    Args:
        tasklist_id (str): The unique identifier of the tasklist to update.
            - Example: "tasklistId1234"
        new_title (str): New title for the tasklist; Max length: 1024 chars.
            - Example: "Updated Project MCP Toolbox"

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: A dictionary containing:
        - 'status' (str): "success", "not_found", or "error"
            On success:
            - 'tasklist' (Dict): Details of the updated tasklist, including:
                - 'etag' (str): ETag of the tasklist resource.
                - 'tasklist_id' (str): Unique identifier of the tasklist.
                - 'title' (str): Updated title of the tasklist.
                - 'updated' (str): Last modification time of the tasklist.
                - 'self_link' (str): URL pointing to the tasklist.
            If not_found:
            - 'message' (str): Message indicating the tasklist ID was not found.
            On failure:
            - 'message' (str): Description of the error.
    
    Example:
        Sample Input:
            update_tasklist(
                tasklist_id="tasklistId1234",
                new_title="Updated Project Alpha Tasks"
            )

        Expected Output:
            {
                "status": "success",
                "tasklist": {
                    "etag": "\"etag_value\"",
                    "tasklist_id": "tasklistId1234",
                    "title": "Updated Project Alpha Tasks",
                    "updated": "2025-09-26T12:34:56.000Z",
                    "self_link": "https://www.googleapis.com/tasks/v1/users..."
                }
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist Id cannot be empty."
        }

    if not new_title or not new_title.strip():
        return {
            "status": "error",
            "message": "New tasklist title cannot be empty."
        }

    if len(new_title) > 1024:
        return {
            "status": "error",
            "message": "Title exceeds maximum length of 1024 characters."
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasklists().patch(
            tasklist=tasklist_id.strip(),
            body={"title": new_title.strip()}
        ).execute()
    )

    if not response:
        return {
            "status": "not_found",
            "message": f"No tasklist found with ID: {tasklist_id}"
        }

    updated_tasklist = {
        "etag": response.get("etag", ""),
        "tasklist_id": response.get("id", tasklist_id),
        "title": response.get("title", ""),
        "updated": response.get("updated", ""),
        "self_link": response.get("selfLink", "")
    }

    return {
        "status": "success",
        "tasklist": updated_tasklist
    }


@mcp.tool(
    title="Delete Tasklist",
    description=schema.DELETE_TASKLIST_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def delete_tasklist(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist to delete.", min_length=1)
    ]
) -> Dict[str, str]:
    """
    Tool to delete an existing tasklist from the user's Google Tasks account.

    This tool interacts with Google Tasks API to remove a tasklist identified 
    by its unique ID.

    Args:
        tasklist_id (str): The unique identifier of the tasklist to delete.
            - Example: "tasklistId1234"

    Returns:
        Dict[str, str]: A dictionary containing:
        - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation indicating tasklist was deleted.
            On failure:
            - 'message' (str): Description of the error.

    Example:
        Sample Input:
            delete_tasklist(tasklist_id="AbcD1234")

        Expected Output: 
            {
                "status": "success",
                "message": "Tasklist with ID `AbcD1234` deleted successfully."
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist ID cannot be empty."
        }

    service = await async_init_google_tasks_service()

    await asyncio.to_thread(
        lambda: service.tasklists().delete(
            tasklist=tasklist_id.strip()
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Tasklist with ID `{tasklist_id}` deleted successfully."
    }


@mcp.tool(
    title="Clear Tasklist",
    description=schema.CLEAR_TASKLIST_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def clear_tasklist(
    tasklist_id: Annotated[
        str,
        Field(description="Unique identifier of the tasklist to be cleared.")
    ]
) -> Dict[str, str]:
    """
    Tool to clear all completed tasks from a specified tasklist in a user's 
    Google Tasks account.

    This tool removes all tasks marked as "completed" from the given tasklist 
    using the Google Tasks API. Active (incomplete) tasks are not affected. 
    If there are no completed tasks, tool returns success but removes nothing.

    Args:
        tasklist_id (str): Unique identifier of the tasklist to clear.
            - Example: "tasklistId1234"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'message': Confirmation that completed tasks were cleared 
                  (if any existed).
            - On error:
                - 'message': Description of the error message.

    Example:
        Sample Input:
            clear_tasklist(tasklist_id="task123")

        Expected Output:
            {
                "status": "success",
                "message": "Completed tasks cleared from tasklist `task123`."
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist ID cannot be empty."
        }
    
    service = await async_init_google_tasks_service()

    await asyncio.to_thread(
        lambda: service.tasks().clear(
            tasklist=tasklist_id.strip(),
            x__xgafv="2"
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Completed tasks cleared from tasklist `{tasklist_id}`."
    }


@mcp.tool(
    title="List Tasks",
    description=schema.LIST_TASKS_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def list_tasks(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist whose tasks should be listed.")
    ],
    completed_max: Annotated[
        Optional[str],
        Field(description="Upper bound for task's completion date (RFC3339).")
    ] = None,
    completed_min: Annotated[
        Optional[str],
        Field(description="Lower bound for task's completion date (RFC3339).")
    ] = None,
    due_max: Annotated[
        Optional[str],
        Field(description="Upper bound for a task's due date (RFC3339).")
    ] = None,
    due_min: Annotated[
        Optional[str],
        Field(description="Lower bound for a task's due date (RFC3339).")
    ] = None,
    max_results: Annotated[
        Optional[int],
        Field(description="Maximum number of tasks returned.", ge=1, le=100)
    ] = None,
    show_assigned: Annotated[
        Optional[bool],
        Field(description="Whether current assigned tasks should be included.")
    ] = None,
    show_completed: Annotated[
        Optional[bool],
        Field(description="Whether completed tasks should be included.")
    ] = None,
    show_deleted: Annotated[
        Optional[bool],
        Field(description="Whether deleted tasks should be included.")
    ] = None,
    show_hidden: Annotated[
        Optional[bool],
        Field(description="Whether hidden tasks should be included.")
    ] = None,
    updated_min: Annotated[
        Optional[str],
        Field(description="Lower bound for a task's last modification time.")
    ] = None,
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Tool to list tasks inside a given tasklist from user's Google Tasks account.

    This tool retrieves tasks within a specified Google tasklist, with optional
    filters like completed time, due dates, updated times, visibility flags etc.

    Args:
        tasklist_id (str): Id of the tasklist whose tasks should be listed.
            - Example: "tasklistId1234"
        completed_max (str): Upper bound for task completion date (RFC3339).
            - Default is not to filter by completion date.
            - Example: 2025-09-26T12:34:56Z
        completed_min (str): Lower bound for task completion date (RFC3339).
            - Default is not to filter by completion date.
            - Example: 2025-09-26T10:34:56Z
        due_max (str): Upper bound for due date (RFC3339).
            - Default is not to filter by due date.
            - Example: 2025-11-26T12:34:56Z
        due_min (str): Lower bound for due date (RFC3339).
            - Default is not to filter by due date.
            - Example: 2025-11-26T12:34:56Z
        max_results (int): Max number of tasks returned per page.
            - Must be a value between 1 to 100; Defaults to 20 if not provided.
            - Example: 10
        show_assigned (bool): Whether to include tasks assigned to user.
            - If not provided, defaults to False internally by the Tasks API.
            - Example: True
        show_completed (bool): Whether completed tasks should be included.
            - If to be set to True, `show_hidden` arg must also be set to True.
              This will take precedence over provided value for `show_hidden`.
            - If not provided, defaults to True internally by the Tasks API.
            - Example: False
        show_deleted (bool): Whether deleted tasks should be included.
            - If not provided, defaults to False internally by the Tasks API.
            - Example: True
        show_hidden (bool): Whether hidden tasks should be included.
            - Must be set to True when `show_completed` is to be set to True. 
              This will take precedence over provided value for `show_hidden`.
            - If not provided, defaults to False internally by the Tasks API.
            - Example: False
        updated_min (str): Lower bound for last modification time (RFC3339).
            - Default is not to filter by last modification time.
            - Example: 2025-11-26T12:34:56Z

    Returns:
        Dict[str, Union[str, List[Dict[str, Any]]]]: A dictionary containing:
            - 'status': "success", "not_found", or "error".
            - On success:
                - 'tasks': List of task metadata, including the title, status,
                  due, completed, updated, webViewLink etc.
            - If not_found:
                - 'message': Message indicating no tasks found.
            - On error:
                - 'message': Description of the error.

    Example:
        Sample Input:
            list_tasks(tasklist_id="stuvwxyz", max_results=1)

        Expected Output:
            {
                "status": "success",
                "tasks": [
                    {
                        "kind": "tasks#task",
                        "id": "abcdefgh",
                        "etag": "ABCD_1234",
                        "title": "MCP Toolbox v0.1.2 announcement",
                        "updated": "2025-09-20T18:30:54.109Z",
                        "selfLink": "https://www.googleapis.com/tasks/v1/...",
                        "position": "123456789",
                        "status": "completed",
                        "due": "2025-09-21T00:00:00.000Z",
                        "completed": "2025-09-21T02:44:08.166Z",
                        "hidden": true,
                        "links": [],
                        "webViewLink": "https://tasks.google.com/task/sampl..."
                    }
                ]
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error", 
            "message": "Tasklist ID cannot be empty."
        }
    
    if completed_max is not None and not validate_rfc3339_timestamp(
        completed_max
    ):
        return {
            "status": "error",
            "message": (
                f"Invalid completed_max format: '{completed_max}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }
    
    if completed_min is not None and not validate_rfc3339_timestamp(
        completed_min
    ):
        return {
            "status": "error",
            "message": (
                f"Invalid completed_min format: '{completed_min}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }
    
    if due_max is not None and not validate_rfc3339_timestamp(due_max):
        return {
            "status": "error",
            "message": (
                f"Invalid due_max format: '{due_max}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }
    
    if due_min is not None and not validate_rfc3339_timestamp(due_min):
        return {
            "status": "error",
            "message": (
                f"Invalid due_min format: '{due_min}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if updated_min is not None and not validate_rfc3339_timestamp(updated_min):
        return {
            "status": "error",
            "message": (
                f"Invalid updated_min format: '{updated_min}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    max_results = 20 if max_results is None else max_results
    show_hidden = True if show_completed is True else show_hidden

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasks().list(
            tasklist=tasklist_id,
            completedMax=completed_max,
            completedMin=completed_min,
            dueMax=due_max,
            dueMin=due_min,
            maxResults=max_results,
            showAssigned=show_assigned,
            showCompleted=show_completed,
            showDeleted=show_deleted,
            showHidden=show_hidden,
            updatedMin=updated_min,
            x__xgafv="2"
        ).execute()
    )

    items = response.get("items", [])

    if not items:
        return {
            "status": "not_found", 
            "message": f"No tasks found in tasklist {tasklist_id}"
        }

    return {
        "status": "success", 
        "tasks": items
    }


@mcp.tool(
    title="Create Task",
    description=schema.CREATE_TASK_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def create_task(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist where the task will be created.")
    ],
    title: Annotated[
        str,
        Field(description="Title of the task.", max_length=1024)
    ],
    notes: Annotated[
        Optional[str],
        Field(description="Notes describing the task.", max_length=8192)
    ] = None,
    due: Annotated[
        Optional[str],
        Field(description="Due date of the task (RFC3339).")
    ] = None,
    status: Annotated[
        Optional[schema.VALID_TASK_STATUSES],
        Field(description="Status of the task.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to create a new task inside a given tasklist in a Google Tasks account.

    This tool allows creating a task with a title, optional notes, due date and 
    status. The tool validates the input fields and interacts with the Google 
    Tasks API to insert the task. 

    Args:
        tasklist_id (str): ID of the tasklist where the task will be created.
            - Example: "tasklistId1234"
        title (str): Title of the task; Maximum length: 1024 characters.
            - Example: "Prepare presentation slides"
        notes (str): Notes describing the task; Maximum length: 8192 characters
            - Example: "Include Q3 sales data and charts."
        due (str): Due date of the task in RFC3339 format.
            - Only date is recorded; time portion is ignored. Defaults to None.
            - Example: 2025-11-26T12:34:56Z
        status (str): Status of the task.
            - Must be one of the following values: "needsAction" or "completed"
            - If not provided, defaults to "needsAction".
            - Example: "needsAction"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'task': Metadata of the created task, including title, status,
                  due, notes, updated, selfLink, and other fields.
            - On error:
                - 'message': Description of the error message.

    Example:
        Sample Input:
            create_task(
                tasklist_id="tasklistId1234",
                title="Prepare presentation slides",
                notes="Include Q3 sales data and charts.",
                status="needsAction"
            )

        Expected Output:
            {
                "status": "success",
                "task": {
                    "kind": "tasks#task",
                    "id": "gfefegeg",
                    "etag": "HQ4IFufR6_s",
                    "title": "Prepare presentation slides",
                    "notes": "Include Q3 sales data and charts.",
                    "status": "needsAction",
                    "selfLink": "https://www.googleapis.com/tasks/v1/lists/...",
                    ...
                }
            }
    """
    VALID_TASK_STATUSES = ["needsAction", "completed"]

    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error", 
            "message": "Tasklist ID cannot be empty."
        }

    if not title or not title.strip():
        return {
            "status": "error", 
            "message": "Task title cannot be empty."
        }

    if len(title) > 1024:
        return {
            "status": "error", 
            "message": "Task title exceeds 1024 characters."
        }

    if notes and len(notes) > 8192:
        return {
            "status": "error", 
            "message": "Task notes exceed 8192 characters."
        }

    if due is not None and not validate_rfc3339_timestamp(due):
        return {
            "status": "error",
            "message": (
                f"Invalid due format: '{due}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }
    
    status = "needsAction" if not status else status

    if status not in VALID_TASK_STATUSES:
        return {
            "status": "error",
            "message": (f"Invalid status value: `{status}`."
                        "Must be one of these: `needsAction` or `completed`.")
        }

    task_body = {
        "title": title,
        "notes": notes,
        "due": due,
        "status": status
    }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasks().insert(
            tasklist=tasklist_id,
            body=task_body
        ).execute()
    )

    if "id" not in response:
        return {
            "status": "error",
            "message": "Failed to create task."
        }

    return {
        "status": "success",
        "task": response
    }


@mcp.tool(
    title="Get Task",
    description=schema.GET_TASK_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def get_task(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist containing the task.")
    ],
    task_id: Annotated[
        str,
        Field(description="ID of the task to retrieve.")
    ]
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to retrieve a specific task from a user's Google Tasks account.

    This tool fetches the details of a task from an authenticated user's Google
    Tasks account, given the tasklist ID and the task ID.

    Args:
        tasklist_id (str): ID of the tasklist containing the task.
            - Example: "tasklistId1234"
        task_id (str): ID of the task to retrieve.
            - Example: "taskid1234"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'task': Metadata of the retrieved task, including the title, 
                  status, due, completed, notes, updated, selfLink, etc.
            - On error:
                - 'message': Description of the error message.

    Example:
        Sample Input:
            get_task(tasklist_id="tasklistId1234", task_id="abcd_1234")

        Expected Output:
            {
                "status": "success",
                "task": {
                    "id": "abcd_1234",
                    "title": "Prepare presentation slides",
                    "status": "needsAction",
                    "due": "2025-11-26T12:34:56Z",
                    "notes": "Include Q3 sales data and charts.",
                    "updated": "2025-09-26T10:34:56Z",
                    "selfLink": "https://www.googleapis.com/tasks/v1/lists/...",
                    ...
                }
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error", 
            "message": "Tasklist ID cannot be empty."
        }

    if not task_id or not task_id.strip():
        return {
            "status": "error", 
            "message": "Task ID cannot be empty."
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasks().get(
            tasklist=tasklist_id,
            task=task_id,
            x__xgafv="2"
        ).execute()
    )

    if not response:
        return {
            "status": "error", 
            "message": f"Task {task_id} not found in tasklist {tasklist_id}."
        }

    return {
        "status": "success", 
        "task": response
    }


@mcp.tool(
    title="Update Task",
    description=schema.UPDATE_TASK_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def update_task(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist containing the task to update.")
    ],
    task_id: Annotated[
        str,
        Field(description="ID of the task to update.")
    ],
    title: Annotated[
        Optional[str],
        Field(description="New title of the task.")
    ] = None,
    notes: Annotated[
        Optional[str],
        Field(description="New notes for the task.")
    ] = None,
    due: Annotated[
        Optional[str],
        Field(description="Updated due date in RFC3339 format.")
    ] = None,
    status: Annotated[
        Optional[schema.VALID_TASK_STATUSES],
        Field(description="Updated status of the task.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to update an existing task inside a user's Google Tasks account.

    This tool allows updating specific fields of a task such as its title, due
    date, notes, or status using the Google Tasks API `patch` semantics. Only 
    provided fields will be updated; others remain unchanged.

    Args:
        tasklist_id (str): ID of the tasklist containing the task.
            - Example: "tasklistId1234"
        task_id (str): ID of the task to update.
            - Example: "taskId5678"
        title (str, optional): New title of the task.
            - Max length: 1024 characters.
            - Example: "Finalize project report"
        notes (str, optional): Notes describing the task.
            - Max length: 8192 characters.
            - Example: "Include budget comparison section."
        due (str, optional): Updated due date of the task in RFC3339 format.
            - Example: "2025-11-26T12:34:56Z"
        status (str, optional): Updated status of the task.
            - Must be one of ["needsAction", "completed"].
            - Example: "completed"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'task': Metadata of the updated task.
            - On error:
                - 'message': Description of the error.

    Example:
        Sample Input:
            update_task(
                tasklist_id="tasklistId1234", 
                task_id="abcd_1234", 
                updates={
                    "title": "Buy groceries",
                    "notes": "Include fruits and vegetables",
                    "due": "2025-09-28T10:00:00.000Z"
                }
            )

        Expected Output:
            {
                "status": "success",
                "task": {
                    "id": "abcd_1234",
                    "title": "Buy groceries",
                    "status": "needsAction",
                    "due": "2025-09-28T10:00:00.000Z",
                    "notes": "Include fruits and vegetables",
                    "updated": "2025-09-27T19:34:56Z",
                    "selfLink": "https://www.googleapis.com/tasks/v1/lists/...",
                    ...
                }
            }
    """
    VALID_TASK_STATUSES = ["needsAction", "completed"]

    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist ID cannot be empty."
        }

    if not task_id or not task_id.strip():
        return {
            "status": "error",
            "message": "Task ID cannot be empty."
        }

    if title and len(title) > 1024:
        return {
            "status": "error",
            "message": "Task title exceeds 1024 characters."
        }

    if notes and len(notes) > 8192:
        return {
            "status": "error",
            "message": "Task notes exceed 8192 characters."
        }

    if due is not None and not validate_rfc3339_timestamp(due):
        return {
            "status": "error",
            "message": (
                f"Invalid due format: '{due}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if status and status not in VALID_TASK_STATUSES:
        return {
            "status": "error",
            "message": (f"Invalid status value: `{status}`. "
                        "Must be 'needsAction' or 'completed'.")
        }

    task_body = {}

    if title is not None:
        task_body["title"] = title
    if notes is not None:
        task_body["notes"] = notes
    if due is not None:
        task_body["due"] = due
    if status is not None:
        task_body["status"] = status

    if not task_body:
        return {
            "status": "error",
            "message": f"No fields provided to update in task `{task_id}`."
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasks().patch(
            tasklist=tasklist_id,
            task=task_id,
            body=task_body,
            x__xgafv="2"
        ).execute()
    )

    if not response or "id" not in response:
        return {
            "status": "error",
            "message": f"Failed to update task {task_id} in {tasklist_id}."
        }

    return {
        "status": "success",
        "task": response
    }


@mcp.tool(
    title="Move Task",
    description=schema.MOVE_TASK_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def move_task(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist containing the task to move.")
    ],
    task_id: Annotated[
        str,
        Field(description="ID of the task to move.")
    ],
    destination_tasklist_id: Annotated[
        Optional[str],
        Field(description="Destination tasklist ID.")
    ] = None,
    parent_task_id: Annotated[
        Optional[str],
        Field(description="New parent task ID.")
    ] = None,
    previous_task_id: Annotated[
        Optional[str],
        Field(description="ID of new previous sibling task.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to move a task within a tasklist or between tasklists in the user's 
    Google Tasks account.

    This tool moves a task to a new position within the same tasklist or to a 
    different tasklist. Optionally, the task can be moved under a new parent 
    task or after a specified sibling task.

    Args:
        tasklist_id (str): ID of the tasklist containing the task.
            - Example: "tasklist1234"
        task_id (str): ID of the task to move.
            - Example: "task5678"
        destination_tasklist_id (str, optional): ID of the destination tasklist.
            - If set task is moved from tasklist to the destination_tasklist_id.
              Otherwise, the task is moved within its current list. Recurrent 
              tasks cannot currently be moved between lists.
            - Example: "tasklist9876"
        parent_task_id (str, optional): New parent task ID.
            - If the task is moved to the top level, this parameter is omitted. 
            - Task set as parent must exist in tasklist and can not be hidden. 
            - Exceptions: 
                1. Assigned and repeating tasks cannot be set as parent tasks, 
                   or be moved under a parent task (become subtasks).
                2. Tasks that are both completed and hidden cannot be nested so 
                   the parent field must be empty.
            - Example: "parentTask123"
        previous_task_id (str, optional): ID of the new `previous` sibling task.
            - If the task is moved to the first position among siblings, this 
              parameter is omitted. 
            - The task set as previous must exist in the task list and can not 
              be hidden. 
            - Exceptions: 
                1. Tasks that are both completed and hidden can only be moved 
                   to position 0, so the previous field must be empty.
            - Example: "prevTask456"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'task': Metadata of the moved task.
            - On error:
                - 'message': Description of the error message.

    Example:
        Sample Input:
            move_task(
                tasklist_id="tasklist1234",
                task_id="task5678",
                parent_task_id="parentTask123",
                previous_task_id="prevTask456"
            )

        Expected Output:
            {
                "status": "success",
                "task": {
                    "id": "task5678",
                    "title": "Prepare presentation slides",
                    "status": "needsAction",
                    "due": "2025-11-26T12:34:56Z",
                    "notes": "Include Q3 sales data and charts.",
                    "parent": "parentTask123",
                    "previous": "prevTask456",
                    "updated": "2025-09-26T10:34:56Z",
                    "selfLink": "https://www.googleapis.com/tasks/v1/lists/...",
                    ...
                }
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error", 
            "message": "Tasklist ID cannot be empty."
        }

    if not task_id or not task_id.strip():
        return {
            "status": "error", 
            "message": "Task ID cannot be empty."
        }
    
    if destination_tasklist_id and not destination_tasklist_id.strip():
        return {
            "status": "error",
            "message": f"Invalid destination_tasklist: {destination_tasklist_id}"
        }

    if parent_task_id and not parent_task_id.strip():
        return {
            "status": "error",
            "message": f"Invalid value provided for parent: {parent_task_id}"
        }

    if previous_task_id and not previous_task_id.strip():
        return {
            "status": "error",
            "message": f"Invalid value provided for previous: {previous_task_id}"
        }

    service = await async_init_google_tasks_service()

    response = await asyncio.to_thread(
        lambda: service.tasks().move(
            tasklist=tasklist_id,
            task=task_id,
            destinationTasklist=destination_tasklist_id,
            parent=parent_task_id,
            previous=previous_task_id,
            x__xgafv="2"
        ).execute()
    )

    if not response:
        return {
            "status": "error",
            "message": f"Failed to move task {task_id} in tasklist {tasklist_id}"
        }

    return {
        "status": "success", 
        "task": response
    }


@mcp.tool(
    title="Delete Task",
    description=schema.DELETE_TASK_TOOL_DESCRIPTION
)
@handle_google_tasks_exceptions
async def delete_task(
    tasklist_id: Annotated[
        str,
        Field(description="ID of the tasklist containing the task to delete.")
    ],
    task_id: Annotated[
        str,
        Field(description="ID of the task to delete.")
    ]
) -> Dict[str, str]:
    """
    Tool to delete a specific task from a user's Google Tasks account.

    This tool removes a task from the specified tasklist given its tasklist ID
    and task ID. Once deleted, the task cannot be recovered. The tool validates
    the input IDs before calling the Google Tasks API. **Use with caution.**

    Args:
        tasklist_id (str): ID of the tasklist containing the task to delete.
            - Example: "tasklistId1234"
        task_id (str): ID of the task to delete.
            - Example: "taskId5678"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status': "success" or "error".
            - On success:
                - 'message': Confirmation that the task was deleted.
            - On error:
                - 'message': Description of the error message.

    Example:
        Sample Input:
            delete_task(tasklist_id="listid1234", task_id="taskId5678")

        Expected Output:
            {
                "status": "success",
                "message": "Task taskId5678 deleted from tasklist `listid1234`"
            }
    """
    if not tasklist_id or not tasklist_id.strip():
        return {
            "status": "error",
            "message": "Tasklist ID cannot be empty."
        }

    if not task_id or not task_id.strip():
        return {
            "status": "error",
            "message": "Task ID cannot be empty."
        }

    service = await async_init_google_tasks_service()

    await asyncio.to_thread(
        lambda: service.tasks().delete(
            tasklist=tasklist_id,
            task=task_id,
            x__xgafv="2"
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Task {task_id} deleted from tasklist `{tasklist_id}`"
    }


if __name__ == "__main__":
    TRANSPORT_PROTOCOL = 'stdio'
    logger.info(
        f"Starting Google Tasks MCP server with {TRANSPORT_PROTOCOL} transport."
    )

    mcp.run(transport=TRANSPORT_PROTOCOL)
