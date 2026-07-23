"""Constants for the Basic-Fit integration."""

DOMAIN = "basic_fit"

# Config entry keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_ACCESS_EXPIRES_AT = "access_expires_at"
CONF_CLIENT_ID = "client_id"
CONF_REDIRECT_URI = "redirect_uri"
CONF_OBTAINED_AT = "obtained_at"
CONF_MEMBER_NAME = "member_name"

# Config flow keys
CONF_REDIRECT = "redirect"

# How far back the visit history is fetched on each refresh.
HISTORY_DAYS = 365

# Manufacturer string used for the Home Assistant device registry entry.
MANUFACTURER = "Basic-Fit"
