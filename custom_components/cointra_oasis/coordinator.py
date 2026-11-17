"""Ferroli cloud requests, conservative polling and rate-limit handling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONNECTION_NETWORK_MAC
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


DOMAIN = "cointra_oasis"
AUTH_URL = "https://usermanagerservice4s.azurewebsites.net/api/User/login"
API_BASE = "https://foursolid0015-egea.azurewebsites.net"
DEFAULT_BASIC_MINUTES = 30
DEFAULT_FULL_MINUTES = 60
HTTP_TIMEOUT_SECONDS = 20

_LOGGER = logging.getLogger(__name__)


class CointraApiError(Exception):
    """A network, server or invalid-response failure (no sensitive details)."""


class CointraAuthError(CointraApiError):
    """The cloud rejected the account credentials or freshly issued token."""


class CointraRateLimited(CointraApiError):
    """The API requested a pause between calls."""

    def __init__(self, retry_after_seconds: int):
        super().__init__("Ferroli cloud rate limit reached")
        self.retry_after_seconds = retry_after_seconds


class CointraEndpointMissing(CointraApiError):
    """One of the cloud's read endpoints is not available."""


def _retry_after(headers: Any) -> int:
    """Interpret either an HTTP Retry-After duration or HTTP date."""
    raw = headers.get("Retry-After") if headers else None
    if raw:
        try:
            return max(60, int(raw))
        except (ValueError, TypeError):
            try:
                when = parsedate_to_datetime(raw)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                return max(60, int((when - datetime.now(timezone.utc)).total_seconds()))
            except (ValueError, TypeError, OverflowError):
                pass
    return 3600  # Conservative default when no rate-limit window is provided.


