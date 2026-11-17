# Changelog

## v0.2.0 (17 November 2026)

- Prepare the first public 0.2.0 release without changing the existing read-only monitoring behaviour.
- Add a Spanish README and link it from the English documentation.
- Classify the integration under both domestic water heating and heat pumps in the Home Assistant integration catalog.
- Correct the integration manifest ordering and repository metadata so that unit tests, hassfest and Marketplace validation can pass.

## v0.1.3 (preview, 17 November 2026)

- Rename the displayed integration to **Cointra Oasis Tech** while preserving the internal `cointra_oasis` domain and existing entity identifiers.
- Restore the device manufacturer information as **Cointra / Ferroli Group**.
- Improve the English setup, device-selection and update-interval screens.
- Replace the dark integration icon with artwork based on the Oasis Tech 200 HT on a transparent background.
- Rewrite the README with the project background, tested device, supported entities, Ferroli cloud API and compatibility limitations.

This is a development preview until tested on a running Home Assistant installation.

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
