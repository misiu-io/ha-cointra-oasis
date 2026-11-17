# HA Cointra Oasis Tech

An unofficial, read-only Home Assistant integration for Cointra Oasis Tech aerothermal hot-water systems, using the Ferroli Home / Four Solid cloud API.

This is a small personal project and is not affiliated, associated, authorised, endorsed by, or in any way officially connected with Cointra or Ferroli.

The integration uses the same email address and password as your Ferroli Home / Four Solid mobile app account. For now, it is strictly read-only: it does not send commands to change the aerothermal system's settings.

## Why I made this

In 2024, I started renovating a very old house in Spain. It quickly became clear that practically everything needed work, including the plumbing and electrics. As part of that renovation, I bought a **Cointra Oasis Tech 200 HT** heat pump for domestic hot water.

It has always frustrated me that I couldn't see its temperatures, current operating mode and other parameters in Home Assistant alongside everything else in the house.

I first investigated the connection on the controller motherboard as a possible route to local monitoring. There are references to Modbus and cascade systems, but I haven't found a reliable register map or confirmed that the available connector provides a conventional RS-485 Modbus interface for direct monitoring. It may be intended for communication between units in a cascade rather than general integration.

So I turned to the cloud API used by the mobile app. Related Cointra and Ferroli systems appear to use a common Wi-Fi module and cloud platform, which suggests that the same API may work with other models. This integration uses the API calls behind the Ferroli Home / Four Solid app, but **I have only tested it on my own physical Oasis Tech 200 HT**. I can't confirm compatibility with other models or firmware versions.

## Supported devices

Currently tested on the **Cointra Oasis Tech 200 HT**. Other models and firmware versions may work, but I haven't tested them.

## Available entities

The integration currently provides these read-only entities in Home Assistant:

| Type | Entities |
| --- | --- |
| Temperature sensors | Water temperature, Tank top temperature, Tank bottom temperature, Coil / defrost temperature, External air temperature, Requested setpoint, Actual setpoint |
| Operating mode sensors | Requested mode, Actual mode |
| Scheduling sensors | Schedule slot start, Schedule slot end |
| Status binary sensors | Scheduling enabled, Schedule slot active, Anti-legionella running, Photovoltaic active, Smart grid active, Solar thermal active, Antifreeze active, Requested silent mode, Actual silent mode, Alarm |
| Diagnostic sensors | Last device communication, Wi-Fi firmware, Motherboard firmware, Display firmware, Wi-Fi MAC address |
| Diagnostic binary sensor | Data read from device |

On my device, some unsupported probes return values such as `0` or `-32768`. The integration currently ignores `-32768`; zero readings from unsupported probes still need to be handled more carefully.

## Setup and polling

You need a valid **Ferroli Home / Four Solid** account with your aerothermal system already registered in the mobile app. During setup, the Home Assistant integration asks for your account email address and password. It then reads the devices registered to your account. If more than one device is found, you choose which one to add. If there is only one, it is selected automatically. The device keeps the name registered in the mobile app, which is also used as its name in Home Assistant.

The integration authenticates with the cloud API and makes a full device read every **30 minutes** by default. You can change the polling interval under the integration's **Configure** option.

## API calls used

These are the three API calls used by the integration:

| Purpose | Method and endpoint |
| --- | --- |
| Login and authentication | `POST /api/User/login` |
| Find devices registered to the account | `GET /v1/Device/GetUserDevicesWithSlavePlain` |
| Read the complete device state | `GET /v1/DeviceCommand/{deviceId}/GetAllLastValuesFromDevice` |

The device discovery call is made during setup. The login and full-state read are used during normal polling. More details on the responses and my API investigation are in [API.md](API.md).

## What I'm not doing yet

**No remote control or writes.** Testing and online research suggest that firmware versions can behave differently, and some attempted control operations can interfere with or disable existing schedules. For now, I'm staying away from anything that changes operating modes, setpoints or scheduling.

**No energy statistics.** The API appears to expose electricity consumption and energy production information, but I haven't been able to make those requests work consistently. Date formatting and data handling have been particularly difficult to pin down, and there is very little documentation. Until I understand the responses properly, I'm leaving energy figures out. I currently use Shelly devices and other power monitors to measure real-time consumption separately.

**No assumptions about other equipment.** I've tested this on one Cointra Oasis Tech 200 HT. I haven't tested cascade configurations, other models or multiple devices registered under the same account.

## How you can help

I'd appreciate bug reports and test results from anyone using a related system. Please include the model, the mobile app you're using, the motherboard, display and Wi-Fi firmware versions, and which readings work or fail. Please don't include personal account details, serial numbers or MAC addresses.

You can report issues at [GitHub Issues](https://github.com/misiu-io/ha-cointra-oasis/issues). I'd also be interested in a verified register map for local monitoring, or help understanding the energy statistics API.

## Current status

This is an early test integration for **Home Assistant 2026.11 or newer**. It has only been tested against my own installation so far. The repository includes automated tests, but they cannot replace testing on a real heater.

See [CHANGELOG.md](CHANGELOG.md) for changes and [API.md](API.md) for more technical details.
