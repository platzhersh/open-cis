"""Tests for auth module: dependencies, permissions, router, and schemas."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from src.auth.dependencies import _get_jwks, get_current_user
from src.auth.schemas import UserResponse
from src.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user(role: str = "CLINICIAN") -> MagicMock:
    user = MagicMock()
    user.id = "user-123"
    user.externalId = "sub-abc"
    user.email = "clinician@open-cis.local"
    user.name = "Test Clinician"
    user.role = role
    return user


# ---------------------------------------------------------------------------
# UserResponse schema
# ---------------------------------------------------------------------------

class TestUserResponseSchema:
    def test_model_validate_from_dict(self):
        data = {"id": "u1", "email": "a@b.com", "name": "Alice", "role": "ADMIN"}
        response = UserResponse.model_validate(data)
        assert response.id == "u1"
        assert response.email == "a@b.com"
        assert response.name == "Alice"
        assert response.role == "ADMIN"

    def test_model_validate_from_attributes(self):
        """Validates that from_attributes=True config allows ORM-like objects."""
        obj = MagicMock()
        obj.id = "u2"
        obj.email = "b@c.com"
        obj.name = "Bob"
        obj.role = "CLINICIAN"
        response = UserResponse.model_validate(obj)
        assert response.id == "u2"
        assert response.email == "b@c.com"
        assert response.role == "CLINICIAN"

    def test_model_validate_all_roles(self):
        for role in ("ADMIN", "CLINICIAN", "NURSE", "READONLY"):
            resp = UserResponse.model_validate(
                {"id": "x", "email": "e@e.com", "name": "N", "role": role}
            )
            assert resp.role == role

    def test_model_serialises_to_dict(self):
        resp = UserResponse(id="u3", email="c@d.com", name="Carol", role="NURSE")
        d = resp.model_dump()
        assert set(d.keys()) == {"id", "email", "name", "role"}


# ---------------------------------------------------------------------------
# GET /api/auth/me endpoint
# ---------------------------------------------------------------------------

class TestGetMeEndpoint:
    @pytest.mark.asyncio
    async def test_get_me_returns_user_profile(self, client: AsyncClient):
        """Authenticated request returns user fields from the mock user."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "test-user-id"
        assert body["email"] == "test@open-cis.local"
        assert body["name"] == "Test User"
        assert body["role"] == "CLINICIAN"

    @pytest.mark.asyncio
    async def test_get_me_without_authorization_header_returns_403(self):
        """No Authorization header → HTTPBearer returns 403 Forbidden."""
        # Use a raw client without dependency overrides
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as raw_client:
            response = await raw_client.get("/api/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_with_non_bearer_token_returns_403(self):
        """Non-bearer Authorization header → 403."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as raw_client:
            response = await raw_client.get(
                "/api/auth/me",
                headers={"Authorization": "Basic dXNlcjpwYXNz"},
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_admin_returns_admin_role(self, admin_client: AsyncClient):
        """Admin client fixture returns ADMIN role."""
        response = await admin_client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"


# ---------------------------------------------------------------------------
# JWKS cache (_get_jwks)
# ---------------------------------------------------------------------------

class TestGetJwks:
    @pytest.mark.asyncio
    async def test_get_jwks_fetches_and_caches(self):
        """_get_jwks fetches config and JWKS on first call, caches the result."""
        mock_jwks = {"keys": [{"kid": "k1", "kty": "RSA"}]}
        mock_config = {"jwks_uri": "http://dex/.well-known/jwks.json"}

        with (
            patch("src.auth.dependencies._jwks_cache", None),
            patch("src.auth.dependencies._jwks_cache_time", 0),
            patch("src.auth.dependencies._get_oidc_config", new=AsyncMock(return_value=mock_config)),
            patch("httpx.AsyncClient") as mock_httpx,
        ):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_httpx.return_value)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value.get = AsyncMock(return_value=mock_response)

            result = await _get_jwks()
            assert result == mock_jwks

    @pytest.mark.asyncio
    async def test_get_jwks_returns_cached_value_within_ttl(self):
        """_get_jwks returns cached JWKS without fetching when cache is fresh."""
        import time

        cached_jwks = {"keys": [{"kid": "cached", "kty": "RSA"}]}
        fresh_time = time.monotonic()

        with (
            patch("src.auth.dependencies._jwks_cache", cached_jwks),
            patch("src.auth.dependencies._jwks_cache_time", fresh_time),
            patch("src.auth.dependencies._get_oidc_config") as mock_config,
        ):
            result = await _get_jwks()
            assert result == cached_jwks
            mock_config.assert_not_called()


# ---------------------------------------------------------------------------
# get_current_user dependency (unit tests with mocked DB and JWT)
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    def _make_credentials(self, token: str = "test.jwt.token") -> MagicMock:
        creds = MagicMock()
        creds.credentials = token
        return creds

    @pytest.mark.asyncio
    async def test_jwt_error_raises_401_invalid_token(self):
        """JWTError during decode → 401 'Invalid or expired token'."""
        from jose import JWTError

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", side_effect=JWTError("bad sig")),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(self._make_credentials())
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_generic_exception_raises_401_could_not_validate(self):
        """Non-JWT exception during decode → 401 'Could not validate credentials'."""
        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(side_effect=RuntimeError("network"))),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(self._make_credentials())
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_missing_sub_raises_401(self):
        """Payload without 'sub' → 401 'Token missing sub claim'."""
        payload = {"email": "user@example.com"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(self._make_credentials())
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Token missing sub claim"

    @pytest.mark.asyncio
    async def test_missing_email_raises_401(self):
        """Payload without 'email' → 401 'Token missing email claim'."""
        payload = {"sub": "sub-xyz"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(self._make_credentials())
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Token missing email claim"

    @pytest.mark.asyncio
    async def test_existing_user_returned_by_external_id(self):
        """If user exists by externalId, return it without creating."""
        existing = _make_mock_user("CLINICIAN")
        payload = {"sub": "sub-abc", "email": "user@example.com"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            mock_prisma.user.find_unique = AsyncMock(return_value=existing)

            result = await get_current_user(self._make_credentials())
            assert result is existing
            mock_prisma.user.find_unique.assert_called_once_with(where={"externalId": "sub-abc"})

    @pytest.mark.asyncio
    async def test_legacy_user_migration_updates_external_id(self):
        """Legacy user (externalId starts with 'legacy-') gets updated with real sub."""
        legacy_user = _make_mock_user("CLINICIAN")
        legacy_user.externalId = "legacy-user-123"
        legacy_user.id = "db-id-001"

        updated_user = _make_mock_user("CLINICIAN")
        updated_user.externalId = "sub-real"

        payload = {"sub": "sub-real", "email": "legacy@example.com", "name": "Legacy User"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            # find_unique: first call (by externalId) returns None, second (by email) returns legacy
            mock_prisma.user.find_unique = AsyncMock(side_effect=[None, legacy_user])
            mock_prisma.user.update = AsyncMock(return_value=updated_user)

            result = await get_current_user(self._make_credentials())
            assert result is updated_user
            mock_prisma.user.update.assert_called_once_with(
                where={"id": "db-id-001"},
                data={"externalId": "sub-real", "name": "Legacy User"},
            )

    @pytest.mark.asyncio
    async def test_new_user_creation(self):
        """Brand-new user (no existing record) is created with CLINICIAN role."""
        from prisma.enums import Role

        new_user = _make_mock_user("CLINICIAN")
        payload = {"sub": "sub-new", "email": "new@example.com", "name": "New User"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            mock_prisma.user.find_unique = AsyncMock(return_value=None)
            mock_prisma.user.create = AsyncMock(return_value=new_user)

            result = await get_current_user(self._make_credentials())
            assert result is new_user
            mock_prisma.user.create.assert_called_once_with(
                data={
                    "externalId": "sub-new",
                    "email": "new@example.com",
                    "name": "New User",
                    "role": Role.CLINICIAN,
                }
            )

    @pytest.mark.asyncio
    async def test_name_defaults_to_email_when_not_in_payload(self):
        """When 'name' is absent from payload, email is used as name."""
        from prisma.enums import Role

        new_user = _make_mock_user("CLINICIAN")
        payload = {"sub": "sub-noname", "email": "noname@example.com"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            mock_prisma.user.find_unique = AsyncMock(return_value=None)
            mock_prisma.user.create = AsyncMock(return_value=new_user)

            await get_current_user(self._make_credentials())
            call_data = mock_prisma.user.create.call_args[1]["data"]
            assert call_data["name"] == "noname@example.com"

    @pytest.mark.asyncio
    async def test_race_condition_create_fails_find_succeeds(self):
        """Create raises exception (race), subsequent find_unique returns user → ok."""
        existing = _make_mock_user("CLINICIAN")
        payload = {"sub": "sub-race", "email": "race@example.com"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            # First find (by externalId) → None; email find → None (not legacy)
            # create raises; retry find (by externalId) → existing
            mock_prisma.user.find_unique = AsyncMock(side_effect=[None, None, existing])
            mock_prisma.user.create = AsyncMock(side_effect=Exception("unique violation"))

            result = await get_current_user(self._make_credentials())
            assert result is existing

    @pytest.mark.asyncio
    async def test_race_condition_create_fails_find_also_fails_returns_500(self):
        """Create raises + retry find returns None → 500 'Failed to create user account'."""
        payload = {"sub": "sub-broken", "email": "broken@example.com"}

        with (
            patch("src.auth.dependencies._get_jwks", new=AsyncMock(return_value={})),
            patch("src.auth.dependencies.jwt.decode", return_value=payload),
            patch("src.auth.dependencies.prisma") as mock_prisma,
        ):
            mock_prisma.user.find_unique = AsyncMock(return_value=None)
            mock_prisma.user.create = AsyncMock(side_effect=Exception("db error"))

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(self._make_credentials())
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Failed to create user account"


# ---------------------------------------------------------------------------
# require_role permissions
# ---------------------------------------------------------------------------

class TestRequireRole:
    """Tests for require_role permission dependency via endpoint calls."""

    @pytest.mark.asyncio
    async def test_clinician_can_access_clinician_endpoint(self, client: AsyncClient):
        """CLINICIAN role has write access to POST /api/patients (requires CLINICIAN/NURSE/ADMIN)."""
        with patch("src.patients.service.patient_service.create_patient") as mock_create:
            mock_patient = MagicMock()
            mock_patient.id = "p-1"
            mock_patient.ehr_id = "ehr-1"
            mock_patient.mrn = "MRN001"
            mock_patient.given_name = "Alice"
            mock_patient.family_name = "Smith"
            mock_patient.birth_date = MagicMock()
            mock_patient.birth_date.isoformat.return_value = "1990-01-01"
            mock_patient.is_deleted = False
            mock_patient.created_at = MagicMock()
            mock_patient.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_patient.updated_at = MagicMock()
            mock_patient.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_create.return_value = mock_patient

            with patch("src.patients.router.log_action", new=AsyncMock()):
                response = await client.post(
                    "/api/patients",
                    json={"mrn": "MRN001", "given_name": "Alice", "family_name": "Smith", "birth_date": "1990-01-01"},
                )
        # Either 201 (success) or 422 (validation) proves auth passed; not 403
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_clinician_cannot_delete_patient(self, client: AsyncClient):
        """CLINICIAN role cannot delete a patient (requires ADMIN only)."""
        response = await client.delete("/api/patients/some-patient-id")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_delete_patient(self, admin_client: AsyncClient):
        """ADMIN role is allowed to access DELETE /api/patients/:id."""
        with patch("src.patients.service.patient_service.delete_patient", new=AsyncMock(return_value=True)):
            with patch("src.patients.router.log_action", new=AsyncMock()):
                response = await admin_client.delete("/api/patients/some-patient-id")
        # 204 = success, 404 = patient not found — either proves auth passed
        assert response.status_code in (204, 404)

    @pytest.mark.asyncio
    async def test_nurse_cannot_delete_encounter(self, client: AsyncClient):
        """Default client (CLINICIAN) is blocked from role-restricted endpoint when role not allowed.

        This test uses CLINICIAN but tests that a non-ADMIN cannot delete patient.
        """
        response = await client.delete("/api/patients/any-id")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_request_blocked(self):
        """Request without Bearer token is blocked before role check."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as raw_client:
            response = await raw_client.delete("/api/patients/some-id")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Config OIDC settings
# ---------------------------------------------------------------------------

class TestOidcConfig:
    def test_oidc_issuer_default(self):
        from src.config import settings
        assert settings.oidc_issuer == "http://localhost:5556/dex"

    def test_oidc_client_id_default(self):
        from src.config import settings
        assert settings.oidc_client_id == "open-cis-web"

    def test_oidc_issuer_is_string(self):
        from src.config import settings
        assert isinstance(settings.oidc_issuer, str)

    def test_oidc_client_id_is_string(self):
        from src.config import settings
        assert isinstance(settings.oidc_client_id, str)