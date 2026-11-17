"""No-network tests for the cloud client and polling coordinator.

Run from the repository root with:
    python -m unittest discover -s tests -v

Home Assistant is stubbed for these isolated API tests; a real Home Assistant
startup/config-flow test is still required on an HA installation.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


def load_coordinator():
    """Load the production module with minimal HA stubs for local unit tests."""
    for name in (
        "homeassistant", "homeassistant.config_entries", "homeassistant.const",
        "homeassistant.core", "homeassistant.exceptions", "homeassistant.helpers",
        "homeassistant.helpers.update_coordinator",
    ):
        sys.modules[name] = ModuleType(name)

    sys.modules["homeassistant.config_entries"].ConfigEntry = object
    sys.modules["homeassistant.const"].CONNECTION_NETWORK_MAC = "mac"
    sys.modules["homeassistant.core"].HomeAssistant = object

    class FakeAuthFailed(Exception):
        pass

    class FakeUpdateFailed(Exception):
        pass

    class FakeCoordinator:
        def __class_getitem__(cls, _):
            return cls

        def __init__(self, *args, **kwargs):
            self.data = None

    sys.modules["homeassistant.exceptions"].ConfigEntryAuthFailed = FakeAuthFailed
    updates = sys.modules["homeassistant.helpers.update_coordinator"]
    updates.DataUpdateCoordinator = FakeCoordinator
    updates.UpdateFailed = FakeUpdateFailed

    path = Path(__file__).resolve().parents[1] / "custom_components" / "cointra_oasis" / "coordinator.py"
    spec = importlib.util.spec_from_file_location("cointra_test_coordinator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api_module = load_coordinator()


class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None):
        self.status = status
        self.payload = payload
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, **kwargs):
        return self.payload


class FakeSession:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.replies.pop(0)


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_and_full_read_use_correct_requests(self):
        session = FakeSession([
            FakeResponse(payload={"accessToken": "a.jwt.token", "refreshToken": "ignored"}),
            FakeResponse(payload={"deviceId": "heater", "h2OTemperature": 54}),
        ])
        api = api_module.CointraCloudApi(session, "example@example.com", "secret")
        token = await api.login()
        reading = await api.read_full(token, "heater")
        self.assertEqual(reading["h2OTemperature"], 54)
        self.assertEqual(session.calls[0][0], "POST")
        self.assertEqual(session.calls[0][2]["json"], {
            "userName": "example@example.com", "password": "secret"
        })
        self.assertEqual(session.calls[1][0], "GET")
        self.assertTrue(session.calls[1][1].endswith("/heater/GetAllLastValuesFromDevice"))
        self.assertEqual(session.calls[1][2]["headers"]["Authorization"], "Bearer a.jwt.token")

    async def test_basic_read_endpoint(self):
        session = FakeSession([FakeResponse(payload={"h2OTemperature": 55})])
        api = api_module.CointraCloudApi(session, "a", "b")
        self.assertEqual((await api.read_basic("token", "heater"))["h2OTemperature"], 55)
        self.assertTrue(session.calls[0][1].endswith("/heater/GetDeviceLastValues"))

    async def test_login_rejection_does_not_retry(self):
        session = FakeSession([FakeResponse(status=401)])
        api = api_module.CointraCloudApi(session, "a", "b")
        with self.assertRaises(api_module.CointraAuthError):
            await api.login()
        self.assertEqual(len(session.calls), 1)

    async def test_rate_limit_honours_retry_after(self):
        session = FakeSession([FakeResponse(status=429, headers={"Retry-After": "5400"})])
        api = api_module.CointraCloudApi(session, "a", "b")
        with self.assertRaises(api_module.CointraRateLimited) as ctx:
            await api.login()
        self.assertEqual(ctx.exception.retry_after_seconds, 5400)


class FakeApi:
    def __init__(self):
        self.calls = []
        self.error = None

    async def login(self):
        self.calls.append("login")
        if self.error:
            raise self.error
        return "token"

    async def read_full(self, token, device_id):
        self.calls.append("full")
        return {
            "deviceId": device_id,
            "h2OTemperature": 54,
            "tankUpperProbeTemperature": 55,
            "isPhotovoltaicActive": False,
        }

    async def read_basic(self, token, device_id):
        self.calls.append("basic")
        return {"deviceId": device_id, "h2OTemperature": 53}


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def make_coordinator(self, api=None):
        entry = SimpleNamespace(
            data={"device_id": "heater", "device_name": "L&V ACS", "model": "200 HT"},
            options={},
        )
        return api_module.CointraOasisCoordinator(object(), entry, api or FakeApi())

    async def test_full_then_basic_preserves_probes(self):
        api = FakeApi()
        coordinator = self.make_coordinator(api)
        full = await coordinator._async_update_data()
        coordinator.data = full
        basic = await coordinator._async_update_data()
        self.assertEqual(api.calls, ["login", "full", "login", "basic"])
        self.assertEqual(basic["h2OTemperature"], 53)
        self.assertEqual(basic["tankUpperProbeTemperature"], 55)

    async def test_full_replaces_basic_after_hour(self):
        api = FakeApi()
        coordinator = self.make_coordinator(api)
        coordinator.data = await coordinator._async_update_data()
        coordinator._last_full = datetime.now(timezone.utc) - timedelta(minutes=61)
        await coordinator._async_update_data()
        self.assertEqual(api.calls[-2:], ["login", "full"])

    async def test_rate_limit_pauses_without_second_login(self):
        api = FakeApi()
        api.error = api_module.CointraRateLimited(3600)
        coordinator = self.make_coordinator(api)
        with self.assertRaises(api_module.UpdateFailed):
            await coordinator._async_update_data()
        with self.assertRaises(api_module.UpdateFailed):
            await coordinator._async_update_data()
        self.assertEqual(api.calls, ["login"])

    async def test_bad_credentials_do_not_retry(self):
        api = FakeApi()
        api.error = api_module.CointraAuthError("bad credentials")
        coordinator = self.make_coordinator(api)
        with self.assertRaises(api_module.ConfigEntryAuthFailed):
            await coordinator._async_update_data()
        self.assertEqual(api.calls, ["login"])

    async def test_reject_wrong_device(self):
        api = FakeApi()
        async def wrong_device(token, device_id):
            return {"deviceId": "another-device", "h2OTemperature": 54}
        api.read_full = wrong_device
        coordinator = self.make_coordinator(api)
        with self.assertRaises(api_module.UpdateFailed):
            await coordinator._async_update_data()


if __name__ == "__main__":
    unittest.main()
