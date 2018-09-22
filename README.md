# Spotify radio deduplicator

Spotify radio has a habit of playing a few particular tracks way too often. 

This is a simple script designed to be left running on an internet-connected PC. It'll use [spotipy](https://github.com/plamere/spotipy/) (which it depends on, and expects to be installed) to monitor the user's Spotify account and automatically skip the currently playing track if it comes from radio (i.e. not an album/playlist/other means of deliberately playing a song) and has been played recently enough (in the last week by default)

You'll need to [register](https://developer.spotify.com/dashboard/applications) your copy of the application, get a client ID, client secret and set a redirect URL (e.g. 'spotify-deduplicator://auth/') on Spotify. 

The script expects a JSON file containing at least this information and also your Spotify username in ~/.spotify-deduplicator/config.json.

The first time you run the script it'll use your web browser to authenticate with Spotify. You'll be prompted to paste the resulting URL into the console. After this, the credentials the script requires will be cached in ~/.spotify-deduplicator/
