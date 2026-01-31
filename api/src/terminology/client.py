"""Async client for FHIR Terminology Server (Snowstorm Lite) operations."""

import logging
from typing import Any

import httpx
from cachetools import TTLCache

from src.config import settings
from src.terminology.schemas import (
    CodeLookupResult,
    SubsumptionResult,
    ValidationResult,
    ValueSetExpansion,
    ValueSetExpansionEntry,
)

logger = logging.getLogger(__name__)


class TerminologyClient:
    """Async client for FHIR Terminology Server operations."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        cache_ttl: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.terminology_server_url).rstrip("/")
        self.timeout = timeout or settings.terminology_server_timeout
        self._client: httpx.AsyncClient | None = None
        self._cache: TTLCache = TTLCache(
            maxsize=1000,
            ttl=cache_ttl or settings.terminology_cache_ttl,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/fhir+json"},
            )
        return self._client

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GET request against the terminology server."""
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        """Check if the terminology server is available."""
        try:
            client = await self._get_client()
            response = await client.get("/metadata")
            return response.status_code == 200
        except Exception:
            return False

    async def lookup(
        self,
        system: str,
        code: str,
        properties: list[str] | None = None,
    ) -> CodeLookupResult:
        """Look up a code and return its display name and properties.

        FHIR Operation: CodeSystem/$lookup
        """
        props_key = ",".join(sorted(properties)) if properties else ""
        cache_key = f"lookup:{system}:{code}:{props_key}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        params: dict[str, Any] = {"system": system, "code": code}
        if properties:
            params["property"] = properties

        data = await self._get("/CodeSystem/$lookup", params)
        result = self._parse_lookup_response(data, system, code)
        self._cache[cache_key] = result
        return result

    async def validate_code(
        self,
        system: str,
        code: str,
        display: str | None = None,
        value_set_url: str | None = None,
    ) -> ValidationResult:
        """Validate that a code exists and optionally belongs to a value set.

        FHIR Operation: CodeSystem/$validate-code or ValueSet/$validate-code
        """
        if value_set_url:
            params: dict[str, Any] = {"url": value_set_url, "system": system, "code": code}
            if display:
                params["display"] = display
            data = await self._get("/ValueSet/$validate-code", params)
        else:
            params = {"system": system, "code": code}
            if display:
                params["display"] = display
            data = await self._get("/CodeSystem/$validate-code", params)

        return self._parse_validation_response(data)

    async def expand_value_set(
        self,
        url: str,
        filter: str | None = None,
        count: int = 100,
        offset: int = 0,
    ) -> ValueSetExpansion:
        """Expand a value set to get all contained codes.

        FHIR Operation: ValueSet/$expand
        """
        params: dict[str, Any] = {"url": url, "count": count, "offset": offset}
        if filter:
            params["filter"] = filter

        data = await self._get("/ValueSet/$expand", params)
        return self._parse_expansion_response(data, url)

    async def subsumes(
        self,
        system: str,
        code_a: str,
        code_b: str,
    ) -> SubsumptionResult:
        """Test subsumption relationship between two codes.

        FHIR Operation: CodeSystem/$subsumes
        """
        params = {"system": system, "codeA": code_a, "codeB": code_b}
        data = await self._get("/CodeSystem/$subsumes", params)

        outcome = "not-subsumed"
        for param in data.get("parameter", []):
            if param.get("name") == "outcome":
                outcome = param.get("valueCode", "not-subsumed")
                break

        return SubsumptionResult(outcome=outcome)

    async def search(
        self,
        system: str,
        term: str,
        count: int = 20,
    ) -> ValueSetExpansion:
        """Search for codes matching a term.

        Uses ValueSet/$expand with an implicit value set for the code system
        and a filter parameter for the search term.
        """
        # For SNOMED CT, use the implicit value set URL
        if "snomed" in system.lower():
            url = "http://snomed.info/sct?fhir_vs"
        else:
            url = f"{system}?fhir_vs"

        return await self.expand_value_set(url=url, filter=term, count=count)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Response parsers ──────────────────────────────────────────────

    def _parse_lookup_response(
        self, data: dict[str, Any], system: str, code: str
    ) -> CodeLookupResult:
        display = ""
        version = None
        properties: dict[str, Any] = {}

        for param in data.get("parameter", []):
            name = param.get("name")
            if name == "display":
                display = param.get("valueString", "")
            elif name == "version":
                version = param.get("valueString")
            elif name == "property":
                prop_code = None
                prop_value = None
                for part in param.get("part", []):
                    if part.get("name") == "code":
                        prop_code = part.get("valueCode")
                    else:
                        # Extract the value regardless of type
                        for key, val in part.items():
                            if key.startswith("value"):
                                prop_value = val
                                break
                if prop_code is not None:
                    properties[prop_code] = prop_value

        return CodeLookupResult(
            code=code,
            system=system,
            display=display,
            version=version,
            properties=properties,
        )

    def _parse_validation_response(self, data: dict[str, Any]) -> ValidationResult:
        valid = False
        message = None
        display = None

        for param in data.get("parameter", []):
            name = param.get("name")
            if name == "result":
                valid = param.get("valueBoolean", False)
            elif name == "message":
                message = param.get("valueString")
            elif name == "display":
                display = param.get("valueString")

        return ValidationResult(valid=valid, message=message, display=display)

    def _parse_expansion_response(self, data: dict[str, Any], url: str) -> ValueSetExpansion:
        expansion = data.get("expansion", {})
        total = expansion.get("total", 0)
        contains = [
            ValueSetExpansionEntry(
                code=entry.get("code", ""),
                system=entry.get("system", ""),
                display=entry.get("display", ""),
            )
            for entry in expansion.get("contains", [])
        ]

        return ValueSetExpansion(url=url, total=total, contains=contains)


# Singleton instance
terminology_client = TerminologyClient()
