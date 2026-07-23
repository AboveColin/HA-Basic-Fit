# Basic-Fit — Home Assistant Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration for
**[Basic-Fit](https://www.basic-fit.com/)** gym memberships. It brings your
check-ins, membership details, in-club body measurements, and earned badges into
Home Assistant, and adds a calendar of every gym visit.

The integration signs in with your own Basic-Fit account and talks to the same
backend the official Basic-Fit app uses. After a one-time browser login it keeps
itself signed in automatically — no scraping, no add-ons, and no third-party
services.

## Features

- **Visit tracking** — sensors for visits this month, this year, and all-time,
  plus a timestamp of your last check-in.
- **Gym-visit calendar** — every check-in as a calendar event, so you can see
  your training history and build automations around it.
- **Membership** — membership type and home club at a glance, and an
  **Outstanding balance** problem sensor if your account owes anything.
- **Body measurements** — weight, body-fat %, muscle mass, and body-water %
  from the in-club InBody / smart-scale measurements linked to your account.
- **Badges** — a running count of the achievements you've earned.

## Requirements

- A recent version of Home Assistant with [HACS](https://hacs.xyz/) (for the
  recommended install).
- An active Basic-Fit account you can sign in to in a normal web browser.

## Installation

### HACS (recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed.
2. In HACS, open the three-dot menu → **Custom repositories**, add
   `https://github.com/abovecolin/HA-Basic-Fit`, and choose the **Integration**
   category.
3. Search for **Basic-Fit** in HACS and install it.
4. Restart Home Assistant.

### Manual

Copy `custom_components/basic_fit` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

Basic-Fit protects its login page with a browser challenge, so the login happens
in your own browser once — after that everything is automatic.

1. Go to **Settings → Devices & Services → Add Integration** and search for
   **Basic-Fit**.
2. Home Assistant shows a **Sign in to Basic-Fit** link. Open it in your
   browser and log in as usual.
3. After signing in, the browser is redirected to an address that will not load
   — it starts with `com.basicfit.trainingapp:/oauthredirect?...`. Copy that
   **full address** from the browser's address bar.
4. Paste it back into Home Assistant.

That's it. Home Assistant exchanges the login for a token and stores it, then
refreshes it automatically in the background — you won't normally need to sign in
again. If the login ever expires, Home Assistant shows a **Reconfigure** prompt
that repeats the same one-time browser step.

> **Why the copy-paste step?** Basic-Fit's sign-in page uses a bot-protection
> challenge that can't be completed by Home Assistant directly, so the actual
> login is done in your browser. Only the short-lived redirect address is handed
> back — your Basic-Fit password is never seen or stored by Home Assistant.

## Under the hood

All of the Basic-Fit API work lives in the standalone
[`basicfit`](https://github.com/abovecolin/basicfit) Python package, which this
integration depends on. It handles the PKCE login, automatic (rotating)
token refresh, and the membership, activity, body-measurement, badge, and
club/workout/recipe endpoints. You can use the package on its own outside of
Home Assistant.

## Contributing

Contributions are welcome — please open an issue or pull request on the
[GitHub repository](https://github.com/abovecolin/HA-Basic-Fit).

## Disclaimer

This is an unofficial, community-built integration and is not affiliated with,
endorsed by, or supported by Basic-Fit. "Basic-Fit" is a trademark of its
respective owner. Use it with your own account and at your own risk.

## License

Released under the MIT License.
