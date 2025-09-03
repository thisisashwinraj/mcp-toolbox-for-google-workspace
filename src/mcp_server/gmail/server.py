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
import base64
import asyncio
import logging
from pydantic import Field
from email.mime.text import MIMEText
from typing import Annotated, Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from auth import async_init_gmail
import registry
from utils import is_valid_email, handle_gmail_exceptions

logger = logging.getLogger(__name__)


mcp = FastMCP(
    "Gmail MCP Server",
    description="""
    The Gmail MCP server offers a comprehensive set of tools for managing 
    emails, drafts and profile information within the user's Gmail account.""",
    version="0.1.0",
    instructions=registry.GMAIL_MCP_SERVER_INSTRUCTIONS,
    settings={"initialization_timeout": 1200.0}
)


@mcp.tool(
    title="Get the user's profile information from their gmail account.",
    description=registry.GET_GMAIL_PROFILE_DESCRIPTION
)
@handle_gmail_exceptions
async def get_profile(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
) -> Dict[str, Union[str, Dict[str, Union[str, int]]]]:
    """
    Tool to retrieve the Gmail profile of a user.

    This tool fetches the profile details for a specified user using the Gmail
    API. If the special identifier 'me' is used, the profile of the 
    authenticated user is retrieved.

    Args:
        user_id (str): User ID of the profile to be retrieved.
            - Use "me" to fetch the profile of the authenticated user.
            - Must be a valid email format if not "me".
            - Example: "user@example.com"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success", "not_found" or "error"
            On success:
            - 'profile_information' (Dict[str, Any]): Dict with user's profile
            information, containing:
                - 'emailAddress' (str): User's primary email address.
                - 'messagesTotal' (int): Total number of messages.
                - 'threadsTotal' (int): Total number of conversation threads.
                - 'historyId' (str): ID of the last history record.
            If not_found:
            - 'message' (str): Message indicating no email message was found.
            On failure:
            - 'status' (str): "error"
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    service = await async_init_gmail()

    response = await asyncio.to_thread(
        lambda: service.users().getProfile(userId=user_id).execute()
    )

    if not response:
        return {
            "status": "not_found", 
            "message": f"Profile not found for user with id: `{user_id}`."
        }

    return {"status": "success", "profile_information": response}


@mcp.tool(
    title="List email messages from user's gmail account.",
    description=registry.LIST_GMAIL_MESSAGES_DESCRIPTION
)
@handle_gmail_exceptions
async def list_messages(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    query: Annotated[
        Optional[str],
        Field(description="Free text search terms to filter messages by.")
    ] = None,
    max_results: Annotated[
        Optional[int],
        Field(description="Maximum number of messages to return", ge=1, le=100)
    ] = None,
    include_spam_and_trash: Annotated[
        Optional[bool],
        Field(description="Whether to include messages from spam and trash.")
    ] = None
) -> Dict[str, Union[str, int, List[Dict[str, Any]], Dict[str, Any]]]:
    """
    Tool to list email messages from the user's gmail account.

    This tool fetches a list of message metadata for a specified user using the
    Gmail API based on specified filters such as the query (search term), label 
    IDs, and the maximum number of results to fetch.

    Args:
        user_id (str): User ID or email address.
            - Use "me" to fetch messages for the authenticated user.
            - Must be a valid email format if not "me".
            - Example: "user@example.com"
        max_results (Optional[int]): Maximum number of messages to return.
            - Example: 15
        include_spam_and_trash (Optional[bool]): Whether to include messages 
            from `SPAM` and `TRASH` in the results.
            - Example: True
        query (Optional[str]): Only return messages matching specified query.
            - Supports the same query format as Gmail's search box.
            - Example: 'from:user@example.com is:unread'

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'status' (str): "success", "not_found" or "error"
            On success:
            - 'email_messages' (List[Dict]): List of messages.
            If not_found:
            - 'message' (str): Message indicating no email messages were found.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}
    
    query = query.strip() if query else None

    service = await async_init_gmail()

    response = await asyncio.to_thread(
        lambda: service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=max_results,
            includeSpamTrash=include_spam_and_trash,
        ).execute()
    )

    messages = response.get("messages", [])

    if not messages:
        return {
            "status": "not_found", 
            "message": f"No messages found for user with id: '{user_id}'"
        }

    return {"status": "success", "email_messages": messages}


