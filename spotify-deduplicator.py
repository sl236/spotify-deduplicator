#!/usr/bin/python
import spotipy
import os, time
import cPickle as pickle

CONFIG_DIR = os.path.join( os.environ.get('HOME', os.environ.get('APPDATA', '') ), '.spotify-deduplicator' )

def load_config():
    import json
    config_defaults = {
        'min_seconds_before_repeat': 60 * 60 * 24 * 7,
        'username': None,
        'client_id': None,
        'client_secret': None,
        'auth_cache_path': os.path.join( CONFIG_DIR, 'auth' ),
        'db_path': os.path.join( CONFIG_DIR, 'db' ),
        'redirect_uri': 'spotify-deduplicator://auth/',
    }

    if not os.path.isdir( CONFIG_DIR ):
        print "Couldn't find config directory: %s\n" % CONFIG_DIR
        exit(1)

    config_path = os.path.join( CONFIG_DIR, 'config.json' )
    if not os.path.isfile( config_path ):
        print "Couldn't find config file: %s\n" % config_path
        exit(1)

    try:
        with open( config_path ) as f:
            config = json.load( f )
    except Exception as e:
        print 'Failed to read json config from %s: %s\n' % ( config_path, e )
        exit(1)

    for item in config_defaults:
        if item not in config:
            if not config_defaults[item]:
                print 'Required config item not present in config file: %s\n' % item
                exit(1)
            config[item] = config_defaults[item]

    return config

def load_db(config):
    try:
        with open( config['db_path'], 'rb' ) as f:
            return pickle.load( f )
    except:
        return { 'last': None }

def store_db(db, config):
    try:
        with open( config['db_path'], 'wb' ) as f:
            pickle.dump( db, f )
    except Exception as e:
        print e

def authenticate(config):
    required_scopes = [ 'user-read-currently-playing',
                        'user-read-playback-state',
                        'user-modify-playback-state' ]
    import spotipy.util
    return spotipy.util.prompt_for_user_token(
            username=config['username'],
            scope=' '.join(required_scopes),
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            cache_path=config['auth_cache_path'],
            redirect_uri=config['redirect_uri']
        )

def check_playback( sp, db, config ):
    currently_playing = sp.current_playback()
    try:
        if currently_playing and currently_playing.get('is_playing', None) and currently_playing.get('item', None):
            item = currently_playing['item']
            left = item['duration_ms'] - currently_playing['progress_ms']

            if item['id'] != db['last']:
                print 'now playing: %s -- "%s" -- %s -- %d/%d' % (
                        item['id'],
                        item['name'],
                        ','.join( artist['name'] for artist in item['artists'] if artist['name'] ),
                        int(currently_playing['progress_ms']/1000),
                        int(item['duration_ms']/1000),
                    )

                curr_time = time.time()
                last_time = db.get( item['id'], 0 )
                db['last'] = item['id']

                if curr_time - last_time < config['min_seconds_before_repeat']:
                    context = currently_playing.get('context', None)
                    if context:
                        print 'Track was last played %d seconds ago, but not skipping because context is populated -> not playing radio'
                    else:
                        print 'Track was last played %d seconds ago; skipping' % (curr_time - last_time)
                        sp.next_track( device_id = currently_playing['device']['id'] )
                        return 1

                db[item['id']] = curr_time
                store_db( db, config )

            return min( int(left/1000)+1, 30 )

    except Exception as e:
        print e

    return 30

def main():
    config = load_config()
    token = authenticate( config )
    sp = spotipy.Spotify( auth=token )
    db = load_db(config)

    while True:
        try:
            wait_time = check_playback( sp, db, config )
        except spotipy.client.SpotifyException:
            token = authenticate()
            sp = spotipy.Spotify( auth=token )
            wait_time = check_playback( sp, db, config ) # so we die if we fail here immediately after authenticate()

        time.sleep( wait_time )

main()
