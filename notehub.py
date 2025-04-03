#!/usr/bin/env python3

import asyncio
from typing import Dict, Any, List, Optional

# MCP libraries
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

# Notehub API base URL
NOTEHUB_API_BASE = "https://api.notefile.net"

# Token cache for performance
token_cache = {}

async def get_session_token(username: str, password: str) -> str:
    """
    Get an X-Session-Token from Notehub API using username and password.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password

    Returns:
        The X-Session-Token for API authentication
    """
    # Check if we have a valid cached token
    cache_key = f"{username}:{password}"
    if cache_key in token_cache and token_cache[cache_key].get("expires_at", 0) > asyncio.get_event_loop().time():
        return token_cache[cache_key]["token"]

    # Configure the API client
    configuration = notehub_py.Configuration(
        host=NOTEHUB_API_BASE
    )

    # Create a login request
    login_request = LoginRequest(
        username=username,
        password=password
    )

    # Get a new token
    with notehub_py.ApiClient(configuration) as api_client:
        api_instance = AuthorizationApi(api_client)
        try:
            login_response = api_instance.login(login_request)

            # Cache the token with expiration (30 minutes)
            # Adding a 1-minute buffer to ensure we refresh before expiration
            expires_at = asyncio.get_event_loop().time() + (30 * 60) - 60
            token_cache[cache_key] = {
                "token": login_response.session_token,
                "expires_at": expires_at
            }

            return login_response.session_token
        except notehub_py.ApiException as e:
            raise Exception(f"Error getting session token: {str(e)}")

@mcp.tool("getProjects")
async def get_projects(username: str, password: str) -> Dict[str, Any]:
    """
    Get all Notehub projects accessible with the provided credentials.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password

    Returns:
         A dictionary with projects information
    """
    try:
        # Get session token
        token = await get_session_token(username, password)

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
    username: str,
    password: str,
    project_uid: str,
    fleet_uid: Optional[str] = None,
    tag: Optional[List[str]] = None,
    device_uid: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all devices for a specific Notehub project with optional filtering.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password
        project_uid: UID of the Notehub project
        fleet_uid: (Optional) Filter by specific fleet UID
        tag: (Optional) Filter by device tags
        device_uid: (Optional) Filter by specific device UID

    Returns:
        A dictionary with devices information
    """
    try:
        # Get session token
        token = await get_session_token(username, password)

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        # Get devices
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = DeviceApi(api_client)
            devices_response = api_instance.get_project_devices(
                project_uid,
                fleet_uid=fleet_uid,
                tag=tag,
                device_uid=device_uid
            )

            return devices_response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("getEvents")
async def get_project_events(
    username: str,
    password: str,
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
        username: Your Notehub account email
        password: Your Notehub account password
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
        token = await get_session_token(username, password)

        # Configure the API client
        configuration = notehub_py.Configuration(
            host=NOTEHUB_API_BASE
        )
        configuration.api_key["api_key"] = token

        # Get events
        with notehub_py.ApiClient(configuration) as api_client:
            api_instance = EventApi(api_client)
            events_response = api_instance.get_project_events(
                project_uid,
                device_uid=device_uid,
                serial_number=serial_number,
                page_size=page_size,
                page_num=page_num,
                notecard_firmware=notecard_firmware,
                location=location,
                host_firmware=host_firmware,
                host_name=host_name,
                product_uid=product_uid,
                sku=sku,
                fleet_uid=fleet_uid,
                files=files,
                select_fields=select_fields
            )

            return events_response.to_dict()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("sendNote")
async def send_note(
    username: str,
    password: str,
    project_uid: str,
    device_uid: str,
    notefile_id: Optional[str] = None,
    body: Optional[Dict[str, Any]] = {},
    payload: Optional[str] = None
) -> bool:
    """
    Send a note to a specific device in a Notehub project.

    Args:
        username: Your Notehub account email
        password: Your Notehub account password
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
        token = await get_session_token(username, password)

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

            return True
    except Exception as e:
        print(f"Exception when calling DeviceApi->handle_note_add: {e}")
        return False

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
