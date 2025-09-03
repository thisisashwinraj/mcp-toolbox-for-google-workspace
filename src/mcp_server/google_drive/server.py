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

import io
import asyncio
import logging
from pydantic import Field
from typing import Annotated, Any, Dict, List, Optional, Union

from googleapiclient.http import MediaIoBaseDownload
from mcp.server.fastmcp import FastMCP

import registry
from auth import async_init_drive
from utils import handle_google_drive_exceptions

logger = logging.getLogger(__name__)


mcp = FastMCP(
    "Google Drive MCP Server",
    description="""
    The Google Drive MCP server provides a suite of tools for managing files 
    and folders within Google Drive""",
    version="0.1.0",
    instructions=registry.GOOGLE_DRIVE_MCP_SERVER_INSTRUCTIONS,
    settings={"initialization_timeout": 120.0}
)


@mcp.tool(
    title="List available files from user's Google Drive account.",
    description=registry.LIST_FILES_TOOL_DESCRIPTION,
)
@handle_google_drive_exceptions
async def list_files(
    max_results: Annotated[
        int, 
        Field(description="Max number of files to retrieve", ge=1, le=15)
    ],
    keyword: Annotated[
        Optional[str], 
        Field(description="Keyword to search for in file names")
    ] = None,
    order_by: Annotated[
        Optional[List[registry.VALID_SORT_KEYS]], 
        Field(description="Sort keys to order results")
    ] = None,
    spaces: Annotated[
        Optional[List[registry.VALID_SPACES]], 
        Field(description="Drive spaces to search, like 'drive', 'photos' etc")
    ] = None,
    drive_id: Annotated[
        Optional[str],
        Field(description="Id of the shared drive to search.")
    ] = None
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """
    Tool to search a user's Google Drive for specified number of files matching 
    a keyword (if provided), with optional sorting and space filtering.

    This tool handles authentication using OAuth2 and uses the Google Drive API
    to return a specified number of files whose name may contain given keyword. 
    The results can be sorted based on one or more sort keys and the search can 
    also be limited to specific Google Drive spaces.

    VALID_SORT_KEYS: 'createdTime', 'name', 'name_natural', 'quotaBytesUsed', 
    'folder', 'modifiedByMeTime', 'modifiedTime', 'recency', 'viewedByMeTime', 
    'sharedWithMeTime', and 'starred'.

    VALID_SPACES: 'drive' (main Google Drive), 'appDataFolder' (app-specific 
    data folder), and 'photos' (Google Photos).

    Args:
        max_results (int): The maximum number of files to retrieve.
            - Defaults to 3, if no max_results is provided.
        keyword (str): The keyword to search for in file names.
        order_by (List[str]): The list of sort keys to order results
            - Each key may optionally include the 'desc' modifier to sort in 
            descending order.
            - Defaults to None, if no order_by are provided.
            - Example: ['folder', 'modifiedTime desc', 'name']
        spaces (List[str]): Comma-separated list of spaces to query.
            - Supported values are 'drive', 'appDataFolder' and 'photos'.
            - Defaults to None (searches all spaces) if no spaces are provided.
            - Example: ['drive', 'photos']
        drive_id (Optional[str]): Unique ID of the shared drive to search.
            - Defaults to None if no drive_id is specified
            - Example: "sample_drive_id"

    Returns:
        Dict[str, Union[str, List[Dict[str, str]]]]: A dictionary containing:
            - 'status' (str): "success", "not_found", or "error"
            On success:
            - 'files' (Union[str, List[Dict[str, str]]]): 
                - A list of dictionaries for matching files, each containing:
                    - 'id' (str): The file's unique identifier.
                    - 'name' (str): The name of the file.
                    - 'webViewLink' (str): A shareable link to view the file.
            If not_found:
                - A string "no files found" if there are no matching results. 
            On failure:
            - 'message' (str): Contains a description of the error.
    """
    VALID_SORT_KEYS = {
        "folder", "modifiedByMeTime", "viewedByMeTime", "name", "starred", 
        "name_natural", "quotaBytesUsed", "recency", "sharedWithMeTime", 
        "createdTime", "modifiedTime",
    }

    VALID_SPACES = {'drive', 'appDataFolder', 'photos'}

    service = await async_init_drive()

    query = None
    if keyword:
        escaped_keyword = keyword.replace('"', '\\"')
        query = f'name contains "{escaped_keyword}"'

    if order_by:
        invalid_keys = [
            k for k in order_by if k.split()[0] not in VALID_SORT_KEYS]

        if invalid_keys:
            return {
                "status": "error",
                "message": f"invalid sort keys: {invalid_keys}"
            }
        
    if spaces:
        invalid_spaces = [
            k for k in spaces if k.split()[0] not in VALID_SPACES]

        if invalid_spaces:
            return {
                "status": "error",
                "message": f"invalid spaces: {invalid_spaces}"
            }

    results = await asyncio.to_thread(
        lambda: service.files()
            .list(
                pageSize=max_results,
                fields="nextPageToken, files(id, name, webViewLink)",
                q=query,
                orderBy=", ".join(order_by) if order_by else None,
                spaces=", ".join(spaces) if spaces else None,
                driveId=drive_id
            ).execute()
    )

    items = results.get("files", [])

    if not items:
        return {'status': 'not_found', 'files': 'no files found'}

    return {'status': 'success', 'files': items}


@mcp.tool(
    title="Create a new file in the specified folder in user's Google Drive account.",
    description=registry.CREATE_NEW_FILE_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def create_file(
    file_name: Annotated[
        str, 
        Field(description="Name of the file to be created", min_length=1)
    ],
    target_mime_type: Annotated[
        str, 
        Field(description=("MIME type of the file to create"), min_length=1)
    ],
    folder_id: Annotated[
        Optional[str],
        Field(description="ID of the parent folder (optional)")
    ] = None,
    enforce_single_parent: Annotated[
        Optional[bool],
        Field(description="Whether the file must have a single parent folder")
    ] = None,
    use_content_as_indexable_text: Annotated[
        Optional[bool],
        Field(description="Whether to use the file content as indexable text")
    ] = None
) -> Dict[str, str]:
    """
    Tool to create a new file in the user's drive with the specified metadata.

    This tool allows the user to create various types of files in their drive 
    (e.g. Google Docs, plain text, PDFs, folders etc). It supports creating the 
    file in a specific folder if a folder ID is provided.

    Args:
        file_name (str): The name of the file to be created.
        target_mime_type (str): The MIME type of the file to be created.
            - Examples of common MIME types:
                - "text/plain" → plain text file
                - "application/pdf" → PDF file
                - "application/vnd.google-apps.document" → Google Doc
                - "application/vnd.google-apps.spreadsheet" → Google Sheet
                - "application/vnd.google-apps.folder" → Google Drive folder
        folder_id (Optional[str]): ID of parent folder to place the file in.
            - If None, the new file will be created in the root directory.
            - Example: "sample_folder_id"
        enforce_single_parent (Optional[bool]): Whether the file must have only 
            a single parent folder.
            - This parameter takes effect if the item is not in a shared drive. 
            - If set to true, requests that specify more than one parent fail.
            - Example: True
        use_content_as_indexable_text (Optional[bool]): Whether to use the file 
            content as indexable text.
            - If set to true, content of the file will be used for indexing.
            - Example: True

    Returns:
        Dict[str, str]: A dictionary with:
            - 'status' (str): "success" or "error"
            On success:
            - 'id' (str): ID of the newly created file
            - 'name' (str): Name of the file
            - 'webViewLink' (str): Link to view the file in Drive
            On failure:
            - 'message' (str): Description of the error
    """
    if not file_name.strip():
        return {"status": "error", "message": "file name cannot be empty"}

    if not target_mime_type.strip():
        return {"status": "error", "message": "file MIME type is required"}

    file_metadata = {
        "name": file_name.strip(),
        "mimeType": target_mime_type.strip()
    }

    if folder_id and folder_id.strip():
        file_metadata["parents"] = [folder_id]

    service = await async_init_drive()

    created_file = await asyncio.to_thread(
        lambda: service.files().create(
            body=file_metadata,
            fields="id, name, webViewLink, mimeType",
            enforceSingleParent=enforce_single_parent,
            useContentAsIndexableText=use_content_as_indexable_text,
        ).execute()
    )

    return {
        "status": "success",
        "id": created_file.get("id"),
        "name": created_file.get("name"),
        "webViewLink": created_file.get("webViewLink")
    }


@handle_google_drive_exceptions
async def fetch_workspace_file_content(
    file_id: Annotated[
        str, 
        Field(description="ID of the Google Workspace file to be exported")
    ],
    export_mime_type: Annotated[
        str, 
        Field(description="MIME type to export the content as")
    ]
) -> Dict[str, Union[str, bytes]]:
    """
    Tool to fetch the content of a Google Workspace file (e.g., Doc, Sheet, or 
    Slide) by exporting it to a specified MIME type.

    Args:
        file_id (str): ID of the file to be exported.
            - Example: "sample_file_id"
        export_mime_type (str): MIME type to export the content as.
            - Examples:
                - 'text/plain' → Google Docs
                - 'text/csv' → Google Sheets
                - 'application/pdf' → Google Slides

    Returns:
        Dict[str, Union[str, bytes]]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On sucess:
            - 'content' (str): Decoded file content (UTF-8)
            On failure:
            - 'message' (str): Error message if operation failed
    """
    if not file_id.strip() or not export_mime_type.strip():
        return {
            "status": "error", 
            "message": "file id and export mime type are required"}

    service = await async_init_drive()

    metadata = await asyncio.to_thread(
        lambda: service.files().get(
            fileId=file_id, fields="mimeType, name, capabilities"
        ).execute()
    )

    if not metadata.get("capabilities", {}).get("canDownload", False):
        return {
            "status": "error",
            "message": "you do not have permission to export this file"
        }

    request = service.files().export_media(
        fileId=file_id, mimeType=export_mime_type)

    file_handle = io.BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)
    
    done = False

    while not done:
        _, done = await asyncio.to_thread(downloader.next_chunk)

    content_bytes = file_handle.getvalue()
    content_str = content_bytes.decode("utf-8-sig", errors="replace")

    return {"status": "success", "content": content_str}


@mcp.tool(
    title="Fetch content of a file from user's Google Drive account.",
    description=registry.FETCH_FILE_CONTENT_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def fetch_file_content(
    file_id: Annotated[
        str, 
        Field(description="ID of the file to fetch from the drive")
    ]
) -> Dict[str, Union[str, bytes]]:
    """
    Tool to fetch the content of a specified file from the Google Drive.

    This function supports both:
    - Binary files (e.g., .txt, .pdf) via `get_media`
    - Google Workspace files (Docs, Sheets, Slides) via `export_media`

    Args:
        file_id (str): The ID of the file whose content is to be retrieved.
            - Example: "sample_file_id"

    Returns:
        Dict[str, Union[str, bytes]]: A dictionary with:
            - 'status' (str): "success" or "error"
            On success:
            - 'content' (str): Decoded file content (UTF-8)
            On failure:
            - 'message' (str): Error message (if status is "error")
    """
    if not file_id.strip():
        return {"status": "error", "message": "file id is required"}

    service = await async_init_drive()

    metadata = await asyncio.to_thread(
        lambda: service.files().get(
            fileId=file_id,
            fields="mimeType, name, capabilities"
        ).execute()
    )

    capabilities = metadata.get("capabilities", {})

    can_download = capabilities.get("canDownload", True)
    can_read_drive = capabilities.get("canReadDrive", True)

    if not can_download and not can_read_drive:
        return {
            "status": "error",
            "message": "you do not have permission to export this file"
        }

    mime_type = metadata.get("mimeType", "")

    if mime_type.startswith("application/vnd.google-apps."):
        mime_map = {
            "document": "text/plain",
            "spreadsheet": "text/csv",
            "presentation": "application/pdf"
        }

        for key, export_mime in mime_map.items():
            if key in mime_type:
                return await fetch_workspace_file_content(
                    file_id, export_mime)

        return {
            "status": "error",
            "message": f"unsupported workspace file type: {mime_type}"
        }

    request = service.files().get_media(fileId=file_id)
    file_handle = io.BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)

    done = False

    while not done:
        _, done = await asyncio.to_thread(downloader.next_chunk)

    content_bytes = file_handle.getvalue()
    content_str = content_bytes.decode("utf-8-sig", errors="replace")

    return {
        "status": "success",
        "content": content_str
    }


@mcp.tool(
    title="Update metadata of a file in user's Google Drive account.",
    description=registry.UPDATE_FILE_METADATA_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def update_file_metadata(
    file_id: Annotated[
        str,
        Field(description="Unique ID of the file to be updated")
    ],
    metadata: Annotated[
        Dict[str, Union[int, str, bool, None, List[str]]],
        Field(description="Dictionary containing metadata fields to update")
    ]
) -> Dict[str, Union[str, Dict[str, Union[int, str, bool, None, List[str]]]]]:
    """
    Tool to update the metadata of a specified file on Google Drive.

    This tool allows modification of a file's metadata such as the file name, 
    description, and to mark/unmark as starred — without changing its content.

    Supported metadata fields include:
        - 'name': To rename the file
        - 'description': To  update file description
        - 'starred': To mark/unmark file as starred
    
    Supported query fields (other than metadata body) include:
        - 'addParents': A comma-separated list of parent IDs to add
        - 'removeParents': A comma-separated list of parent IDs to remove

    Args:
        file_id (str): The unique ID of the file to be updated.
            - Example: "sample_file_id"
        metadata (Dict[str, Union[str, bool]]): Dictionary containing metadata 
            fields to be updated. 
            - Example: {"name": "Updated Report.txt", "starred": True}

    Returns:
        Dict[str, Union[str, Dict[str, Union[int, str, bool, None, List]]]]: A 
            dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'updated_file_metadata' (dict): The updated file metadata
            On failure:
            - 'message' (str, optional): An error message if operation fails
    """
    ALLOWED_METADATA_FIELDS = {"name", "description", "starred"}

    if not file_id.strip():
        return {"status": "error", "message": "file id is required"}

    if not metadata:
        return {"status": "error", "message": "metadata is required"}
    
    if not isinstance(metadata, dict):
        return {
            "status": "error", 
            "message": f"metadata must be a valid dictionary"}

    service = await async_init_drive()

    parents_to_add = metadata.get("addParents", None)
    parents_to_remove = metadata.get("removeParents", None)

    metadata_body = {
        k: v for k, v in metadata.items() if k in ALLOWED_METADATA_FIELDS}

    fields_to_return = (
        "id, name, mimeType, webViewLink, description, starred, "
        "modifiedTime, parents")

    updated_file = await asyncio.to_thread(
        lambda: service.files().update(
            fileId=file_id,
            body=metadata_body if metadata_body else None,
            fields=fields_to_return,
            supportsAllDrives=True,
            addParents=(
                ", ".join(parents_to_add) 
                if parents_to_add 
                else None),
            removeParents=(
                ", ".join(parents_to_remove) 
                if parents_to_remove 
                else None),
        ).execute()
    )

    updated_file['addedParents'] = (
        ", ".join(parents_to_add) 
        if parents_to_add 
        else None)
    
    updated_file['removedParents'] = (
        ", ".join(parents_to_remove) 
        if parents_to_remove 
        else None)

    return {"status": "success", "updated_file_metadata": updated_file}


@mcp.tool(
    title="Delete a file from user's Google Drive account.",
    description=registry.DELETE_FILE_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def delete_file(
    file_id: Annotated[
        str, 
        Field(description="The unique ID of the file to be deleted")
    ]
) -> Dict[str, str]:
    """
    Tool to delete a specified file from the user's Google Drive.

    This tool permanently removes the file from the user's drive, provided the 
    user has sufficient permissions to perform the delete operation. This tool 
    supports files in both `My Drive` and `Shared Drives`. The file must not be 
    in `trash` for this to work. **Use with caution.**

    Args:
        file_id (str): Unique ID of the file to be deleted.
            - Example: "sample_file_id"

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'status' (str): "success" or "error"
            On success:
            - 'message' (str): Confirmation that the file was deleted
            On failure:
            - 'message' (str): Reason for the failure 
                - e.g., permission denied, invalid ID, api error etc
    """
    if not file_id or not file_id.strip():
        return {"status": "error", "message": "file id is required"}

    service = await async_init_drive()

    await asyncio.to_thread(
        lambda: service.files().delete(
            fileId=file_id, supportsAllDrives=True).execute())

    return {
        "status": "success", 
        "message": f"file with id '{file_id}' deleted successfully"}


@mcp.tool(
    title="Fetch metadata of a file from user's Google Drive account.",
    description=registry.EMPTY_TRASH_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def fetch_file_metadata(
    file_id: Annotated[
        str,
        Field(description="ID of the file whose metadata is to be retrieved.")
    ],
    metadata: Annotated[
        Optional[List[registry.VALID_METADATA_FIELDS]],
        Field(description="Optional list of metadata fields to fetch.")
    ] = None,
) -> Dict[str, Any]:
    """
    Retrieves the specified metadata for a specific file from the user's Google 
    Drive.

    This tool allows the selective retrieval of metadata fields for a file 
    identified by its file ID. If no list is provided, all available metadata 
    will be fetched using a wildcard. The tool returns the requested metadata 
    as returned by the Drive API, based on the user's access permissions.

    VALID_METADATA_FIELDS: ['hasThumbnail', 'mimeType', 'modifiedByMeTime', 
    'thumbnailLink', 'thumbnailVersion', 'explicitlyTrashed', 'teamDriveId', 
    'isAppAuthorized', 'writersCanShare', 'ownedByMe', 'viewedByMeTime', 'id', 
    'shortcutDetails', 'size', 'videoMediaMetadata', 'lastModifyingUser', 
    'sharingUser', 'folderColorRgb', 'appProperties', 'version', 'parents', 
    'capabilities', 'trashedTime', 'webViewLink', 'sharedWithMeTime', 
    'exportLinks', 'shared', 'copyRequiresWriterPermission', 'driveId', 
    'fullFileExtension', 'originalFilename', 'description', 'modifiedTime', 
    'viewersCanCopyContent', 'viewedByMe', 'modifiedByMe', 'owners', 
    'createdTime', 'quotaBytesUsed', 'starred', 'properties', 'md5Checksum', 
    'iconLink', 'imageMediaMetadata', 'kind', 'name', 'webContentLink', 
    'trashingUser', 'spaces', 'permissionIds', 'trashed', 'headRevisionId',
    'contentHints', 'fileExtension', 'hasAugmentedPermissions', 'permissions']

    Args:
        file_id (str): Unique ID of file for which metadata is to be fetched.
            - Example: "sample_file_id"
        metadata (Optional[List[str]]): List of metadata fields to retrieve. If 
        not provided (None), all metadata fields will be retrieved using '*'.
            - Example: ["mimeType", "modifiedTime"]

    Returns:
        Dict[str, Any]: A dictionary containing:
        - 'status': Indicates the result of the operation ('success').
        On success:
        - 'file_metadata' (Dict): Dictionary containing the requested metadata 
        fields or a message indicating no metadata found.
        On failure:
        - 'message' (str): Reason for the failure.
    """
    service = await async_init_drive()

    metadata = ", ".join(metadata) if metadata else "*"

    file_metadata = await asyncio.to_thread(
        lambda: service.files().get(fileId=file_id, fields=metadata).execute())

    if file_metadata:
        return {"status": "success", "file_metadata": file_metadata}

    return {
        "status": "success", 
        "message": "No metadata found for the specified fields"}


@mcp.tool(
    title="Create copy of an existing file in user's Google Drive account.",
    description=registry.COPY_FILE_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def copy_file(
    file_id: Annotated[
        str,
        Field(description="ID of the file to be copied", min_length=1)
    ],
    new_name: Annotated[
        Optional[str],
        Field(description="Optional new name for the copied file")
    ] = None,
    parent_folder_id: Annotated[
        Optional[str],
        Field(description="Optional ID of the folder to place the file in")
    ] = None,
    enforce_single_parent: Annotated[
        Optional[bool],
        Field(description="Whether the file must have a single parent folder")
    ] = None,
) -> Dict[str, str]:
    """
    Tool to create a copy of an existing file in the user's Google Drive.

    This tool allows users to duplicate any supported file (excluding folders).
    The copied file will retain the same content and MIME type. Optionally, the
    user can specify a new name and a target folder for the copied file.

    Args:
        file_id (str): The unique ID of the file to copy.
            - Example: "sample_file_id"
        new_name (Optional[str]): The new name for the copied file.
            - Example: "Copy of Report"
        parent_folder_id (Optional[str]): The folder ID to place the copy in.
            - Example: "sample_folder_id"
        enforce_single_parent (Optional[bool]): Whether the file must have only
            a single parent folder.
            - This parameter takes effect if the item is not in a shared drive. 
            - If set to true, requests that specify more than one parent fail.
            - Example: True

    Returns:
        Dict[str, str]: A dictionary with:
        - 'status' (str): "success" or "error"
        On success:
        - 'id' (str): ID of the copied file
        - 'name' (str): Name of the copied file
        - 'webViewLink' (str): Link to view the copied file
        On failure:
        - 'message' (str): Reason for the failure.
    """
    if not file_id.strip():
        return {"status": "error", "message": "File ID is required"}

    copy_metadata = {}

    if new_name:
        copy_metadata["name"] = new_name.strip()

    if parent_folder_id:
        copy_metadata["parents"] = [parent_folder_id]

    service = await async_init_drive()

    copied_file = await asyncio.to_thread(
        lambda: service.files().copy(
            fileId=file_id.strip(),
            body=copy_metadata,
            fields="id, name, webViewLink",
            enforceSingleParent=enforce_single_parent
        ).execute()
    )

    return {
        "status": "success",
        "id": copied_file.get("id"),
        "name": copied_file.get("name"),
        "webViewLink": copied_file.get("webViewLink")
    }


@mcp.tool(
    title="Empty the trash in user's Google Drive account.",
    description=registry.EMPTY_TRASH_TOOL_DESCRIPTION
)
@handle_google_drive_exceptions
async def empty_trash() -> Dict[str, str]:
    """
    Tool to permanently delete all files and folders in the user's Google Drive 
    trash folder.

    This function permanently deletes all items currently residing in the trash 
    folder of the user's Google Drive. The operation is irreversible, i.e. once 
    completed, the files and folders cannot be recovered. **Use with caution.**

    Returns:
        Dict[str, str]: A dictionary containing:
            - status (str): "success" or "error"
            - message (str): Descriptive message about the operation's outcome
    """
    service = await async_init_drive()

    await asyncio.to_thread(lambda: service.files().emptyTrash().execute())

    return {"status": "success", "message": "trash emptied successfully"}


if __name__ == "__main__":
    TRANSPORT_PROTOCOL = 'stdio'
    logger.info(
        f"Starting Google Drive MCP server with {TRANSPORT_PROTOCOL} transport"
    )
    
    mcp.run(transport=TRANSPORT_PROTOCOL)
