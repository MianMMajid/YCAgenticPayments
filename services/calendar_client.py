"""Google Calendar API client for viewing scheduling."""
import httpx
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.settings import settings

logger = logging.getLogger(__name__)


class CalendarAPIError(Exception):
    """Exception raised for Google Calendar API errors."""
    pass


class CalendarClient:
    """Client for interacting with the Google Calendar API."""
    
    BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize the Calendar client.
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
        """
        if not client_id or not client_secret:
            raise ValueError("Google Calendar credentials are required")
        
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Google Calendar API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            access_token: User's OAuth access token
            json_data: Request body
            params: Query parameters
            timeout: Request timeout
            
        Returns:
            Response JSON
            
        Raises:
            CalendarAPIError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=timeout
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 401:
                    raise CalendarAPIError("Invalid or expired access token")
                elif response.status_code == 403:
                    raise CalendarAPIError("Insufficient permissions")
                elif response.status_code == 404:
                    raise CalendarAPIError("Calendar or event not found")
                else:
                    error_msg = f"Calendar API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', {}).get('message', '')}"
                    except:
                        pass
                    raise CalendarAPIError(error_msg)
                    
        except httpx.TimeoutException:
            raise CalendarAPIError("Request timeout")
        except httpx.NetworkError as e:
            raise CalendarAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, CalendarAPIError):
                raise
            raise CalendarAPIError(f"Unexpected error: {str(e)}")

    
    async def check_availability(
        self,
        access_token: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Check if a time slot is available in the user's calendar.
        
        Args:
            access_token: User's OAuth access token
            start_time: Start of time slot to check
            end_time: End of time slot to check
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            Dictionary with availability information:
            {
                "is_available": bool,
                "conflicts": List[Dict],
                "alternative_slots": List[Dict]
            }
            
        Raises:
            CalendarAPIError: If the request fails
        """
        logger.info(f"Checking availability from {start_time} to {end_time}")
        
        # Query for events in the time range
        params = {
            "timeMin": start_time.isoformat() + "Z",
            "timeMax": end_time.isoformat() + "Z",
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        try:
            response = await self._make_request(
                "GET",
                f"/calendars/{calendar_id}/events",
                access_token=access_token,
                params=params
            )
            
            events = response.get("items", [])
            
            # Check for conflicts
            conflicts = []
            for event in events:
                # Skip all-day events and declined events
                if "dateTime" not in event.get("start", {}):
                    continue
                if event.get("status") == "cancelled":
                    continue
                
                event_start = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00"))
                event_end = datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00"))
                
                # Check for overlap
                if event_start < end_time and event_end > start_time:
                    conflicts.append({
                        "summary": event.get("summary", "Busy"),
                        "start": event_start.isoformat(),
                        "end": event_end.isoformat()
                    })
            
            is_available = len(conflicts) == 0
            
            # Generate alternative slots if not available
            alternative_slots = []
            if not is_available:
                alternative_slots = await self._find_alternative_slots(
                    access_token=access_token,
                    preferred_time=start_time,
                    duration_minutes=int((end_time - start_time).total_seconds() / 60),
                    calendar_id=calendar_id
                )
            
            result = {
                "is_available": is_available,
                "conflicts": conflicts,
                "alternative_slots": alternative_slots
            }
            
            logger.info(f"Availability check: {'Available' if is_available else f'{len(conflicts)} conflicts'}")
            return result
            
        except CalendarAPIError as e:
            logger.error(f"Failed to check availability: {e}")
            raise
    
    async def _find_alternative_slots(
        self,
        access_token: str,
        preferred_time: datetime,
        duration_minutes: int,
        calendar_id: str = "primary",
        search_window_hours: int = 48
    ) -> List[Dict[str, str]]:
        """Find alternative available time slots.
        
        Args:
            access_token: User's OAuth access token
            preferred_time: Original preferred time
            duration_minutes: Duration of the appointment
            calendar_id: Calendar ID
            search_window_hours: How far ahead to search
            
        Returns:
            List of alternative time slots
        """
        alternatives = []
        
        # Search in 2-hour increments
        for hours_offset in [2, 4, 24, 26]:
            candidate_start = preferred_time + timedelta(hours=hours_offset)
            candidate_end = candidate_start + timedelta(minutes=duration_minutes)
            
            # Check if this slot is available
            result = await self.check_availability(
                access_token=access_token,
                start_time=candidate_start,
                end_time=candidate_end,
                calendar_id=calendar_id
            )
            
            if result["is_available"]:
                alternatives.append({
                    "start": candidate_start.isoformat(),
                    "end": candidate_end.isoformat()
                })
            
            if len(alternatives) >= 3:
                break
        
        return alternatives
    
    async def create_event(
        self,
        access_token: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        status: str = "confirmed",
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Create a calendar event.
        
        Args:
            access_token: User's OAuth access token
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
            status: Event status ("confirmed" or "tentative")
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            Dictionary with event details:
            {
                "event_id": str,
                "html_link": str,
                "status": str
            }
            
        Raises:
            CalendarAPIError: If event creation fails
        """
        logger.info(f"Creating event: {summary} at {start_time}")
        
        # Build event object
        event = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": settings.timezone
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": settings.timezone
            },
            "status": status
        }
        
        if description:
            event["description"] = description
        
        if location:
            event["location"] = location
        
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        
        try:
            response = await self._make_request(
                "POST",
                f"/calendars/{calendar_id}/events",
                access_token=access_token,
                json_data=event
            )
            
            event_id = response["id"]
            html_link = response.get("htmlLink", "")
            event_status = response.get("status", "")
            
            logger.info(f"Created event {event_id} with status {event_status}")
            
            return {
                "event_id": event_id,
                "html_link": html_link,
                "status": event_status
            }
            
        except CalendarAPIError as e:
            logger.error(f"Failed to create event: {e}")
            raise
    
    async def update_event_status(
        self,
        access_token: str,
        event_id: str,
        status: str,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Update the status of an existing event.
        
        Args:
            access_token: User's OAuth access token
            event_id: Event ID to update
            status: New status ("confirmed", "tentative", or "cancelled")
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            Updated event details
            
        Raises:
            CalendarAPIError: If update fails
        """
        logger.info(f"Updating event {event_id} status to {status}")
        
        # Get current event
        try:
            current_event = await self._make_request(
                "GET",
                f"/calendars/{calendar_id}/events/{event_id}",
                access_token=access_token
            )
            
            # Update status
            current_event["status"] = status
            
            # Send update
            response = await self._make_request(
                "PUT",
                f"/calendars/{calendar_id}/events/{event_id}",
                access_token=access_token,
                json_data=current_event
            )
            
            logger.info(f"Successfully updated event {event_id}")
            return response
            
        except CalendarAPIError as e:
            logger.error(f"Failed to update event: {e}")
            raise
    
    async def delete_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete a calendar event.
        
        Args:
            access_token: User's OAuth access token
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: "primary")
            
        Returns:
            True if successful
            
        Raises:
            CalendarAPIError: If deletion fails
        """
        logger.info(f"Deleting event {event_id}")
        
        try:
            await self._make_request(
                "DELETE",
                f"/calendars/{calendar_id}/events/{event_id}",
                access_token=access_token
            )
            
            logger.info(f"Successfully deleted event {event_id}")
            return True
            
        except CalendarAPIError as e:
            logger.error(f"Failed to delete event: {e}")
            raise
