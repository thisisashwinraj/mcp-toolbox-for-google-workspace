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
import uuid
import asyncio
import requests
import warnings
import streamlit as st

from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

from static.firestore import UserActivityCollection
from toolbox_agent.runner import initialize_adk, run_adk_sync


st.set_page_config(
    page_title="MCP Toolbox for Google Workspace",
    page_icon="assets/logos/logiq_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

warnings.filterwarnings("ignore")

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

st.html(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 325px !important;
        }
    </style>
    """
)

st.html(
    "<style>[data-testid='stHeaderActionElements'] {display: none;}</style>"
)

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] > div:first-child {
        height: 100vh;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
        <style>
               .block-container {
                    padding-top: 0.2rem;
                    padding-bottom: 1.55rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

try:
    with open("static/css/client_home.css") as f:
        css = f.read()

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

except Exception as error:
    pass

st.markdown(
    """
    <style> 
        #MainMenu  {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        .stMarkdown a {
            text-decoration: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()).replace("-", "")[:12]

if "user_details" not in st.session_state:
    st.session_state.user_details = {}

if "themes" not in st.session_state:
    st.session_state.themes = {
        "current_theme": st.context.theme.get("type", "light").lower(),
        "refreshed": True,
        "light": {
            "theme.base": "dark",
            "theme.backgroundColor": "#131314",
            "theme.primaryColor": "#669DF5",
            "theme.secondaryBackgroundColor": "#18191B",
            "theme.textColor": "#E8EAED",
            "cardColor": "#f9fafb",
            "containerColor": "#f0f2f6",
            "containerBoundaryColor": "rgba(229, 231, 235, 1)",
            "alertColor": "#0D79FF",
            "button_face": ":material/dark_mode:",
        },
        "dark": {
            "theme.base": "light",
            "theme.backgroundColor": "#FFFFFF",
            "theme.primaryColor": "#0D79FF",
            "theme.secondaryBackgroundColor": "#F1F3F4",
            "theme.textColor": "#040316",
            "cardColor": "#202124",
            "containerColor": "#18191B",
            "containerBoundaryColor": "rgba(49, 51, 63, 0.2)",
            "alertColor": "#669DF5",
            "button_face": ":material/light_mode:",
        },
    }
    st.rerun()

@st.cache_data
def fetch_and_cache_recent_conversations(session_id, user_id, limit):
    user_activity_collection = UserActivityCollection()

    recent_conversations = user_activity_collection.fetch_latest_conversations(
        uid=user_id,
        limit=limit
    )

    return recent_conversations

def load_image_safe(path_or_url):
    try:
        if path_or_url.startswith("http"):
            response = requests.get(path_or_url, timeout=5)
            response.raise_for_status()

            return Image.open(BytesIO(response.content))
        
        else:
            if os.path.exists(path_or_url):
                return Image.open(path_or_url)

            else:
                raise FileNotFoundError

    except Exception:
        if st.session_state.themes['current_theme'] == 'light':
            placeholder_user = "static/images/placeholder/user.png"
        else:
            placeholder_user = "static/images/placeholder/user_dark.png"

        return Image.open(placeholder_user)

def change_streamlit_theme():
    previous_theme = st.session_state.themes["current_theme"]
    tdict = (
        st.session_state.themes["light"]
        if st.session_state.themes["current_theme"] == "light"
        else st.session_state.themes["dark"]
    )

    for vkey, vval in tdict.items():
        if vkey.startswith("theme"):
            st._config.set_option(vkey, vval)

    st.session_state.themes["refreshed"] = False

    if previous_theme == "dark":
        st.session_state.themes["current_theme"] = "light"

    elif previous_theme == "light":
        st.session_state.themes["current_theme"] = "dark"


if st.session_state.themes["refreshed"] == False:
    st.session_state.themes["refreshed"] = True
    st.rerun()


if st.session_state.themes["current_theme"] == "dark":
    AVATAR_AGENT = "static/images/placeholder/agent_dark.png"
else:
    AVATAR_AGENT = "static/images/placeholder/agent_light.png"


