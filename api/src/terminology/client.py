"""Async FHIR R4 terminology client backed by httpx with in-memory TTL cache."""

import logging
import time

import httpx
from cachetools import TTLCache

from src.config import settings

logger = logging.getLogger(__name__)


class TerminologyClient:
    """Async FHIR R4 terminology client.

    Backed by httpx.AsyncClient and cachetools TTLCache.
    All operations fail softly — returning None/False on errors
    so that a terminology server outage never blocks composition reads.
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._lookup_cache: TTLCache = TTLCache(
            maxsize=10_000, ttl=settings.terminology_cache_ttl_seconds
        )
        self._validate_cache: TTLCache = TTLCache(
            maxsize=5_000, ttl=settings.terminology_cache_ttl_seconds
        )

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.terminology_server_url,
                timeout=settings.terminology_timeout_seconds,
                headers={"Accept": "application/fhir+json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def lookup(self, system: str, code: str) -> str | None:
        """Return display term for a code, or None if not found.

        Uses CodeSystem/$lookup FHIR operation.
        Results are cached in-memory with TTL.
        """
        if not settings.terminology_enabled:
            return None

        cache_key = (system, code)
        if cache_key in self._lookup_cache:
            return self._lookup_cache[cache_key]

        try:
            client = self._ensure_client()
            response = await client.get(
                "/CodeSystem/$lookup",
                params={"system": system, "code": code},
            )
            if response.status_code != 200:
                logger.debug(
                    "Terminology lookup failed: %s %s → HTTP %d",
                    system, code, response.status_code,
                )
                self._lookup_cache[cache_key] = None
                return None

            data = response.json()
            display = self._extract_display_from_parameters(data)
            self._lookup_cache[cache_key] = display
            return display
        except Exception as e:
            logger.debug("Terminology lookup error for %s|%s: %s", system, code, e)
            return None

    async def validate_code(
        self, value_set_url: str, system: str, code: str
    ) -> bool:
        """Return True if code is a member of the given ValueSet.

        Uses ValueSet/$validate-code FHIR operation.
        """
        if not settings.terminology_enabled:
            return True  # permissive when disabled

        cache_key = (value_set_url, system, code)
        if cache_key in self._validate_cache:
            return self._validate_cache[cache_key]

        try:
            client = self._ensure_client()
            response = await client.get(
                "/ValueSet/$validate-code",
                params={"url": value_set_url, "system": system, "code": code},
            )
            if response.status_code != 200:
                logger.debug(
                    "Terminology validate-code failed: HTTP %d", response.status_code
                )
                return True  # permissive on error

            data = response.json()
            result = self._extract_boolean_from_parameters(data, "result")
            self._validate_cache[cache_key] = result
            return result
        except Exception as e:
            logger.debug("Terminology validate-code error: %s", e)
            return True  # permissive on error

    async def expand(
        self,
        value_set_url: str,
        filter: str | None = None,
        count: int = 200,
    ) -> dict:
        """Return FHIR ValueSet $expand response as dict."""
        try:
            client = self._ensure_client()
            params: dict[str, str | int] = {"url": value_set_url, "count": count}
            if filter:
                params["filter"] = filter

            response = await client.get("/ValueSet/$expand", params=params)
            if response.status_code != 200:
                logger.warning(
                    "Terminology expand failed for %s: HTTP %d",
                    value_set_url, response.status_code,
                )
                return {"resourceType": "OperationOutcome", "issue": [{
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": f"Upstream returned HTTP {response.status_code}",
                }]}

            return response.json()
        except Exception as e:
            logger.warning("Terminology expand error for %s: %s", value_set_url, e)
            return {"resourceType": "OperationOutcome", "issue": [{
                "severity": "error",
                "code": "exception",
                "diagnostics": str(e),
            }]}

    async def health_check(self) -> tuple[str, int | None]:
        """Check upstream connectivity. Returns (status, response_ms)."""
        try:
            client = self._ensure_client()
            start = time.monotonic()
            response = await client.get("/metadata", params={"_summary": "true"})
            elapsed_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                if elapsed_ms > 2000:
                    return "degraded", elapsed_ms
                return "online", elapsed_ms
            return "offline", elapsed_ms
        except Exception:
            return "offline", None

    @staticmethod
    def _extract_display_from_parameters(data: dict) -> str | None:
        """Extract display value from a FHIR Parameters response."""
        for param in data.get("parameter", []):
            if param.get("name") == "display":
                return param.get("valueString")
        return None

    @staticmethod
    def _extract_boolean_from_parameters(data: dict, name: str) -> bool:
        """Extract a boolean parameter from a FHIR Parameters response."""
        for param in data.get("parameter", []):
            if param.get("name") == name:
                return param.get("valueBoolean", False)
        return False


terminology_client = TerminologyClient()
