# CHANGELOG

## In Development (not yet released)

## v0.2.7 (2019-07-04)

- Fixed bug where artwork would not display if the media url was not http.
  Now nfs/local/samba paths to artwork will be converted to an http url that
  is served up by kodi.  Note that this will only work if the web UI is enabled.

## v0.2.5 (2019-05-02)

- Added exception logging when encountering unexpected json responses from kodi.

## v0.2.4 (2019-04-26)

- Removed kodi from dependencies in manifest.json

## v0.2.3 (2019-04-25)

- Added required manifest.json for 0.92.

## v0.2.2 (2019-04-13)

- Fixed import error due to great migration.  Caused installs of HA >=0.91 to fail.

## v0.2.1 (2019-03-10)

- Fixed error that occured when there was a TransportError getting data from kodi.

## v0.2.0 (2019-03-10)

- Updated directory structure to work with HA >= 0.88
- Fixed bug if a show had no fanart.
- Added exception logging if a key is absent when parsing a tv show or movie

## v0.1.0 (2019-01-20)

- Initial release.

