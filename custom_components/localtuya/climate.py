"""Platform to locally control Tuya-based climate devices.
    # PRESETS and HVAC_MODE Needs to be handle in better way.
"""
import asyncio
import logging
from functools import partial
from .config_flow import _col_to_select

import voluptuous as vol
from homeassistant.components.climate import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DOMAIN,
    ClimateEntity,
)
from homeassistant.components.climate.const import (
    HVACMode,
    HVACAction,
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
    ClimateEntityFeature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_TEMPERATURE_UNIT,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    UnitOfTemperature,
)

from .common import LocalTuyaEntity, async_setup_entry
from .const import (
    CONF_CURRENT_TEMPERATURE_DP,
    CONF_ECO_DP,
    CONF_ECO_VALUE,
    CONF_HEURISTIC_ACTION,
    CONF_HVAC_ACTION_DP,
    CONF_HVAC_ACTION_SET,
    CONF_HVAC_MODE_DP,
    CONF_HVAC_MODE_SET,
    CONF_PRECISION,
    CONF_PRESET_DP,
    CONF_PRESET_SET,
    CONF_TARGET_PRECISION,
    CONF_TARGET_TEMPERATURE_DP,
    CONF_TEMPERATURE_STEP,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_HVAC_ADD_OFF,
)

_LOGGER = logging.getLogger(__name__)

HVAC_MODE_SETS = {
    "manual/auto": {
        HVACMode.HEAT: "manual",
        HVACMode.AUTO: "auto",
    },
    "Manual/Program": {
        HVACMode.HEAT: "Manual",
        HVACMode.AUTO: "Program",
    },
    "freeze/manual/auto": {
        HVACMode.COOL: "freeze",
        HVACMode.HEAT: "manual",
        HVACMode.AUTO: "auto",
    },
    "auto/cold/hot/wet": {
        HVACMode.AUTO: "auto",
        HVACMode.COOL: "cold",
        HVACMode.HEAT: "hot",
        HVACMode.DRY: "wet",
    },
    "m/p": {
        HVACMode.HEAT: "m",
        HVACMode.AUTO: "p",
    },
    "True/False": {
        HVACMode.HEAT: True,
    },
    "1/0": {
        HVACMode.HEAT: "1",
        HVACMode.AUTO: "0",
    },
    "smart/auto": {
        HVACMode.HEAT_COOL: "1",
        HVACMode.AUTO: "auto",
    },
}
HVAC_ACTION_SETS = {
    "True/False": {
        HVACAction.HEATING: True,
        HVACAction.IDLE: False,
    },
    "open/close": {
        HVACAction.HEATING: "open",
        HVACAction.IDLE: "close",
    },
    "opened/closed": {
        HVACAction.HEATING: "opened",
        HVACAction.IDLE: "closed",
    },
    "heating/no_heating": {
        HVACAction.HEATING: "heating",
        HVACAction.IDLE: "no_heating",
    },
    "heating/cooling": {
        HVACAction.HEATING: "heating",
        HVACAction.COOLING: "cooling",
        HVACAction.IDLE: "ventilation",
        HVACAction.OFF: "off",
    },
    "Heat/Warming": {
        HVACAction.HEATING: "Heat",
        HVACAction.IDLE: "Warming",
    },
    "heating/warming": {
        HVACAction.HEATING: "heating",
        HVACAction.IDLE: "warming",
    },
}
PRESET_SETS = {
    "Manual/Holiday/Program": {
        PRESET_AWAY: "Holiday",
        PRESET_HOME: "Program",
        PRESET_NONE: "Manual",
    },
    "auto/smart": {
        "auto": "Auto",
        "smart": "Smart",
    },
    "auto/manual/smart/comfortable/eco": {
        "auto": "Auto",
        "manual": "Manual",
        "smart": "Smart",
        "comfortable": "Comfort",
        "eco": "ECO",
    },
}

