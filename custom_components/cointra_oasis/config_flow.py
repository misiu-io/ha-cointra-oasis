"""User-facing account setup, reauthentication and polling options."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import (
    CointraApiError,
    CointraAuthError,
    CointraCloudApi,
    CointraRateLimited,
    DEFAULT_POLL_MINUTES,
    DOMAIN,
)


LOGIN_SCHEMA = vol.Schema(
    {vol.Required("username"): str, vol.Required("password"): str}
)


class CointraOasisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one Cointra/Ferroli account and select its heater."""

    VERSION = 1

    def __init__(self) -> None:
        self._username = ""
        self._password = ""
        self._devices: list[dict] = []

    async def _get_devices(self, username: str, password: str) -> list[dict]:
        api = CointraCloudApi(async_get_clientsession(self.hass), username, password)
        token = await api.login()
        return await api.list_devices(token)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                devices = await self._get_devices(
                    user_input["username"], user_input["password"]
                )
            except CointraAuthError:
                errors["base"] = "invalid_auth"
            except CointraRateLimited:
                errors["base"] = "rate_limited"
            except (CointraApiError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self._username = user_input["username"]
                    self._password = user_input["password"]
                    self._devices = devices
                    if len(devices) == 1:
                        return await self._create_entry(devices[0])
                    return await self.async_step_device()

        return self.async_show_form(
            step_id="user", data_schema=LOGIN_SCHEMA, errors=errors
        )

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            device = next(
                d for d in self._devices
                if d.get("deviceId") == user_input["device_id"]
            )
            return await self._create_entry(device)
        options = {
            d["deviceId"]: d.get("deviceName") or d.get("modelDescription") or d["deviceId"]
            for d in self._devices if d.get("deviceId")
        }
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required("device_id"): vol.In(options)}),
        )

    async def _create_entry(self, device):
        device_id = device["deviceId"]
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()
        name = device.get("deviceName") or "Cointra Oasis Tech"
        return self.async_create_entry(
            title=name,
            data={
                "username": self._username,
                "password": self._password,
                "device_id": device_id,
                "device_name": name,
                "model": device.get("modelDescription") or "Oasis Tech",
                "serial_number": device.get("serialNumber"),
                "mac_address": device.get("macAddressWifiModule"),
            },
        )

    async def async_step_reauth(self, entry_data):
        """Begin a user-driven correction of rejected credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                devices = await self._get_devices(
                    user_input["username"], user_input["password"]
                )
            except CointraAuthError:
                errors["base"] = "invalid_auth"
            except CointraRateLimited:
                errors["base"] = "rate_limited"
            except CointraApiError:
                errors["base"] = "cannot_connect"
            else:
                entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
                if entry and any(d.get("deviceId") == entry.data["device_id"] for d in devices):
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            "username": user_input["username"],
                            "password": user_input["password"],
                        },
                    )
                errors["base"] = "no_devices"
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=LOGIN_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CointraOasisOptionsFlow()


class CointraOasisOptionsFlow(config_entries.OptionsFlow):
    """Configure how often the complete, read-only response is fetched."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "poll_minutes",
                        default=options.get("poll_minutes", DEFAULT_POLL_MINUTES),
                    ): vol.In([30, 60, 120, 180, 240, 360]),
                }
            ),
        )
