# Kodi Recently Added Component

Home Assistant component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Kodi's recently added media.


### If you're having issues, check out the [troubleshooting guide](https://github.com/custom-cards/upcoming-media-card/blob/master/troubleshooting.md) before posting an issue or asking for help on the forums.

## Installation:
1. Install this component by copying [kodi_recently_added.py](https://raw.githubusercontent.com/custom-components/sensor.kodi_recently_added/master/custom_components/sensor/kodi_recently_added.py) to your `/custom_components/sensor/` folder.
2. Install the card: [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card)
3. Add the code to your `configuration.yaml` using the config options below.
4. Add the code for the card to your `ui-lovelace.yaml`. 
5. **You will need to restart after installation for the component to start working.**

### Platform Options:

| key | default | required | description
| --- | --- | --- | ---
| host | localhost | no | The host Kodi is running on.
| port | 8080 | no | The port Kodi is running on.
| tcp_port | 9090 | no | The TCP port number. Used for WebSocket connections to Kodi.
| username | | no | The Kodi HTTP username.
| password | | no | The Kodi HTTP password.

### Sample for configuration.yaml:

    sensor:
    - platform: kodi_recently_added
      username: YOUR_KODI_USERNAME
      host: YOUR_KODI_HOST
      password: YOUR_KODI_PASSWORD
      port: YOUR_KODI_PORT

### Sample for ui-lovelace.yaml:

    - type: custom:upcoming-media-card
      entity: sensor.kodi_recently_added_tv
      title: Recently Added Episodes
      image_style: fanart

    - type: custom:upcoming-media-card
      entity: sensor.kodi_recently_added_movies
      title: Recently Added Movies
      image_style: fanart

*NOTE: Currently genres, rating, and studio only work for Movies.*
