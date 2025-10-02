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

from typing import Literal


VALID_TASK_STATUSES = Literal["needsAction", "completed"]

GOOGLE_TASKS_MCP_SERVER_INSTRUCTIONS = """
# Google Tasks MCP Server

This MCP server provides a suite of tools for managing tasklists and tasks 
within a user's Google Tasks account. It supports operations like creating, 
retrieving, updating, moving, and deleting tasks, as well as managing 
tasklists and clearing completed tasks.

### IMPORTANT: Always Use MCP Tools for Google Tasks Operations

Always use the MCP tools provided by this server for interacting with Google 
Tasks. This ensures that authentication, RFC3339 timestamp handling, task 
hierarchies and API-specific error handling are managed correctly by the server, 
preventing common issues and ensuring consistent behavior.

---

## Usage Notes

- **Authentication:** The Google Tasks MCP server requires a one-time OAuth 2.0 
    authentication flow. On first use, the server will guide you through this 
    process by redirecting to a OAuth window to grant the necessary permissions. 
    All actions are performed using the authenticated Google account.
- **Tasklist and Task Ids:** Most operations require `tasklist_id` or `task_id`. 
    You can use `list_tasklists()` tool to list the available tasklists and the 
    `list_tasks()` tool to list the available tasks.
- **Timestamps:** All datetime values must be provided in valid RFC3339 format 
    (e.g. `2025-11-26T12:34:56Z`). Only date and time components are considered 
    depending on the field (e.g., due dates, completed timestamps).
- **Parent and Subtasks:** When creating or moving tasks, the parent-child 
    relationships must follow Google Tasks rules. Tasks that are completed and 
    hidden cannot become parents or subtasks.

---

## Common Workflows

### Creating a New Task
1.  Identify the target tasklist ID: 
    `list_tasklists(max_results=15)`
2.  Create the task: 
    `create_task(tasklist_id='sample_tasklist', title='Complete MCP Writeup')`

### Finding and Updating a Task
1. Identify the target tasklist ID:  
    `list_tasklists(max_results=5)`
2. List tasks in the tasklist to find the correct task ID:  
    `list_tasks(tasklist_id='sample_tasklist', show_completed=False)`
3. Update the task fields (title, notes, due date, status, etc.):  
    `update_task(tasklist_id='sample_tasklist', task_id='sample_task', 
    title='Finalize MCP Writeup', status='completed')`

### Moving a Task from One List to Another
1. Identify the `tasklist_id` of the source and destination tasklist IDs:  
    `list_tasklists(max_results=10)`  
2. Move the task to a new tasklist (e.g. set a new parent or previous sibling):  
    `move_task(tasklist_id='source_tasklist', task_id='task1234', 
    destination_tasklist_id='destination_tasklist', parent_task_id=None, 
    previous_task_id=None)`

### Clearing a Tasklist
1. Identify the target tasklist ID:  
    `list_tasklists(max_results=5)`  
2. Clear all completed tasks from the tasklist:  
    `clear_tasklist(tasklist_id='sample_tasklist')`

---

## Best Practices

- **Validate Task IDs and Tasklist IDs:** Always confirm the task and tasklist 
    IDs before performing create, update, deletion, move etc. operations.
- **Use RFC3339 Format for Dates:** Ensure all due dates, completed timestamps, 
    and updated fields are in valid RFC3339 format.
- **Parent-Child Rules:** Avoid assigning completed or hidden tasks as parents 
    or subtasks.
- **Check API Responses:** Inspect the `status` and `message` field in the tool
    responses to confirm success and handle errors gracefully.
- **Limit API Calls:** Use filtering parameters such as `show_completed` and/or 
    `max_results` when listing tasks to reduce unnecessary data fetch.
- **Task Hierarchy Awareness:** When moving tasks, consider impact on subtasks 
    and sibling relationships.
"""


