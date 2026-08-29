# Basic-Fit for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration for
[Basic-Fit](https://www.basic-fit.com/) gym memberships. It reads your check-ins,
membership details, in-club body measurements and badges, and adds a calendar of
every gym visit.

The integration signs in with your own Basic-Fit account and talks to the same
backend the official app uses. After a one-time browser login it keeps itself
signed in. No scraping, no add-ons, no third-party services.

## What you get

- Visit sensors: this month, this year, all-time, and a timestamp of your last
  check-in.
- A calendar with every check-in as an event, so automations can act on your
  training history.
- Membership type and home club, plus an outstanding-balance problem sensor if
  your account owes anything.
- Body measurements from the in-club InBody scale linked to your account:
  weight, body fat, muscle mass and body water.
- A count of the badges you have earned.

## Requirements

- Home Assistant 2024.2.0 or newer.
- [HACS](https://hacs.xyz/), for the recommended install.
- A Basic-Fit account you can sign in to in a normal web browser.

## Installation

### HACS

1. In HACS, open the three-dot menu, choose **Custom repositories**, add
   `https://github.com/abovecolin/HA-Basic-Fit` and pick the **Integration**
   category.
2. Search for **Basic-Fit** in HACS and install it.
3. Restart Home Assistant.

### Manual

Copy `custom_components/basic_fit` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

Basic-Fit's login page runs a bot-protection challenge that Home Assistant
cannot complete, so you log in once in your own browser and hand back the
redirect address.

1. Go to **Settings**, **Devices & Services**, **Add Integration**, and search
   for **Basic-Fit**.
2. Open the **Sign in to Basic-Fit** link that appears and log in as usual.
3. The browser then redirects to an address starting with
   `com.basicfit.trainingapp:/oauthredirect?...`, which will not load. Copy the
   full address from the address bar.
4. Paste it back into Home Assistant.

Home Assistant exchanges that address for a token, stores it, and refreshes it
in the background. If the login expires you get a **Reconfigure** prompt that
repeats the same step. Your Basic-Fit password never reaches Home Assistant.

## The library

All the API work lives in the standalone
[`basicfit`](https://github.com/abovecolin/basicfit) package, which this
integration requires. It does the PKCE login, the rotating token refresh, and
the membership, activity, body-measurement, badge and club endpoints. You can
use it outside Home Assistant.

## Contributing

Open an issue or a pull request on the
[repository](https://github.com/abovecolin/HA-Basic-Fit).

## Disclaimer

This is an unofficial, community-built integration. It is not affiliated with
or supported by Basic-Fit, and "Basic-Fit" is a trademark of its owner. Use it
with your own account, at your own risk.

## License

MIT.
