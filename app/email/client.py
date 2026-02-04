"""
Gmail Client - Gmail API authentication and service creation

This module handles OAuth2 authentication flow and Gmail API service creation.
"""

import base64
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Gmail API scopes - readonly access to messages
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# File paths (relative to project root)
APP_DIR = Path(__file__).parent.parent.parent
CREDENTIALS_FILE = APP_DIR / "credentials.json"
TOKEN_FILE = APP_DIR / "token.json"


class GmailClient:
    """
    Gmail API client with OAuth2 authentication.

    Handles:
    - Loading existing credentials from token.json
    - Refreshing expired credentials
    - Initiating OAuth flow for new credentials
    - Building Gmail API service
    """

    def __init__(self, credentials_file: Optional[Path] = None, token_file: Optional[Path] = None):
        """
        Initialize Gmail client.

        Args:
            credentials_file: Path to OAuth2 credentials.json
            token_file: Path to store/load token.json
        """
        self.credentials_file = credentials_file or CREDENTIALS_FILE
        self.token_file = token_file or TOKEN_FILE
        self._service = None
        self._creds = None

    def get_service(self):
        """
        Get authenticated Gmail API service.

        Returns:
            googleapiclient.discovery.Resource: Authenticated Gmail API service

        Raises:
            FileNotFoundError: If credentials.json is missing
            Exception: If authentication fails
        """
        if self._service is not None:
            return self._service

        self._authenticate()
        self._service = build("gmail", "v1", credentials=self._creds)
        return self._service

    def _authenticate(self):
        """Handle OAuth2 authentication flow."""
        creds = None

        # Load existing credentials
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh Gmail credentials: {e}")
                    if self.token_file.exists():
                        self.token_file.unlink()
                    raise
            else:
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Missing {self.credentials_file}. Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        self._creds = creds

    def get_message(self, msg_id: str, format: str = "full") -> dict:
        """
        Get a single email message.

        Args:
            msg_id: Gmail message ID
            format: Response format ('full', 'minimal', 'raw')

        Returns:
            Message dictionary from Gmail API
        """
        service = self.get_service()
        return service.users().messages().get(userId="me", id=msg_id, format=format).execute()

    def search_messages(self, query: str, max_results: int = 100) -> list:
        """
        Search for messages matching a query.

        Args:
            query: Gmail search query string
            max_results: Maximum number of results to return

        Returns:
            List of message metadata dictionaries
        """
        service = self.get_service()
        results = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        return results.get("messages", [])


def get_email_body(payload: dict) -> str:
    """
    Recursively extract HTML body from Gmail message payload.

    Args:
        payload: Gmail message payload dictionary

    Returns:
        Decoded HTML body as string
    """
    body = ""
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    elif "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/html" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break
            elif "parts" in part:
                body = get_email_body(part)
                if body:
                    break
    return body


# Singleton client instance
_client: Optional[GmailClient] = None


def get_gmail_client() -> GmailClient:
    """Get singleton Gmail client instance."""
    global _client
    if _client is None:
        _client = GmailClient()
    return _client


def get_gmail_service():
    """
    Get authenticated Gmail API service (backwards compatible function).

    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail API service
    """
    return get_gmail_client().get_service()
