#!/usr/bin/env python3

import asyncio
import time
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# Notehub SDK
import notehub_py
from notehub_py.api.authorization_api import AuthorizationApi
from notehub_py.models.login_request import LoginRequest
from notehub_py.api.project_api import ProjectApi
from notehub_py.api.device_api import DeviceApi
from notehub_py.api.event_api import EventApi

# Initialize the FastMCP server
mcp = FastMCP("notehub")

# Load environment variables from .env file
load_dotenv()

# Notehub API base URL
NOTEHUB_API_BASE = "https://api.notefile.net"

# Token cache configuration
TOKEN_EXPIRY_SECONDS = 3600
token_cache: Dict[str, Dict[str, Any]] = {}
current_credentials: Optional[Dict[str, str]] = None

def set_credentials(username: str, password: str):
    """
    Set the credentials to use for Notehub API authentication.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password
    """
    global current_credentials
    current_credentials = {
        "username": username,
        "password": password
    }

def load_credentials_from_env():
    """
    Load credentials from environment variables if they exist.
    Returns True if credentials were loaded, False otherwise.
    """
    username = os.getenv("NOTEHUB_USERNAME")
    password = os.getenv("NOTEHUB_PASSWORD")

    if username and password:
        set_credentials(username, password)
        return True
    return False

def clear_expired_tokens():
    """Clear expired tokens from the cache."""
    current_time = time.time()
    expired_keys = [
        key for key, value in token_cache.items()
        if current_time - value["timestamp"] > TOKEN_EXPIRY_SECONDS
    ]
    for key in expired_keys:
        del token_cache[key]

async def get_session_token() -> str:
    """
    Get an X-Session-Token from Notehub API using cached credentials.

    Returns:
        The X-Session-Token for API authentication

    Raises:
        Exception: If credentials haven't been set or token retrieval fails
    """
    if not current_credentials:
        raise Exception("Credentials not set. Call set_credentials() first.")

    clear_expired_tokens()

    cache_key = f"{current_credentials['username']}:{current_credentials['password']}"
    if cache_key in token_cache:
        return token_cache[cache_key]["token"]

    configuration = notehub_py.Configuration(
        host=NOTEHUB_API_BASE
    )

    login_request = LoginRequest(
        username=current_credentials["username"],
        password=current_credentials["password"]
    )

    with notehub_py.ApiClient(configuration) as api_client:
        api_instance = AuthorizationApi(api_client)
        try:
            login_response = api_instance.login(login_request)

            # Cache the token with timestamp
            token_cache[cache_key] = {
                "token": login_response.session_token,
                "timestamp": time.time()
            }

            return login_response.session_token
        except notehub_py.ApiException as e:
            raise Exception(f"Error getting session token: {str(e)}")

@mcp.tool("getCredentials")
async def get_credentials() -> Dict[str, Any]:
    """
    Get the current credentials.
    This should always be called before using any other functions.
    """
    if current_credentials:
        return {"status": "success", "message": "Credentials are already set programmatically"}
    if load_credentials_from_env():
        return {"status": "success", "message": "Credentials loaded from environment variables"}
    return {"status": "error", "message": "Credentials could not be loaded from environment variables, use setCredentials to manually set them"}


