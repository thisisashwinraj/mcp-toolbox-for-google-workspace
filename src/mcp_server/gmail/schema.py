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


GMAIL_MESSAGE_FORMAT = Literal["full", "metadata", "minimal", "raw"]

GMAIL_MCP_SERVER_INSTRUCTIONS = """
# Gmail MCP Server

This MCP server provides a comprehensive suite of tools for managing messages 
and drafts within Gmail. 

### IMPORTANT: Always Use MCP Tools for Gmail Operations

Always use the MCP tools provided by this server when interacting with Gmail. 
This ensures that authentication, error handling, and asynchronous operations 
are handled correctly by the server, preventing common issues and ensuring 
consistent behavior.

---

## Usage Notes

- **Authentication:** The Gmail MCP server requires a one-time OAuth 2.0 
    authentication flow. On the first run, the server will guide you through 
    this process by redirecting to a Google OAuth window where you can grant 
    permissions. All actions are performed using the permissions granted by 
    the authenticated Google account.
- **Permissions:** During authentication, the server requests specific OAuth 
    scopes that determine the level of access (e.g., read, send, draft). If 
    you encounter a permission error, it may be due to missing scopes or 
    because the authenticated account does not have access to the requested 
    resource.
- **Message IDs:** Many operations require a unique message_id or draft_id. Use 
    the list_messages or list_drafts tools to retrieve the correct IDs before 
    attempting to read, update, send, or delete an item. If multiple messages 
    share similar attributes (like subject lines), confirm the intended ID 
    with the user to avoid ambiguity.

---

## Common Workflows

### Reading Unread Emails
1.  List unread messages in the inbox: 
    list_messages(query="is:unread", max_results=5)
2.  Retrieve the full content of a message using its ID: 
    get_message(user_id="me", message_id="message_id_from_step_1")

### Sending an Existing Draft
1.  Retrieve the draft_id with list_drafts or by name.
2.  Send the draft using its draft_id: 
    send_draft(user_id="me", draft_id="draft_id_from_step_1")

### Updating an Existing Draft
1.  Retrieve the draft_id with list_drafts or by name.
2.  Update recipients, subject, or body content: 
    update_draft(user_id="me", draft_id="draft_id_from_step_1", 
    add_to=["new@example.com"], subject="Updated Subject")

---

## Best Practices

- **Use Queries Effectively:** When listing messages, leverage Gmail search 
    queries (e.g., "from:example.com is:unread") to quickly filter relevant 
    results.
- **Validate Recipients:** Ensure that all email addresses provided in the 
    To, Cc, or Bcc fields are valid before creating or updating drafts.
- **Check Responses:** Always inspect the status and message fields in the 
    tool's response to confirm success or handle failures gracefully.
- **Preserve Draft Content:** When updating a draft, only modify the fields 
    that need changes to avoid overwriting existing data.
- **Organize with Labels:** Use add_label and remove_label to categorize and 
    manage emails more effectively.
"""

GET_GMAIL_PROFILE_DESCRIPTION = """
Retrieves the Gmail profile information for a given user. Returns the user's 
Gmail profile details, such as email address, messages total, threads total and 
history ID, on success, or an error message if the user ID is invalid.

This tool is useful for retrieving account-level metadata before performing 
other Gmail operations. It helps verify the mailbox identity and gives an 
overview of the message and thread counts without accessing individual emails.
"""

LIST_GMAIL_MESSAGES_DESCRIPTION = """
Lists the messages in the user's Gmail mailbox using the Gmail API. By default, 
it retrieves messages for the user. Additional filters such as a query can be 
provided to refine the results. Returns a dictionary containing the list of 
messages (with their IDs and thread IDs). In case of an invalid or missing user 
ID, an error message is returned.

This tool is useful for exploring the contents of a mailbox before fetching the
individual message details. It helps users preview available messages without 
retrieving full message payloads.
"""

