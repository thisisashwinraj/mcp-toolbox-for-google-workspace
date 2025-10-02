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

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


RFC3339_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

def validate_rfc3339_timestamp(value: str) -> bool:
    if not isinstance(value, str):
        return False

    return RFC3339_REGEX.match(value)


def handle_google_tasks_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HttpError as http_error:
            status = http_error.resp.status
            reason = http_error._get_reason()
            
            if status == 400:
                message = "Invalid request or file metadata might be incorrect"
            
            elif status == 401:
                message = (
                    "Unauthorized access. "
                    "Check if the credentials are valid or expired."
                )

            elif status == 403:
                message = (
                    "Permission denied. "
                    "Ensure your OAuth scope includes tasks access and that "
                    "authenticated user has permission to perform this action."
                )
            
            elif status == 404:
                message = (
                    "Resource not found. "
                    "The tasks or tasklists may not exist or was deleted."
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
                    "The Google Tasks service is temporarily unavailable. "
                    "Please retry after some time."
                )
            
            else:
                message = f"Unexpected error with the Tasks API: {reason}"

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
