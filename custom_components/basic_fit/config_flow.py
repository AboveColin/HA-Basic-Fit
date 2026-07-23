"""Config flow for the Basic-Fit integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from basicfit import AuthManager, BasicFitClient, PkceChallenge, parse_redirect, start_login
from basicfit.exceptions import BasicFitError, BasicFitValidationError

from .const import (
    CONF_ACCESS_EXPIRES_AT,
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_MEMBER_NAME,
    CONF_OBTAINED_AT,
    CONF_REDIRECT,
    CONF_REDIRECT_URI,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """The Basic-Fit service could not be reached."""


class InvalidAuth(HomeAssistantError):
    """The pasted redirect / code was invalid."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the one-time browser (PKCE) login for Basic-Fit."""

    VERSION = 1

    def __init__(self) -> None:
        self._challenge: PkceChallenge | None = None
        self._entry: config_entries.ConfigEntry | None = None

    def _new_challenge(self) -> PkceChallenge:
        self._challenge = start_login()
        return self._challenge

    async def _exchange_and_validate(self, redirect: str) -> tuple[dict, str]:
        """Exchange the pasted redirect for tokens and read the member name."""
        assert self._challenge is not None
        try:
            code = parse_redirect(redirect, expected_state=self._challenge.state)
        except BasicFitValidationError as err:
            raise InvalidAuth(str(err)) from err

        session = async_get_clientsession(self.hass)
        try:
            tokens = await AuthManager.async_exchange_code(
                session, code, self._challenge.verifier
            )
        except BasicFitError as err:
            raise InvalidAuth(str(err)) from err

        client = BasicFitClient.create(tokens, session=session)
        try:
            member = await client.get_member()
        except BasicFitError as err:
            raise CannotConnect(str(err)) from err

        data = {
            CONF_REFRESH_TOKEN: tokens.refresh_token,
            CONF_ACCESS_TOKEN: tokens.access_token,
            CONF_ACCESS_EXPIRES_AT: tokens.access_expires_at,
            CONF_CLIENT_ID: tokens.client_id,
            CONF_REDIRECT_URI: tokens.redirect_uri,
            CONF_OBTAINED_AT: tokens.obtained_at,
            CONF_MEMBER_NAME: member.name,
        }
        return data, member.name or "Basic-Fit"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Present the login URL and collect the pasted redirect."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data, title = await self._exchange_and_validate(user_input[CONF_REDIRECT])
                await self.async_set_unique_id(str(data.get(CONF_MEMBER_NAME) or title))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"Basic-Fit ({title})", data=data)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected Basic-Fit login failure")
                errors["base"] = "unknown"

        challenge = self._new_challenge()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_REDIRECT): str}),
            errors=errors,
            description_placeholders={"authorize_url": challenge.authorize_url},
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Start re-authentication for an existing entry."""
        entry_id = self.context.get("entry_id")
        self._entry = (
            self.hass.config_entries.async_get_entry(entry_id) if entry_id else None
        )
        if self._entry is None:
            return self.async_abort(reason="unknown_entry")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Collect a fresh browser login and update the existing entry."""
        errors: dict[str, str] = {}
        if user_input is not None and self._entry is not None:
            try:
                data, _ = await self._exchange_and_validate(user_input[CONF_REDIRECT])
                return self.async_update_reload_and_abort(
                    self._entry, data={**self._entry.data, **data}
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected Basic-Fit re-authentication failure")
                errors["base"] = "unknown"

        challenge = self._new_challenge()
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_REDIRECT): str}),
            errors=errors,
            description_placeholders={"authorize_url": challenge.authorize_url},
        )
