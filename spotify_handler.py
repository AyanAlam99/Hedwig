import spotipy 
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os 
import random

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

def play_on_spotify(search_query: str) -> dict:
    if not search_query:
        return {"success": False, "message": "No song provided."}

    try:
        # Request permission to read devices and modify playback
        scope = (
            "user-read-playback-state,"
            "user-modify-playback-state"
        )
        
        auth_manager = SpotifyOAuth(
             client_id=SPOTIFY_CLIENT_ID,
             client_secret=SPOTIFY_CLIENT_SECRET,
             redirect_uri=SPOTIPY_REDIRECT_URI,
             scope=scope,
             open_browser=True
        )

        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # --- 1. SEARCH FOR TRACK ---
        result = sp.search(q=search_query, type='track', limit=10)
        tracks = result.get('tracks', {}).get('items', [])

        if not tracks: 
            return {"success": False, "message": f"Could not find '{search_query}' on Spotify."}
        
        best_track = pick_best_track(tracks, search_query)
        track_uri = best_track['uri']
        track_name = best_track['name']
        artist_name = best_track['artists'][0]['name']

        # --- 2. FIND ACTIVE DEVICE ---
        devices = sp.devices()
        print(f"  [Spotify] Devices found: {len(devices.get('devices', []))}")

        active_devices = [d for d in devices.get('devices', []) if d.get('is_active')]

        if not devices.get('devices'):
             return {"success": False, "message": "No Spotify devices found. Open Spotify first."}
        
        device_id = active_devices[0]['id'] if active_devices else devices['devices'][0]['id']

        # --- 3. EXECUTE PLAYBACK & QUEUE (The Search Bypass) ---
        sp.start_playback(device_id=device_id, uris=[track_uri])
        print(f"  [Spotify] Playing {track_name}. Fetching radio mix...")
        
        valid_tracks = []
        
        # Step A: Try to find and read a Radio playlist
        try:
            pl_search = sp.search(q=f"{artist_name} Radio", type='playlist', limit=5)
            playlists = pl_search.get('playlists', {}).get('items', [])
            
            radio_uri = None
            for pl in playlists:
                if pl and pl.get('uri'): 
                    radio_uri = pl['uri']
                    print(f"  [Spotify] Found Playlist: {pl.get('name')}")
                    break
                    
            if radio_uri:
                # If this throws a 403 Forbidden, it will safely drop to the except block below
                pl_data = sp.playlist_tracks(radio_uri, limit=30)
                for item in pl_data.get('items', []):
                    track = item.get('track')
                    if track and track.get('uri') and track.get('uri') != track_uri:
                        valid_tracks.append(track)
                        
        except Exception as playlist_err:
            print(f"  [Spotify] API blocked reading playlist. Skipping to fallback.")
            # valid_tracks remains empty, which safely triggers Step B!
            
        # Step B & C & D: The safe fallback and queueing
        try:
            # If Step A failed or returned nothing, do the safe artist search
            if not valid_tracks:
                print("  [Spotify] Falling back to guaranteed artist tracks...")
                artist_search = sp.search(q=f'artist:"{artist_name}"', type='track', limit=10)
                artist_tracks = artist_search.get('tracks', {}).get('items', [])
                valid_tracks = [t for t in artist_tracks if t and t.get('uri') and t.get('uri') != track_uri]
            
            # Shuffle the tracks
            random.shuffle(valid_tracks)
            
            queued_count = 0
            MAX_SONGS_TO_QUEUE = 10 
            
            for track in valid_tracks:
                try:
                    sp.add_to_queue(uri=track['uri'], device_id=device_id)
                    queued_count += 1
                    if queued_count >= MAX_SONGS_TO_QUEUE:
                        break
                except Exception as q_err:
                    print(f"  [Spotify] Skipped queue item: {q_err}")
                        
            return {
                "success": True,
                "message": f"Playing {track_name}. Queued {queued_count} tracks."
            }
            
        except Exception as e:
            print(f"  [Spotify] Queue error: {e}")
            return {
                "success": True,
                "message": f"Playing {track_name} by {artist_name}."
            }
    except Exception as e:
        error = str(e)
        print(f"  [Spotify Error]: {error}")
        if "NO_ACTIVE_DEVICE" in error or "404" in error:
            return {"success": False, "message": "Open Spotify on your device first, then try again."}
        if "PREMIUM" in error.upper():
            return {"success": False, "message": "Spotify Premium is required to control playback."}
        return {"success": False, "message": f"Spotify API error: {error}"}


    #     return {
    #         "success": True, 
    #         "message": (
    #             f"Playing {track_name} by {artist_name}. "
    #             f"Queued {len(rec_tracks)} similar songs after it."
    #         )

    #     }

    # except spotipy.exceptions.SpotifyException as e:
    #     return {"success": False, "message": f"Spotify API Error: {str(e)}"}
    # except Exception as e:
    #     return {"success": False, "message": f"Execution error: {str(e)}"}
    

def pick_best_track(tracks: list, query: str) -> dict:
    """
    Picks the most relevant track from search results
    instead of blindly returning the first one.
    
    Scores each track by how many query words appear
    in the song name + artist name.
    """
    query_words = set(query.lower().split())
    
    best_score = -1
    best_track = tracks[0]  # fallback to first

    for track in tracks:
        song_name   = track["name"].lower()
        artist_name = track["artists"][0]["name"].lower()
        combined    = f"{song_name} {artist_name}"

        # score = number of query words found in song+artist
        score = sum(1 for word in query_words if word in combined)

        print(f"  [Match] '{track['name']}' by '{track['artists'][0]['name']}' — score: {score}")

        if score > best_score:
            best_score = score
            best_track = track

    return best_track