TEMPERATURE_CELSIUS = "celsius"
TEMPERATURE_FAHRENHEIT = "fahrenheit"
DEFAULT_TEMPERATURE_UNIT = TEMPERATURE_CELSIUS
DEFAULT_PRECISION = PRECISION_TENTHS
DEFAULT_TEMPERATURE_STEP = PRECISION_HALVES
# Empirically tested to work for AVATTO thermostat
MODE_WAIT = 0.1


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_TARGET_TEMPERATURE_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_CURRENT_TEMPERATURE_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_TEMPERATURE_STEP): _col_to_select(
            [PRECISION_WHOLE, PRECISION_HALVES, PRECISION_TENTHS]
        ),
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION): _col_to_select(
            [PRECISION_WHOLE, PRECISION_HALVES, PRECISION_TENTHS]
        ),
        vol.Optional(CONF_HVAC_MODE_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_HVAC_MODE_SET): _col_to_select(list(HVAC_MODE_SETS.keys())),
        vol.Optional(CONF_HVAC_ACTION_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_HVAC_ACTION_SET): _col_to_select(
            list(HVAC_ACTION_SETS.keys())
        ),
        vol.Optional(CONF_ECO_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_ECO_VALUE): str,
        vol.Optional(CONF_PRESET_DP): _col_to_select(dps, is_dps=True),
        vol.Optional(CONF_PRESET_SET): _col_to_select(list(PRESET_SETS.keys())),
        vol.Optional(CONF_TEMPERATURE_UNIT): _col_to_select(
            [TEMPERATURE_CELSIUS, TEMPERATURE_FAHRENHEIT]
        ),
        vol.Optional(CONF_TARGET_PRECISION): _col_to_select(
            [PRECISION_WHOLE, PRECISION_HALVES, PRECISION_TENTHS]
        ),
        vol.Optional(CONF_HVAC_ADD_OFF, default=True): bool,
        vol.Optional(CONF_HEURISTIC_ACTION): bool,
    }


