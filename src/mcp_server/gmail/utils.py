import re
import logging
import functools
from datetime import datetime
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def handle_gmail_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HttpError as http_error:
            status = http_error.resp.status
            reason = http_error._get_reason()

            if status == 400:
                message = """Bad request. 
                Please check if required fields are valid."""

            elif status == 401:
                message = """Unauthorized access. 
                Check if the credentials are valid or expired."""

            elif status == 403:
                message = """Permission denied. 
                Ensure your OAuth scope includes gmail access and that the 
                authenticated user has permission to perform this action."""

            elif status == 404:
                message = """Resource not found. 
                The email or message may not exist or was deleted."""

            elif status == 409:
                message = """Conflict error. 
                This could be due to duplicate operations."""

            elif status == 410:
                message = """The resource is no longer available and no 
                forwarding address is known."""

            elif status == 412:
                message = """Precondition failed. 
                Try syncing again or verify versioning headers like etag."""

            elif status == 429:
                message = """Quota exceeded. Too many requests.
                Try again later or use exponential backoff."""

            elif status in [500, 503]:
                message = """Gmail service is temporarily unavailable. 
                Please retry after some time."""

            else:
                message = f"Unexpected error with Gmail API: {reason}"

            logger.error(f"[Status Code {status}]: {message}", exc_info=True)

            return {"status": "error", "message": message}

        except Exception as error:
            logger.error("An unexpected error occured", exc_info=True)

            return {
                "status": "error",
                "message": f"An unexpected error occurred: {error}",
            }

    return wrapper


def is_valid_email(email: str) -> bool:
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

    return bool(EMAIL_REGEX.match(email))