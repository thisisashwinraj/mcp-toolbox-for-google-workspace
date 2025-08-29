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


VALID_SORT_KEYS = Literal[
    "folder", "modifiedByMeTime", "viewedByMeTime", "name", "starred",
    "name_natural", "quotaBytesUsed", "recency", "sharedWithMeTime",
    "createdTime", "modifiedTime", "folder desc", "modifiedByMeTime desc", 
    "viewedByMeTime desc", "name desc", "starred desc", "name_natural desc", 
    "quotaBytesUsed desc", "recency desc", "sharedWithMeTime desc",
    "createdTime desc", "modifiedTime desc"
]

VALID_SPACES = Literal["drive", "appDataFolder", "photos"]

VALID_METADATA_FIELDS = Literal["hasThumbnail", "mimeType", "modifiedByMeTime", 
    "thumbnailLink", "thumbnailVersion", "explicitlyTrashed", "teamDriveId", 
    "isAppAuthorized", "writersCanShare", "ownedByMe", "viewedByMeTime", "id", 
    "shortcutDetails", "size", "videoMediaMetadata", "lastModifyingUser", 
    "sharingUser", "folderColorRgb", "appProperties", "version", "parents", 
    "capabilities", "trashedTime", "webViewLink", "sharedWithMeTime", 
    "exportLinks", "shared", "copyRequiresWriterPermission", 
    "fullFileExtension", "originalFilename", "description", "modifiedTime", 
    "viewersCanCopyContent", "viewedByMe", "modifiedByMe", "owners", 
    "createdTime", "quotaBytesUsed", "starred", "properties", "md5Checksum", 
    "iconLink", "imageMediaMetadata", "kind", "name", "webContentLink", 
    "trashingUser", "driveId", "spaces", "permissionIds", "trashed", 
    "contentHints", "fileExtension", "hasAugmentedPermissions", "permissions", 
    "headRevisionId"
]

GOOGLE_DRIVE_MCP_SERVER_INSTRUCTIONS = """
# Google Drive MCP Server

This MCP server provides a suite of tools for managing files and folders within 
Google Drive.

### IMPORTANT: Always Use MCP Tools for Google Drive Operations

Always use the MCP tools provided by this server for interacting with Google 
Drive. This ensures that authentication, error handling, and asynchronous 
operations are managed correctly by the server, preventing common issues and 
ensuring consistent behavior.

---

## Usage Notes

- **Authentication:** The Google Drive MCP server require you to complete a 
    one-time OAuth 2.0 authentication flow. The server will guide you through 
    this process on the first run by redirecting to a Google OAuth window for 
    you to grant permissions.  All actions are performed using the permissions 
    granted by the authenticated Google account.
- **Permissions:** During authentication, the server requests specific OAuth 
    scopes which define what kind of access (e.g., read, write, metadata) the 
    server is allowed. If you encounter a permission error, it could be because 
    the authenticated account lacks access to a specific file, or the requested 
    scope doesn't permit that action.
- **File IDs:** Most operations require a unique file_id. Use the list_files 
    tool to retrieve the correct ID before attempting to read, modify or delete 
    a file. If multiple files share similar names, confirm the intended file ID 
    with the user to avoid ambiguity. Providing the wrong file_id may result in 
    errors or unintended operations.

---

## Common Workflows

### Creating a Folder and Adding a File
1.  Create a new folder and note the returned id: create_new_file(file_name='My 
    Project Folder', target_mime_type='application/vnd.google-apps.folder')
2.  Create a new file inside that folder using the folder_id from the previous 
    step: create_new_file(file_name='My Document', 
    target_mime_type='application/vnd.google-apps.document', 
    folder_id='folder_id_from_step_1')

### Finding and Reading a File Content
1.  Search for a file by name and get its file_id: list_files(keyword='Annual 
    Report', max_results=1)
2.  Fetch its content using the file_id from the search result: 
    fetch_file_content(file_id='file_id_from_step_1')

### Moving a File to a Different Folder
1.  Find the source file and destination folder to get their respective IDs: 
    list_files(keyword='file_or_folder_name')
2.  Move the file by updating its parent folders. This example moves a file 
    from the root directory to a new folder: 
    update_file_metadata(file_id='source_file_to_move_id', 
    metadata={'addParents': ['destination_folder_id'])

---

## Best Practices

- **Use Descriptive Names:** When creating files or folders, use clear and 
    descriptive names to make them easier to identify and manage later.
- **Leverage Metadata:** Use update_file_metadata to add descriptions or star 
    important files for better organization and quick access.
- **Organize with Folders:** Use create_new_file with the 
    application/vnd.google-apps.folder MIME type to create folders and keep 
    your Drive tidy.
- **Check for Errors:** Always inspect the status and message fields in the 
    tool's response to confirm success or handle failures gracefully.
- **Sort for Clarity:** When listing files, use the sort_keys parameter (e.g., 
    ['modifiedTime desc']) to find the most recently modified or relevant files 
    quickly.
- **Verify Permissions:** The Google OAuth consent screen will show you exactly 
    which permissions the server requires. All actions are performed on your 
    behalf with these granted permissions.
"""