@mcp.tool("setCredentials")
async def set_credentials_tool(username: str, password: str) -> Dict[str, Any]:
    """
    Set the credentials to use for Notehub API authentication.
    This should only be called if an authentication request fails, or if the credentials are not set in the environment variables.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password

    Returns:
        A dictionary indicating success or failure
    """
    try:
        # If no credentials provided, try to load from environment
        if not username and not password:
            if load_credentials_from_env():
                return {"status": "success", "message": "Credentials loaded from environment variables"}
            return {"status": "error", "message": "No credentials provided and none found in environment variables"}

        # Use provided credentials
        set_credentials(username, password)
        # Verify credentials by getting a token
    except ValueError as ve:
        return {"status": "error", "message": f"Invalid input: {str(ve)}"}
    except ConnectionError as ce:
        return {"status": "error", "message": f"Connection error: {str(ce)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool("getProjects")
async def get_projects() -> Dict[str, Any]:
    """
    Get all Notehub projects accessible with the current credentials.

    Returns:
         A dictionary with projects information
    """
    try:
        # Get session token
        token = await get_session_token()

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        # Get projects
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = ProjectApi(api_client)
            projects_response = api_instance.get_projects()

            return projects_response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("getDevices")
async def get_project_devices(
    project_uid: str,
    fleet_uid: Optional[List[str]] = None,
    tag: Optional[List[str]] = None,
    device_uid: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all devices for a specific Notehub project with optional filtering.

    Args:
        project_uid: UID of the Notehub project
        fleet_uid: (Optional) Filter by specific fleet UIDs
        tag: (Optional) Filter by device tags
        device_uid: (Optional) Filter by specific device UID

    Returns:
        A dictionary with devices information
    """
    try:
        # Get session token
        token = await get_session_token()

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        # Prepare parameters, filtering out None values
        params = {
            "tag": tag,
            "device_uid": device_uid
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}

        # Get devices
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = DeviceApi(api_client)
            devices_response = api_instance.get_project_devices(
                project_uid,
                fleet_uid=fleet_uid,
                **filtered_params
            )

            return devices_response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("getEvents")
async def get_project_events(
    project_uid: str,
    device_uid: Optional[List[str]] = None,
    serial_number: Optional[List[str]] = None,
    page_size: Optional[int] = 50,
    page_num: Optional[int] = 1,
    notecard_firmware: Optional[List[str]] = None,
    location: Optional[List[str]] = None,
    host_firmware: Optional[List[str]] = None,
    host_name: Optional[List[str]] = None,
    product_uid: Optional[List[str]] = None,
    sku: Optional[List[str]] = None,
    fleet_uid: Optional[str] = None,
    files: Optional[str] = None,
    select_fields: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get events for a specific Notehub project with optional filtering.

    Args:
        project_uid: UID of the Notehub project
        device_uid: (Optional) Filter by specific device UID
        serial_number: (Optional) Filter by device serial number
        page_size: (Optional) Number of events to return per page (default: 50)
        page_num: (Optional) Page number to return (default: 1)
        notecard_firmware: (Optional) Filter by Notecard firmware version
        location: (Optional) Filter by device location
        host_firmware: (Optional) Filter by host firmware version
        host_name: (Optional) Filter by host name
        product_uid: (Optional) Filter by product UID
        sku: (Optional) Filter by SKU
        fleet_uid: (Optional) Filter by specific fleet UID
        files: (Optional) Filter by specific files like "_health.qo" or "data.qo"
        select_fields: (Optional) Comma-separated list of fields to return from the JSON payload

    Returns:
        A dictionary with events information
    """
    try:
        # Get session token
        token = await get_session_token()

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        # Prepare parameters, filtering out None values
        params = {
            "device_uid": device_uid,
            "serial_number": serial_number,
            "page_size": page_size,
            "page_num": page_num,
            "notecard_firmware": notecard_firmware,
            "location": location,
            "host_firmware": host_firmware,
            "host_name": host_name,
            "product_uid": product_uid,
            "sku": sku,
            "fleet_uid": fleet_uid,
            "files": files,
            "select_fields": select_fields
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}

        # Get events
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = EventApi(api_client)
            events_response = api_instance.get_project_events(
                project_uid,
                **filtered_params
            )

            return events_response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("sendNote")
async def send_note(
    project_uid: str,
    device_uid: str,
    notefile_id: Optional[str] = None,
    body: Optional[Dict[str, Any]] = {},
    payload: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a note to a specific device in a Notehub project.

    Args:
        project_uid: UID of the Notehub project
        device_uid: UID of the device
        notefile_id: (Optional) ID of the notefile
        body: (Optional) JSON payload to send
        payload: (Optional) JSON payload to send

    Returns:
        A dictionary with the response information
    """
    try:
        # Get session token
        token = await get_session_token()

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        note = notehub_py.Note()

        if body is not None:
            note.body = body

        if payload is not None:
            note.payload = payload

        # Send note
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = DeviceApi(api_client)
            api_instance.handle_note_add(
                project_uid,
                device_uid,
                notefile_id=notefile_id,
                note=note
            )

            return {"status": "success", "message": "Note sent successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
