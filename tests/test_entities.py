"""Isolated entity mapping tests using the user's verified response shapes."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


class Description:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.device_class = kwargs.get("device_class")


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


def load_entity_modules():
    modules = (
        "homeassistant", "homeassistant.components",
        "homeassistant.components.sensor", "homeassistant.components.binary_sensor",
        "homeassistant.const", "homeassistant.helpers",
        "homeassistant.helpers.update_coordinator", "homeassistant.util",
        "homeassistant.util.dt",
    )
    for name in modules:
        sys.modules[name] = ModuleType(name)
    sensors = sys.modules["homeassistant.components.sensor"]
    sensors.SensorDeviceClass = SimpleNamespace(TEMPERATURE="temperature", TIMESTAMP="timestamp")
    sensors.SensorEntity = type("SensorEntity", (), {})
    sensors.SensorEntityDescription = Description
    sensors.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement")

    binary = sys.modules["homeassistant.components.binary_sensor"]
    binary.BinarySensorDeviceClass = SimpleNamespace(PROBLEM="problem")
    binary.BinarySensorEntity = type("BinarySensorEntity", (), {})
    binary.BinarySensorEntityDescription = Description

    const = sys.modules["homeassistant.const"]
    const.EntityCategory = SimpleNamespace(DIAGNOSTIC="diagnostic")
    const.UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity
    sys.modules["homeassistant.util"].dt = sys.modules["homeassistant.util.dt"]
    dt = sys.modules["homeassistant.util.dt"]
    dt.parse_datetime = datetime.fromisoformat
    dt.as_utc = lambda d: d.astimezone(timezone.utc)

    root = Path(__file__).resolve().parents[1] / "custom_components" / "cointra_oasis"
    result = []
    for filename in ("sensor.py", "binary_sensor.py"):
        spec = importlib.util.spec_from_file_location(f"cointra_test_{filename[:-3]}", root / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result.append(module)
    return result


sensor_module, binary_module = load_entity_modules()


class EntityTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = SimpleNamespace(
            device_id="heater", device_info={"name": "L&V ACS"},
            data={
                "tankUpperProbeTemperature": 54,
                "tankBottomProbeTemperature": -32768,
                "defrostProbeTemperature": 21,
                "currentOperationMode": {"name": "Standby"},
                "currentSchedulingSlot": {
                    "timeSlotStartOn": "00:00:00", "timeSlotEndOn": "05:30:00",
                    "isSchedulingSlotInRunning": False,
                },
                "isSchedulingEnabled": True,
                "isPhotovoltaicActive": False,
                "alarm": None,
                "lastCommunicationDate": "2026-11-11T23:20:00+00:00",
            },
        )

    def sensor(self, key):
        description = next(d for d in sensor_module.SENSORS if d.key == key)
        return sensor_module.CointraOasisSensor(self.coordinator, description)

    def binary(self, key):
        description = next(d for d in binary_module.BINARY_SENSORS if d.key == key)
        return binary_module.CointraOasisBinarySensor(self.coordinator, description)

    def test_temperatures_and_invalid_sentinel(self):
        self.assertEqual(self.sensor("tankUpperProbeTemperature").native_value, 54)
        self.assertIsNone(self.sensor("tankBottomProbeTemperature").native_value)
        self.assertEqual(self.sensor("defrostProbeTemperature").native_value, 21)

    def test_mode_and_slot(self):
        self.assertEqual(self.sensor("currentOperationMode").native_value, "Standby")
        self.assertEqual(self.sensor("slotEnd").native_value, "05:30:00")

    def test_timestamp(self):
        value = self.sensor("lastCommunicationDate").native_value
        self.assertEqual(value.hour, 23)
        self.assertIsNotNone(value.tzinfo)

    def test_binary_status_and_alarm(self):
        self.assertTrue(self.binary("isSchedulingEnabled").is_on)
        self.assertFalse(self.binary("slotRunning").is_on)
        self.assertFalse(self.binary("isPhotovoltaicActive").is_on)
        self.assertFalse(self.binary("alarm").is_on)

    def test_alarm_false_positives_are_not_problems(self):
        for value in (None, False, 0, "", "0", "false", [], {}):
            with self.subTest(alarm=value):
                self.coordinator.data["alarm"] = value
                self.assertFalse(self.binary("alarm").is_on)

    def test_real_alarm_and_absent_alarm_are_distinct(self):
        for value in (True, 2, "overheat", {"code": 2}):
            with self.subTest(alarm=value):
                self.coordinator.data["alarm"] = value
                self.assertTrue(self.binary("alarm").is_on)
        self.coordinator.data.pop("alarm")
        self.assertIsNone(self.binary("alarm").is_on)

    def test_absent_schedule_is_not_false(self):
        self.coordinator.data.pop("isSchedulingEnabled")
        self.coordinator.data.pop("currentSchedulingSlot")
        self.assertIsNone(self.binary("isSchedulingEnabled").is_on)
        self.assertIsNone(self.binary("slotRunning").is_on)


if __name__ == "__main__":
    unittest.main()