@mcp.tool(
    title="Get the specified message from user's gmail account.",
    description=registry.GET_EMAIL_MESSAGE_DESCRIPTION
)
@handle_gmail_exceptions
async def get_email_message(
    message_id: Annotated[
        str,
        Field(description="Unique ID of the Gmail message to retrieve.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    format: Annotated[
        Optional[registry.GMAIL_MESSAGE_FORMAT],
        Field(description="Format to return the message in.")
    ] = None,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to retrieve a specific Gmail message from the user's gmail account.

    This tool fetches the details of a Gmail message using the Gmail API. The 
    message is identified by its unique message ID. If the special identifier 
    'me' is used for `user_id`, the message is retrieved from the authenticated 
    user's mailbox.

    Args:
        message_id (str): Unique ID of the Gmail message to retrieve.
            - Example: "178fc3c89e1e2a4d"
        user_id (Optional[str]): Email ID of the profile to be retrieved.
            - Use "me" to fetch the profile of the authenticated user.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "user@example.com"
        format (Optional[str]): The format to return the message in.
            - Possible values are "full", "metadata", "minimal" and "raw". 
            - Example: "metadata"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success", "not_found" or "error"
            On success:
            - 'email_message' (Dict[str, Any]): User's email message resource.
            If not_found:
            - 'message' (str): Message indicating no email message was found.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not message_id.strip():
        return {"status": "error", "message": "Message Id cannot be empty."}

    service = await async_init_gmail()

    message = await asyncio.to_thread(
        lambda: service.users().messages().get(
            userId=user_id, id=message_id, format=format
        ).execute()
    )

    if not message:
        return {
            "status": "not_found", 
            "message": f"Message id: {message_id} not found for user {user_id}"
        }

    return {"status": "success", "email_message": message}


@mcp.tool(
    title="Send an email message.",
    description=registry.SEND_MESSAGE_DESCRIPTION
)
@handle_gmail_exceptions
async def send_message(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    to: Annotated[
        str,
        Field(description="Comma-separated recipient email address(es).")
    ],
    body: Annotated[
        str,
        Field(description="Content/body of the email message")
    ],
    subject: Annotated[
        Optional[str],
        Field(description="Subject line of the email.")
    ] = None,
    cc: Annotated[
        Optional[str],
        Field(description="Comma-separated CC recipient email address.")
    ] = None,
    bcc: Annotated[
        Optional[str],
        Field(description="Comma-separated BCC recipient email address.")
    ] = None,
    thread_id: Annotated[
        Optional[str],
        Field(description="Thread ID of the email this belongs to.")
    ] = None,
    in_reply_to: Annotated[
        Optional[str],
        Field(description="Message ID of the email this is replying to.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any], List[str]]]:
    """
    Tool to send an email using the user's Gmail account.

    This tool composes and sends a new Gmail message. The recipient, subject, 
    and body of the email must be provided, along with optional parameters such 
    as CC, BCC, and thread ID.

    Args:
        user_id (str): The sender's email address.
            - Use "me" to send from the authenticated user's account.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "sender@example.com"
        to (str): Comma-separated recipient email address(es)
            - Example: "user1@example.com, user2@example.com"
        body (str): Body content of the email in plain text or HTML.
            - Example: "Hi Team, Please find the attached report..."
        subject (Optional[str]): Subject line of the email.
            - Example: "Project Update - Q3 Report"
        cc (Optional[str]): Comma-separated CC recipients.
            - Example: "cc1@example.com, cc2@example.com"
        bcc (Optional[str]): Comma-separated BCC recipients.
            - Example: "hidden@example.com"
        thread_id (Optional[str]): Thread ID of the email this belongs to.
            - Example: "1234567890"
        in_reply_to (Optional[str]): ID of the email this is replying to.
            - Example: "9876543210"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Delivery confirmation message with `message ID`.
            - 'warning' (str, optional): Warning message if invalid email id(s) 
               were provided in CC or BCC.
            - 'invalid_emails_in_cc' (list): Invalid email ids in cc, if any.
            - 'invalid_emails_in_bcc' (list): Invalid email ids in bcc, if any.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if not to.strip():
        return {
            "status": "error",
            "message": "Recipient email id cannot be empty."
        }
    
    to = re.sub(r"[\(\)\[\]\{\}\<\>]", "", to)

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    valid_to = []

    for email in re.split(r",\s*", to):
        if not is_valid_email(email.strip()):
            return {
                "status": "error", 
                "message": f"Invalid recipient email address: {email.strip()}."
            }
        else: valid_to.append(email)

    if valid_to:
        to = ", ".join(valid_to)
    else:
        return {
            "status": "error",
            "message": "Recipient email id cannot be empty."
        }

    subject = "(No Subject)" if not subject else subject

    if in_reply_to and not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    message = MIMEText(body or "")

    if user_id != "me":
        message["from"] = user_id

    message['to'] = to
    message['subject'] = subject

    valid_cc = []
    invalid_cc_email = []

    if cc:
        cc = re.sub(r"[\(\)\[\]\{\}\<\>]", "", cc)

        for email in re.split(r",\s*", cc):
            if not is_valid_email(email.strip()):
                invalid_cc_email.append(email.strip())
            else:
                valid_cc.append(email)

        if valid_cc:
            message['cc'] = ", ".join(valid_cc)

    valid_bcc = []
    invalid_bcc_email = []

    if bcc:
        bcc = re.sub(r"[\(\)\[\]\{\}\<\>]", "", bcc)

        for email in re.split(r",\s*", bcc):
            if not is_valid_email(email.strip()):
                invalid_bcc_email.append(email.strip())
            else:
                valid_bcc.append(email)

        if valid_bcc:
            message['bcc'] = ", ".join(valid_bcc)

    if in_reply_to:
        message['In-Reply-To'] = in_reply_to
        message['References'] = in_reply_to

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    message_payload = {"raw": raw_message}

    if thread_id:
        message_payload["threadId"] = thread_id

    service = await async_init_gmail()

    response = await asyncio.to_thread(
        lambda: service.users().messages().send(
            userId=user_id, 
            body=message_payload
        ).execute()
    )

    result = {
        "status": "success", 
        "message": f"Email delivered with id: {response.get('id')}"
    }

    if invalid_cc_email:
        result["warning"] = "Skipped some email addresses that were invalid."
        result["invalid_emails_in_cc"] = invalid_cc_email

    if invalid_bcc_email:
        result["warning"] = "Skipped some email addresses that were invalid."
        result["invalid_emails_in_bcc"] = invalid_bcc_email

    return result


@mcp.tool(
    title="Modify labels of a message from the user's gmail account.",
    description=registry.MODIFY_MESSAGE_LABEL_DESCRIPTION
)
@handle_gmail_exceptions
async def modify_message_label(
    message_id: Annotated[
        str,
        Field(description="Unique ID of the Gmail message to modify.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    add_labels: Annotated[
        Optional[List[str]],
        Field(description="List of label IDs to add to the message.")
    ] = None,
    remove_labels: Annotated[
        Optional[List[str]],
        Field(description="List of label IDs to remove from the message.")
    ] = None
) -> Dict[str, str]:
    """
    Tool to modify labels of a Gmail message.

    This tool updates the labels assigned to a specific Gmail message by either 
    adding new labels, removing existing ones, or both. It requires the user's 
    Gmail account and the target message ID to perform this operation.

    Args:
        user_id (str): The user's email address.
            - Use "me" to refer to the authenticated user's account.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "me"
        message_id (str): The unique ID of the Gmail message to update.
            - Example: "17c693d97f54a2b5"
        add_labels (Optional[List[str]]): List of label IDs to add.
            - Example: ["INBOX", "STARRED", "CUSTOM_LABEL"]
        remove_labels (Optional[List[str]]): List of label IDs to remove.
            - Example: ["UNREAD", "CATEGORY_SOCIAL"]

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation message.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not message_id.strip():
        return {"status": "error", "message": "Message Id cannot be empty."}

    body = {}

    if add_labels:
        body["addLabelIds"] = add_labels
    if remove_labels:
        body["removeLabelIds"] = remove_labels

    if not body:
        return {"status": "error", "message": "No labels provided to modify."}

    service = await async_init_gmail()

    await asyncio.to_thread(
        lambda: service.users().messages().modify(
            userId=user_id,
            id=message_id,
            body=body
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Labels modified for message id: {message_id}."
    }


@mcp.tool(
    title="Trash a message from the user's gmail account.",
    description=registry.TRASH_MESSAGE_DESCRIPTION
)
@handle_gmail_exceptions
async def trash_message(
    message_id: Annotated[
        str,
        Field(description="Unique ID of the Gmail message to trash.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ]
) -> Dict[str, str]:
    """
    Tool to delete a gmail message and move it to the trash folder. 
    
    This tool deletes the message and moves it to the trashed folder. Trashed
    messages remain in the user's account until they are either permanently
    deleted or restored by the user.

    Args:
        user_id (str): The user's email address.
            - Use "me" to refer to the authenticated user's account.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "me" or "user@example.com"
        message_id (str): The unique ID of the Gmail message to delete.
            - Example: "17c693d97f54a2b5"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation message.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not message_id.strip():
        return {"status": "error", "message": "Message Id cannot be empty."}
    
    service = await async_init_gmail()

    await asyncio.to_thread(
        lambda: service.users().messages().trash(
            userId=user_id,
            id=message_id
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Message with id: {message_id} has been trashed."
    }


@mcp.tool(
    title="Recover message from the trashed folder of a user's gmail account.",
    description=registry.UNTRASH_MESSAGE_DESCRIPTION
)
@handle_gmail_exceptions
async def untrash_message(
    message_id: Annotated[
        str,
        Field(description="Unique ID of the Gmail message to recover.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
) -> Dict[str, str]:
    """
    Tool to recover a gmail message from the trash folder.

    This tool restores a previously trashed message back to the inbox. The
    message will remain in the user's account until it is either permanently
    deleted or trashed by the user.

    Args:
        user_id (str): The user's email address.
            - Use "me" to refer to the authenticated user's account.
            - Must be a valid email format if not "me".
            - Example: "me" or "user@example.com"
        message_id (str): The unique ID of the Gmail message to recover.
            - Example: "17c693d97f54a2b5"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation message.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not message_id.strip():
        return {"status": "error", "message": "Message Id cannot be empty."}

    service = await async_init_gmail()

    await asyncio.to_thread(
        lambda: service.users().messages().untrash(
            userId=user_id,
            id=message_id
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Message with id: {message_id} has been recovered."
    }


@mcp.tool(
    title="List email drafts from a user's gmail account.",
    description=registry.LIST_DRAFTS_DESCRIPTION
)
@handle_gmail_exceptions
async def list_drafts(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    query: Annotated[
        Optional[str],
        Field(description="Search query to filter drafts.")
    ] = None,
    max_results: Annotated[
        Optional[int],
        Field(description="Maximum number of drafts to return.", le=100, ge=1)
    ] = None,
    include_spam_and_trash: Annotated[
        Optional[bool],
        Field(description="Whether to include drafts from spam and trash.")
    ] = None
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Tool to list draft messages from a user's Gmail account.

    This tool retrieves a list of draft messages created in the Gmail account 
    of the specified user using the Gmail API. It can filter drafts based on 
    the provided search query and include drafts from spam and trash folders.

    Args:
        user_id (str): Email ID of the user whose drafts are to be retrieved.
            - Use "me" to fetch drafts of the authenticated user.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "user@example.com"
        query (Optional[str]): Search query to filter drafts.
            - Supports standard Gmail search syntax. Defaults to None.
            - Example: "has:attachment"
        max_results (Optional[int]): Maximum number of drafts to return.
            - Must be between 1 and 100.
            - Example: 15
        include_spam_and_trash (Optional[bool]): Whether to include drafts from 
            spam and trash.
            - Example: True

    Returns:
        Dict[str, Union[str, List[Dict[str, Any]]]]: A dictionary containing:
            - 'status' (str): "success", "not_found", or "error".
            On success:
                - 'drafts' (List[Dict[str,Any]]): List of drafts with metadata.
                    - 'draft_id' (str): ID of the draft.
                    - 'message_id' (str): ID of the message inside the draft
                    - 'thread_id' (str): ID of the thread the draft belongs to
                    - 'label_ids' (List[str]): Labels associated with the draft
                    - 'snippet' (str): Short preview of the draft message
            If not_found:
                - 'message' (str): Message indicating no drafts were found.
            On failure:
                - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}
    
    if query is not None and not query.strip():
        query = None

    service = await async_init_gmail()

    results = await asyncio.to_thread(
        lambda: service.users().drafts().list(
            userId=user_id,
            q=query,
            maxResults=max_results,
            includeSpamTrash=include_spam_and_trash
        ).execute()
    )

    drafts = results.get("drafts", [])
    draft_list = []

    if not drafts:
        return {
            "status": "not_found",
            "message": "No drafts found in user's gmail account."
        }

    for draft in drafts:
        draft_id = draft.get("id")
        message_id = draft.get("message", {}).get("id")
        thread_id = draft.get("message", {}).get("threadId")
        label_ids = draft.get("message", {}).get("labelIds", [])

        snippet = draft.get("message", {}).get("snippet")

        draft_list.append({
            "draft_id": draft_id,
            "message_id": message_id,
            "thread_id": thread_id,
            "label_ids": label_ids,
            "snippet": snippet
        })

    return {"status": "success", "drafts": draft_list}


@mcp.tool(
    title="Get the specified draft from user's gmail account.",
    description=registry.GET_DRAFT_DESCRIPTION
)
@handle_gmail_exceptions
async def get_draft(
    draft_id: Annotated[
        str,
        Field(description="ID of the draft to retrieve.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    format: Annotated[
        Optional[registry.GMAIL_MESSAGE_FORMAT],
        Field(description="Format to return the draft in.")
    ] = None,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to retrieve a specific draft from a user's Gmail account.

    This tool fetches a draft using its `draft_id` and returns the message in a 
    specified format. If the special identifier 'me' is used for `user_id`, the 
    message is retrieved from the authenticated user's mailbox.

    Args:
        user_id (str): Email ID of the user whose draft is to be retrieved.
            - Use "me" to fetch drafts of the authenticated user.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "user@example.com"
        draft_id (str): The unique ID of the draft to retrieve.
            - Example: "123draft456"
        format (Optional[str]): The format to return the draft message in.
            - Possible values are "full", "metadata", "minimal" and "raw". 
            - Example: "metadata"

    Returns:
        Dict[str, Union[str, List[Dict[str, Any]]]]: A dictionary containing:
            - "status": "success", "error", or "not_found"
            On success:
                - "draft" (dict): The message object from the draft response.
            If not_found:
                - "message" (str): Message indicating no drafts were found.
            On error:
                - "message" (str): An error or info message when applicable.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not draft_id.strip():
        return {"status": "error", "message": "Draft Id cannot be empty."}

    service = await async_init_gmail()

    draft = await asyncio.to_thread(
        lambda: service.users().drafts().get(
            userId=user_id,
            id=draft_id,
            format=format
        ).execute()
    )

    if not draft:
        return {
            "status": "not_found", 
            "message": f"Draft id: {draft_id} not found for user {user_id}"
        }
    
    if "message" not in draft:
        return {
            "status": "error",
            "message": f"Draft {draft_id} does not contain a message object."
        }

    return {"status": "success", "draft": draft.get("message")}


@mcp.tool(
    title="Send an existing email draft from a user's gmail account.",
    description=registry.SEND_DRAFT_DESCRIPTION
)
@handle_gmail_exceptions
async def send_draft(
    draft_id: Annotated[
        str,
        Field(description="ID of the draft message to be sent.")
    ],
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ]
) -> Dict[str, Union[str, Dict[str, Any], List[str]]]:
    """
    Tool to send the specified, existing draft to the recipients in the To, Cc, 
    and Bcc fields.

    This tool sends the existing draft to specified recipients. This tool can 
    read the recipients, subject, and body of the email message, along with
    optional parameters such as CC and BCC.

    Args:
        user_id (str): Email ID of the user whose draft is to be sent.
            - Use "me" to fetch drafts of the authenticated user.
            - Must be a valid email format if not "me". Defaults to "me".
            - Example: "user@example.com"
        draft_id (str): The unique ID of the draft to be sent.
            - Example: "123draft456"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Delivery confirmation message with `message ID`
            On failure:
            - 'message' (str): Description of the error
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not draft_id.strip():
        return {"status": "error", "message": "Draft Id cannot be empty."}

    service = await async_init_gmail()

    response = await asyncio.to_thread(
        lambda: service.users().drafts().send(
            userId=user_id, 
            body={"id": draft_id}
        ).execute()
    )

    if not response:
        return {
            "status": "error",
            "message": "No response received for send operation from Gmail API"
        }

    return {
        "status": "success", 
        "message": f"Email delivered with id: {response.get('id')}."
    }


@mcp.tool(
    title="Create a draft email message in user's gmail account.",
    description=registry.CREATE_DRAFT_DESCRIPTION
)
@handle_gmail_exceptions
async def create_draft(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    to: Annotated[
        Optional[str],
        Field(description="Comma-separated recipient email addresses.")
    ] = None,
    body: Annotated[
        Optional[str],
        Field(description="Content/body of the email message")
    ] = None,
    subject: Annotated[
        Optional[str],
        Field(description="Subject line of the email.")
    ] = None,
    cc: Annotated[
        Optional[str],
        Field(description="Comma-separated CC recipient email address.")
    ] = None,
    bcc: Annotated[
        Optional[str],
        Field(description="Comma-separated BCC recipient email address.")
    ] = None,
    thread_id: Annotated[
        Optional[str],
        Field(description="Thread ID of the email this belongs to.")
    ] = None,
    in_reply_to: Annotated[
        Optional[str],
        Field(description="Message ID of the email this is replying to.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any], List[str]]]:
    """
    Tool to create a draft email in the user's Gmail account.

    This tool allows users to compose and save an email draft with customizable 
    metadata such as recipient addresses, subject line, message body, and 
    headers. Drafts are stored in the user's Gmail Drafts folder and can later 
    be reviewed, updated, or sent.

    Args:
        user_id (str): Unique identifier of the Gmail user account.
            - Use "me" to indicate the authenticated user
            - Example: "me"
        to (Optional[str]): Comma-separated list of recipient email addresses.
            - Example: "alice@example.com, bob@example.com"
        body (Optional[str]): Body content of the email.
            - Example: "Hi Team, Please find the attached report..."
        subject (Optional[str]): Subject line of the email.
            - Example: "Project Update - Q3 Report"
        cc (Optional[str]): Comma-separated email addresses of CC recipients.
            - Example: "cc1@example.com, cc2@example.com"
        bcc (Optional[str]): Comma-separated email addresses of BCC recipients.
            - Example: "hidden@example.com"
        thread_id (Optional[str]): Thread ID of the email this belongs to.
            - Example: "1234567890"
        in_reply_to (Optional[str]): ID of the email this draft is replying to.
            - Example: "9876543210"

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Delivery confirmation message with `message ID`.
            - 'warning' (str, optional): Warning message if invalid email id(s) 
               were provided in CC or BCC.
            - 'invalid_emails_in_to' (list): Invalid email ids in to, if any.
            - 'invalid_emails_in_cc' (list): Invalid email ids in cc, if any.
            - 'invalid_emails_in_bcc' (list): Invalid email ids in bcc, if any.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}
    
    invalid_to_email = []

    if to.strip():
        valid_to = []

        for email in re.split(r",\s*", to):
            if not is_valid_email(email.strip()):
                invalid_to_email.append(email.strip())
            else:
                valid_to.append(email)

        to = ", ".join(valid_to)

    subject = "(No Subject)" if not subject else subject

    if in_reply_to and not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    message = MIMEText(body or "")

    if user_id != "me":
        message["from"] = user_id

    if to:
        message['to'] = to

    message['subject'] = subject

    valid_cc = []
    invalid_cc_email = []

    if cc:
        cc = re.sub(r"[\(\)\[\]\{\}\<\>]", "", cc)

        for email in re.split(r",\s*", cc):
            if not is_valid_email(email.strip()):
                invalid_cc_email.append(email.strip())
            else:
                valid_cc.append(email)

        if valid_cc:
            message['cc'] = ", ".join(valid_cc)

    valid_bcc = []
    invalid_bcc_email = []

    if bcc:
        bcc = re.sub(r"[\(\)\[\]\{\}\<\>]", "", bcc)

        for email in re.split(r",\s*", bcc):
            if not is_valid_email(email.strip()):
                invalid_bcc_email.append(email.strip())
            else:
                valid_bcc.append(email)

        if valid_bcc:
            message['bcc'] = ", ".join(valid_bcc)

    if in_reply_to:
        message['In-Reply-To'] = in_reply_to
        message['References'] = in_reply_to

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    message_payload = {"raw": raw_message}

    if thread_id:
        message_payload["threadId"] = thread_id

    service = await async_init_gmail()

    response = await asyncio.to_thread(
        lambda: service.users().drafts().create(
            userId=user_id, 
            body={"message": message_payload}
        ).execute()
    )

    result = {
        "status": "success", 
        "message": f"Draft created with id: {response.get('id')}"
    }

    warnings = []

    if invalid_to_email:
        warnings.append("Skipped invalid email addresses in to.")
        result["invalid_emails_in_to"] = invalid_to_email

    if invalid_cc_email:
        warnings.append("Skipped invalid email addresses in cc.")
        result["invalid_emails_in_cc"] = invalid_cc_email

    if invalid_bcc_email:
        warnings.append("Skipped invalid email addresses in bcc.")
        result["invalid_emails_in_bcc"] = invalid_bcc_email

    if warnings:
        result["warnings"] = " ".join(warnings)

    return result


@mcp.tool(
    title="Update an existing email draft in user's Gmail account.",
    description=registry.UPDATE_DRAFT_DESCRIPTION
)
@handle_gmail_exceptions
async def update_draft(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    draft_id: Annotated[
        str,
        Field(description="ID of the draft to update.")
    ],
    body: Annotated[
        Optional[str],
        Field(description="Content/body of the email message")
    ] = None,
    subject: Annotated[
        Optional[str],
        Field(description="Subject line of the email.")
    ] = None,
    add_to: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to add to the 'To' field.")
    ] = None,
    remove_to: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to remove from the 'To' field.")
    ] = None,
    add_cc: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to add to the 'Cc' field.")
    ] = None,
    remove_cc: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to remove from the 'Cc' field.")
    ] = None,
    add_bcc: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to add to the 'Bcc' field.")
    ] = None,
    remove_bcc: Annotated[
        Optional[List[str]],
        Field(description="Email addresses to remove from the 'Bcc' field.")
    ] = None
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Tool to update the specified draft with the provided details.

    This tool updates an existing draft in a user's Gmail account. It allows 
    modification of the To, Cc, and Bcc recipients, the subject line, and 
    the email body.

    Args:
        user_id (str): Unique identifier of the Gmail user account.
            - Use "me" to indicate the authenticated user
            - Example: "me"
        draft_id (str): The unique ID of the draft to update.
            - Example: "123draft456"
        body (Optional[str]): Body content of the email.
            - Example: "Hi Team, Please find the attached report..."
        subject (Optional[str]): Subject line of the email.
            - Example: "Project Update - Q3 Report"
        add_to (Optional[List[str]]): Email Ids of recipients to add to To.
            - Example: ["to1@example.com", "to2@example.com"]
        remove_to (Optional[List[str]]): Email addresses to remove from To.
            - Example: ["to3@example.com"]
        add_cc (Optional[List[str]]): Email Ids of recipients to add to Cc.
            - Example: ["cc1@example.com", "cc2@example.com"]
        remove_cc (Optional[List[str]]): Email addresses to remove from Cc.
            - Example: ["cc3@example.com"]
        add_bcc (Optional[List[str]]): Email Ids of recipients to add to Bcc.
            - Example: ["bcc1@example.com", "bcc2@example.com"]
        remove_bcc (Optional[List[str]]): Email addresses to remove from Bcc.
            - Example: ["bcc3@example.com"]

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation message with the updated draft ID.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not draft_id.strip():
        return {"status": "error", "message": "Draft Id cannot be empty."}
    
    service = await async_init_gmail()

    existing_draft = await asyncio.to_thread(
        lambda: service.users().drafts().get(
            userId=user_id,
            id=draft_id
        ).execute()
    )

    existing_message = existing_draft.get("message", {}).get("payload", {})
    existing_body = ""

    if "body" in existing_message and "data" in existing_message["body"]:
        existing_body = base64.urlsafe_b64decode(
            existing_message["body"]["data"].encode("UTF-8")
        ).decode("utf-8")

    elif "parts" in existing_message:
        for part in existing_message["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part["body"]:
                existing_body = base64.urlsafe_b64decode(
                    part["body"]["data"].encode("UTF-8")
                ).decode("utf-8")
                break

    message = MIMEText(body if body is not None else existing_body)

    headers = {
        h["name"]: h["value"] for h in existing_message.get("headers", [])
    }

    if subject:
        if subject.strip():
            message["Subject"] = subject.strip()
        else:
            message["Subject"] = "(No Subject)"
    else:
        message["Subject"] = headers.get("Subject", "(No Subject)")

    existing_to = [e for e in re.split(r",\s*", headers.get("To", "")) if e]
    invalid_to_email = []

    if add_to:
        for email in add_to:
            if is_valid_email(email):
                existing_to.append(email)
            else:
                invalid_to_email.append(email)

    if remove_to:
        for email in remove_to:
            if is_valid_email(email):
                try:
                    existing_to.remove(email)
                except ValueError:
                    pass
            else:
                invalid_to_email.append(email)

    message["To"] = ", ".join(list(set(existing_to)))

    existing_cc = [e for e in re.split(r",\s*", headers.get("Cc", "")) if e]
    invalid_cc_email = []

    if add_cc:
        for email in add_cc:
            if is_valid_email(email):
                existing_cc.append(email)
            else:
                invalid_cc_email.append(email)

    if remove_cc:
        for email in remove_cc:
            if is_valid_email(email):
                try:
                    existing_cc.remove(email)
                except ValueError:
                    pass
            else:
                invalid_cc_email.append(email)

    message['Cc'] = ", ".join(list(set(existing_cc)))

    existing_bcc = [e for e in re.split(r",\s*", headers.get("Bcc", "")) if e]
    invalid_bcc_email = []

    if add_bcc:
        for email in add_bcc:
            if is_valid_email(email):
                existing_bcc.append(email)
            else:
                invalid_bcc_email.append(email)

    if remove_bcc:
        for email in remove_bcc:
            if is_valid_email(email):
                try:
                    existing_bcc.remove(email)
                except ValueError:
                    pass
            else:
                invalid_bcc_email.append(email)

    message['Bcc'] = ", ".join(list(set(existing_bcc)))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    message_payload = {"message": {"raw": raw_message}}

    response = await asyncio.to_thread(
        lambda: service.users().drafts().update(
            userId=user_id,
            id=draft_id,
            body=message_payload
        ).execute()
    )

    result = {
        "status": "success",
        "message": f"Draft updated successfully with id: {response['id']}."
    }

    warnings = []

    if invalid_to_email:
        warnings.append("Skipped invalid email addresses in to.")
        result["invalid_emails_in_to"] = invalid_to_email

    if invalid_cc_email:
        warnings.append("Skipped invalid email addresses in cc.")
        result["invalid_emails_in_cc"] = invalid_cc_email

    if invalid_bcc_email:
        warnings.append("Skipped invalid email addresses in bcc.")
        result["invalid_emails_in_bcc"] = invalid_bcc_email

    if warnings:
        result["warnings"] = " ".join(warnings)

    return result


@mcp.tool(
    title="Delete the specified email draft from user's gmail account.",
    description=registry.DELETE_DRAFT_DESCRIPTION
)
@handle_gmail_exceptions
async def delete_draft(
    user_id: Annotated[
        str,
        Field(description="User's email id. Use 'me' for authenticated users.")
    ],
    draft_id: Annotated[
        str,
        Field(description="ID of the draft to update.")
    ],
) -> Dict[str, str]:
    """
    Tool to delete a gmail draft.

    This tool immediately and permanently deletes the specified draft from the 
    user's Gmail account. The tool doesn't simply add it to the trashed folder.
    This action cannot be undone. **Use with caution.**
    
    Args:
        user_id (str): Unique identifier of the Gmail user account.
            - Use "me" to indicate the authenticated user
            - Example: "me"
        draft_id (str): The unique ID of the draft to be deleted.
            - Example: "123draft456"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation message.
            On failure:
            - 'message' (str): Description of the error.
    """
    if not user_id.strip():
        return {"status": "error", "message": "User Id cannot be empty."}

    if user_id != "me" and not is_valid_email(user_id):
        return {"status": "error", "message": "Invalid User Id format."}

    if not draft_id.strip():
        return {"status": "error", "message": "Draft Id cannot be empty."}

    service = await async_init_gmail()

    await asyncio.to_thread(
        lambda: service.users().drafts().delete(
            userId=user_id,
            id=draft_id
        ).execute()
    )

    return {
        "status": "success",
        "message": f"Draft with id: {draft_id} has been deleted permanently."
    }


if __name__ == "__main__":
    TRANSPORT_PROTOCOL = 'stdio'
    logger.info(
        f"Starting Gmail MCP server with {TRANSPORT_PROTOCOL} transport"
    )
    
    mcp.run(transport=TRANSPORT_PROTOCOL)
