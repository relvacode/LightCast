import typing
import collections.abc
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.template import area_entities, device_entities
from homeassistant.helpers.entity import entity_sources
from homeassistant.const import ATTR_ENTITY_ID

GROUP_DOMAIN_PREFIX = 'group.'
AREA_DOMAIN_PREFIX = 'area.'
DEVICE_DOMAIN_PREFIX = 'device.'

EntityRef = str | State


def expand_entities(
        hass: HomeAssistant,
        expand_id: EntityRef | typing.Iterable[EntityRef],
        in_domain: str = 'light') -> typing.List[State]:
    """
    Expand an entity reference given by expand_id to a list of HomeAssistant states that are a member of that reference.
    expand_id can be one of:
        - A string referencing an entity id
        - A State itself
        - A device ID
        - An area ID
        - A group helper ID

    :param hass:
        Instance of HASS client
    :param expand_id:
        The entity ID or group reference to resolve
    :param in_domain:
        Filter returned entities to only those that are of the given domain
    :return:
        A list of de-duplicated resolved states
    """
    search = [expand_id]
    found: typing.Dict[str, State] = {}

    while search:
        entity = search.pop()

        if isinstance(entity, State):
            found[entity.entity_id] = entity
            continue

        if (not (is_str := isinstance(entity, str))) and isinstance(entity, collections.abc.Iterable):
            search += entity
            continue

        # Must be a string by this point
        if not is_str:
            continue  # ignore

        entity_id = entity

        # Entity ref is an area
        if entity_id.startswith(AREA_DOMAIN_PREFIX):
            search += area_entities(hass, entity_id.removeprefix(AREA_DOMAIN_PREFIX))
            continue

        # Entity ref is a device
        if entity_id.startswith(DEVICE_DOMAIN_PREFIX):
            search += device_entities(hass, entity_id)
            continue

        # Entity ref should be an entity (or a group helper)
        if (entity := hass.states.get(entity_id)) is None:
            continue  # not defined

        if entity_id.startswith(GROUP_DOMAIN_PREFIX) or (
                (source := entity_sources(hass).get(entity_id))
                and source["domain"] == "group"
        ):
            if group_entities := entity.attributes.get(ATTR_ENTITY_ID):
                search += group_entities
                continue

        # Finally, this should be a single entity in the light domain
        if entity.domain == in_domain:
            found[entity.entity_id] = entity

    return list(found.values())
