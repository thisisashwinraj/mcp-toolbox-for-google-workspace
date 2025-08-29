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

import os
import asyncio
import logging
import argparse
import traceback

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Google Drive MCP Server")
    parser.add_argument(
        "--credentials",
        type=str,
        required=True,
        help="Path to credentials.json file"
    )
    return parser.parse_args()


def _init_gmail() -> Credentials:
    try:
        PROJECT_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../..")
        )

        CREDENTIALS_DIR = os.path.join(PROJECT_ROOT, ".credentials")
        TOKEN_PATH = os.path.join(
            CREDENTIALS_DIR, "gmail_auth_token.json"
        )
        
        args = parse_args()
        CREDENTIALS_PATH = args.credentials

        SCOPES = [
            "https://www.googleapis.com/auth/gmail.labels",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.insert",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic"
        ]

        creds = None
        os.makedirs(CREDENTIALS_DIR, exist_ok=True)

        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        return service

    except Exception as error:
        logger.error("Failed to initialize Google Gmail", exc_info=error)
        logger.error("Traceback", exc_info=traceback.format_exc())

        raise RuntimeError(
            f"Failed to initialize Google Gmail:\n{traceback.format_exc()}"
        ) from error


async def async_init_gmail() -> Credentials:
    return await asyncio.to_thread(_init_gmail)
