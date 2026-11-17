# Ferroli Home / Four Solid API notes

These are notes from investigating the cloud API used with a Cointra Oasis Tech 200 HT through the Ferroli Home / Four Solid app. They are **not official API documentation**. Paths and field names can change without notice; only one appliance and set of firmware versions has been tested.

Everything the Home Assistant integration sends is read-only with respect to the heater. It performs one login followed by a GET for discovery or a full snapshot. Other paths below are documented for research and are **not used by the integration**.

## Services and authorization

| Service | Host |
| --- | --- |
| User authentication | `https://usermanagerservice4s.azurewebsites.net` |
| Heater API | `https://foursolid0015-egea.azurewebsites.net` |

`POST /api/User/login` accepts JSON of the following shape, with the **user's own** app credentials:

```json
{"userName": "<your-app-email>", "password": "<your-app-password>"}
```

The JSON response contains an `accessToken` (and may contain other token fields). Subsequent requests carry `Authorization: Bearer <accessToken>`. In my tests the token was short-lived, about five minutes, so the integration requests a fresh token for each poll and does not persist it. Never copy a live token or credentials into an issue or repository.

## Endpoints

| Method | Relative path | Status |
| --- | --- | --- |
| POST | `/api/User/login` | Used for authentication |
| GET | `/v1/Device/GetUserDevicesWithSlavePlain` | Used to discover devices for an account |
| GET | `/v1/DeviceCommand/{deviceId}/GetAllLastValuesFromDevice` | **Only endpoint used for polling**; observed working in Postman and Home Assistant |
| GET | `/v1/Device/{deviceId}/GetDeviceLastValues` | Investigated in an earlier preview; not sufficiently understood, now removed from code |
| POST | `/v1/DeviceCommand/{deviceId}/GetLastSchedulingFromDevice` | Read-oriented scheduling operation from Swagger; not used or validated in the integration |

The exact energy-history GET and statistics POST route strings are **not confirmed in these notes**, so I have deliberately not guessed their URLs. The Swagger descriptions indicate a date-parameterized history request and a statistics request with `date`, `requestPeriodType`, and `responsePeriodType` fields.

## Full snapshot shape

The following illustrates the fields currently mapped into Home Assistant. It is a **redacted, abridged schema example**, not a verbatim packet and not a promise that all devices return every key:

```json
{
  "deviceId": "<device-id>",
  "h2OTemperature": 57,
  "tankUpperProbeTemperature": 57,
  "tankBottomProbeTemperature": 56,
  "defrostProbeTemperature": 20,
  "externalTemperature": 26,
  "userSetPointTemperature": 58,
  "realSetPointTemperature": 58,
  "userOperationMode": {"name": "Eco"},
  "currentOperationMode": {"name": "Eco"},
  "isSchedulingEnabled": true,
  "currentSchedulingSlot": {
    "timeSlotStartOn": "08:00:00",
    "timeSlotEndOn": "14:00:00",
    "isSchedulingSlotInRunning": true
  },
  "alarm": null,
  "isAntilegionellaRunning": false,
  "isAntifreezeActive": false,
  "isPhotovoltaicActive": false,
  "isSmartGridActive": false,
  "isThermicSolarActive": false,
  "userSilentModeEnabled": false,
  "currentSilentModeEnabled": false,
  "firmwareVersionMotherBoard": "1.7",
  "firmwareVersionWifiModule": "2.2",
  "firmwareVersionDisplay": "1.0",
  "lastCommunicationDate": "<timestamp>",
  "macAddressWifiModule": "<redacted>"
}
```

`alarm: null` meant **no active alarm** in the verified full response. A prior integration release incorrectly treated anything other than `null`, including zero or false, as a problem when the partial endpoint returned a different shape. Version 0.1.2 uses truthiness, treating null, zero, false and empty values as clear, with absent alarm information left unknown.

Known API states also include the data-read flag `isDataReadFromDevice`. Firmware reports refer to **three components**, not one overall appliance version. Additional slave, cascade, and valve properties were present in Swagger but have deliberately not been mapped without further verification.

## Energy and history: unresolved

The API documentation suggests statistics including `totalElectricityConsumption`, `totalEnergyProduced`, `totalRenewableEnergy`, and a `chartSeries` collection. A statistics request uses fields resembling:

```json
{
  "date": "<format not confirmed>",
  "requestPeriodType": "<value not confirmed>",
  "responsePeriodType": "<value not confirmed>"
}
```

That is a **shape reference, not a working request**. The date format and permitted period values have not been established; my Postman trials returned HTTP 400. The phone app itself can display energy information, but I will not fabricate a consumption sensor from an unverified cloud response. I currently rely on separate electrical metering (Shelly and other monitors) for actual power consumption.

## Boundaries and troubleshooting

The integration does **not** call endpoints for changing operating mode, setpoints, timers, scheduling or anti-legionella behavior. The fact that Swagger may describe those operations is not permission to try them on a live heater.

The full snapshot is currently polled every 30 minutes by default. Each cycle is one short-lived login and one full GET. A failed request leaves Home Assistant entities unavailable, rather than substituting false, zero or stale values. HTTP 429 backoff and credential reauthentication are handled in the code.

The RS-485/Modbus connection is a separate possible route. I have found no verified register map for the Cointra Oasis Tech 200 HT firmware, and these cloud JSON names should **not** be mistaken for Modbus register numbers. If you can share a verified, model-specific mapping or redacted API responses, please open a [GitHub issue](https://github.com/misiu-io/ha-cointra-oasis/issues).
