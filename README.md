![MCP Toolbox for Google Workspace Banner](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/gh_banner/mcp_toolbox_for_google_workspace_banner_dark.png#gh-dark-mode-only)
![MCP Toolbox for Google Workspace Banner](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/gh_banner/mcp_toolbox_for_google_workspace_banner_light.png#gh-light-mode-only)


<p align="justify">
<B>MCP Toolbox for Google Workspace</B> is an open-source MCP server for interacting with Google Workspace services. It allows you to interact with Google Workspace APIs more easily and securely by handling complexities such as request formatting, authentication and error handling. The toolbox sits between your application’s orchestration framework & the GWS APIs to easily connect your agentic AI workflows and IDEs with services such as GDrive, GCalendar, and more
</p>

<p align="justify">
This project is licensed under the Apache-2.0 License and is maintained as an open-source project. Contributions and suggestions are welcome. Ready-to-use examples of the MCP servers in action are available in the <a href="https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/tree/main/examples">examples</a> directory
</p>


## Available MCP Servers

<table>
  <thead>
    <tr>
      <th width=147>Server</th>
      <th>Description</th>
      <th width=140>Extension</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Google Drive</td>
      <td><p align="justify">This server provides a suite of tools for managing files and folders within Google Drive. It offers tools to list files, create new ones, view file content and metadata, update metadata, make copies, delete files and clear trash</p></td>
      <td><a href="https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/releases/download/v0.1.0/google-drive-mcp-server.dxt"><img alt="Google Drive MCP Server" src="https://img.shields.io/badge/Install-Calude-DA7756?logo=claude"></a></td>
    </tr>
    <tr>
      <td>Gmail</td>
      <td><p align="justify">This server provides tools for managing emails and drafts within Gmail. It provides tools to send and receive emails, list and view message content and metadata, create and update drafts, manage profile and trash emails</p></td>
      <td><a href="https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/releases/download/v0.1.0/gmail-mcp-server.dxt"><img alt="Gmail MCP Server" src="https://img.shields.io/badge/Install-Calude-DA7756?logo=claude"></a></td>
    </tr>
    <tr>
      <td>Google Calendar</td>
      <td><p align="justify">This server provides a range of tools for managing calendars and events within Google Calendar. It offers tools to create, list, update, and delete events and calendars associated with your authenticated Google account</p></td>
      <td><a href="https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/releases/download/v0.1.0/google-calendar-mcp-server.dxt"><img alt="Google Calendar MCP Server" src="https://img.shields.io/badge/Install-Calude-DA7756?logo=claude"></a></td>
    </tr>
  </tbody>
</table>


## Installation and Setup

<p align="justify">
<b>Before you Begin</b>: Ensure that <a href="https://www.python.org/downloads/">Python</a> (>=3.13), <a href="https://nodejs.org/en/download">Node.js</a>, and <a href="https://docs.astral.sh/uv/getting-started/installation/">uv</a> are installed on your system. You should also have a Google Cloud project set up & a Google Workspace, or personal Google account ready for connecting with the server
</p>

![List MCP servers](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_claude/list_servers_on_claude_for_desktop.png)
![List server tools](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_claude/list_server_tools_on_claude_for_desktop.png)


### Configure OAuth 2.0 Credentials

Next you need to create OAuth 2.0 credentials in the GCP Console. Start by navigating to the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) in the Google Cloud Console. Click ```Get Started```, and provide the app information. For the ```audience```, choose **Internal** if you are using Google Workspace or **External** for a personal account and enter your contact information. Click ```Create```

After the OAuth consent screen is ready, select ```Clients``` from the left-hand menu and click on ```Create Client```. Select ```Desktop app``` as the authentication type, provide a name, and click ```Create```. Once ready, download ```credentials.json``` file and store it securely in a safe location of your choice. You will need this later for authenticating to Workspace APIs

If you plan to use the streamlit web client provided in this repo, you must create a second OAuth client in the console. Select ```Web application``` as the auth type and add ```http://localhost:8501/oauth2callback``` to authorised redirect URIs


### Enable Google Workspace APIs

Before you can access any Google Workspace service, you need to enable the respective APIs from your GCP console.

<p align="justify">
For example, if you want to interact with Google Drive, navigate to the search bar, type <code>Google Drive API</code> and select it from the results. Click <code>Enable</code> to make the Drive API available for your project. Repeat this process for other APIs you want to use, such as Gmail, Calendar etc. Each API must be explicitly <b>enabled</b> before your app can make requests.
</p>


## One-Click Claude for Desktop Installation (Recommended)

You can easily install the **MCP servers** of your choice using our ```desktop extensions```. Begin by downloading the latest desktop extension for your preferred Google Workspace service from our [GitHub Releases](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/releases/tag/v0.1.0) page. Next, install the MCP extension by either double-clicking the file to open it in Claude for Desktop or by dragging the extension directly into the application; the app will then launch and display a dialog box prompting you to install the mcp server to your app

Click ```Install``` in the **top-right** corner, and if your operating system requests confirmation, click ```Install``` again. Next, browse and select your oauth ```credentials.json``` file and click Save. If the extension is not already enabled, toggle the switch to activate it. After completing these steps, the server will be ready for use. To start using it, simply open a new Claude chat, and enter any prompt that requires calling **one or more tools** available within the server you've installed.

![Setup MCP Server Extension](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_extensions/google_drive_extension_setup_install.png)
![Select OAuth Credentials for MCP Server](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_extensions/google_drive_extension_setup_select_credentials.png)


## Use with Custom Streamlit Client

This repo includes a streamlit-based client built with the Google ADK framework to interact with the MCP Servers. The client provides a simple **Streamlit UI** for testing and running agents to interact with the Toolbox without writing code.

To begin with the setup, clone this repository, create a virtual environment, and install all the necessary dependencies:

```shell
# Clone this repository
git clone https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace.git
cd mcp-toolbox-for-google-workspace

# Create virtual environment and activate it
uv venv
.venv\Scripts\activate

# Install the requierd packages
uv sync
```

Next, create a `secrets.toml` file inside the `.streamlit` directory and add your **OAuth configuration** for a **web** client:
```
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "long cookie secret string"

[auth.google]
client_id = "oauth client id"
client_secret = "oauth client secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Then, add `GOOGLE_API_KEY` to your `.env` file. Once done, run the streamlit client locally with the following command:
```
streamlit run client.py
```

![Streamlit Client Welcome Page](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_streamlit_client/streamlit_client_home_page_dark.png)
![Streamlit Client Chat Page](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_streamlit_client/streamlit_client_chat_dark.png)


## Claude for Desktop Setup (Legacy)

To use the MCP servers with ```Claude for Desktop```, first install the MCP server locally using the following uv command:

```shell
uv run mcp install path/to/server.py

# For e.g. to install google drive server
uv run mcp install src/mcp_server/google_drive/server.py
```

Next, open your Claude for Desktop app. Ignore any warnings. Click on the three-bar icon in the top-left corner, go to ```Files > Settings```. In the settings pane, select Developer from the left-hand menu and under Local MCP Servers, click on Edit Config. You’ll then need to add your servers in the ```mcpServers``` key. The MCP UI elements will only show up in Claude for Desktop if at least one server is properly configured. Below is the config file format for the toolbox servers:

```json
{
  "mcpServers": {
    "<server-display-name>": {
      "command": "uv",
      "args": [
        "--directory",
        "<absolute-path-to-parent-folder>",
        "run",
        "<absolute-path-to-parent-folder>\\src\\mcp_server\\gmail\\server.py",
        "--credentials",
        "<absolute-path-to-credentials.json>"
      ]
    }
  }
}
```

<!--Here, set the value of the command key to the absolute path of the MCP executable inside your virtual environment’s ```Scripts``` folder. The path to the server file under args will be automatically populated by the ```mcp install``` command-->

For example, if you have cloned the MCP Toolbox repo to your Desktop and want to use Google Drive and Gmail with Claude for Desktop, first install each server individually and then update the claude config file to the following format:

```json
{
  "mcpServers": {
    "Google Drive MCP Server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace",
        "run",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace\\src\\mcp_server\\google_drive\\server.py",
        "--credentials",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace\\.credentials\\credentials.json"
      ]
    },
    "Gmail MCP Server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace",
        "run",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace\\src\\mcp_server\\gmail\\server.py",
        "--credentials",
        "C:\\Users\\Admin\\Desktop\\mcp-toolbox-for-google-workspace\\.credentials\\credentials.json"
      ]
    }
  }
}
```

![Create file in Google Drive](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_claude/google_drive_demo/create_file_in_google_drive.png)
![Fetch file content from Google Drive](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_claude/google_drive_demo/fetch_file_content_from_google_drive.png)
<!--![Delete file and empty trash in Google Drive](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_claude/google_drive_demo/delete_file_and_empty_trash_in_google_drive.png)-->

To run an MCP server locally on your system and listen for messages from MCP hosts, use the following uv command:

```shell
uv run path/to/server.py --credentials path/to/credentials.json
```

**Example:** If you want to run the Google Drive server locally, run cmd: ```uv run src/mcp_server/google_drive/server.py```


## Test using MCP Inspector

Alternatively, you can test the MCP server with MCP Inspector using the command: ```uv run mcp dev <path-to-server>```
Once the MCP Inspector is running, ensure the **Command** field is set to ```uv``` and update the **Arguments** field from the left pane to use command ```run src/mcp_server/<service-name>/server.py --credentials <path-to-credentials.json>```

Replace ```<service-name>``` with the service being tested (e.g. gmail), and ```<path-to-credentials.json>``` with the path to your OAuth credentials file (```credentials.json```). Next, expand Configurations and set the Request Timeout to ```100000```

Click on ```Connect``` to start testing the server. Then, go to the Tools tab to try the different tools available on the server.

![Fetch file content from Google Drive](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_mcp_inspector/fetch_file_content_mcp_inspector.png)
![Delete file from Google Drive](https://github.com/thisisashwinraj/mcp-toolbox-for-google-workspace/blob/main/.github/gh_readme_assets/demo_mcp_inspector/delete_file_mcp_inspector.png)


## Example Usage

<ul>
  <li><p align="justify"><B>Query Workspace in Plain English:</B> Ask your AI assistant things like “Show me all unread emails from last week” or “List upcoming calendar events in March with meeting links”—No need to manually navigate each Google app</p></li>
  <li><p align="justify"><B>Automate Routine Tasks:</B> Describe what you want, and let MCP Toolbox handle it. Be it creating calendar events, uploading files to Drive, sending emails with meet link, or even updating your tasks, without any manual API calls</p></li>
  <li><p align="justify"><B>Multi-Service AI Workflows:</B> Chain actions across Google Drive, Calendar & other workspace apps with a single command. For example, “Draft an email to Jon Doe, attach the sprint report, and schedule a meeting today at 12"</p></li>
</ul>


## Support and Feedback

<p align="justify">Contributions are always welcome from the community. If you have any queries or would like to share any feedback, please drop a line at thisisashwinraj@gmail.com. You can also connect with me over <a href="https://www.linkedin.com/in/thisisashwinraj/">LinkedIn</a> or <a href=
"https://x.com/thisisashwinraj">X (previously Twitter)</a></p>
