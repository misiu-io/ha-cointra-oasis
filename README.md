# HA Cointra Oasis Tech

**An unofficial, read-only Home Assistant integration for Cointra Oasis Tech heat-pump water heaters.**

This is a small personal project, not a Cointra, Ferroli or Home Assistant product. I am not affiliated with any of them. The integration uses the same cloud account that works with the Ferroli Home / Four Solid mobile app, and it never sends a command to change the heater's settings.

## Why I made this

I bought a **Cointra Oasis Tech 200 HT** hot-water heat pump for my house in Spain. I like the heater, but it has always frustrated me that I couldn't see its temperatures, current mode and scheduling information in Home Assistant alongside everything else in the house.

I initially looked at the unit's RS-485 / Modbus interface. There is an accessible connection on the controller, but finding a trustworthy register map for this model and firmware has been much harder than expected. I still think local access would be interesting, but I haven't got a verified Modbus implementation to share.

Then I looked at the phone app and the cloud API behind it. The Ferroli Home / Four Solid platform appears to serve several related hot-water heaters, including rebadged variants. The Wi-Fi module and cloud interface may therefore be common across more devices than the Cointra model I own. That is promising, but **I have only tested one actual heater** and don't want to pretend compatibility has been established for the others.

I put this integration together so I could get the data into Home Assistant without replacing the manufacturer's controls or upsetting the schedule I already use.

## What it reads

From the heater's full cloud response, Home Assistant can show:

| Group | Read-only information |
| --- | --- |
| Water | Tank top and bottom temperatures, reported water temperature, requested and actual setpoints |
| Operation | Requested and actual operating modes, requested and actual silent mode |
| Scheduling | Whether scheduling is enabled, whether the current slot is active, slot start and end |
| Protection and inputs | Alarm, anti-legionella, antifreeze, photovoltaic, smart-grid and solar-thermal flags |
| Probes | Coil / defrost and external air temperatures |
| Diagnostics | Last device communication, data-read status, motherboard, display and Wi-Fi firmware, Wi-Fi MAC |

The serial number and MAC may also appear in Home Assistant's device details. They are not hard-coded into this project. Unsupported probe values (such as `-32768`) appear as unavailable, not as plausible temperatures. An active scheduling slot does **not** necessarily mean the compressor is running.

The device name you chose in the manufacturer's app is retained. Home Assistant identifies the device by its existing unique ID, so updating the integration should not create a second heater or new entity IDs.

## How it works

You need a working **Ferroli Home / Four Solid app account**, with your heater already visible in the phone app. The Home Assistant setup asks for that account's email and password and, if necessary, which heater to monitor. You don't need to discover Modbus registers, alter the heater or run a separate gateway.

I use the Home Assistant Marketplace to distribute the GitHub repository. It handles installing the custom integration and showing updates. This README deliberately doesn't duplicate the Marketplace's installation interface.

The integration asks the cloud for a fresh, short-lived access token, then makes **one full read request every 30 minutes** by default. You can change that to 60 minutes or longer under the integration's **Configure** option. The shorter, partially understood API call used by older preview versions has been removed: it caused missing or default fields to corrupt otherwise valid Home Assistant readings.

If a request fails, Home Assistant marks the current readings unavailable and retains their history. Missing fields are not silently converted into `Off` or alarm states. Rate limits are respected, and repeated failures back off instead of hammering the service. This is cloud polling, so there is no promise of instant state updates or continued operation if the manufacturer's cloud is unavailable.

## The API I found

The useful information came from the cloud service's Swagger definitions and requests I checked with Postman. The integration itself currently calls only these endpoints:

| Purpose | Method and endpoint | Used? |
| --- | --- | --- |
| Login | `POST /api/User/login` | Yes, once per polling cycle |
| Discover devices | `GET /v1/Device/GetUserDevicesWithSlavePlain` | Yes, during setup |
| Complete heater snapshot | `GET /v1/DeviceCommand/{deviceId}/GetAllLastValuesFromDevice` | Yes, every poll |

The full response includes nested requested/actual modes and a current scheduling slot, plus temperatures, status flags, alarm data and firmware versions. I have documented the relevant JSON names, example shapes, hostnames, and the other endpoints I explored in [API.md](API.md).

Some other Swagger operations look interesting, particularly scheduling details and energy history, but they are **not part of this integration** yet. I do not use any API write command to set temperature, switch modes or change schedules. HTTP `POST` for login is authentication, not a command to the heater.

## What I am deliberately not doing

**No heater control.** This integration is for observing the appliance, not changing it. My existing schedules and the manufacturer's phone app remain in charge. There are no switch, button, climate or water-heater control entities, and no code paths that send configuration commands.

**No made-up energy readings.** I can monitor the actual electrical consumption at home with Shelly and other metering equipment, but that is separate from the manufacturer's historical energy figures. I haven't integrated those statistics because I haven't got the cloud request's date handling working reliably.

**No claim of universal compatibility.** The platform seems to be shared by more than one brand and model, but only my Cointra Oasis Tech 200 HT has been exercised against this code. Cascade devices, slave valves and auxiliary fields are excluded for now.

## Where I could use some help

I would love to hear from anyone with a related Cointra, Ferroli, EGEA or rebadged hot-water heat pump who can test read-only monitoring. In particular, please tell me the model, app you use and the **motherboard, display and Wi-Fi firmware versions**, along with which readings behave correctly. Please **do not publish serial numbers, MAC addresses, email addresses, passwords or API tokens** in an issue.

The energy API has been particularly maddening. Swagger describes date-based statistics with fields such as `date`, `requestPeriodType` and `responsePeriodType`, but my Postman experiments returned HTTP 400 for the date formats I tried. If anyone has worked out its exact accepted format or has clean, redacted examples, that would be extremely useful. I'd also welcome a confirmed Modbus register map for this specific family.

You can raise bugs or share test results in [GitHub Issues](https://github.com/misiu-io/ha-cointra-oasis/issues). This is early software, so I would rather know when a value is wrong than quietly display something misleading.

## Versions and testing

This release is **v0.1.2**, a preview for Home Assistant **2026.11 or newer**. It replaces the two-interval polling design with full reads only and corrects false alarm interpretations. The integration's internal domain remains `cointra_oasis`, which keeps existing installations and entity identifiers compatible.

Release numbers are GitHub Releases tagged `v0.1.2`, `v0.1.3`, and so on. The version inside `manifest.json` matches without the leading `v`. Without a published GitHub Release, the Marketplace shows a commit hash instead of a friendly version number.

The repository includes local, no-network tests, which you can run with:

```bash
python -m unittest discover -s tests -v
```

These tests simulate API responses and a small part of Home Assistant. They catch response-mapping regressions, but **do not replace real testing on Home Assistant Green or other installations**. GitHub Actions also run the tests and the Marketplace validation checks.

For version-specific details, see [CHANGELOG.md](CHANGELOG.md). The [API notes](API.md) are intended for people interested in continuing the investigation.
