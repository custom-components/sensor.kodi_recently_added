import json
import logging
from urllib import parse

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import STATE_ON, STATE_OFF, CONF_ENTITY_ID, STATE_PROBLEM, STATE_UNKNOWN, ATTR_ENTITY_ID, STATE_UNAVAILABLE

try:
    # >= v0.91
    from homeassistant.components.kodi.media_player import (
            CONF_TCP_PORT, DEFAULT_TCP_PORT, KodiDevice, EVENT_KODI_CALL_METHOD_RESULT,
            SERVICE_CALL_METHOD, DOMAIN as KODI_DOMAIN)
    try:
        # >= v0.98
        from homeassistant.components.kodi import ATTR_METHOD
    except ImportError:
        from homeassistant.components.kodi.media_player import ATTR_METHOD
except ImportError:
    # Pre v0.91
    from homeassistant.components.media_player.kodi import (
        CONF_TCP_PORT, DEFAULT_TCP_PORT, KodiDevice, EVENT_KODI_CALL_METHOD_RESULT,
        SERVICE_CALL_METHOD, DOMAIN as KODI_DOMAIN, ATTR_METHOD)


from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME)
from homeassistant.helpers.restore_state import RestoreEntity


__version__ = '0.2.8'

PLATFORM_SCHEMA = vol.Any(PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_PORT, default=8080): cv.port,
    vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): cv.port,
    vol.Inclusive(CONF_USERNAME, 'auth'): cv.string,
    vol.Inclusive(CONF_PASSWORD, 'auth'): cv.string,
}), PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ENTITY_ID): cv.entity_id
}))
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    sensors = [
        KodiRecentlyAddedMoviesSensor(hass, config),
        KodiRecentlyAddedTVSensor(hass, config)
    ]
    async_add_entities(sensors, True)


class KodiMediaSensor(RestoreEntity):

    properties = NotImplemented
    update_method = NotImplemented
    result_key = NotImplemented

    def __init__(self, hass, config):
        if CONF_ENTITY_ID in config:
            self.kodi = config[CONF_ENTITY_ID]
        else:
            self.kodi = KodiDevice(
                hass, self.name, config.get(CONF_HOST), config.get(CONF_PORT),
                config.get(CONF_TCP_PORT), username=config.get(CONF_USERNAME),
                password=config.get(CONF_PASSWORD))
        self._state = None
        self.data = []
        self.base_web_url = 'http://{}:{}/image/image%3A%2F%2F'.format(
            config.get(CONF_HOST), config.get(CONF_PORT))

        hass.bus.async_listen(EVENT_KODI_CALL_METHOD_RESULT, self._handle_update_event)

    @property
    def state(self):
        return self._state

    def get_web_url(self, path: str) -> str:
        """Get the web URL for the provided path.

        This is used for fanart/poster images that are not a http url.  For
        example the path is local to the kodi installation or a path to
        an NFS share.

        :param path: The local/nfs/samba/etc. path.
        :returns: The web url to access the image over http.
        """
        if path.lower().startswith('http'):
            return path
        # This looks strange, but the path needs to be quoted twice in order
        # to work.
        quoted_path = parse.quote(parse.quote(path, safe=''))
        return self.base_web_url + quoted_path

    def _handle_result(self, result):
        error = result.get('error')
        if error:
            _LOGGER.error('Error while fetching %s: [%d] %s' % (self.result_key, error.get('code'), error.get('message')))
            self._state = STATE_PROBLEM
            return

        new_data = result.get(self.result_key, [])
        
        if not new_data:
            _LOGGER.warning('No %s found after requesting data from Kodi, assuming empty.' % self.result_key)
            self._state = STATE_UNKNOWN
            return
        
        self.data = new_data
        self._state = STATE_ON

    async def _handle_update_event(self, event):
        """Handle update event after Kodi finishes replying."""
        if event.data['input'][ATTR_METHOD] == self.update_method:
            if event.data['result_ok']:
                self._handle_result(event.data['result'])
            else:
                self._state = STATE_OFF
            await self.async_update_ha_state()
    
    async def async_update(self):
        if isinstance(self.kodi, KodiDevice):
            result = await self.kodi.async_call_method(self.update_method, properties=self.properties)
            if result:
                self._handle_result(result)
            else:
                self._state = STATE_OFF
        else:
            media_player_state = self.hass.states.get(self.kodi)
            if media_player_state is None or media_player_state.state in (STATE_OFF, STATE_UNAVAILABLE):
                self._state = STATE_OFF
            else:
                self._state = STATE_ON
                await self.hass.services.async_call(KODI_DOMAIN, SERVICE_CALL_METHOD, {
                    ATTR_ENTITY_ID: self.kodi,
                    ATTR_METHOD: self.update_method,
                    'properties': self.properties,
                })


