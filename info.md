![Kodi Recently Added Media](https://github.com/custom-components/sensor.kodi_recently_added/raw/master/example.png)

Feeds your recently added movies and tv shows of your kodi library to the
[Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card).

### Installation and Configuration

1. Install the card: [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card)
2. Add the code to your `configuration.yaml` using the config options below.
3. Add the code for the card to your `ui-lovelace.yaml`. 
4. **You will need to restart after installation for the component to start working.**

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
