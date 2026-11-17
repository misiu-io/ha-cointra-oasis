"""Read-only on/off status entities from the heater's cloud data."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity


BINARY_SENSORS = (
    BinarySensorEntityDescription(key="isSchedulingEnabled", name="Scheduling enabled"),
    BinarySensorEntityDescription(key="slotRunning", name="Schedule slot active"),
    BinarySensorEntityDescription(key="isAntilegionellaRunning", name="Anti-legionella running"),
    BinarySensorEntityDescription(key="isPhotovoltaicActive", name="Photovoltaic active"),
    BinarySensorEntityDescription(key="isSmartGridActive", name="Smart grid active"),
    BinarySensorEntityDescription(key="isThermicSolarActive", name="Solar thermal active"),
    BinarySensorEntityDescription(key="isAntifreezeActive", name="Antifreeze active"),
    BinarySensorEntityDescription(key="userSilentModeEnabled", name="Requested silent mode"),
    BinarySensorEntityDescription(key="currentSilentModeEnabled", name="Actual silent mode"),
    BinarySensorEntityDescription(
        key="alarm", name="Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="isDataReadFromDevice", name="Data read from device",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(CointraOasisBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class CointraOasisBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A boolean status or alarm; no controls are exposed."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def is_on(self):
        values = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "slotRunning":
            value = (values.get("currentSchedulingSlot") or {}).get(
                "isSchedulingSlotInRunning"
            )
        elif key == "alarm":
            if "alarm" not in values:
                return None
            return values["alarm"] is not None
        else:
            value = values.get(key)
        return value if isinstance(value, bool) else None
