"""
bright_scraper.py
Handles data extraction requests using Bright Data Scraper Studio API.

Production-hardened with:
  - Custom exception hierarchy for clear error semantics
  - HTTP timeouts on every request (default 30s)
  - Exponential-backoff retry on transient failures (429/5xx, network errors)
  - Bounded polling loop with configurable max attempts (no infinite hangs)
  - Safe JSON parsing with descriptive errors
  - Structured logging via the `logging` module
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, Timeout

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exception Hierarchy
# ---------------------------------------------------------------------------

class ScraperError(Exception):
    """Base exception for all scraper-related errors."""
    pass


class ConfigurationError(ScraperError):
    """Raised when required credentials or configuration are missing."""
    pass


class ScraperAPIError(ScraperError):
    """Raised when the Bright Data API returns a non-recoverable error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Bright Data API error (HTTP {status_code}): {message}")


class ScraperTimeoutError(ScraperError):
    """Raised when polling for dataset results exceeds the maximum wait time."""
    pass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TRANSIENT_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
_PLACEHOLDER_VALUES = frozenset({"YOUR_API_TOKEN_HERE", "YOUR_COLLECTOR_ID_HERE", ""})


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class BrightDataClient:
    """Client for triggering and polling Bright Data Scraper Studio collectors."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        collector_id: Optional[str] = None,
        *,
        request_timeout: float = 30.0,
        max_trigger_retries: int = 3,
        max_poll_attempts: int = 60,
        poll_interval: float = 5.0,
    ) -> None:
        """
        Initialize the Bright Data client.

        Args:
            api_token:           API token. Falls back to ``BRIGHT_DATA_API_TOKEN`` env var.
            collector_id:        Collector ID. Falls back to ``BRIGHT_DATA_COLLECTOR_ID`` env var.
            request_timeout:     HTTP timeout (seconds) for every request.
            max_trigger_retries: Max retries for the trigger POST on transient errors.
            max_poll_attempts:   Max polling iterations before raising ScraperTimeoutError.
            poll_interval:       Base seconds between poll requests.

        Raises:
            ConfigurationError: If api_token or collector_id resolve to a
                                placeholder or empty value.
        """
        self.api_token: str = (
            api_token or os.environ.get("BRIGHT_DATA_API_TOKEN", "")
        )
        self.collector_id: str = (
            collector_id or os.environ.get("BRIGHT_DATA_COLLECTOR_ID", "")
        )

        # --- Fail fast on missing credentials ---
        if self.api_token in _PLACEHOLDER_VALUES:
            raise ConfigurationError(
                "BRIGHT_DATA_API_TOKEN is not set. "
                "Provide it as a constructor argument or set the environment variable."
            )
        if self.collector_id in _PLACEHOLDER_VALUES:
            raise ConfigurationError(
                "BRIGHT_DATA_COLLECTOR_ID is not set. "
                "Provide it as a constructor argument or set the environment variable."
            )

        self.trigger_url: str = (
            f"https://api.brightdata.com/dca/trigger"
            f"?collector={self.collector_id}&queue_next=1"
        )
        self.dataset_url: str = "https://api.brightdata.com/dca/dataset"
        self.request_timeout: float = request_timeout
        self.max_trigger_retries: int = max_trigger_retries
        self.max_poll_attempts: int = max_poll_attempts
        self.poll_interval: float = poll_interval

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self, *, include_content_type: bool = False) -> Dict[str, str]:
        """Build standard authorization headers."""
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.api_token}"}
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        max_retries: int,
        headers: Dict[str, str],
        json_payload: Optional[List[Dict[str, Any]]] = None,
    ) -> requests.Response:
        """
        Execute an HTTP request with exponential-backoff retry on transient errors.

        Retries on: ``ConnectionError``, ``Timeout``, and HTTP 429 / 5xx responses.

        Returns:
            The successful ``requests.Response``.

        Raises:
            ScraperAPIError: If all retries are exhausted due to transient HTTP errors.
            ScraperError: If all retries are exhausted due to network errors.
        """
        last_exception: Optional[Exception] = None
        backoff: float = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                if method.upper() == "POST":
                    response = requests.post(
                        url,
                        headers=headers,
                        json=json_payload,
                        timeout=self.request_timeout,
                    )
                else:
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=self.request_timeout,
                    )

                # Transient HTTP error — retry with backoff
                if response.status_code in _TRANSIENT_STATUS_CODES:
                    logger.warning(
                        "Transient HTTP %d on attempt %d/%d for %s",
                        response.status_code, attempt, max_retries, url,
                    )
                    last_exception = ScraperAPIError(response.status_code, response.text[:300])
                    if attempt < max_retries:
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 30.0)
                        continue
                    raise last_exception

                return response

            except (ConnectionError, Timeout) as exc:
                logger.warning(
                    "Network error on attempt %d/%d for %s: %s",
                    attempt, max_retries, url, exc,
                )
                last_exception = exc
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)
                    continue
                raise ScraperError(
                    f"Request to {url} failed after {max_retries} retries: {exc}"
                ) from exc

        # Defensive guard — should be unreachable
        raise ScraperError(
            f"Request to {url} failed after {max_retries} retries"
        ) from last_exception

    def _parse_json_safe(self, response: requests.Response) -> Any:
        """
        Safely parse JSON from a response.

        Raises:
            ScraperAPIError: If the response body is not valid JSON.
        """
        try:
            return response.json()
        except (ValueError, requests.exceptions.JSONDecodeError) as exc:
            raise ScraperAPIError(
                response.status_code,
                f"Expected JSON but received: {response.text[:500]}",
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_page_data(self, target_url: str) -> Dict[str, Any]:
        """
        Trigger a Bright Data collector for *target_url* and poll until
        structured data is returned.

        Args:
            target_url: The page URL to scrape.

        Returns:
            The first extracted record as a dictionary, or an empty dict
            if the API returns no snapshot ID (local/mock mode).

        Raises:
            ScraperAPIError: On non-recoverable API errors.
            ScraperTimeoutError: If polling exceeds ``max_poll_attempts``.
            ScraperError: On exhausted retries due to network failures.
        """
        if not target_url or not isinstance(target_url, str):
            raise ValueError("target_url must be a non-empty string.")

        # --- Step 1: Trigger the collector ---
        payload: List[Dict[str, str]] = [{"url": target_url}]
        logger.info("Triggering Bright Data collector for URL: %s", target_url)

        trigger_response = self._request_with_retry(
            "POST",
            self.trigger_url,
            max_retries=self.max_trigger_retries,
            headers=self._headers(include_content_type=True),
            json_payload=payload,
        )

        if trigger_response.status_code != 200:
            raise ScraperAPIError(
                trigger_response.status_code,
                trigger_response.text[:300],
            )

        res_data = self._parse_json_safe(trigger_response)
        snapshot_id: Optional[str] = (
            res_data.get("collection_id") or res_data.get("snapshot_id")
        )

        if not snapshot_id:
            logger.warning(
                "No snapshot ID in trigger response. Returning empty dict (local/mock mode)."
            )
            return {}

        logger.info(
            "Collector triggered. Snapshot ID: %s — polling for results…",
            snapshot_id,
        )

        # --- Step 2: Poll for dataset completion (bounded) ---
        poll_url: str = f"{self.dataset_url}?id={snapshot_id}"
        poll_headers: Dict[str, str] = self._headers()
        current_interval: float = self.poll_interval

        for attempt in range(1, self.max_poll_attempts + 1):
            time.sleep(current_interval)

            try:
                dataset_response = self._request_with_retry(
                    "GET",
                    poll_url,
                    max_retries=2,  # Light retry per poll tick
                    headers=poll_headers,
                )
            except ScraperError:
                logger.warning(
                    "Poll attempt %d/%d failed — will retry next tick.",
                    attempt, self.max_poll_attempts,
                )
                current_interval = min(current_interval * 1.5, 30.0)
                continue

            if dataset_response.status_code == 200:
                body = self._parse_json_safe(dataset_response)
                if isinstance(body, list) and len(body) > 0:
                    logger.info(
                        "Data fetched successfully on poll attempt %d.", attempt
                    )
                    return body[0]

            logger.debug(
                "Poll attempt %d/%d — dataset not ready yet.",
                attempt, self.max_poll_attempts,
            )

        raise ScraperTimeoutError(
            f"Dataset for snapshot {snapshot_id} not ready after "
            f"{self.max_poll_attempts} poll attempts "
            f"(~{self.max_poll_attempts * self.poll_interval:.0f}s)."
        )