class LocaltuyaClimate(LocalTuyaEntity, ClimateEntity):
    """Tuya climate device."""

    def __init__(
        self,
        device,
        config_entry,
        switchid,
        **kwargs,
    ):
        """Initialize a new LocaltuyaClimate."""
        super().__init__(device, config_entry, switchid, _LOGGER, **kwargs)
        self._state = None
        self._target_temperature = None
        self._current_temperature = None
        self._hvac_mode = None
        self._preset_mode = None
        self._hvac_action = None
        self._precision = float(self._config.get(CONF_PRECISION, DEFAULT_PRECISION))
        self._target_precision = float(
            self._config.get(CONF_TARGET_PRECISION, self._precision)
        )
        self._conf_hvac_mode_dp = self._config.get(CONF_HVAC_MODE_DP)
        self._conf_hvac_mode_set = HVAC_MODE_SETS.get(
            self._config.get(CONF_HVAC_MODE_SET), {}
        )
        self._conf_preset_dp = self._config.get(CONF_PRESET_DP)
        self._conf_preset_set = PRESET_SETS.get(self._config.get(CONF_PRESET_SET), {})
        self._conf_hvac_action_dp = self._config.get(CONF_HVAC_ACTION_DP)
        self._conf_hvac_action_set = HVAC_ACTION_SETS.get(
            self._config.get(CONF_HVAC_ACTION_SET), {}
        )
        self._conf_eco_dp = self._config.get(CONF_ECO_DP)
        self._conf_eco_value = self._config.get(CONF_ECO_VALUE, "ECO")
        self._has_presets = self.has_config(CONF_ECO_DP) or self.has_config(
            CONF_PRESET_DP
        )

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = 0
        if self.has_config(CONF_TARGET_TEMPERATURE_DP):
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.has_config(CONF_PRESET_DP) or self.has_config(CONF_ECO_DP):
            supported_features |= ClimateEntityFeature.PRESET_MODE
        return supported_features

    @property
    def precision(self):
        """Return the precision of the system."""
        return self._precision

    @property
    def target_precision(self):
        """Return the precision of the target."""
        return self._target_precision

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        # Unit may rely on self.hass.config.units.temperature_unit [System Unit]
        if self._config.get(CONF_TEMPERATURE_UNIT) == TEMPERATURE_FAHRENHEIT:
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        # DEFAULT_MIN_TEMP is in C
        return self._config.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        # DEFAULT_MAX_TEMP is in C
        return self._config.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if not self.has_config(CONF_HVAC_MODE_DP):
            return None
        modes = list(self._conf_hvac_mode_set)
        if self._config.get(CONF_HVAC_ADD_OFF, True) and HVACMode.OFF not in modes:
            modes.append(HVACMode.OFF)
        return modes

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        if self._config.get(CONF_HEURISTIC_ACTION, False):
            if self._hvac_mode == HVACMode.HEAT:
                if self._current_temperature < (
                    self._target_temperature - self._precision
                ):
                    self._hvac_action = HVACMode.HEAT
                if self._current_temperature == (
                    self._target_temperature - self._precision
                ):
                    if self._hvac_action == HVACMode.HEAT:
                        self._hvac_action = HVACMode.HEAT
                    if self._hvac_action == HVACAction.IDLE:
                        self._hvac_action = HVACAction.IDLE
                if (
                    self._current_temperature + self._precision
                ) > self._target_temperature:
                    self._hvac_action = HVACAction.IDLE
            return self._hvac_action
        return self._hvac_action

    @property
    def preset_mode(self):
        """Return current preset."""
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return the list of available presets modes."""
        if not self._has_presets:
            return None
        presets = list(self._conf_preset_set)
        if self._conf_eco_dp:
            presets.append(PRESET_ECO)
        return presets

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._config.get(CONF_TEMPERATURE_STEP, DEFAULT_TEMPERATURE_STEP)

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return NotImplementedError()

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return NotImplementedError()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs and self.has_config(CONF_TARGET_TEMPERATURE_DP):
            temperature = round(kwargs[ATTR_TEMPERATURE] / self._target_precision)
            await self._device.set_dp(
                temperature, self._config[CONF_TARGET_TEMPERATURE_DP]
            )

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        return NotImplementedError()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self._device.set_dp(False, self._dp_id)
            return
        if not self._state and self._conf_hvac_mode_dp != self._dp_id:
            await self._device.set_dp(True, self._dp_id)
            # Some thermostats need a small wait before sending another update
            await asyncio.sleep(MODE_WAIT)
        await self._device.set_dp(
            self._conf_hvac_mode_set[hvac_mode], self._conf_hvac_mode_dp
        )

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._device.set_dp(True, self._dp_id)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._device.set_dp(False, self._dp_id)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if preset_mode == PRESET_ECO:
            await self._device.set_dp(self._conf_eco_value, self._conf_eco_dp)
            return
        await self._device.set_dp(
            self._conf_preset_set[preset_mode], self._conf_preset_dp
        )

    def status_updated(self):
        """Device status was updated."""
        self._state = self.dp_value(self._dp_id)

        if self.has_config(CONF_TARGET_TEMPERATURE_DP):
            self._target_temperature = (
                self.dp_value(CONF_TARGET_TEMPERATURE_DP) * self._target_precision
            )

        if self.has_config(CONF_CURRENT_TEMPERATURE_DP):
            self._current_temperature = (
                self.dp_value(CONF_CURRENT_TEMPERATURE_DP) * self._precision
            )

        if self._has_presets:
            if (
                self.has_config(CONF_ECO_DP)
                and self.dp_value(CONF_ECO_DP) == self._conf_eco_value
            ):
                self._preset_mode = PRESET_ECO
            else:
                for preset, value in self._conf_preset_set.items():  # todo remove
                    if self.dp_value(CONF_PRESET_DP) == value:
                        self._preset_mode = preset
                        break
                else:
                    self._preset_mode = PRESET_NONE

        # Update the HVAC status
        if self.has_config(CONF_HVAC_MODE_DP):
            if not self._state:
                self._hvac_mode = HVACMode.OFF
            else:
                for mode, value in self._conf_hvac_mode_set.items():
                    if self.dp_value(CONF_HVAC_MODE_DP) == value:
                        self._hvac_mode = mode
                        break
                else:
                    # in case hvac mode and preset share the same dp
                    self._hvac_mode = HVACMode.AUTO

        # Update the current action
        for action, value in self._conf_hvac_action_set.items():
            if self.dp_value(CONF_HVAC_ACTION_DP) == value:
                self._hvac_action = action


async_setup_entry = partial(async_setup_entry, DOMAIN, LocaltuyaClimate, flow_schema)
