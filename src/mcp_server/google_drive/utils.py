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
import functools
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def handle_google_drive_exceptions(func):
    """
    A decorator to handle common Google Drive API errors and other exceptions
    for MCP tool functions. It standardizes the error response format.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HttpError as http_error:
            status = http_error.resp.status
            reason = http_error._get_reason()
            
            if status == 400:
                message = "Invalid request or file metadata might be incorrect"

            elif status == 403:
                message = """Permission denied. You may not have access to the 
                requested resource or action."""
            
            elif status == 404:
                message = """The requested file or folder was not found. It may 
                have been deleted."""
            
            elif status in [500, 503]:
                message = """Google Drive service is temporarily unavailable. 
                Please try again later."""
            
            else:
                message = f"Unexpected error with Drive API: {reason}"

            logger.error(f"[Status Code {status}]: {message}", exc_info=True)

            return {"status": "error", "message": message}

        except Exception as error:
            logger.error("An unexpected error occured", exc_info=True)

            return {
                'status': 'error', 
                'message': f"An unexpected error occurred: {error}", 
            }
    
    return wrapper
