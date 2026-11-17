# Cointra Oasis Tech for Home Assistant

Unofficial, **strictly read-only** cloud monitoring for the Cointra Oasis Tech
200 HT family, using the Ferroli Home / Four Solid API. Version 0.1.1 is a
private preview and is **not yet published** to the Home Assistant Marketplace.

This project has been built using API responses verified against one Cointra
Oasis Tech 200 HT. Other models and firmware versions have not been tested.

## Installation (Home Assistant 2026.11 or newer)

1. Unzip the release.
2. Copy only the `cointra_oasis` folder from `custom_components` into
   `/config/custom_components/` on your Home Assistant installation.
3. Restart Home Assistant.
4. Open **Settings > Devices & services > Add integration** and search for
   **Cointra Oasis Tech**.
5. Enter the email and password from **Ferroli Home**. If several devices are
   attached to the account, choose the correct heater.

The integration uses Home Assistant's credential configuration storage. No
credentials are included in these files or in the release ZIP. Home Assistant
configuration storage and backup files still require access protection; they
are not a dedicated encrypted password vault.

## Data and polling

Default polling is **30 minutes** for basic values and **60 minutes** for full
values. At each hourly boundary, a full request replaces the basic request.
Each cycle obtains a fresh access token and immediately sends one read request.
The token is not saved to disk or exposed as an entity.

The supported read endpoints are:

* `GET /v1/Device/{id}/GetDeviceLastValues` for basic values.
* `GET /v1/DeviceCommand/{id}/GetAllLastValuesFromDevice` for full values.

Both use the manufacturer's HTTPS cloud service. Whether the basic GET is
served from a cloud cache remains unverified. Its first production use is
therefore monitored conservatively. If that endpoint returns 404, basic polling
is disabled and only full requests continue at the configured full interval.

To adjust polling, open **Settings > Devices & services > Cointra Oasis Tech >
Configure**. The full interval must be an exact multiple of the basic interval.

All full-temperature probes and auxiliary states are retained through
intervening basic polls. `-32768` probe values are treated as unavailable.
Cascade, slave-valve and slave-temperature data are deliberately omitted.

## Entities

Temperature sensors: water, tank top, tank bottom, coil/defrost, outside air,
requested setpoint and actual setpoint.

Other sensors: requested and actual mode, current scheduled slot start/end,
last heater communication, Wi-Fi, motherboard and display firmware versions,
and actual Wi-Fi MAC address.

Binary sensors: scheduling enabled, current schedule slot active,
anti-legionella running, PV, smart grid, solar thermal, antifreeze, requested and
actual silent mode, alarm, and data-read-from-device status.

The serial number and MAC address also appear in device metadata. Note that
"schedule slot active" does **not** mean the compressor is running.

## Safety and failures

No write endpoints exist in this integration. It cannot change temperatures,
operating modes, schedule slots or appliance settings.

* HTTP 401/403 on a freshly obtained token stops normal polling and asks for
  account reauthentication in Home Assistant.
* HTTP 429 respects a Retry-After interval where supplied, otherwise applies
  a conservative one-hour pause.
* Network and server failures cause capped exponential backoff, with no
  immediate retry or repeated login bursts.
* API errors do not include tokens, passwords or response bodies in logs.
* If a poll fails, entity availability reflects the connection failure;
  Home Assistant history is preserved.

## Not included yet

Energy statistics (manufacturer's date/period API remains unverified), Modbus,
heater control, schedule modification, cascade support, compressor run-state.

## Private preview and eventual Marketplace distribution

For now, install by copying the integration folder as above. The ZIP also
includes `hacs.json` and this README, forming the beginning of a Marketplace
compatible GitHub repository. Publishing later requires creating the public
repository, adding an icon, release tags and automated repository validation.
The current integration itself will not need to be redesigned.

## Verification status

The API endpoints, JSON field names, and successful read data come from the
manufacturer's Swagger specification and user Postman tests. Automated tests
are included in the development package. Compatibility with a running Home
Assistant Green must still be verified after private installation.
