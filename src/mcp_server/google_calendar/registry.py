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


CALENDAR_EVENT_SORT_KEYS = Literal["startTime", "updateTime"]

CALENDAR_ACCESS_ROLES = Literal["freeBusyReader", "owner", "reader", "writer"]

CALENDAR_EVENT_VISIBILITY = Literal[
    "default", "public", "private", "confidential"]

CALENDAR_EVENT_TRANSPARENCY = Literal["transparent", "opaque"]

CALENDAR_EVENT_SEND_UPDATES = Literal["all", "externalOnly", "none"]

GOOGLE_CALENDAR_MCP_SERVER_INSTRUCTIONS = """
# Google Calendar MCP Server

This MCP server provides a suite of tools for managing calendars, events, and 
related scheduling tasks within a user's Google Calendar account.

### IMPORTANT: Always Use MCP Tools for Google Calendar Operations

Always use the MCP tools provided by this server for interacting with Google 
Calendar. This ensures that authentication, time zone handling, recurrence 
parsing, and API-specific error handling are managed correctly by the server, 
preventing common issues and ensuring consistent behavior.

---

## Usage Notes

- **Authentication:** The Google Calendar MCP server requires a one-time 
    OAuth 2.0 authentication flow. On first use, the server will guide you 
    through this process by redirecting to a Google OAuth window to grant the 
    necessary permissions. All actions are performed using the authenticated 
    Google account.
- **Permissions:** During authentication, the server requests specific OAuth 
    scopes (e.g., read, write, or modify events). If you receive a permission 
    error, it may be because:
    - The authenticated account doesn't have access to the target calendar.
    - The required scope was not granted during authentication.
- **Calendar IDs:** Most operations require a `calendar_id`. You can use 
    `list_calendars` to find available calendars and their IDs. When working 
    with the primary calendar, you can simply use the calendar ID `primary`.
- **Event IDs:** To update or delete an event, you must provide its unique 
    `event_id`. Use `list_events` to retrieve the correct event ID.
- **Time Zones:** All datetime values must be provided in valid IANA time zone 
    format (e.g., `Asia/Kolkata`) or as RFC3339 timestamps (e.g., 
    `2023-10-01T12:00:00Z`).
- **Recurrence Rules:** Recurrence (`RRULE`) must follow the iCalendar 
    specification (RFC 5545) as supported by Google Calendar 
    (e.g., `RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR`).

---

## Common Workflows

### Creating a New Event
1.  Identify the target calendar ID: 
    `list_calendars()`
2.  Create the event: 
    `create_event(calendar_id='primary', summary='Team Meeting', 
    start_time='2025-08-15T10:00:00+05:30', 
    end_time='2025-08-15T11:00:00+05:30', time_zone='Asia/Kolkata')`

### Finding and Updating an Event
1.  Search for events in a date range:  
    `list_events(calendar_id='primary', time_min='2025-08-01T00:00:00Z', 
    time_max='2025-08-31T23:59:59Z')`
2.  Update the event using its `event_id`:  
    `update_event(calendar_id='primary', event_id='event_id_here', 
    updates={'summary': 'Updated Meeting Title'})`

### Adding a Recurring Event
1.  Create a recurring event using RRULE:  
    `create_event(calendar_id='primary', summary='Weekly Standup', 
    start_time='2025-08-15T09:00:00+05:30', 
    end_time='2025-08-15T09:30:00+05:30', 
    time_zone='Asia/Kolkata', 
    recurrence=['RRULE:FREQ=WEEKLY;BYDAY=MO'])`

### Deleting an Event
1.  Locate the event ID via `list_events`.
2.  Delete it:  
    `delete_event(calendar_id='primary', event_id='event_id_here')`

---

## Best Practices

- **Validate Time Zones & Formats:** Ensure all dates are in RFC3339 format and 
    all time zones are valid IANA names.
- **Confirm Event IDs:** Always verify `event_id` before modifying or deleting 
    events to avoid affecting the wrong entry.
- **Use Recurrence Carefully:** Always validate recurrence rules against 
    Google Calendar's supported patterns to avoid API rejections.
- **Check API Responses:** Inspect the `status` and `message` fields in 
    responses to confirm success and handle errors gracefully.
- **Limit API Calls:** Use filtering parameters like `time_min`, `time_max`, 
    and `max_results` when listing events to reduce unnecessary data fetch.
- **Leverage Descriptions & Attendees:** Use the `description` and `attendees` 
    fields to provide complete context for meetings.
- **Sort for Relevance:** When listing events, use sorting options to quickly 
    find upcoming or recently updated items.
"""

CREATE_CALENDAR_TOOL_DESCRIPTION = """
Creates a new secondary calendar in the user's Google Calendar account with a 
specified title. Optionally accepts a time zone (IANA format) and a description 
for the calendar. If no time zone is provided, it defaults to 'UTC'. Returns 
the calendar ID, summary, time zone, and a direct link to view the calendar in 
Google Calendar upon success, or an error message upon failure.

---

**Example:**
**Sample Input:**
    create_calendar(
        summary="Team Sync Calendar",
        time_zone="Asia/Kolkata",
        description="Weekly sync meetings and planning discussions"
    )

**Expected Output:**
    {
        "status": "success",
        "calendarId": "sample_calendar_id@group.calendar.google.com",
        "summary": "Team Sync Calendar",
        "timeZone": "Asia/Kolkata",
        "calendar_url": "https://calendar.google.com/calendar/u/0/r?cid=cal_id"
    }
"""

