import logging
from datetime import datetime
from json import JSONDecodeError
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import httpx
import jwt


class OsdV4Api:
    """OpenShift Dedicated v4 (OCM) API client interface"""

    access_token: Optional[str] = None
    access_expiration: datetime = datetime.utcnow()
    element_lookup: Dict[str, str] = {
        "clusters": "clusters_mgmt",
        "accounts": "accounts_mgmt",
        "resource_quota": "accounts_mgmt",
        "organizations": "accounts_mgmt",
        "subscriptions": "accounts_mgmt",
        "skus": "accounts_mgmt",
        "reserved_resources": "accounts_mgmt",
    }

    def __init__(self, api_endpoint_url: str, token_endpoint_url: str, offline_jwt: str, client_id: str):
        """Setup API-wide configuration details"""
        self.api_url = api_endpoint_url
        self.token_url = token_endpoint_url
        self.refresh_token = offline_jwt
        self.client_id = client_id
        self.log = logging.getLogger("api")
        self.headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "OCM/0.1.87",
        }

    @staticmethod
    async def _decode_jwt(encoded_jwt: str) -> Dict[str, Any]:
        """Decode the JWT token in order to capture internal details"""
        return jwt.decode(encoded_jwt, algorithms=["HS256"], options={"verify_signature": False})

    async def _authorize(self) -> None:
        """Retrieve an access token if non-existent or previous token is expired.""" ""
        if self.access_token and self.access_expiration > datetime.utcnow():
            # Short circuit if the token is already authorized
            return
        async with httpx.AsyncClient(headers=self.headers) as client:
            resp = await client.post(
                url=self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": "",
                    "refresh_token": str(self.refresh_token),
                    "grant_type": "refresh_token",
                },
            )

            try:
                data = resp.json()
            except JSONDecodeError:
                self.log.warning(f'Unable to decode JSON from "{resp.text}"')
                return

            self.access_token = data.get("access_token", None)
            if self.access_token:
                decoded_access_token = await self._decode_jwt(self.access_token)
                self.access_expiration = datetime.utcfromtimestamp(decoded_access_token["exp"])
            else:
                self.log.error(f"Authorization request failed: {data}")

    async def _call(self, endpoint: str, method: str = "get", **params: Any) -> Dict[str, Any]:
        """Perform the actual API call to the backend service."""
        await self._authorize()
        # Allow for 60 second read timeouts to handle large datasets
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(headers=self.headers, timeout=timeout) as client:
            client.headers.update({"authorization": f"bearer {self.access_token}"})
            if method == "get":
                params = {"params": params}
            else:
                params = {"data": params}
            resp: httpx.Response = await client.request(method=method, url=f"{self.api_url}/{endpoint}", **params)

            json_response: Dict[str, Any] = {}
            try:
                json_response: Dict[str, Any] = resp.json()
            except JSONDecodeError:
                self.log.warning(f'Unable to decode JSON from "{resp.text}"')

            return json_response

    def _get_service(self, element: str) -> str:
        """Perform a lookup of the API service endpoint for a given element, and log any errors."""
        try:
            return self.element_lookup[element]
        except KeyError:
            self.log.error(f"API element, {element}, doesn't have a service lookup available")
            return ""

    async def get_item(self, element: str, identity: str) -> Dict[str, Any]:
        """Get a single item from the API endpoint"""
        return await self._call(f"{self._get_service(element)}/v1/{element}/{identity}")

    async def get_list(
        self,
        element: str,
        search: Optional[str] = None,
        sub_element: Optional[str] = None,
        sub_identity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get a list of objects that match provided elements in `search`, perform automatic page collection."""
        if sub_element and sub_identity:
            endpoint: str = f"{self._get_service(element)}/v1/{element}/{sub_identity}/{sub_element}"
        else:
            endpoint: str = f"{self._get_service(element)}/v1/{element}"

        # Make an initial call with a small size. This allows for a small amount of data to come through
        # while also allowing us to quickly call the total value
        response: Dict[str, Any] = await self._call(endpoint, search=search, size=5)

        # Ensure that this is a paged response
        if all(key in response.keys() for key in ("total", "size", "items")):
            # There are more records, re-send the call specifying size == total
            # This should allow us to get all records in one call
            if response["size"] < response["total"]:
                response = await self._call(endpoint, size=response["total"], search=search)
            return response["items"]

        return [response]
