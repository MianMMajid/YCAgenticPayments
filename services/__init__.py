"""External API client services."""
from services.rentcast_client import RentCastClient, RentCastAPIError
from services.fema_client import FEMAClient, FEMAAPIError
from services.apify_client import ApifyClient, ApifyAPIError
from services.docusign_client import DocusignClient, DocusignAPIError
from services.calendar_client import CalendarClient, CalendarAPIError
from services.email_client import EmailClient, EmailAPIError
from services.crime_client import CrimeClient, CrimeAPIError
from services.notification_engine import (
    NotificationEngine,
    NotificationChannel,
    NotificationEventType,
    NotificationError
)
from services.notification_queue import NotificationQueue, NotificationStatus
from services.notification_service import (
    NotificationService,
    NotificationPreferences,
    get_notification_service
)

__all__ = [
    "RentCastClient",
    "RentCastAPIError",
    "FEMAClient",
    "FEMAAPIError",
    "ApifyClient",
    "ApifyAPIError",
    "DocusignClient",
    "DocusignAPIError",
    "CalendarClient",
    "CalendarAPIError",
    "EmailClient",
    "EmailAPIError",
    "CrimeClient",
    "CrimeAPIError",
    "NotificationEngine",
    "NotificationChannel",
    "NotificationEventType",
    "NotificationError",
    "NotificationQueue",
    "NotificationStatus",
    "NotificationService",
    "NotificationPreferences",
    "get_notification_service",
]
