# Overview

This site is based on the Django framework. The main functionality is in an app
called 'core' and other apps provide support to that. All the custom code can be
found in 'pombola'.

Python dependencies are specified in the 'requirements.txt' file. Most are
standard Python packages but some are repositories.

Configuration is done by editing the values in 'pombola/settings/base.py' and
additional settings modules that import it.

When installing the system note that many additional files and directories will
be created in the `data/` directory in the top level git repo checkout. These
include the 'media_root' for uploaded images, the virtualenv and various others.

All data is stored in the database, but some is copied into the search engine
implemented using Haystack for full text searching.

Location searches are carried out using Google's geolocate tools, with calls
being made to their API. These are cached after the first request.

Boundary data is taken from a MaPit service (an embedded app), this is used
to find the constituency for a point and also to serve the KML boundaries used
on the Google maps.