LIST_CALENDARS_TOOL_DESCRIPTION = """
Retrieves a list of calendars associated with the authenticated user's Google 
Calendar account. Supports filtering based on minimum access role, inclusion of 
deleted or hidden calendars and maximum number of results. Returns key calendar 
details such as calendar ID, summary, visibility, and whether it is the primary 
calendar.

---

**Example:**
**Sample Input:**
    list_calendars(
        max_results=10,
        min_access_role="owner",
        show_deleted=False,
        show_hidden=True
    )

**Expected Output:**
    {
        "status": "success",
        "calendars": [
            {
                "calendar_id": "sample_calendar_id@group.calendar.google.com",
                "summary": "Sample Calendar",
                "hidden": False,
                "deleted": False,
                "primary": True
            },
            {
                "calendar_id": "sample_user@mail.com",
                "summary": "Personal Calendar",
                "hidden": True,
                "deleted": False,
                "primary": False
            }
        ]
    }

    **If no calendars are found, the response will include a message instead:**

    {
        "status": "success",
        "message": "No calendars found for this Google account"
    }
"""

UPDATE_CALENDAR_TOOL_DESCRIPTION = """
Updates metadata of a specified calendar in the authenticated user's Google 
Calendar account. Allows partial updates to the calendar's title (summary), 
description, location, and time zone. Validates provided time zone against 
standard IANA time zones.

---

**Example:**
**Sample Input:**
    update_calendar_metadata(
        calendar_id="sample_calendar_id@group.calendar.google.com",
        summary="Team Events",
        description="Calendar for tracking all team-related events",
        location="Bangalore, India",
        timezone="Asia/Kolkata"
    )

**Expected Output:**
    {
        "status": "success",
        "metadata": {
            "calendar_id": "sample_calendar_id@group.calendar.google.com",
            "summary": "Team Events",
            "description": "Calendar for tracking all team-related events",
            "location": "Bangalore, India",
            "timeZone": "Asia/Kolkata"
        }
    }
"""

DELETE_CALENDAR_TOOL_DESCRIPTION = """
Deletes a secondary calendar from the user's Google Calendar account. This tool 
first fetches calendar metadata to determine whether the calendar is the user's 
primary calendar. If it is, the deletion is blocked to prevent removing the 
primary calendar. Only secondary calendars can be deleted.

---

**Example:**
**Sample Input:**
    delete_calendar(calendar_id="sample_calendar_id")

**Expected Output:**
    {
        "status": "success",
        "message": "Calendar with ID 'sample_calendar_id' deleted successfully"
    }

    **If the calendar id corresponds to the Primary Calendar of the user:**

    {
        "status": "error",
        "message": "Cannot delete the user's primary calendar."
    }
"""

CLEAR_PRIMARY_CALENDAR_TOOL_DESCRIPTION = """
Clears all events from users primary Google Calendar. This tool does not delete 
the calendar itself but permanently removes all events associated with it. This 
includes both past and upcoming events. It is especially useful for resetting a 
calendar while retaining its metadata and sharing settings.

This operation is irreversible, and care should be taken before invoking it.

---

**Example:**
**Sample Input:**
    clear_calendar_events(calendar_id="sample_id")

**Expected Output:**
    {
        "status": "success",
        "message": "All events from calendar sample_id have been cleared."
    }
"""

GET_CALENDAR_TOOL_DESCRIPTION = """
Fetches metadata of a specified calendar from a user's Google Calendar account. 
This includes properties such as the calendar's summary (name), time zone, 
access control, and whether it is a primary or secondary calendar.

This tool is useful for inspecting calendar configuration before performing any 
read/write operations on it. It helps verify calendar ownership, access rights, 
and basic settings without modifying any data or events.

---

**Example:**
**Sample Input:**
    get_calendar(calendar_id="primary")

**Expected Output:**
    {
        "status": "success",
        "metadata": {
            "id": "primary",
            "summary": "My Calendar",
            "timeZone": "Asia/Kolkata",
            ...
        }
    }
"""

LIST_CALENDAR_EVENTS_TOOL_DESCRIPTION = """
Fetches a list of events from the specified calendar in the user's Google 
Calendar account.

This tool allows fine-grained filtering of events based on query text, time 
range, modification timestamp, attendee count, visibility of deleted/hidden 
invitations, and recurrence handling. Useful for applications that need to view 
upcoming or historical calendar events, perform keyword-based event search, or 
sync calendar data within a specific window.

You may optionally sort results and control the number of attendees and events 
returned. Supports both primary and secondary calendars.

---

**Example:**
**Sample Input:**
    list_calendar_events(
        calendar_id="primary",
        query="team sync",
        time_min="2025-08-01T00:00:00Z",
        show_deleted=False,
        single_events=True,
        order_by="startTime"
    )

**Expected Output:**
    {
        "status": "success",
        "events": [
            {
                "id": "sample_event_1",
                "summary": "Internal Team Sync",
                "start": { "dateTime": "2025-08-02T10:00:00+05:30" },
                "end": { "dateTime": "2025-08-02T11:00:00+05:30" },
                ...
            },
            ...
        ]
    }
"""