class CointraCloudApi:
    """Minimal read-only API client; credentials and tokens are never logged."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self._session = session
        self._username = username
        self._password = password

    async def _request(
        self, method: str, url: str, *, token: str | None = None,
        payload: dict[str, str] | None = None,
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS),
        }
        if method == "POST":
            kwargs["json"] = payload if payload is not None else {}

        try:
            async with self._session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise CointraRateLimited(_retry_after(response.headers))
                if response.status in (401, 403) or (
                    response.status == 400 and token is None
                ):
                    raise CointraAuthError("Ferroli cloud rejected authentication")
                if response.status == 404:
                    raise CointraEndpointMissing("Read endpoint was not found")
                if response.status >= 400:
                    raise CointraApiError(f"Ferroli cloud returned HTTP {response.status}")
                try:
                    return await response.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError) as exc:
                    raise CointraApiError("Ferroli cloud returned invalid JSON") from exc
        except (aiohttp.ClientError, TimeoutError) as exc:
            # Never stringify HTTP transport exceptions: URLs can carry secrets.
            raise CointraApiError("Connection to Ferroli cloud failed") from exc

    async def login(self) -> str:
        """Obtain a token for this one polling cycle, without storing it."""
        result = await self._request(
            "POST",
            AUTH_URL,
            payload={"userName": self._username, "password": self._password},
        )
        token = result.get("accessToken") if isinstance(result, dict) else None
        if not isinstance(token, str) or not token:
            raise CointraAuthError("Login returned no access token")
        return token

    async def list_devices(self, token: str) -> list[dict[str, Any]]:
        result = await self._request(
            "GET", f"{API_BASE}/v1/Device/GetUserDevicesWithSlavePlain", token=token
        )
        if not isinstance(result, list):
            raise CointraApiError("Invalid device-discovery response")
        return [device for device in result if isinstance(device, dict)]

    async def read_basic(self, token: str, device_id: str) -> dict[str, Any]:
        result = await self._request(
            "GET", f"{API_BASE}/v1/Device/{device_id}/GetDeviceLastValues",
            token=token,
        )
        if not isinstance(result, dict):
            raise CointraApiError("Invalid basic-values response")
        return result

    async def read_full(self, token: str, device_id: str) -> dict[str, Any]:
        result = await self._request(
            "GET", f"{API_BASE}/v1/DeviceCommand/{device_id}/GetAllLastValuesFromDevice",
            token=token,
        )
        if not isinstance(result, dict):
            raise CointraApiError("Invalid full-values response")
        return result


class CointraOasisCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll basic and full read endpoints without overlapping requests."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: CointraCloudApi
    ) -> None:
        self.api = api
        self.device_id = entry.data["device_id"]
        self.device_name = entry.data.get("device_name") or "Cointra Oasis Tech"
        self.model = entry.data.get("model") or "Oasis Tech"
        self.serial_number = entry.data.get("serial_number")
        self.mac_address = entry.data.get("mac_address")
        self.basic_minutes = int(
            entry.options.get("basic_minutes", DEFAULT_BASIC_MINUTES)
        )
        self.full_minutes = int(
            entry.options.get("full_minutes", DEFAULT_FULL_MINUTES)
        )
        self._last_full: datetime | None = None
        self._pause_until: datetime | None = None
        self._failures = 0
        self._basic_supported = True
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.device_id}",
            update_interval=timedelta(minutes=self.basic_minutes),
            config_entry=entry,
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """One HA device containing all sensors and the actual Wi-Fi MAC."""
        data = self.data or {}
        model = self.model
        if "oasis" not in model.lower():
            model = f"Oasis Tech {model}"
        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
            "manufacturer": "Cointra / Ferroli",
            "model": model,
        }
        serial = data.get("serialNumber") or self.serial_number
        mac = data.get("macAddressWifiModule") or self.mac_address
        firmware = data.get("firmwareVersionMotherBoard")
        if serial:
            info["serial_number"] = serial
        if mac:
            info["connections"] = {(CONNECTION_NETWORK_MAC, mac)}
        if firmware:
            info["sw_version"] = str(firmware)
        return info

    async def _async_update_data(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        full_due = (
            self._last_full is None
            or now - self._last_full >= timedelta(minutes=self.full_minutes) - timedelta(seconds=10)
        )

        if not self._basic_supported and not full_due and self.data:
            # Unknown basic endpoint: avoid extra device queries; wait for full.
            return self.data

        if self._pause_until is not None and now < self._pause_until:
            raise UpdateFailed("Ferroli cloud polling is temporarily paused")

        try:
            # Exactly one login and one data GET per normal cycle.
            token = await self.api.login()
            if full_due:
                values = await self.api.read_full(token, self.device_id)
            else:
                values = await self.api.read_basic(token, self.device_id)
        except CointraAuthError as exc:
            # Do not try the same password again on a timer after an auth error.
            raise ConfigEntryAuthFailed("Cointra credentials need attention") from exc
        except CointraEndpointMissing as exc:
            if not full_due:
                self._basic_supported = False
                _LOGGER.warning(
                    "Basic read endpoint not available; using hourly full reads only"
                )
            raise UpdateFailed(str(exc)) from exc
        except CointraRateLimited as exc:
            seconds = max(1800, min(exc.retry_after_seconds, 86400))
            self._pause_until = now + timedelta(seconds=seconds)
            _LOGGER.warning("Ferroli API rate limited; pausing for %d minutes", seconds // 60)
            raise UpdateFailed("Ferroli cloud rate limit reached") from exc
        except CointraApiError as exc:
            self._failures += 1
            delay_minutes = min(1440, 30 * (2 ** min(self._failures - 1, 6)))
            self._pause_until = now + timedelta(minutes=delay_minutes)
            raise UpdateFailed(str(exc)) from exc

        if values.get("deviceId") not in (None, self.device_id):
            raise UpdateFailed("Cloud response belongs to an unexpected device")
        if "h2OTemperature" not in values:
            raise UpdateFailed("Cloud response lacks the expected water-temperature field")

        self._failures = 0
        self._pause_until = None
        if full_due:
            self._last_full = now
            return values

        # Basic reads omit detailed probe fields. Preserve their last readings.
        return {**(self.data or {}), **values}
