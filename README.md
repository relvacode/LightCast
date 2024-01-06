# LightCast

Transform your Home Assistant smart bulbs into a media player

When an image is played on a LightCast media player, it uses [colorgram.py](https://github.com/obskyr/colorgram.py/tree/master) 
to extract a palette of colors equal to the amount of lights configured in the LightCast player and sets those lights to that color palette.

## Installation

This integration is compatible with HACS

Add a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) pointing to `relvacode/LightCast` and install

## Configuration

`configuration.yml`

```yaml
media_player:
  - platform: lightcast
    name: Living Room LightCast
    target: area.living_room
    # Enable filter_on to only consider lights that are already on
    # filter_on: false
```

Target can be a light, area, group or device.

You can specify target as a list of entities as well, LightCast will resolve all lights found in all targets. 
Note that LightCast cannot resolve individual lights if you provide a Zigbee coordinator group.

```yaml
media_player:
  - platform: lightcast
    name: Living Room LightCast
    target:
      - entity.living_room_ceiling
      - entity.living_room_backlight
```

You can create multiple LightCast media players for each area in your home

```yaml
media_player:
  - platform: lightcast
    name: Living Room LightCast
    target: area.living_room
  - platform: lightcast
    name: Office LightCast
    target: area.office
```