GET_EVENT_TOOL_DESCRIPTION = """
Fetches detailed metadata of a specific event from a user's Google Calendar.

This tool allows you to retrieve all available properties of a given event such 
as its summary, location, start and end times, recurrence rules, attendees, 
reminders, visibility, and more.

This tool is helpful for inspecting scheduled meetings, extracting event
details for processing or reporting, or verifying properties of an event before 
updating or deleting it.

If time_zone is provided and valid, the event timings in the response will be 
adjusted accordingly. Otherwise, the calendar's default time zone is used. You 
can also limit the number of attendees returned via the max_attendees parameter 
to avoid excessive payload.

---

**Example:**
**Sample Input:**
    get_event(
        calendar_id="primary",
        event_id="sample_event_id",
        max_attendees=50,
        time_zone="Asia/Kolkata"
    )

**Expected Output:**
    {
        "status": "success",
        "event": {
            "id": "sample_event_id",
            "summary": "Team Sync",
            "start": { "dateTime": "2025-08-10T10:00:00+05:30" },
            "end": { "dateTime": "2025-08-10T11:00:00+05:30" },
            "attendees": [...],
            "location": "Meeting Room 2",
            ...
        }
    }
"""

CREATE_EVENT_TOOL_DESCRIPTION = """
Creates a new event on a user's Google Calendar with full customization 
support. You can specify event details such as the title, description, 
location, start and end times (with time zones), recurrence rules, attendees, 
reminders, and more.

It also allows fine-grained control over visibility, transparency, and guest 
permissions like whether attendees can invite other guests or see each other.

This tool is useful for scheduling one-time or recurring events, setting up 
meetings, and automating calendar-based workflows.

---

**Example:**  
**Sample Input:**  
    create_event(
        calendar_id="primary",
        summary="Team Sync",
        description="Weekly team sync for project updates",
        location="Conference Room 3",
        start_time="2025-08-07T10:00:00+05:30",
        end_time="2025-08-07T11:00:00+05:30",
        attendees=["alice@example.com", "bob@example.com"],
        recurrence=["RRULE:FREQ=WEEKLY;BYDAY=TH"],
        visibility="default",
        transparency="opaque",
        guestsCanInviteOthers=True,
        guestsCanSeeOtherGuests=False
    )

**Expected Output:**  
    {
        "status": "success",
        "event": {
            "id": "sample_event_id",
            "summary": "Team Sync",
            "start": { "dateTime": "2025-08-07T10:00:00+05:30" },
            "end": { "dateTime": "2025-08-07T11:00:00+05:30" },
            "location": "Conference Room 3",
            ...
        }
    }
"""

UPDATE_EVENT_TOOL_DESCRIPTION = """
Updates an existing event on a user's Google Calendar with complete flexibility 
to modify its details. You can update the event's title, description, location, 
start and end times (with time zones), recurrence rules, attendees, reminders, 
and other properties.

This tool also allows changing visibility, transparency, and guest permissions, 
giving fine-grained control over how the updated event behaves.

This tool is useful for rescheduling meetings, changing participants, extending 
durations, or modifying recurring event patterns without creating a new event.

---

**Example:**  
**Sample Input:**  
    update_event(
        calendar_id="primary",
        event_id="sample_event_id",
        summary="Updated Team Sync",
        description="Extended weekly sync with additional discussion on tests",
        location="Conference Room 5",
        start_time="2025-08-07T10:30:00+05:30",
        end_time="2025-08-07T12:00:00+05:30",
        attendees=["alice@example.com", "bob@example.com", "cody@example.com"],
        guestsCanInviteOthers=True,
        guestsCanSeeOtherGuests=True
    )

**Expected Output:**  
    {
        "status": "success",
        "event": {
            "id": "sample_event_id",
            "summary": "Updated Team Sync",
            "start": { "dateTime": "2025-08-07T10:30:00+05:30" },
            "end": { "dateTime": "2025-08-07T12:00:00+05:30" },
            "location": "Conference Room 5",
            ...
        }
    }
"""

DELETE_EVENT_TOOL_DESCRIPTION = """
Deletes an existing event from a user's Google Calendar permanently. This tool 
requires the calendar ID and event ID to precisely target the event you want to 
remove. Once deleted, the event will no longer appear in the calendar, and 
attendees will receive cancellation notifications if applicable.

This tool is useful for removing any canceled meetings, outdated events, or 
erroneously created entries.

---

**Example:**  
**Sample Input:**  
    delete_event(
        calendar_id="primary",
        event_id="sample_event_id"
    )

**Expected Output:**  
    {
        "status": "success",
        "message": "Event 'sample_event_id' deleted from calendar 'primary'."
    }
"""