class KodiRecentlyAddedTVSensor(KodiMediaSensor):

    properties = [
        'art', 'dateadded', 'episode', 'fanart', 'firstaired', 'playcount',
        'rating', 'runtime', 'season', 'showtitle', 'title'
    ]
    update_method = 'VideoLibrary.GetRecentlyAddedEpisodes'
    result_key = 'episodes'

    @property
    def name(self):
        return 'kodi_recently_added_tv'

    @property
    def device_state_attributes(self):
        attrs = {}
        card_json = [{
            'title_default': '$title',
            'line1_default': '$episode',
            'line2_default': '$release',
            'line3_default': '$rating - $runtime',
            'line4_default': '$number',
            'icon': 'mdi:arrow-down-bold',
        }]
        for show in self.data:
            try:
                card = {
                    'airdate': show['dateadded'].replace(' ', 'T') + 'Z',
                    'episode': show['title'],
                    'fanart': '',
                    'flag': show['playcount'] == 0,
                    'genres': '',
                    'number': 'S{0:0>2}E{1:0>2}'.format(
                        show['season'], show['episode']),
                    'poster': '',
                    'release': '$day, $date',
                    'runtime': show['runtime'] // 60,
                    'title': show['showtitle'],
                    'studio': '',
                }
                rating = round(show['rating'], 1)
                if rating:
                    rating = '\N{BLACK STAR} {}'.format(rating)
                card['rating'] = rating
                fanart = show['art'].get('tvshow.fanart', '')
                poster = show['art'].get('tvshow.poster', '')
                if fanart:
                    card['fanart'] = self.get_web_url(
                        parse.unquote(fanart)[8:].strip('/'))
                if poster:
                    card['poster'] = self.get_web_url(
                        parse.unquote(poster)[8:].strip('/'))
            except KeyError:
                _LOGGER.exception('Error parsing key from tv blob: %s', show)
            card_json.append(card)
        attrs['data'] = json.dumps(card_json)
        return attrs


class KodiRecentlyAddedMoviesSensor(KodiMediaSensor):

    properties = [
        'art', 'dateadded', 'genre', 'playcount', 'premiered', 'rating',
        'runtime', 'studio', 'title']
    update_method = 'VideoLibrary.GetRecentlyAddedMovies'
    result_key = 'movies'

    @property
    def name(self):
        return 'kodi_recently_added_movies'

    @property
    def device_state_attributes(self):
        attrs = {}
        card_json = [{
            'title_default': '$title',
            'line1_default': '$genres',
            'line2_default': '$release',
            'line3_default': '$rating - $runtime',
            'line4_default': '$studio',
            'icon': 'mdi:arrow-down-bold',
        }]
        for show in self.data:
            try:
                card = {
                    'aired': show['premiered'],
                    'airdate': show['dateadded'].replace(' ', 'T') + 'Z',
                    'flag': show['playcount'] == 0,
                    'genres': ','.join(show['genre']),
                    'rating': round(show['rating'], 1),
                    'release': '$date',
                    'runtime': show['runtime'] // 60,
                    'title': show['title'],
                    'studio': ','.join(show['studio']),
                }
                rating = round(show['rating'], 1)
                if rating:
                    rating = '\N{BLACK STAR} {}'.format(rating)
                card['rating'] = rating
                fanart = show['art'].get('fanart', '')
                poster = show['art'].get('poster', '')
            except KeyError:
                _LOGGER.exception(
                    'Error parsing key from movie blob: %s', show)
            if fanart:
                fanart = self.get_web_url(parse.unquote(fanart)[8:].strip('/'))
            if poster:
                poster = self.get_web_url(parse.unquote(poster)[8:].strip('/'))
            card['fanart'] = fanart
            card['poster'] = poster
            card_json.append(card)
        attrs['data'] = json.dumps(card_json)
        return attrs