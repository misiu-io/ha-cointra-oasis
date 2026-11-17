"""No-network tests for the cloud client and polling coordinator.

Run from the repository root with:
    python -m unittest discover -s tests -v

Home Assistant is stubbed for these isolated API tests; a real Home Assistant
startup/config-flow test is still required on an HA installation.
"""

from __future__ import annotations

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
        "homeassistant.helpers.device_registry", "homeassistant.helpers.update_coordinator",
    ):
        sys.modules[name] = ModuleType(name)

    sys.modules["homeassistant.config_entries"].ConfigEntry = object
    # 2026.11 exports this from device_registry, not homeassistant.const.
    sys.modules["homeassistant.helpers.device_registry"].CONNECTION_NETWORK_MAC = "mac"
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


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def make_coordinator(self, api=None):
        entry = SimpleNamespace(
            data={"device_id": "heater", "device_name": "L&V ACS", "model": "200 HT"},
            options={},
        )
        return api_module.CointraOasisCoordinator(object(), entry, api or FakeApi())

    async def test_every_poll_uses_complete_endpoint(self):
        api = FakeApi()
        coordinator = self.make_coordinator(api)
        await coordinator._async_update_data()
        await coordinator._async_update_data()
        self.assertEqual(api.calls, ["login", "full", "login", "full"])

    async def test_full_response_never_merges_stale_fields(self):
        api = FakeApi()
        coordinator = self.make_coordinator(api)
        coordinator.data = {
            "deviceId": "heater", "h2OTemperature": 53,
            "isSchedulingEnabled": False, "firmwareVersionDisplay": None,
        }
        result = await coordinator._async_update_data()
        self.assertNotIn("isSchedulingEnabled", result)
        self.assertNotIn("firmwareVersionDisplay", result)
        self.assertEqual(result["tankUpperProbeTemperature"], 55)

    async def test_old_polling_options_are_ignored(self):
        api = FakeApi()
        entry = SimpleNamespace(
            data={"device_id": "heater", "device_name": "L&V ACS", "model": "200 HT"},
            options={"basic_minutes": 60, "full_minutes": 120},
        )
        coordinator = api_module.CointraOasisCoordinator(object(), entry, api)
        self.assertEqual(coordinator.poll_minutes, 30)
        await coordinator._async_update_data()
        self.assertEqual(api.calls, ["login", "full"])

    async def test_reject_missing_or_invalid_temperature(self):
        api = FakeApi()
        coordinator = self.make_coordinator(api)
        async def incomplete_read(token, device_id):
            return {"deviceId": device_id, "isSchedulingEnabled": False}
        api.read_full = incomplete_read
        with self.assertRaises(api_module.UpdateFailed):
            await coordinator._async_update_data()

        async def null_read(token, device_id):
            return {"deviceId": device_id, "h2OTemperature": None}
        api.read_full = null_read
        with self.assertRaises(api_module.UpdateFailed):
            await coordinator._async_update_data()

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
