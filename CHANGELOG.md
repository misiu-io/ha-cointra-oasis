# Changelog

## v0.1.2 (17 November 2026)

- Use only the verified full cloud snapshot endpoint, every 30 minutes by default.
- Remove the unverified lightweight endpoint and the fragile basic/full response merge.
- Fix false alarm states when the cloud reports null, false, zero or an empty alarm.
- Simplify the options screen to one full polling interval. Existing basic/full options are ignored safely.
- Preserve the existing integration domain and entity unique IDs.
- Make the independent, unofficial name clear in the Marketplace and Home Assistant.
- Use the appliance's model from discovery without adding a guessed prefix; distinguish the three firmware versions as diagnostics instead of putting the motherboard version in the device-wide firmware field.
- Add local icon artwork, a personal README, API investigation notes, and additional regression tests.
- Add GitHub Actions for tests, hassfest and Marketplace repository validation.

**Update note:** After the Marketplace installs the new code, restart Home Assistant when prompted. The previous two polling options are replaced by one setting, `Full data polling, minutes`, defaulting to 30.

## v0.1.1

- Correct the `CONNECTION_NETWORK_MAC` import for Home Assistant 2026.11 so the setup flow loads.

## v0.1.0

- First private, read-only cloud monitoring preview.
