# Cointra Oasis Tech

Read-only monitoring of Cointra Oasis Tech aerothermal domestic hot water (DHW) systems in **Home Assistant**, using the same Ferroli cloud service as the **Ferroli Home / Four Solid** mobile app.

This is an unofficial personal project. It is not affiliated, associated, authorised or endorsed by Cointra or Ferroli.

**What it does:** brings water temperatures, operating modes, setpoints, scheduling status and device diagnostics into Home Assistant. It **does not send control commands** or change the settings of your DHW system.

**Requirements:** Home Assistant 2026.11 or newer, plus a working Ferroli Home / Four Solid account with a device already registered. It needs internet access to the cloud service; it is not a local integration.

<!-- ha-marketplace:exclude-start -->
## Installation

1. In Home Assistant, open **Settings → Marketplace → Add from link**.
2. Add the [Cointra Oasis Tech repository](https://github.com/misiu-io/ha-cointra-oasis): `https://github.com/misiu-io/ha-cointra-oasis`.
3. Open **Cointra Oasis Tech** in Marketplace and select **Install**.
4. Go to **Settings → Devices & services → Add Integration** and select **Cointra Oasis Tech**.

Marketplace can install this as a custom repository. It is not yet listed in the public Marketplace catalog. An update to an already loaded integration requires a Home Assistant restart.
<!-- ha-marketplace:exclude-end -->

## Setup

Enter the email address and password used by your **Ferroli Home / Four Solid** mobile app. The integration retrieves the devices registered to your account. Select the device to add; if there is only one, it is selected automatically. Its name in the mobile app is used in Home Assistant.

The integration authenticates with the cloud API and reads the complete device state every **30 minutes** by default. You can change the polling interval through the integration's **Configure** option.

Account credentials are stored in Home Assistant's configuration entry for authentication. Protect your Home Assistant configuration files and backups.

## What you'll see

| Group | Readings |
| --- | --- |
| Water and temperature | Water temperature, tank top and bottom temperatures, coil / defrost temperature, external air temperature |
| Operation | Actual and requested modes, actual and requested setpoints |
| Scheduling | Scheduling enabled, active slot, slot start and end |
| Status | Alarm, anti-legionella, antifreeze, photovoltaic, smart grid, solar thermal and silent-mode states |
| Diagnostics | Device communication time, firmware versions, Wi-Fi MAC address and device data-read status |

All entities are read-only. Some readings may be unavailable if your particular device does not provide them.

## Compatibility and limitations

**Tested:** Cointra Oasis Tech 200 HT, using my own unit.

Cointra is part of the Ferroli Group. The [manufacturer's declaration of conformity](https://www.cointra.es/wp-content/uploads/2023/10/declaracion-conformidad-oasis-tech.pdf) groups the Oasis Tech 200 HT with the **Ferroli EGEA Tech 200 HT** and **Dora Tech 200 HT**. They appear to share a product platform and related Wi-Fi modules, but I have **not tested** those models or their firmware. Compatibility is not guaranteed. Devices using Tuya / Smart Life are not supported.

**No control:** The integration deliberately avoids writes. Different firmware versions may handle commands differently, and there have been reports of control attempts affecting existing schedules.

**No energy statistics yet:** The cloud service appears to expose consumption and production data, but I have not been able to obtain reliable results consistently. I currently monitor electricity use separately with Shelly and other power-monitoring devices.

**Cloud dependency:** The integration relies on an unofficial API that can change without notice. A service outage, authentication change or unsupported response may temporarily make entities unavailable. As with any third-party custom integration, I cannot guarantee it will behave correctly on every Home Assistant or firmware version.

## Why I made this

While renovating an old house in Spain in 2024, I replaced the plumbing and electrics and installed a **Cointra Oasis Tech 200 HT** high-temperature aerothermal DHW system. Almost everything else in the house is connected to Home Assistant, so it was frustrating not to see its temperatures, mode and other readings there too.

I looked into the controller's Modbus / cascade connection, but couldn't establish a usable register map or confirm a suitable local interface. That led me to investigate the Ferroli cloud API used by the mobile app.

## Bugs, testing and contributions

If you try this with another model or firmware version, I'd be interested to hear what works. Please [open an issue](https://github.com/misiu-io/ha-cointra-oasis/issues/new) with the model, mobile app, motherboard / display / Wi-Fi firmware versions and the readings or errors you see. Don't include account credentials, serial numbers or MAC addresses.

This is still an early project, tested on one physical system. Local automated tests are included, but don't replace real-device testing.

For further details, see [the API notes](API.md) and [changelog](CHANGELOG.md).