LIST_FILES_TOOL_DESCRIPTION = """
Searches a user's Google Drive for up to 15 files matching an optional keyword 
in their names. Supports optional sorting and filtering based on specific Drive 
spaces (e.g. drive, photos, appDataFolder). Returns file metadata including ID, 
name, and a shareable link upon success, or an error message upon failure.

---

**Example:**
**Sample Input:**
    list_files(
        max_results=2,
        keyword="sample",
        sort_keys=["modifiedTime", "name desc"],
        spaces=["drive"]
    )

**Expected Output:** 
    {
        "status": "success",
        "files": [
            {
                "id": "sample_file_id_1",
                "name": "sample_text.txt",
                "webViewLink": "https://drive.google.com/file/d/sample_id_1"
            },
            {
                "id": "sample_file_id_2",
                "name": "sample_image.png",
                "webViewLink": "https://drive.google.com/file/d/sample_id_2"
            }
        ]
    }
"""

CREATE_NEW_FILE_TOOL_DESCRIPTION = """
Creates a new file in the user's Google Drive with a specified name and MIME 
type (e.g., Google Doc, plain text, PDF, folder, etc.). Optionally allows 
placement inside a specific folder using its ID. Returns the file ID, name, and 
a shareable link upon success, or an error message upon failure.

---

**Example:**
**Sample Input:**
    create_new_file(
        file_name="sample_gsheet"
        target_mime_type="application/vnd.google-apps.spreadsheet"
        folder_id="sample_folder_id"
    )

**Expected Output:**
    {
        "status": "success",
        "id": "sample_file_id",
        "name": "sample_gsheet",
        "webViewLink": "https://drive.google.com/file/d/sample_gsheet_id"
    }
"""

FETCH_FILE_CONTENT_TOOL_DESCRIPTION = """
Retrieves the content of a file stored in Google Drive using its file ID. 
Supports both binary files (e.g., .txt, .pdf) via direct download and Google 
Workspace files (e.g., Docs, Sheets, Slides) by exporting them to a supported 
MIME type. Returns the file content (decoded as UTF-8) or an error message if 
retrieval fails.

---

**Example:**
**Sample Input:**
    fetch_file_content(
        file_id="sample_file_id"
    )

**Expected Output:**
    {
        "status": "success",
        "content": "Lorem ipsum dolor sit amet consectetur adipiscing elit. 
        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    }
"""

UPDATE_FILE_METADATA_TOOL_DESCRIPTION = """
Updates metadata of a specified file in Google Drive without altering its 
content. Supports changes to file name, description, and starred status. Also 
allows modifying file hierarchy by adding or removing parent folders. Returns 
the updated metadata on success, or an error message on failure.

---

**Example:**
**Sample Input:**
    update_file_metadata(
        file_id="sample_file_id",
        metadata={
            "name": "renamed_sample_file.txt",
            "starred": true,
            "addParents": ["sample_parent_folder_id"]
        }
    )

**Expected Output:**
    {
        "status": "success",
        "updated_file_metadata": {
            "id": "sample_file_id",
            "name": "renamed_sample_file.txt",
            "mimeType": "text/plain",
            "starred": true,
            parents:[
                0: "sample_parent_folder_id"
            ],
            "webViewLink": "https://drive.google.com/file/d/file_id",
            "modifiedTime": "2025-07-16T09:07:58.389Z",
            "addedParents": "sample_parent_folder_id",
            "removedParents": None
        }
    }
"""

DELETE_FILE_TOOL_DESCRIPTION = """
Permanently deletes a specified file from the user's Google Drive, including 
files in both 'My Drive' and 'Shared Drives' provided the user has the required 
permissions. The file must not be in the trash. Returns a success message upon 
deletion or an error message if the operation fails.

---

**Example:**
**Sample Input:**
    delete_file(
        file_id="sample_file_id"
    )

**Expected Output:**
    {
        "status": "success",
        "message": "file with id 'sample_file_id' deleted successfully"
    }
"""

EMPTY_TRASH_TOOL_DESCRIPTION = """
Permanently deletes all items currently in the authenticated users Google Drive 
trash. This operation is irreversible — once deleted items cannot be recovered. 
Use this tool to programmatically clear the trash and free up storage space.

---

**Example:**
**Sample Input:**
    empty_trash()

**Expected Output:**
    {
        "status": "success",
        "message": "trash emptied successfully"
    }
"""

FETCH_FILE_METADATA_TOOL_DESCRIPTION = """
Retrieves selected metadata of a specific file from Google Drive using its file 
ID. If no specific metadata fields are provided, all available metadata is 
fetched using a wildcard (`*`). The tool returns the metadata based on the 
user's access permissions. If a requested metadata field is not available for 
the specified file, the tool gracefully ignores it. If no metadata is found for 
the specified fields, an appropriate message is returned.

---

**Example:**
**Sample Input:**
    fetch_file_metadata(
        file_id="sample_file_id",
        metadata=["mimeType", "modifiedTime"]
    )

**Expected Output:**
    {
        "status": "success",
        "file_metadata": {
            "mimeType": "text/plain",
            "modifiedTime": "2025-07-16T09:07:58.389Z"
        }
    }
"""

COPY_FILE_TOOL_DESCRIPTION = """
Creates a copy of an existing file in the user's Google Drive. Allows the user 
to optionally modify metadata such as the new file's name, description, and 
parent folder. Returns the copied file's ID, name, and a shareable link upon 
success, or an error message upon failure.

---

**Example:**
**Sample Input:**
    copy_file(
        file_id="original_file_id",
        new_name="copy_of_file",
        folder_id="target_folder_id",
        copy_permissions=True
    )

**Expected Output:**
    {
        "status": "success",
        "id": "copied_file_id",
        "name": "copy_of_file",
        "webViewLink": "https://drive.google.com/file/d/copied_file_url"
    }
"""