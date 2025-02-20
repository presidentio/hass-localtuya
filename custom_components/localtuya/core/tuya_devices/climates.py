"""
    This a file contains available tuya data
    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq

    Credits: official HA Tuya integration.
    Modified by: xZetsubou
"""

from homeassistant.components.climate import (
    HVACMode,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
)
from homeassistant.const import CONF_TEMPERATURE_UNIT

from .base import DPCode, LocalTuyaEntity, CONF_DEVICE_CLASS, EntityCategory
from ...const import (
    CONF_ECO_VALUE,
    CONF_HVAC_ACTION_SET,
    CONF_HVAC_MODE_SET,
    CONF_PRECISION,
    CONF_PRESET_SET,
    CONF_TARGET_PRECISION,
    CONF_TEMPERATURE_STEP,
    CONF_HVAC_ADD_OFF,
)


UNIT_C = "celsius"
UNIT_F = "fahrenheit"


def localtuya_climate(
    hvac_mode_set=None,
    temp_step=1,
    actions_set=None,
    echo_value=None,
    preset_set=None,
    unit=None,
    values_precsion=0.1,
    target_precision=0.1,
    includes_off_mode=True,
) -> dict:
    """Create localtuya climate configs"""
    data = {ATTR_MIN_TEMP: DEFAULT_MIN_TEMP, ATTR_MAX_TEMP: DEFAULT_MAX_TEMP}
    for key, conf in {
        CONF_HVAC_MODE_SET: hvac_mode_set,
        CONF_TEMPERATURE_STEP: temp_step,
        CONF_HVAC_ACTION_SET: actions_set,
        CONF_ECO_VALUE: echo_value,
        CONF_PRESET_SET: preset_set,
        CONF_TEMPERATURE_UNIT: unit,
        CONF_PRECISION: values_precsion,
        CONF_TARGET_PRECISION: target_precision,
        CONF_HVAC_ADD_OFF: includes_off_mode,
    }.items():
        if conf:
            data.update({key: conf})

    return data


CLIMATES: dict[str, tuple[LocalTuyaEntity, ...]] = {
    # Air conditioner
    # https://developer.tuya.com/en/docs/iot/categorykt?id=Kaiuz0z71ov2n
    "kt": (
        LocalTuyaEntity(
            id=DPCode.SWITCH,
            target_temperature_dp=(DPCode.TEMP_SET_F, DPCode.TEMP_SET),
            current_temperature_dp=DPCode.TEMP_CURRENT,
            hvac_mode_dp=DPCode.MODE,
            hvac_action_dp=(DPCode.WORK_MODE, DPCode.WORK_STATUS, DPCode.WORK_STATE),
            custom_configs=localtuya_climate(
                hvac_mode_set="auto/cold/hot/wet",
                temp_step=1,
                actions_set="heating/cooling",
                unit=UNIT_C,
                values_precsion=0.1,
                target_precision=0.1,
            ),
        ),
    ),
    # Heater
    # https://developer.tuya.com/en/docs/iot/f?id=K9gf46epy4j82
    "qn": (
        LocalTuyaEntity(
            id=DPCode.SWITCH,
            target_temperature_dp=(DPCode.TEMP_SET_F, DPCode.TEMP_SET),
            current_temperature_dp=(DPCode.TEMP_CURRENT, DPCode.TEMP_CURRENT_F),
            preset_dp=DPCode.MODE,
            hvac_action_dp=(DPCode.WORK_STATE, DPCode.WORK_MODE, DPCode.WORK_STATUS),
            custom_configs=localtuya_climate(
                temp_step=1,
                actions_set="heating/warming",
                values_precsion=0.1,
                target_precision=0.1,
                preset_set="auto/smart",
            ),
        ),
    ),
    # Heater
    # https://developer.tuya.com/en/docs/iot/categoryrs?id=Kaiuz0nfferyx
    "rs": (
        LocalTuyaEntity(
            id=DPCode.SWITCH,
            target_temperature_dp=(DPCode.TEMP_SET_F, DPCode.TEMP_SET),
            current_temperature_dp=(DPCode.TEMP_CURRENT, DPCode.TEMP_CURRENT_F),
            preset_dp=DPCode.MODE,
            hvac_action_dp=(DPCode.WORK_STATE, DPCode.WORK_MODE, DPCode.WORK_STATUS),
            custom_configs=localtuya_climate(
                temp_step=1,
                actions_set="heating/warming",
                unit=UNIT_C,
                values_precsion=0.1,
                target_precision=0.1,
                preset_set="auto/manual/smart/comfortable/eco",
            ),
        ),
    ),
    # Thermostat
    # https://developer.tuya.com/en/docs/iot/f?id=K9gf45ld5l0t9
    "wk": (
        LocalTuyaEntity(
            id=(DPCode.SWITCH, DPCode.MODE),
            target_temperature_dp=(DPCode.TEMP_SET_F, DPCode.TEMP_SET),
            current_temperature_dp=(DPCode.TEMP_CURRENT_F, DPCode.TEMP_CURRENT),
            hvac_mode_dp=(DPCode.SWITCH, DPCode.MODE),
            hvac_action_dp=(DPCode.WORK_STATE, DPCode.WORK_MODE, DPCode.WORK_STATUS),
            preset_dp=DPCode.MODE,
            custom_configs=localtuya_climate(
                hvac_mode_set="True/False",
                temp_step=1,
                actions_set="True/False",
                unit=UNIT_C,
                values_precsion=0.1,
                target_precision=0.1,
            ),
        ),
    ),
    # Thermostatic Radiator Valve
    # Not documented
    "wkf": (
        LocalTuyaEntity(
            id=(DPCode.SWITCH, DPCode.MODE),
            target_temperature_dp=(DPCode.TEMP_SET_F, DPCode.TEMP_SET),
            current_temperature_dp=(DPCode.TEMP_CURRENT_F, DPCode.TEMP_CURRENT),
            hvac_mode_dp=DPCode.MODE,
            hvac_action_dp=(DPCode.WORK_STATE, DPCode.WORK_MODE, DPCode.WORK_STATUS),
            custom_configs=localtuya_climate(
                hvac_mode_set="manual/auto",
                temp_step=1,
                actions_set="opened/closed",
                unit=UNIT_C,
                values_precsion=0.1,
                target_precision=0.1,
            ),
        ),
    ),
}