GET_EMAIL_MESSAGE_DESCRIPTION = """
Retrieves the content of a specific Gmail message for a given user. Supports 
various response formats such as full, metadata, minimal, and raw. Returns the 
message details including internalDate, payload, and historyId.

This tool is useful for inspecting the details of a message after obtaining its 
ID from the list_messages response. It helps users access subject lines, sender 
information, and message body content.
"""

SEND_MESSAGE_DESCRIPTION = """
Sends an email on behalf of the authenticated user via their Gmail account. 
Supports specifying sender, recipients (To, Cc, Bcc), subject and message body. 

This tool is useful for automating email communication, such as sending emails,
notifications, reports, or alerts. It allows applications to deliver messages 
directly from a user's Gmail account without manual intervention.
"""

MODIFY_MESSAGE_LABEL_DESCRIPTION = """
Modifies the labels on an existing Gmail message using the Gmail API. Supports 
adding and removing both gmail provided and custom-created labels.

This tool is useful for managing Gmail messages, such as organizing emails into 
categories, marking emails as read/unread, or applying/removing system and 
custom labels. It allows applications to streamline email management tasks 
directly from a user's Gmail account.
"""

TRASH_MESSAGE_DESCRIPTION = """
Moves a specified Gmail message to the trash. This does not permanently delete 
the email, but rather marks it as "trashed," allowing recovery from the Trash 
folder if needed. The Gmail API securely handles the operation.

This tool is useful for managing email workflows where certain messages should 
no longer appear in the inbox, such as archiving outdated conversations, 
cleaning up spam, or temporarily removing clutter while retaining the option to 
restore later.
"""

UNTRASH_MESSAGE_DESCRIPTION = """
Restores a previously trashed Gmail message for the user. Once untrashed, the 
message will reappear in the user's mailbox (e.g., Inbox or its original 
folder), making it accessible again for normal use. The Gmail API securely 
handles the restoration operation.

This tool is useful for recovering emails that were accidentally moved to trash 
or restoring messages that need further action. It ensures that important 
communications can be brought back into the regular mailbox workflow without 
data loss.
"""

LIST_DRAFTS_DESCRIPTION = """
Lists all drafts in the user's Gmail account. This tool retrieves a collection 
of draft messages, including their metadata such as subject, recipients, and 
status. It allows users to view and manage their email drafts efficiently.

This tool is useful for exploring the draft messages in a user's mailbox before 
fetching the individual draft details. It helps users preview available drafts 
without retrieving full message payloads.
"""

GET_DRAFT_DESCRIPTION = """
Retrieves a specific draft from the user's Gmail account. This tool allows to 
access and manage email drafts directly, providing the ability to view, edit or 
delete draft messages as needed.

This tool is useful for inspecting the details of a draft after obtaining its 
ID from the `list_drafts` response. It helps users access subject lines, sender 
information, and message body content.
"""

SEND_DRAFT_DESCRIPTION = """
Sends a draft email message for the user. This tool allows users to send 
previously created drafts without needing to recreate the email content. The 
Gmail API securely handles the sending operation.

This tool is useful for automating email workflows where drafts are prepared 
in advance and need to be sent at a later time. It ensures that users can 
efficiently manage their email communications without duplicating effort.
"""

CREATE_DRAFT_DESCRIPTION = """
Creates a new draft email message for the user. This tool allows users to 
compose and save email drafts without sending them immediately.

This tool is useful for preparing email messages in advance, allowing users 
to refine their content before sending. It ensures that users can manage their 
email communications efficiently without the need for immediate delivery.
"""

UPDATE_DRAFT_DESCRIPTION = """
Updates an existing draft email message for the user. This tool allows users to 
modify the content or metadata of a draft without creating a new one. The Gmail 
API handles the update operation securely.

This tool is useful for refining email drafts after initial creation, ensuring 
that users can make adjustments as needed before sending.
"""

DELETE_DRAFT_DESCRIPTION = """
Permanently deletes a specific draft from the user's Gmail account. This tool
immediately removes the draft message without moving it to the trash.

This tool is useful for managing email drafts, allowing users to clean unwanted 
drafts efficiently. **Use with caution, as this action cannot be undone.**
"""
        