import logging
import io
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, \
    MediaType, MediaPlayerDeviceClass
from homeassistant.components import media_source
from homeassistant.components.media_player.browse_media import (
    BrowseMedia,
    async_process_play_media_url,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components import light

from . import const
from .entity_resolver import expand_entities
from .color_extract import extract_palette

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
) -> None:
    _LOGGER.info('LightCast media_player setup: %s', config)

    cast_device = LightCastPlayer(
        hass,
        config[const.CONF_NAME],
        config[const.CONF_TARGET],
        config.get(const.CONF_FILTER_ON) or False,
        True if (downsample := config.get(const.CONF_DOWNSAMPLE)) is None else downsample,
    )

    add_entities([cast_device])


class LightCastPlayer(MediaPlayerEntity):
    _attr_available = True
    _attr_supported_features = MediaPlayerEntityFeature.PLAY_MEDIA | MediaPlayerEntityFeature.BROWSE_MEDIA
    _attr_device_class = MediaPlayerDeviceClass.TV

    def __init__(self, hass: HomeAssistant, name: str, device_target: str, filter_on: bool, downsample: bool) -> None:
        self.hass = hass
        self._attr_name = name
        self.device_target = device_target
        self.filter_on = filter_on
        self.downsample = downsample

    async def async_browse_media(self, media_content_type: str | None = None,
                                 media_content_id: str | None = None) -> BrowseMedia:
        """
        Implement MediaPlayerEntityFeature.BROWSE_MEDIA
        :param media_content_type:
        :param media_content_id:
        :return:
        """
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith('image/')
        )

    async def process_image(self, media_type: str, media_id: str) -> None:
        """
        Download an image found at media_id to an in-memory buffer.
        Resolve the entity list of lights referenced by device_target which are currently in the on state
        and extract that many colors from the image using colorgram.
        For each pair of light and color, call light.turn_on with that color
        :param media_type:
        :param media_id:
        """
        _LOGGER.info('Processing image %s: %s', media_type, media_id)

        found_entities = expand_entities(self.hass, self.device_target)
        _LOGGER.info('Found %d entities matching %s', len(found_entities), self.device_target)

        valid_entities = found_entities
        if self.filter_on:
            valid_entities = [e for e in found_entities if e.state == 'on']

        if not valid_entities:
            _LOGGER.warning('No entities were matched')
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(media_id,
                                   raise_for_status=True,
                                   timeout=aiohttp.ClientTimeout(total=30, connect=5)
                                   ) as response:
                response_data = await response.read()

        palette = extract_palette(io.BytesIO(response_data), len(valid_entities), downsample=self.downsample)

        for e, color in zip(valid_entities, palette):
            _LOGGER.info('Set light %s to %s', e.entity_id, color)
            await self.hass.services.async_call(
                light.DOMAIN,
                light.SERVICE_TURN_ON,
                {
                    ATTR_ENTITY_ID: e.entity_id,
                    light.ATTR_RGB_COLOR: color
                }
            )

    async def async_play_media(self, media_type: MediaType, media_id: str, **kwargs: any) -> None:
        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            media_id = async_process_play_media_url(self.hass, play_item.url)

        self.hass.async_create_task(
            self.process_image(media_type, media_id)
        )
