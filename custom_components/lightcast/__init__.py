"""
LightCast integration
"""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.MEDIA_PLAYER])
