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

import uuid
import asyncio
import logging
from pydantic import Field
from pytz import all_timezones_set
from typing import Annotated, Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

import schema
from auth import async_init_google_calendar_service
from utils import (
    handle_google_calendar_exceptions, 
    is_valid_email,
    validate_rfc3339_timestamp,
    is_rfc3339_start_time_before_end_time
)

logger = logging.getLogger(__name__)


mcp = FastMCP(
    "Google Calendar MCP Server",
    description="""
    The Google Calendar MCP server offers a comprehensive set of tools for 
    managing calendars and events within a user's Google Calendar account.""",
    version="0.1.1",
    instructions=schema.GOOGLE_CALENDAR_MCP_SERVER_INSTRUCTIONS,
    settings={
        "initialization_timeout": 1200.0
    }
)


@mcp.tool(
    title="List Calendars",
    description=schema.LIST_CALENDARS_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def list_calendars(
    max_results: Annotated[
        int,
        Field(description="Maximum number of entries per page.", ge=1, le=250)
    ],
    min_access_role: Annotated[
        Optional[schema.CALENDAR_ACCESS_ROLES],
        Field(description="Minimum access role for user in returned entries.")
    ] = None,
    show_deleted: Annotated[
        Optional[bool],
        Field(description="Whether to include deleted calendar list entries.")
    ] = None,
    show_hidden: Annotated[
        Optional[bool],
        Field(description="Whether to include hidden calendar list entries.")
    ] = None,
) -> Dict[str, Union[str, List[Dict[str, Union[str, bool]]]]]:
    """
    Tool to list the calendars in an authenticated user's Google Calendar based 
    on access level, visibility, and deletion status.

    This tool handles authentication using OAuth2 and uses the Google Calendar 
    API to retrieve the list of calendars available with the user. It supports 
    optional filters such as minimum access level, inclusion of deleted 
    calendars, and visibility of hidden calendars.

    Args:
        max_results (Optional[int]): Maximum number of calendars to retrieve.
            - Must be greater than or equal to 1, or less than or equal to 250.
            - Defaults to 5 internally, if not provided.
            - Example: 10
        min_access_role (Optional[str]): Minimum access level a user must have.
            - If not provided, defaults to 'None' i.e. no restriction.
            - Valid values: "freeBusyReader", "owner", "reader", "writer"
            - Example: "reader"
        show_deleted (Optional[bool]): Whether to include deleted calendars.
            - Example: True
        show_hidden (Optional[bool]): Whether to include hidden calendars.
            - Example: False

    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, bool]]]]]: A dictionary 
            containing:
            - 'status' (str): "success", "not_found", or "error"
            On success:
            - 'calendars' (List[Dict]): List of calendar entries with fields:
                - 'calendar_id' (str): Unique identifier of the calendar
                - 'summary' (str): Title of the calendar
                - 'hidden' (bool): Whether the calendar is hidden
                - 'deleted' (bool): Whether the calendar is deleted
                - 'primary' (bool): Whether calendar is user's primary calendar
            If not_found:
            - 'message' (str): Message indicating no calendars were found
            On failure:
            - 'message' (str): Description of the error
    """
    CALENDAR_ACCESS_ROLES = ["freeBusyReader", "owner", "reader", "writer"]

    if min_access_role and min_access_role not in CALENDAR_ACCESS_ROLES:
        return {
            "status": "error",
            "message": f"Invalid calendar access role: {min_access_role}"
        }

    service = await async_init_google_calendar_service()

    response = await asyncio.to_thread(
        lambda: service.calendarList().list(
            minAccessRole=min_access_role,
            maxResults=max_results,
            showDeleted=show_deleted,
            showHidden=show_hidden
        ).execute()
    )

    items = response.get("items", [])

    if not items:
        return {
            "status": "not_found",
            "message": "No calendars found for this Google account"
        }

    calendars = []

    for calendar in items:
        calendars.append({
            "calendar_id": calendar.get("id", ""),
            "summary": calendar.get("summary", ""),
            "primary": calendar.get("primary", False),
            "hidden": calendar.get("hidden", False),
            "deleted": calendar.get("deleted", False)
        })

    return {
        "status": "success", 
        "calendars": calendars
    }


@mcp.tool(
    title="Create Calendar",
    description=schema.CREATE_CALENDAR_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def create_calendar(
    summary: Annotated[
        str,
        Field(description="Name/title of the calendar to be created.")
    ],
    description: Annotated[
        Optional[str],
        Field(description="Optional description of the calendar.")
    ] = None,
    time_zone: Annotated[
        Optional[str],
        Field(description="Optional time zone of the calendar (e.g., 'UTC').")
    ] = None,
    location: Annotated[
        Optional[str],
        Field(description="Optional geographic location of the calendar.")
    ] = None,
) -> Dict[str, str]:
    """
    Tool to create a new secondary calendar in the user's Google Calendar.

    This tool creates a new secondary calendar with specified title, time zone, 
    and description. It uses the Google Calendar API to create a new secondary 
    calendar. If no time zone is provided, it defaults to 'UTC'.

    Args:
        summary (str): Title of the calendar to be created.
            - Example: "Team Meetings"
        description (Optional[str]): Description or notes about the calendar.
            - Example: "Calendar for weekly syncs"
        time_zone (Optional[str]): IANA time zone for the calendar.
            - If not provided, defaults to 'UTC'.
            - Example: "Asia/Kolkata"
        location (Optional[str]): Geographic location of the calendar.
            - Example: "New York"

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'id' (str): Unique identifier of the created calendar
            - 'summary' (str): Title of the calendar
            - 'timeZone' (str): IANA time zone of the calendar
            - 'calendar_url' (str): Direct link to view the calendar in web UI
            On failure:
            - 'message' (str): Description of the error
    """
    if not summary or not summary.strip():
        return {
            "status": "error", 
            "message": "Calendar summary cannot be empty."
        }

    if time_zone:
        time_zone = time_zone.strip()

        if time_zone not in all_timezones_set:
            return {
                "status": "error",
                "message": (
                    f"Invalid time zone: '{time_zone}'."
                    "Please provide a valid IANA time zone (e.g. Asia/Kolkata)"
                )
            }
    else:
        time_zone = "UTC"
    
    calendar_body = {
        "summary": summary.strip(), 
        "timeZone": time_zone
    }

    if description and description.strip():
        calendar_body["description"] = description.strip()

    if location and location.strip():
        calendar_body["location"] = location.strip()

    service = await async_init_google_calendar_service()

    calendar = await asyncio.to_thread(
        lambda: service.calendars().insert(
            body=calendar_body
        ).execute()
    )

    cid = calendar['id']
    calendar_url =f"https://calendar.google.com/calendar/u/0/r?cid={cid}"

    return {
        "status": "success",
        "id": calendar.get("id", "unavailable"),
        "summary": calendar.get("summary", "unavailable"),
        "timeZone": calendar.get("timeZone", "unavailable"),
        "calendar_url": calendar_url
    }


@mcp.tool(
    title="Get Calendar",
    description=schema.GET_CALENDAR_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def get_calendar(
    calendar_id: Annotated[
        str,
        Field(description="Unique ID of the calendar to retrieve metadata for")
    ]
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to fetch metadata of a calendar from a user's Google Calendar account.

    This tool retrieves details such as calendar name, time zone, access roles, 
    and other settings associated with the specified calendar.It is useful for 
    retrieving calendar configuration details without accessing or modifying 
    any of its events. Can be used to verify calendar existence, inspect 
    ownership, or confirm properties before performing further actions.

    Args:
        calendar_id (str): ID of the primary calendar to retrieve metadata for.
            - Example: "sample_calendar@group.calendar.google.com"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success", "error", or "not_found".
            On success:
            - 'metadata' (dict, optional): Calendar metadata if found.
            On failure/not found:
            - 'message' (str, optional): Additional details or error messages.
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    service = await async_init_google_calendar_service()

    calendar_metadata = await asyncio.to_thread(
        lambda: service.calendars().get(
            calendarId=calendar_id
        ).execute()
    )

    if calendar_metadata:
        return {
            "status": "success", 
            "metadata": calendar_metadata
        }

    return {
        "status": "not_found", 
        "message": f"No metadata found for calendar with id '{calendar_id}'."
    }


@mcp.tool(
    title="Update Calendar",
    description=schema.UPDATE_CALENDAR_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def update_calendar(
    calendar_id: Annotated[
        str,
        Field(description="Unique ID of the calendar to update.")
    ],
    summary: Annotated[
        Optional[str],
        Field(description="New title/name of the calendar.")
    ] = None,
    description: Annotated[
        Optional[str],
        Field(description="New description of the calendar.")
    ] = None,
    location: Annotated[
        Optional[str],
        Field(description="New geographic location of the calendar.")
    ] = None,
    timezone: Annotated[
        Optional[str],
        Field(description="New time zone of the calendar.")
    ] = None,
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Tool to update an existing Calendar on user's Google Calendar account.

    This tool allows modification of a calendar's title, description, location, 
    and time zone using the Google Calendar API. Only the fields provided will 
    be patched. To clear out a field, pass an empty string for that parameter. 
    If no field is provided for updated, the update request is rejected. The 
    `Summary` field can not be empty.

    Args:
        calendar_id (str): The unique identifier of the calendar to be updated.
            - Example: "sample_calendar_id@group.calendar.google.com"
        summary (Optional[str]): New title/name of the calendar.
            - Example: "Team Sync Schedule"
        description (Optional[str]): New description of the calendar.
            - Example: "Used for daily sync-up meetings."
        location (Optional[str]): New geographic location of the calendar.
            - Example: "Bangalore"
        timezone (Optional[str]): New time zone (must be a valid IANA zone).
            - Example: "Asia/Kolkata"

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            - On success:
                - 'metadata' (Dict): Dictionary with updated calendar fields.
            - On failure:
                - 'message' (str): Description of the error

    """
    if not any([summary, description, location, timezone]):
        return {
            "status": "error",
            "message": "No fields provided to update the calendar."
        }

    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    calendar_id = calendar_id.strip()
    calendar_body = {}

    if summary is not None:
        if summary.strip() == "":
            return {
                "status": "error", 
                "message": "Summary cannot be empty."
            }
        
        calendar_body["summary"] = summary
    
    if description is not None:
        calendar_body["description"] = description
    
    if location is not None:
        calendar_body["location"] = location

    if timezone:
        timezone = timezone.strip()

        if timezone not in all_timezones_set:
            return {
                "status": "error",
                "message": (
                    f"Invalid time zone: '{timezone}'."
                    "Please provide a valid IANA time zone (e.g. Asia/Kolkata)"
                )
            }

        calendar_body["timeZone"] = timezone

    service = await async_init_google_calendar_service()

    updated_calendar = await asyncio.to_thread(
        lambda: service.calendars().patch(
            calendarId=calendar_id, 
            body=calendar_body
        ).execute()
    )

    return {
        "status": "success",
        "metadata": {
            "calendar_id": updated_calendar.get("id", ""),
            "summary": updated_calendar.get("summary", ""),
            "description": updated_calendar.get("description", ""),
            "location": updated_calendar.get("location", ""),
            "time_zone": updated_calendar.get("timeZone", "")
        }
    }


@mcp.tool(
    title="Delete Calendar",
    description=schema.DELETE_CALENDAR_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def delete_calendar(
    calendar_id: Annotated[
        str,
        Field(description="The ID of the calendar to delete.")
    ]
) -> Dict[str, str]:
    """
    Tool to delete a secondary calendar from a user's Google Calendar account.

    This tool removes an existing secondary calendar using the Google Calendar 
    API. Before deletion, it verifies whether the specified calendar is the 
    user's primary calendar. Primary calendar cannot be deleted via this method 
    to prevent accidental loss of core data. **Use with caution.**

    Args:
        calendar_id (str): Unique identifier of the calendar to be deleted
            - Example: "sample_calendar_id@group.calendar.google.com"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            - 'message' (str): Confirmation meassage, or reason for failure
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    service = await async_init_google_calendar_service()

    calendar = await asyncio.to_thread(
        lambda: service.calendars().get(
            calendarId=calendar_id
        ).execute()
    )

    if calendar.get("primary", False):
        return {
            "status": "error",
            "message": "Cannot delete the user's primary calendar."
        }

    await asyncio.to_thread(
        lambda: service.calendars().delete(
            calendarId=calendar_id
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Calendar with ID '{calendar_id}' deleted successfully."
    }


@mcp.tool(
    title="List Events",
    description=schema.LIST_CALENDAR_EVENTS_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def list_events(
    calendar_id: Annotated[
        str,
        Field(description="Unique ID of the calendar to retrieve events from.")
    ],
    query: Annotated[
        Optional[str],
        Field(description="Free text search terms to find events that match.")
    ] = None,
    max_results: Annotated[
        Optional[int],
        Field(description="Maximum number of events to return.", ge=1, le=250)
    ] = None,
    max_attendees: Annotated[
        Optional[int],
        Field(
            description="Maximum number of attendees to include in response.",
            ge=1, le=250
        )
    ] = None,
    show_hidden_invitations: Annotated[
        Optional[bool],
        Field(description="Whether to include hidden invitations in result.")
    ] = None,
    show_deleted: Annotated[
        Optional[bool],
        Field(description="Whether to include deleted events in result.")
    ] = None,
    time_min: Annotated[
        Optional[str],
        Field(description="Lower bound (RFC3339 timestamp) for event end time")
    ] = None,
    time_max: Annotated[
        Optional[str],
        Field(description="Upper bound (RFC3339 timestamp) for event end time")
    ] = None,
    time_zone: Annotated[
        Optional[str],
        Field(description="Time zone used in the response.")
    ] = None,
    updated_min: Annotated[
        Optional[str],
        Field(description="""Lower bound (RFC3339 timestamp) for an event's 
            last modification time.""")
    ] = None,
    single_events: Annotated[
        Optional[bool],
        Field(description="""Whether to expand recurring events into single 
            instances.""")
    ] = None,
    order_by: Annotated[
        Optional[schema.CALENDAR_EVENT_SORT_KEYS],
        Field(description="The order of the events returned in the results.")
    ] = None
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Tool to list events from a specified calendar in the user's Google Calendar 
    account.

    This tool retrieves a list of events based on specified filters such as the 
    updated time, start time, end time, search keyword, and result count. This 
    tool is useful for displaying calendar schedules, building custom views, 
    checking recent updates to calendar events, or syncing calendar data with 
    external systems.

    Args:
        calendar_id (str): Unique ID of the calendar to list events from
            - Example: "sample_id@group.calendar.google.com"
        query (Optional[str]): Free text search terms to find events that match
            - Example: "meeting" or "project update"
        max_results (Optional[int]): Maximum number of events to return
            - Range: 1 to 250. Defaults to 250 if not specified.
            - Example: 10
        max_attendees (int): Maximum number of attendees to include per event
            - Range: 1 to 250. Defaults to 250 if not specified.
            - Example: 50
        show_hidden_invitations (Optional[bool]): Include hidden invitations
            - Example: True
        show_deleted (Optional[bool]): Whether to include deleted events
            - Example: False
        time_min (Optional[str]): Fetch events starting after this time
            - Timestamp should be in RFC3339 format.
            - Example: "2023-09-30T12:43:45Z"
        time_max (Optional[str]): Fetch events starting before this time
            - Timestamp should be in RFC3339 format.
            - Example: "2023-09-30T23:59:59Z"
        time_zone (Optional[str]): Time zone used in the response.
            - Must be a valid IANA time zone. Defaults to calendar's time zone.
            - Example: "Asia/Kolkata"
        updated_min (Optional[str]): Fetch events updated after this time
            - Timestamp should be in RFC3339 format.
            - Example: "2023-09-30T00:00:00Z"
        single_events (Optional[bool]): Expand recurring event into single ones
            - Example: True
        order_by (Optional[str]): Order of the events returned in the results.
            - Can take any of the following values: "startTime", "updateTime"
            - Example: "startTime"

    Returns:
        Dict[str, Union[str, List[Dict[str, Any]]]]: A dictionary containing:
            - 'status' (str): "success", "error", or "not_found".
            On success:
            - 'events' (list): A list of events matching the criteria.
            - 'warning' (str, optional): Warning message if timezone is invalid
            On Failure/Not Found:
            - 'message' (str): Additional details or error messages.

    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    query = query.strip() if query and query.strip() else None

    if time_min and not validate_rfc3339_timestamp(time_min):
        return {
            "status": "error",
            "message": (
                f"Invalid time_min format: '{time_min}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if time_max and not validate_rfc3339_timestamp(time_max):
        return {
            "status": "error",
            "message": (
                f"Invalid time_max format: '{time_max}'. "
               "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if updated_min and not validate_rfc3339_timestamp(updated_min):
        return {
            "status": "error",
            "message": (
                f"The provided timestamp '{updated_min}' is not in a valid "
                "RFC3339 format. Defaults to calendar's configured timezone."
            )
        }

    service = await async_init_google_calendar_service()

    result = await asyncio.to_thread(
        lambda: service.events().list(
            calendarId=calendar_id,
            q=query,
            maxResults=max_results,
            maxAttendees=max_attendees,
            showHiddenInvitations=show_hidden_invitations,
            showDeleted=show_deleted,
            timeMin=time_min,
            timeMax=time_max,
            timeZone=time_zone if time_zone in all_timezones_set else None,
            updatedMin=updated_min,
            singleEvents=single_events,
            orderBy=order_by,
        ).execute()
    )

    if result:
        response = {
            "status": "success", 
            "events": result.get("items", [])
        }

        if time_zone and time_zone not in all_timezones_set:
            response['warning'] = (
                f"Passed invalid time zone: '{time_zone}'. "
                "Defaulted to calendar's configured timezone."
            )

        return response

    return {
        "status": "not_found",
        "message": f"No events found for calendar {calendar_id}."
    }


@mcp.tool(
    title="Get Event",
    description=schema.GET_EVENT_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def get_event(
    calendar_id: Annotated[
        str,
        Field(description="Unique ID of the calendar containing the event.")
    ],
    event_id: Annotated[
        str,
        Field(description="Unique ID of the event to retrieve.")
    ],
    max_attendees: Annotated[
        Optional[int],
        Field(description="Max. number of attendees to include.", ge=1, le=250)
    ] = None,
    time_zone: Annotated[
        Optional[str],
        Field(description="Time zone to be used in the response.")
    ] = None
) -> Dict[str, Any]:
    """
    Tool to fetch the details of a specific event from a users Google Calendar.

    This tool retrieves comprehensive metadata of a calendar event such as its 
    summary, location, description, attendees, time zone, recurrence rules, 
    reminders, and more. The event must exist on the specified calendar.

    Args:
        calendar_id (str): Unique ID of the calendar containing the event
            - Example: "sample_calendar_id@group.calendar.google.com"
        event_id (str): Unique identifier of the event to be fetched
            - Example: "sample_event_id"
        max_attendees (Optional[int]): Maximum number of attendees to include
            - Valid Range: 1 to 250. Defaults to 250 if not specified
            - Example: 50
        time_zone (Optional[str]): Time zone to apply to the response
            - If unspecified or invalid, defaults to the calendar's time zone
            - Example: "Asia/Kolkata"

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'status' (str): "success", "error", or "not_found"
            On success:
            - 'event' (dict): Complete event metadata if found
            - 'warning' (str, optional): Warning message if timezone is invalid
            On failure/not found:
            - 'message' (str): Any relevant messages or error info
    """
    if not calendar_id or not calendar_id.strip(): 
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    if not event_id or not event_id.strip():
        return {
            "status": "error", 
            "message": "Event ID cannot be empty."
        }

    service = await async_init_google_calendar_service()

    event = await asyncio.to_thread(
        lambda: service.events().get(
            calendarId=calendar_id, 
            eventId=event_id,  
            timeZone=time_zone if time_zone in all_timezones_set else None,
            maxAttendees=max_attendees
        ).execute()
    )

    if not event:
        return {
            "status": "not_found",
            "message": f"No event found with ID {event_id} in {calendar_id}."
        }

    response = {
        "status": "success", 
        "event": event
    }

    if time_zone and time_zone not in all_timezones_set:
        response['warning'] = (
            f"Passed invalid time zone: '{time_zone}'. "
            "Defaulted to calendar's configured timezone."
        )

    return response


@mcp.tool(
    title="Create Event",
    description=schema.CREATE_EVENT_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def create_event(
    calendar_id: Annotated[
        str,
        Field(description="ID of the calendar where event should be created.")
    ],
    summary: Annotated[
        str,
        Field(description="The title or subject of the event.")
    ],
    start_time: Annotated[
        str,
        Field(description="The start time of the event in RFC3339 format.")
    ],
    end_time: Annotated[
        str,
        Field(description="The end time of the event in RFC3339 format.")
    ],
    time_zone: Annotated[
        Optional[str],
        Field(description="The time zone of the event.")
    ] = None,
    description: Annotated[
        Optional[str],
        Field(description="Detailed description or notes about the event.")
    ] = None,
    location: Annotated[
        Optional[str],
        Field(description="The geographical location where the event is held.")
    ] = None,
    add_google_meet_link: Annotated[
        Optional[bool],
        Field(description="Whether to add a Google Meet link to the event.")
    ] = None,
    attendees: Annotated[
        Optional[List[str]],
        Field(description="The list of attendee email addresses.")
    ] = None,
    recurrence: Annotated[
        Optional[List[str]],
        Field(description='Recurrence rules as specified in RFC5545 format.')
    ] = None,
    visibility: Annotated[
        Optional[schema.CALENDAR_EVENT_VISIBILITY],
        Field(description="The visibility of the event in the calendar.")
    ] = None,
    guests_can_invite_others: Annotated[
        Optional[bool],
        Field(description="Whether attendees can invite others to the event.")
    ] = None,
    guests_can_see_other_guests: Annotated[
        Optional[bool],
        Field(description="Whether attendees can see each other.")
    ] = None,
    transparency: Annotated[
        Optional[schema.CALENDAR_EVENT_TRANSPARENCY],
        Field(description="Whether the event blocks calendar time.")
    ] = None,
    send_updates: Annotated[
        Optional[schema.CALENDAR_EVENT_SEND_UPDATES],
        Field(description="Whether to send updates to attendees.")
    ] = None,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to create a new event in the user's Google Calendar account.

    This tool allows users to schedule an event with customizable metadata such 
    as summary, location, description, timing, attendees, and visibility 
    settings. It also supports options for specifying whether guests can invite 
    others or view each other, as well as the transparency level of the event 
    (whether it blocks calendar time or not).

    Args:
        calendar_id (str): ID of the calendar where the event will be created
            - Example: "sample_calendar_id@group.calendar.google.com"
        summary (str): Title or the subject of the Google calendar event
            - Example: "Team Sync Meeting"
        start_time (str): Start timestamp of the event in valid RFC3339 format
            - Example: "2025-08-10T10:00:00+05:30"
        end_time (str): End timestamp of the event in valid RFC3339 format
            - Example: "2025-08-10T11:00:00+05:30"
        time_zone (Optional[str]): Time zone to apply to the start and end time
            - If invalid or unspecified, defaults to UTC
            - Example: "Asia/Kolkata"
        description (Optional[str]): Additional details or agenda for the event
            - Example: "Monthly planning and retrospective"
        location (Optional[str]): Physical or virtual location of the event
            - Example: "Conference Room A"
        add_google_meet_link (Optional[bool]): Whether to add Google Meet link
            - Example: True
        attendees (Optional[List[str]]): List of attendee email addresses
            - Invalid emails are ignored with a warning
            - Example: ["alice@example.com", "john@example.com"]
        recurrence (Optional[List[str]]): Event recurrence rules
            - Format should be as specified in RFC5545
            - DTSTART and DTEND lines are not allowed in this field.
            - Example: ["RRULE:FREQ=DAILY;COUNT=2"]
        visibility (Optional[str]): Visibility of the event in the calendar
            - Possible values: "default", "public", "private", "confidential"
            - Defaults to "default"
            - Example: "public"
        guests_can_invite_others (Optional[bool]): If guests can invite others
            - Example: True
        guests_can_see_other_guests (Optional[bool]): If guests can see others
            - Example: False
        transparency (Optional[str]): Whether the event blocks calendar time
            - Possible values: "transparent", "opaque"
            - "opaque" blocks time; "transparent" does not. Defaults to opaque.
            - Example: "opaque"
        send_updates (Optional[str]): Controls the update notification behavior
            - Possible values: "all", "externalOnly", "none"; Defaults to "none"
            - Example: "all"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            - On success:
                - 'event' (str): Details of the created event
                - 'warning' (str, optional): Warning if invalid values found
            - On failure:
                - 'message' (str): Error message or explanation
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }
    
    if not summary or not summary.strip():
        return {
            "status": "error", 
            "message": "Event summary cannot be empty."
        }

    if start_time and not validate_rfc3339_timestamp(start_time):
        return {
            "status": "error",
            "message": (
                f"Invalid start_time format: '{start_time}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if end_time and not validate_rfc3339_timestamp(end_time):
        return {
            "status": "error",
            "message": (
                f"Invalid end_time format: '{end_time}'. "
                "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
            )
        }

    if not is_rfc3339_start_time_before_end_time(
        start=start_time, end=end_time
    ):
        return {
            "status": "error",
            "message": "start_time must be before end_time."
        }

    time_zone = (time_zone or "UTC").strip()
    time_zone = time_zone if time_zone in all_timezones_set else "UTC"

    send_updates = "none" if not send_updates else send_updates.strip()
    transparency = "opaque" if not transparency else transparency.strip()
    visibility = "default" if not visibility else visibility.strip()

    event_body = {
        "summary": summary.strip(),
        "location": location,
        "start": {
            "dateTime": start_time, 
            "timeZone": time_zone
        },
        "end": {
            "dateTime": end_time, 
            "timeZone": time_zone
        },
        "visibility": visibility,
        "guestsCanInviteOthers": guests_can_invite_others,
        "transparency": transparency,
        "guestsCanSeeOtherGuests": guests_can_see_other_guests,
        "conferenceDataVersion": 1
    }

    if description:
        event_body["description"] = description.strip()

    if recurrence:
        event_body["recurrence"] = recurrence

    invalid_attendees = []

    if attendees:
        valid_attendees = []

        for email in attendees:
            if is_valid_email(email):
                valid_attendees.append({"email": email})
            else:
                invalid_attendees.append(email)

        if valid_attendees:
            event_body["attendees"] = valid_attendees

    if add_google_meet_link:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                }
            }
        }

    service = await async_init_google_calendar_service()

    event = await asyncio.to_thread(
        lambda: service.events().insert(
            calendarId=calendar_id.strip(),
            body=event_body,
            sendUpdates=send_updates,
            conferenceDataVersion=1
        ).execute()
    )

    response = {
        "status": "success", 
        "event": event
    }

    if invalid_attendees:
        response['warning'] = "Invalid attendee emails: " + ", ".join(
            invalid_attendees
        )

    return response


@mcp.tool(
    title="Update Event",
    description=schema.UPDATE_EVENT_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def update_event(
    calendar_id: Annotated[
        str,
        Field(description="The ID of the calendar where the event is stored.")
    ],
    event_id: Annotated[
        str,
        Field(description="ID of the event on Google Calendar to be updated.")
    ],
    summary: Annotated[
        Optional[str],
        Field(description="The title or subject of the event.")
    ] = None,
    description: Annotated[
        Optional[str],
        Field(description="Detailed description or notes about the event.")
    ] = None,
    location: Annotated[
        Optional[str],
        Field(description="The geographical location where the event is held.")
    ] = None,
    start_time: Annotated[
        Optional[str],
        Field(description="The start time of the event in RFC3339 format.")
    ] = None,
    end_time: Annotated[
        Optional[str],
        Field(description="The end time of the event in RFC3339 format.")
    ] = None,
    time_zone: Annotated[
        Optional[str],
        Field(description="The time zone of the event.")
    ] = None,
    recurrence: Annotated[
        Optional[List[str]],
        Field(description='Recurrence rules as specified in RFC5545 format.')
    ] = None,
    visibility: Annotated[
        Optional[schema.CALENDAR_EVENT_VISIBILITY],
        Field(description="The visibility of the event in the calendar.")
    ] = None,
    transparency: Annotated[
        Optional[schema.CALENDAR_EVENT_TRANSPARENCY],
        Field(description="Whether the event blocks calendar time.")
    ] = None,
    guests_can_invite_others: Annotated[
        Optional[bool],
        Field(description="Whether attendees can invite others to the event.")
    ] = None,
    guests_can_see_other_guests: Annotated[
        Optional[bool],
        Field(description="Whether attendees can see each other.")
    ] = None,
    send_updates: Annotated[
        Optional[schema.CALENDAR_EVENT_SEND_UPDATES],
        Field(description="Whether to send update notification to attendees.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to update an existing event in the user's Google Calendar account.

    This tool allows modification of an event's metadata such as its summary, 
    location, description, timing, recurrence rules and visibility settings etc.
    Partial updates are supported, i.e. only the fields that are changed will 
    be updated. However, when modifying the start or end time, both fields must 
    be provided together in valid RFC3339 format.To clear out a field, pass an 
    empty string for that parameter. If no field is provided for updating, the 
    update request is rejected. `Summary` can not be empty.

    Args:
        calendar_id (str): Unique ID of the calendar where the event is stored.
            - Example: "sample_calendar_id@group.calendar.google.com"
        event_id (str): Unique identifier of the event to update.
            - Example: "sample_event_id"
        summary (str): Title or the subject of the Google calendar event
            - Example: "Team Sync Meeting"
        description (Optional[str]): Additional details or agenda for the event
            - Example: "Monthly planning and retrospective"
        location (Optional[str]): Physical or virtual location of the event
            - Example: "Conference Room A"
        start_time (str): Start timestamp of the event in valid RFC3339 format
            - Example: "2025-08-10T10:00:00+05:30"
        end_time (str): End timestamp of the event in valid RFC3339 format.
            - Example: "2025-08-10T11:00:00+05:30"
        time_zone (Optional[str]): Time zone to apply to the start and end time
            - If unspecified, defaults to the calendar's time zone.
            - Example: "Asia/Kolkata"
        recurrence (Optional[List[str]]): Event recurrence rules
            - Format should be as specified in RFC5545
            - DTSTART and DTEND lines are not allowed in this field.
            - Example: ["RRULE:FREQ=DAILY;COUNT=2"]
        visibility (Optional[str]): Visibility of the event in the calendar
            - Possible values: "default", "public", "private", "confidential"
            - Example: "public"
        transparency (Optional[str]): Whether the event blocks calendar time
            - Possible values: "transparent", "opaque"
            - "opaque" blocks time; "transparent" does not. Defaults to opaque
        guests_can_invite_others (Optional[bool]): If guests can invite others
            - Example: True
        guests_can_see_other_guests (Optional[bool]): If guests can see others
            - Example: False
        send_updates (Optional[str]): Controls the notification behavior.
            - Possible values: "all", "externalOnly", "none"
            - Example: "all"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            - On success:
                - 'event' (dict): Updated event details from Google Calendar
                - 'warning' (str, optional): Warning if invalid timezone found
            - On failure:
                - 'message' (str): Error message or explanation
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    if not event_id or not event_id.strip():
        return {
            "status": "error", 
            "message": "Event ID cannot be empty."
        }

    event_body = {}

    if summary is not None:
        if summary.strip() == "":
            return {
                "status": "error", 
                "message": "Summary cannot be empty."
            }

        event_body["summary"] = summary

    if description is not None:
        event_body["description"] = description

    if location is not None:
        event_body["location"] = location
    
    service = await async_init_google_calendar_service()

    event = await asyncio.to_thread(
        lambda: service.events().get(
            calendarId=calendar_id, 
            eventId=event_id,
        ).execute()
    )

    start_time_tz = event.get("start", {}).get("timeZone", "")
    end_time_tz = event.get("end", {}).get("timeZone", "")

    if (start_time and not end_time) or (end_time and not start_time):
        return {
            "status": "error",
            "message": "Both start_time and end_time must be provided together."
        }

    bad_timezone = False

    if start_time:
        if not validate_rfc3339_timestamp(start_time):
            return {
                "status": "error",
                "message": (
                    f"Invalid start_time format: '{start_time}'. "
                    "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
                )
            }

        if time_zone and time_zone.strip() in all_timezones_set:
            updated_start_time_zone = time_zone.strip()
        else:
            if len(start_time_tz.strip()) < 1:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid time_zone provided: {time_zone}."
                        "Default timezone for start_time could not be resolved."
                    )
                }
            
            bad_timezone = True
            updated_start_time_zone = start_time_tz

        event_body["start"] = {
            "dateTime": start_time,
            "timeZone": updated_start_time_zone
        }

    if end_time:
        if not validate_rfc3339_timestamp(end_time):
            return {
                "status": "error",
                "message": (
                    f"Invalid end_time format: '{end_time}'. "
                    "Expected RFC3339 format (e.g., 2023-10-01T12:00:00Z)."
                )
            }

        if time_zone and time_zone.strip() in all_timezones_set:
            updated_end_time_zone = time_zone.strip()
        else:
            if len(end_time_tz.strip()) < 1:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid time_zone provided: {time_zone}."
                        "Default timezone for end_time could not be resolved."
                    )
                }

            bad_timezone = True
            updated_end_time_zone = end_time_tz

        event_body["end"] = {
            "dateTime": end_time,
            "timeZone": updated_end_time_zone
        }

    if recurrence:
        event_body["recurrence"] = recurrence

    if visibility:
        event_body["visibility"] = visibility

    if transparency:
        event_body["transparency"] = transparency

    if guests_can_invite_others is not None:
        event_body["guestsCanInviteOthers"] = guests_can_invite_others

    if guests_can_see_other_guests is not None:
        event_body["guestsCanSeeOtherGuests"] = guests_can_see_other_guests

    if not event_body:
        return {
            "status": "error",
            "message": "No fields provided to update the event."
        }

    updated_event = await asyncio.to_thread(
        lambda: service.events().patch(
            calendarId=calendar_id.strip(),
            eventId=event_id.strip(),
            body=event_body,
            sendUpdates=send_updates,
            conferenceDataVersion=1
        ).execute()
    )

    response = {
        "status": "success", 
        "event": updated_event
    }

    if bad_timezone:
        response['warning'] = (
            "Invalid time zone provided. "
            "Defaulted to the event's original time zone."
        )

    return response


@mcp.tool(
    title="Delete Event",
    description=schema.DELETE_EVENT_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def delete_event(
    calendar_id: Annotated[
        str,
        Field(description="The ID of the calendar where the event is stored.")
    ],
    event_id: Annotated[
        str,
        Field(description="ID of the event on Google Calendar to be deleted.")
    ],
    send_updates: Annotated[
        Optional[schema.CALENDAR_EVENT_SEND_UPDATES],
        Field(description="Whether to send update notification to attendees.")
    ] = None,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Deletes an event from a user's specified Google Calendar account.

    This function removes an event identified by its event_id from the calendar
    specified by calendar_id. Optional notifications can be sent to all or some 
    attendees informing them about the deletion.

    Parameters:
        calendar_id (str): The ID of the calendar where the event is stored
            - Example: "primary"
        event_id (str): The unique identifier of the event to be deleted
            - Example: "abc123xyz"
        send_updates (str): Whether to notify attendees about the deletion
            - "all" to notify all attendees
            - "externalOnly" to notify only external attendees
            - "none" to not send any notifications

    Returns:
        dict: A dictionary containing:
            - "status" (str): "success" if deletion successful, else "error"
            - "message" (str): Descriptive message about the operation outcome
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    if not event_id or not event_id.strip():
        return {
            "status": "error", 
            "message": "Event ID cannot be empty."
        }

    send_updates = (send_updates or "none").strip()

    service = await async_init_google_calendar_service()

    await asyncio.to_thread(
        lambda: service.events().delete(
            calendarId=calendar_id.strip(),
            eventId=event_id.strip(),
            sendUpdates=send_updates
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Event '{event_id}' deleted from calendar '{calendar_id}'."
    }


@mcp.tool(
    title="Clear Primary Calendar.",
    description=schema.CLEAR_PRIMARY_CALENDAR_TOOL_DESCRIPTION
)
@handle_google_calendar_exceptions
async def clear_primary_calendar(
    calendar_id: Annotated[
        str,
        Field(description="Unique ID of the calendar to clear all events from")
    ]
) -> Dict[str, str]:
    """
    Tool to clear all events from a user's primary Calendar. This tool does not
    delete the calendar itself, only the events within it.

    This tool deletes all events from a user's primary calendar. This operation 
    can't be undone and affects all future and past events within the calendar. 
    It is useful for resetting the primary calendar.

    Args:
        calendar_id (str): The unique identifier of the calendar to clear.
            - Example: "sample_calendar_id"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error".
            - 'message' (str): Description of the result or reason for failure.        
    """
    if not calendar_id or not calendar_id.strip():
        return {
            "status": "error", 
            "message": "Calendar ID cannot be empty."
        }

    service = await async_init_google_calendar_service()

    calendar = await asyncio.to_thread(
        lambda: service.calendars().get(
            calendarId=calendar_id
        ).execute()
    )

    if not calendar.get("primary", False):
        return {
            "status": "error",
            "message": (
                "Cannot clear secondary calendar. "
                "Only the primary calendar can be cleared."
            )
        }

    await asyncio.to_thread(
        lambda: service.calendars().clear(
            calendarId=calendar_id
        ).execute()
    )

    return {
        "status": "success",
        "message": f"All events from calendar {calendar_id} have been cleared."
    }


if __name__ == "__main__":
    TRANSPORT_PROTOCOL = 'stdio'
    logger.info(
        f"Starting Google Calendar MCP server with {TRANSPORT_PROTOCOL} "
        "transport"
    )
    
    mcp.run(transport=TRANSPORT_PROTOCOL)
