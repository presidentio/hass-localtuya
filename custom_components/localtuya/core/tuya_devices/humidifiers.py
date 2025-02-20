"""
    This a file contains available tuya data
    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq

    Credits: official HA Tuya integration.
    Modified by: xZetsubou
"""

from .base import DPCode, LocalTuyaEntity, CONF_DEVICE_CLASS, EntityCategory
from homeassistant.components.humidifier import HumidifierDeviceClass

CONF_HUMIDIFIER_SET_HUMIDITY_DP = "humidifier_set_humidity_dp"
CONF_HUMIDIFIER_CURRENT_HUMIDITY_DP = "humidifier_current_humidity_dp"
CONF_HUMIDIFIER_MODE_DP = "humidifier_mode_dp"
CONF_HUMIDIFIER_AVAILABLE_MODES = "humidifier_available_modes"


def localtuya_humidifier(modes):
    """Define localtuya fan configs"""
    data = {"humidifier_available_modes": modes}
    return data


HUMIDIFIERS: dict[str, tuple[LocalTuyaEntity, ...]] = {
    # Dehumidifier
    # https://developer.tuya.com/en/docs/iot/categorycs?id=Kaiuz1vcz4dha
    "cs": (
        LocalTuyaEntity(
            id=DPCode.SWITCH,
            humidifier_current_humidity_dp=DPCode.HUMIDITY_INDOOR,
            humidifier_set_humidity_dp=DPCode.DEHUMIDITY_SET_VALUE,
            humidifier_mode_dp=(DPCode.MODE, DPCode.WORK_MODE),
            custom_configs=localtuya_humidifier("dehumidify,drying,continuous"),
            device_class=HumidifierDeviceClass.DEHUMIDIFIER,
        )
    ),
    # Humidifier
    # https://developer.tuya.com/en/docs/iot/categoryjsq?id=Kaiuz1smr440b
    "jsq": (
        LocalTuyaEntity(
            id=DPCode.SWITCH,
            humidifier_current_humidity_dp=DPCode.HUMIDITY_CURRENT,
            humidifier_set_humidity_dp=DPCode.HUMIDITY_SET,
            humidifier_mode_dp=(DPCode.MODE, DPCode.WORK_MODE),
            custom_configs=localtuya_humidifier("large,middle,small"),
            device_class=HumidifierDeviceClass.HUMIDIFIER,
        )
    ),
}
