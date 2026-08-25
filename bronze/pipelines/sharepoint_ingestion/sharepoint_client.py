import logging
from typing import Any, Dict, List, Optional
import requests
import msal

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SharePointGraphClient:
    """Client for authenticating and fetching data from SharePoint via Microsoft Graph API."""

    GRAPH_AUTHORITY_HOST = "https://login.microsoftonline.com"
    GRAPH_RESOURCE = "https://graph.microsoft.com/.default"
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = f"{self.GRAPH_AUTHORITY_HOST}/{tenant_id}"
        self._access_token: Optional[str] = None

    def get_access_token(self) -> str:
        """Acquire an app-only OAuth2 access token using MSAL ConfidentialClientApplication."""
        if self._access_token:
            return self._access_token

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

        result = app.acquire_token_for_client(scopes=[self.GRAPH_RESOURCE])
        if "access_token" in result:
            self._access_token = result["access_token"]
            logger.info("Successfully acquired Azure AD access token for MS Graph API.")
            return self._access_token
        else:
            error_msg = f"Failed to acquire token: {result.get('error_description', result.get('error'))}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_list_items(self, site_id: str, list_id: str, expand_fields: bool = True) -> List[Dict[str, Any]]:
        """Fetch all items from a SharePoint list using Microsoft Graph API with OData pagination.

        :param site_id: SharePoint Site ID (e.g. 'tenant.sharepoint.com,site-guid,web-guid')
        :param list_id: SharePoint List ID or Name
        :param expand_fields: If True, includes expanded fields ($expand=fields)
        :return: List of item dictionaries
        """
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        url = f"{self.GRAPH_API_BASE}/sites/{site_id}/lists/{list_id}/items"
        if expand_fields:
            url += "?$expand=fields"

        all_items: List[Dict[str, Any]] = []

        while url:
            logger.info(f"Fetching SharePoint items: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("value", [])
            all_items.extend(items)

            # OData next page link
            url = data.get("@odata.nextLink")

        logger.info(f"Retrieved {len(all_items)} total items from SharePoint list '{list_id}'.")
        return all_items
