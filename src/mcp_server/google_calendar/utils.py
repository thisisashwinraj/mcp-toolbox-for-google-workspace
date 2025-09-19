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

import re
import logging
import functools
from datetime import datetime
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


EMAIL_REGEX = re.compile(
        r"^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
        r"(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r'|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]'
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'
        r"@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
        r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        r"|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:"
        r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]"
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$', 
        re.IGNORECASE
    )

RFC3339_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False

    return bool(EMAIL_REGEX.match(email))

def validate_rfc3339_timestamp(value: str) -> bool:
    if not isinstance(value, str):
        return False

    return RFC3339_REGEX.match(value)

def is_rfc3339_start_time_before_end_time(start: str, end: str) -> bool:
    try:
        start_dt = datetime.fromisoformat(
            start.replace("Z", "+00:00")
        )

        end_dt = datetime.fromisoformat(
            end.replace("Z", "+00:00")
        )

        return start_dt < end_dt

    except ValueError:
        return False

def handle_google_calendar_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HttpError as http_error:
            status = http_error.resp.status
            reason = http_error._get_reason()

            if status == 400:
                message = (
                    "Bad request. Please check if required fields like "
                    "summary, time zone, or event timing are valid."
                )

            elif status == 401:
                message = (
                    "Unauthorized access. "
                    "Check if the credentials are valid or expired."
                )

            elif status == 403:
                message = (
                    "Permission denied. "
                    "Ensure your OAuth scope includes calendar access and that "
                    "authenticated user has permission to perform this action."
                )

            elif status == 404:
                message = (
                    "Resource not found. "
                    "The calendar or event may not exist or was deleted."
                )

            elif status == 409:
                message = (
                    "Conflict error. "
                    "This could be due to duplicate operations."
                )

            elif status == 410:
                message ="The resource is no longer available."

            elif status == 412:
                message = (
                    "Precondition failed. "
                    "Try syncing again or verify versioning headers."
                )

            elif status == 429:
                message = (
                    "Quota exceeded. Too many requests. "
                    "Try again later or use exponential backoff."
                )

            elif status in [500, 503]:
                message = (
                    "The Google Calendar service is temporarily unavailable. "
                    "Please retry after some time."
                )

            else:
                message = f"Unexpected error with the Calendar API: {reason}"

            logger.error(f"[Status Code {status}]: {message}", exc_info=True)

            return {
                "status": "error", 
                "message": message
            }

        except Exception as error:
            logger.error("An unexpected error occured", exc_info=True)

            return {
                "status": "error",
                "message": f"An unexpected error occurred: {error}",
            }

    return wrapper