if __name__ == "__main__":
    if not st.user or not st.user.is_logged_in:
        login_col, banner_col = st.columns(
            [2, 2], 
            vertical_alignment="top",
            gap="medium"
        )

        with login_col:
            cola, _ = st.columns([1, 9], vertical_alignment='center')

            if st.session_state.themes['current_theme'] == 'light':
                cola.image("static/images/placeholder/favicon.png")
            else:
                cola.image("static/images/placeholder/favicon_dark.png")

            st.markdown("<BR>"*3, unsafe_allow_html=True)
            st.write(" ")

            if st.session_state.themes['current_theme'] == 'light':
                st.image("static/images/placeholder/login_title_light.png")
            else:
                st.image("static/images/placeholder/login_title_dark.png")

            st.markdown(
                """<font size=6>
                All your Workspace tools in one toolbox!
                </font><br><br>
                Simplify daily tasks, automate routine work, and keep 
                everything organized with MCP Toolbox for 
                Google Workspace.
                Toolbox brings all your work together so you can focus 
                on what matters most
                <br><br>
                """,
                unsafe_allow_html=True
            )

            col1, col2, _ = st.columns(
                [2, 0.5, 3.7], 
                vertical_alignment="center"
            )

            if col1.button(
                "Sign in with Google",
                icon=":material/login:",
                width="stretch",
                type="primary"
            ):
                st.login("google")

        with banner_col:
            st.write(" ")

            if st.session_state.themes['current_theme'] == 'light':
                st.image("static/images/placeholder/login_banner_light.png")
            else:
                st.image("static/images/placeholder/login_banner_dark.png")
    
        st.stop()

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    try:
        if not st.session_state.user_details:
            st.session_state.user_details = st.user.to_dict()

            st.session_state.user_id = st.session_state.user_details.get(
                "email", "Not Available"
            ).split("@")[0]

        adk_runner, current_session_id = initialize_adk(
            user_id=st.session_state.user_id,
            session_id=st.session_state.session_id
        )

    except Exception as e:
        st.error(f"""
            **Fatal Error:** Could not initialize the ADK Runner or Session 
            Service: {e}""",
            icon=":material/cancel:"
        )

        st.stop()

    with st.sidebar:
        if st.session_state.themes['current_theme'] == 'light':
            st.image("static/images/placeholder/logo_light.png")
        else:
            st.image("static/images/placeholder/logo_dark.png")

        st.markdown("---")

        with st.container(border=True, vertical_alignment="center"):
            colx, coly = st.columns(
                [1, 2.65], 
                vertical_alignment="center", 
                gap='small'
            )

            with colx:
                if st.session_state.themes['current_theme'] == 'light':
                    placeholder_user = "static/images/placeholder/user.png"
                else:
                    placeholder_user = "static/images/placeholder/user_dark.png"

                profile_picture_url = load_image_safe(
                    st.session_state.user_details.get(
                        "picture", placeholder_user
                    )
                )

                st.image(
                    profile_picture_url,
                    width="stretch"
                )

            with coly:
                if st.session_state.themes["current_theme"] == "dark":
                    subtitle_color = "#BDC1C6"
                else:
                    subtitle_color = "#45494E"

                st.markdown(
                    f"""<B>
                    {st.session_state.user_details.get("name", "User")}
                    </B><BR><font color="{subtitle_color}">
                    Username: {st.session_state.user_details.get(
                        "email", 
                        "Not Available"
                    ).split("@")[0]}</font>
                    """,
                    unsafe_allow_html=True,
                )

        with st.container(height=267, border=False):
            st.markdown("Features", unsafe_allow_html=True)

            with st.container(border=False, vertical_alignment="center"):
                cola, colb, colc, cold = st.columns(
                    4, vertical_alignment="center", gap='small'
                )

                if st.session_state.themes["current_theme"] == "dark":
                    icon_path = "static/images/icons/drive_icon_dark.png"
                else:
                    icon_path = "static/images/icons/drive_icon.png"

                with cola:
                    st.image(icon_path, width="stretch")
                
                if st.session_state.themes["current_theme"] == "dark":
                    icon_path = "static/images/icons/gmail_icon_dark.png"
                else:
                    icon_path = "static/images/icons/gmail_icon.png"

                with colb:
                    st.image(icon_path, width="stretch")

                if st.session_state.themes["current_theme"] == "dark":
                    icon_path = "static/images/icons/calendar_icon_dark.png"
                else:
                    icon_path = "static/images/icons/calendar_icon.png"

                with colc:
                    st.image(icon_path, width="stretch")

                if st.session_state.themes["current_theme"] == "dark":
                    icon_path = "static/images/icons/gmeet_icon_dark.png"
                else:
                    icon_path = "static/images/icons/gmeet_icon.png"

                with cold:
                    st.image(icon_path, width="stretch")

        st.markdown("---")

        cola, colb, colc = st.columns([4, 1, 1], vertical_alignment='center')

        with cola:
            if st.button(
                "New Chat",
                icon=":material/edit_square:",
                width="stretch",
                help="New Chat"
            ):
                try:
                    initialize_adk.clear()

                    del st.session_state['messages']
                    del st.session_state['adk_session_id']

                    st.rerun()

                except Exception as error: pass
        
        with colb:
            btn_face = (
                st.session_state.themes["light"]["button_face"]
                if st.session_state.themes["current_theme"] == "light"
                else st.session_state.themes["dark"]["button_face"]
            )

            st.button(
                "",
                icon=btn_face,
                type="secondary",
                help="Toggle Light/Dark Mode",
                width="stretch",
                on_click=change_streamlit_theme,
            )

        with colc:
            if st.button(
                "",
                icon=":material/logout:",
                help="Logout"
            ):
                st.session_state.clear()
                st.cache_data.clear()
                st.cache_resource.clear()

                st.logout()
                st.stop()

    if st.session_state.themes['current_theme'] == 'light':
        placeholder_user = "static/images/placeholder/user.png"
    else:
        placeholder_user = "static/images/placeholder/user_dark.png"

    profile_picture_url = st.session_state.user_details.get(
        "picture", placeholder_user
    )

    for message in st.session_state['messages']:
        if message["role"] == "user":
            avatar_url = profile_picture_url
        else:
            avatar_url = AVATAR_AGENT

        with st.chat_message(message["role"], avatar=avatar_url):
            st.markdown(message["content"], unsafe_allow_html=False)
    
    if prompt := st.chat_input("Type your question here..."):
        st.session_state['messages'].append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user", avatar=profile_picture_url):
            st.markdown(prompt, unsafe_allow_html=False)

        with st.chat_message("assistant", avatar=AVATAR_AGENT):
            message_placeholder = st.empty()

            with st.spinner("Thinking.....", show_time=True):
                try:
                    agent_response = run_adk_sync(
                        st.session_state.user_id, 
                        adk_runner, 
                        current_session_id, 
                        prompt
                    )

                except Exception as error:
                    agent_response = """Sorry, an error occurred while 
                    processing your request. Please try again later."""

                st.session_state.messages.append(
                    {
                        "role": "assistant", 
                        "content": agent_response
                    }
                )

                user_activity_collection = UserActivityCollection()

                user_activity_collection.add_chat_to_adk_session_id(
                    uid=st.session_state.user_id,
                    adk_session_id=st.session_state.adk_session_id,
                    query=str(prompt),
                    response=str(agent_response)
                )

            def response_generator(response):
                for word in response:
                    asyncio.run(asyncio.sleep(0.025))

                    try:
                        yield word.text
                    except Exception as err:
                        yield word

            try:
                response = st.write_stream(
                    response_generator(agent_response)
                )

            except Exception as err:
                fallback_message = (
                    f"Sorry, I am unable to answer this."
                )

                response = st.write_stream(
                    response_generator(fallback_message)
                )
    
    if not st.session_state['messages']:
        st.markdown(
            f"""
            <BR><BR><BR><BR><BR>
            <H1 class='h1-home-welcome-title'>
                Hello, {st.session_state.user_details.get("given_name", "User")}
            </H1>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <H1 class='h1-home-welcome-subtitle'>
                How can I help you today?
            </H1><BR>
            """,
            unsafe_allow_html=True,
        )

        welcome_message = f"""
        Your conversations may be reviewed by human evaluators for the 
        purpose of improving the overall quality, reliability, and 
        effectiveness of this product. Please avoid sharing sensitive, 
        personal, or confidential information that you would not be 
        comfortable being accessed, or analyzed!

        Learn more here: 
        github.com/thisisashwinraj/mcp-toolbox-for-google-workspace
        """

        st.info(
            welcome_message,
            icon=":material/security:"
        )
