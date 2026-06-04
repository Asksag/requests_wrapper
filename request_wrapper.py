import requests
from requests.exceptions import (
    RequestException,
    ConnectionError,
    Timeout,
    TooManyRedirects,
    HTTPError
)
from requests.models import Response
from typing import Optional, Any
import logging
import json

logger = logging.getLogger(__name__)


class RequestHandler:
    """
    A safe and minimal wrapper around Python's requests library.

    Handles errors gracefully and returns the native Response object on success,
    while wrapping failures into a consistent JSON error structure.

    Typical response on exception:
        {
            "status_code": int,
            "message": str,
            "data": null,
            "error": str
        }

    Example:
        handler = RequestHandler()
        response = handler.get("https://api.example.com/data")

        if response.ok:
            result = response.json()
        else:
            error = response.json().get("error")
    """

    def _format_response(
            self,
            status_code: int,
            message: str,
            data: Optional[Any] = None,
            error: Optional[str] = None
    ) -> Response:
        """
        Build a synthetic Response object with a consistent JSON structure.

        Args:
            status_code (int): HTTP status code.
            message (str): Response message.
            data (Any, optional): Response payload (if any).
            error (str, optional): Error details (if any).

        Returns:
            Response: A mocked `requests.Response` object with JSON content.
        """
        response = Response()
        response.status_code = status_code
        response._content = json.dumps({
            "status_code": status_code,
            "message": message,
            "data": data,
            "error": error
        }).encode('utf-8')
        response.headers['Content-Type'] = 'application/json'
        return response

    def _handle_request_exception(self, exception: Exception) -> Response:
        """
        Convert known `requests` exceptions into standardized error responses.

        Args:
            exception (Exception): Caught exception from `requests`.

        Returns:
            Response: A custom response with error details in JSON.
        """
        if isinstance(exception, ConnectionError):
            return self._format_response(503, "Service Unavailable", error="Connection failed")
        elif isinstance(exception, Timeout):
            return self._format_response(504, "Gateway Timeout", error="Request timed out")
        elif isinstance(exception, TooManyRedirects):
            return self._format_response(429, "Too Many Redirects", error="Too many redirects")
        elif isinstance(exception, HTTPError):
            print("HTTP error occurred.", exception.__str__())
            status_code = exception.response.status_code if exception.response else 500
            return self._format_response(status_code, "HTTP Error", error=str(exception))
        else:
            print("Unexpected exception during HTTP request.")
            return self._format_response(500, "Internal Server Error", error=str(exception))

    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        """
        Internal method to issue a request and handle any failures.

        Args:
            method (str): HTTP method to use (GET, POST, etc.).
            url (str): Full URL for the request.
            **kwargs: Additional options (headers, params, json, etc.).

        Returns:
            Response: Native `requests.Response` on success, formatted response on failure.
        """
        kwargs.setdefault("timeout", 10)  # Default timeout

        try:
            logger.info(f"Making {method.upper()} request to {url} with kwargs: {kwargs}")
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response  # Native response on success

        except RequestException as e:
            return self._handle_request_exception(e)

    # Public HTTP methods

    def get(self, url: str, **kwargs) -> Response:
        """Make a GET request."""
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        """Make a POST request."""
        return self._make_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        """Make a PUT request."""
        return self._make_request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        """Make a DELETE request."""
        return self._make_request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> Response:
        """Make a PATCH request."""
        return self._make_request("PATCH", url, **kwargs)
