import json
import logging
from urllib import parse

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
try:
    # Pre v0.91
    from homeassistant.components.media_player.kodi import (
        CONF_TCP_PORT, DEFAULT_TCP_PORT, KodiDevice)
except ImportError:
    # >= v0.91
    from homeassistant.components.kodi.media_player import (
        CONF_TCP_PORT, DEFAULT_TCP_PORT, KodiDevice)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity


__version__ = '0.2.7'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_PORT, default=8080): cv.port,
    vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): cv.port,
    vol.Inclusive(CONF_USERNAME, 'auth'): cv.string,
    vol.Inclusive(CONF_PASSWORD, 'auth'): cv.string,
})
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    sensors = [
        KodiRecentlyAddedMoviesSensor(hass, config),
        KodiRecentlyAddedTVSensor(hass, config)
    ]
    async_add_entities(sensors, True)


class KodiMediaSensor(Entity, RestoreEntity):

    def __init__(self, hass, config):
        self.kodi = KodiDevice(
            hass, self.name, config.get(CONF_HOST), config.get(CONF_PORT),
            config.get(CONF_TCP_PORT), username=config.get(CONF_USERNAME),
            password=config.get(CONF_PASSWORD))
        self._state = None
        self.data = []
        self.base_web_url = 'http://{}:{}/image/image%3A%2F%2F'.format(
            config.get(CONF_HOST), config.get(CONF_PORT))

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


class KodiRecentlyAddedTVSensor(KodiMediaSensor):

    properties = [
        'art', 'dateadded', 'episode', 'fanart', 'firstaired', 'playcount',
        'rating', 'runtime', 'season', 'showtitle', 'title'
    ]

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

    async def async_update(self):
        result = await self.kodi.async_call_method(
            'VideoLibrary.GetRecentlyAddedEpisodes',
            properties=self.properties)
        if result:
            episodes = result.get('episodes', [])
            
            if not episodes:
                _LOGGER.warning('No episodes found after requesting data from Kodi.')
            
            self.data = episodes


class KodiRecentlyAddedMoviesSensor(KodiMediaSensor):

    properties = [
        'art', 'dateadded', 'genre', 'playcount', 'premiered', 'rating',
        'runtime', 'studio', 'title']

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

    async def async_update(self):
        result = await self.kodi.async_call_method(
            'VideoLibrary.GetRecentlyAddedMovies', properties=self.properties)
        if result:
            try:
                self.data = result['movies']
            except KeyError:
                _LOGGER.exception(
                    'Unexpected result while fetching movies: %s', result)
