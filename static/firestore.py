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

import json
import time
import warnings
import streamlit as st
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
warnings.filterwarnings("ignore")


class UserActivityCollection:
    def __init__(self):
        try:
            creds = credentials.Certificate(
                json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT_KEY"])
            )

            firebase_admin.initialize_app(creds)

        except BaseException:
            pass

        self.db = firestore.client()
    
    def add_chat_to_adk_session_id(self, uid, adk_session_id, query, response):
        try:        
            doc_ref = self.db.collection(uid).document(adk_session_id)
            doc = doc_ref.get()

            payload = {query: response}            

            if doc.exists and "conversations" in doc.to_dict():
                doc_ref.update({
                    "conversations": firestore.ArrayUnion([payload])
                })

            else:
                doc_ref.set({
                    "conversations": [payload],
                    "session_info":{
                        "created_at": int(time.time()) or "unavailable",
                        "host": st.context.headers.get('Host', "unavailable"),
                        "origin": st.context.headers.get(
                            "Origin", "unavailable"
                        ),
                        "locale": st.context.locale or "unavailable",
                        "ip_address": st.context.ip_address or "unavailable",
                        "theme": st.context.theme.type or "unavailable",
                        "timezone": st.context.timezone or "unavailable",
                        "url": st.context.url or "unavailable"
                    }
                }, merge=True)

            return True

        except Exception as error:
            return False
    
    def fetch_chats_by_adk_session_id(self, adk_session_id):
        try:
            doc = self.db.collection("chats").document(adk_session_id).get()

            if doc.exists:
                chat_history = doc.to_dict().get("conversations", [])
                chat_history = chat_history[-100:]

                response = []

                for chat in chat_history:
                    (user_content, assistant_content), = chat.items()

                    response.append({"role": "user", "content": user_content})
                    response.append(
                        {"role": "assistant", "content": assistant_content}
                    )

                return response

        except Exception as error:
            return False
        
    def fetch_latest_conversations(self, uid, limit):
        docs = (
            self.db.collection(uid)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        latest_conversations = [doc.id for doc in docs]
        return latest_conversations
