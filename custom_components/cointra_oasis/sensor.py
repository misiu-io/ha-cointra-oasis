"""Temperatures, mode, scheduling text and device diagnostics."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util


def _temperature(key, name):
    return SensorEntityDescription(
        key=key,
        name=name,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )


SENSORS = (
    _temperature("h2OTemperature", "Water temperature"),
    _temperature("tankUpperProbeTemperature", "Tank top temperature"),
    _temperature("tankBottomProbeTemperature", "Tank bottom temperature"),
    _temperature("defrostProbeTemperature", "Coil / defrost temperature"),
    _temperature("externalTemperature", "External air temperature"),
    _temperature("userSetPointTemperature", "Requested setpoint"),
    _temperature("realSetPointTemperature", "Actual setpoint"),
    SensorEntityDescription(key="userOperationMode", name="Requested mode"),
    SensorEntityDescription(key="currentOperationMode", name="Actual mode"),
    SensorEntityDescription(key="slotStart", name="Schedule slot start"),
    SensorEntityDescription(key="slotEnd", name="Schedule slot end"),
    SensorEntityDescription(
        key="lastCommunicationDate", name="Last device communication",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="firmwareVersionWifiModule", name="Wi-Fi firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="firmwareVersionMotherBoard", name="Motherboard firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="firmwareVersionDisplay", name="Display firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="macAddressWifiModule", name="Wi-Fi MAC address",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(CointraOasisSensor(coordinator, d) for d in SENSORS)


class CointraOasisSensor(CoordinatorEntity, SensorEntity):
    """One sensor backed by the shared poll response."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def native_value(self):
        values = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "slotStart":
            return (values.get("currentSchedulingSlot") or {}).get("timeSlotStartOn")
        if key == "slotEnd":
            return (values.get("currentSchedulingSlot") or {}).get("timeSlotEndOn")
        if key in ("userOperationMode", "currentOperationMode"):
            return (values.get(key) or {}).get("name")
        value = values.get(key)
        if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            return None if value == -32768 else value
        if key == "lastCommunicationDate" and isinstance(value, str):
            timestamp = dt_util.parse_datetime(value)
            return dt_util.as_utc(timestamp) if timestamp else None
        return value
