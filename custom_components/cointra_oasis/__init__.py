"""Read-only cloud monitoring for Cointra Oasis Tech heat-pump water heaters."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import CointraCloudApi, CointraOasisCoordinator


PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the heater using credentials held by Home Assistant."""
    api = CointraCloudApi(
        async_get_clientsession(hass),
        entry.data["username"],
        entry.data["password"],
    )
    coordinator = CointraOasisCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply changed polling settings by reloading the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unregister entities and stop background updates."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return True
    return False