LIST_TASKLISTS_TOOL_DESCRIPTION = """
Retrieves up to 1000 tasklists from a user's Google Tasks account. Supports an 
optional parameter to limit the maximum number of tasklists returned. Returns 
tasklist metadata including ID, title, updated timestamp, and API selfLink upon 
success, or an error message upon failure.
"""

CREATE_TASKLIST_TOOL_DESCRIPTION = """
Creates a new tasklist in the authenticated user's Google Tasks account 
with the specified title. Ensures the title is non-empty and does not exceed 
1024 characters. Returns metadata of the created tasklist including its ID, 
title, last updated time, ETag, and a link to the tasklist.
"""

GET_TASKLIST_TOOL_DESCRIPTION = """
Retrieves a single tasklist from the authenticated user's Google Tasks account 
by its unique tasklist ID. Returns metadata including the tasklist ID, title, 
last updated time, ETag, and a link to the tasklist. Handles cases where the 
tasklist does not exist.
"""

UPDATE_TASKLIST_TOOL_DESCRIPTION = """
Updates the title of an existing tasklist in the user's Google Tasks account. 
Ensures the new title is not empty and does not exceed 1024 characters. Returns
the updated tasklist metadata including ETag, ID, title, last updated time, and 
a URL pointing to the tasklist upon success or an error message if the tasklist 
does not exist or input validation fails.
"""

DELETE_TASKLIST_TOOL_DESCRIPTION = """
Deletes a tasklist from a user's Google Tasks account using its unique ID. The
tool validates the tasklist ID and interacts with Google Tasks API to remove 
the tasklist. Returns a success message upon deletion, or an error message if 
the tasklist was not found or if the input is invalid.
"""

CLEAR_TASKLIST_TOOL_DESCRIPTION = """
Clears all completed tasks from a specified tasklist in a user's Google Tasks 
account using its unique ID. The tool validates the tasklist ID and interacts 
with the Google Tasks API to remove all tasks marked as completed. Active 
(incomplete) tasks remain untouched. Returns a success message upon completion 
or an error message if the input is invalid.
"""

LIST_TASKS_TOOL_DESCRIPTION = """
Retrieves all tasks from a specified tasklist in a user's Google Tasks account. 
The tool requires the tasklist ID and optionally supports filtering by task 
status or time constraints. It interacts with the Google Tasks API and returns 
a list of tasks with their details such as title, status, due date, and links.
"""

CREATE_TASK_TOOL_DESCRIPTION = """
Creates a new task inside a specified tasklist in a user's Google Tasks account. 
The tool allows setting a task title, optional notes, due date, and status. It 
validates input fields and interacts with the Google Tasks API to insert the 
new task. 
"""

GET_TASK_TOOL_DESCRIPTION = """
Retrieves a specific task from a user's Google Tasks account using its tasklist 
ID and task ID. The tool validates the input IDs and interacts with the Google 
Tasks API to fetch the task details. Returns the task metadata on success or an 
error message if the task is not found or if the input is invalid.
"""

UPDATE_TASK_TOOL_DESCRIPTION = """
Updates an existing task in a user's Google Tasks account using its tasklist ID 
and task ID. This tool performs a partial update (PATCH), modifying only the 
fields provided in the update payload while leaving other fields unchanged.
"""

MOVE_TASK_TOOL_DESCRIPTION = """
Moves a task to a new position within the same tasklist in user's Google Tasks 
account. The task can be moved under a new parent task or after a specified 
sibling task. Cross-tasklist moves are supported. Returns updated task metadata 
on success or an error message if the move fails or the input is invalid.
"""

DELETE_TASK_TOOL_DESCRIPTION = """
Deletes a specific task from a user's Google Tasks account using its tasklist 
ID and task ID. The tool validates the input IDs and interacts with the Google 
Tasks API to remove the task. Returns a success message upon deletion, or an 
error message if the task is not found or the inputs are invalid.
"""
