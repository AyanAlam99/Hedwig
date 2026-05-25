import spotipy 
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os 
import random

from thefuzz import fuzz
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

def ensure_spotify_open(sp) -> bool:

    import subprocess
    import time
    import os

    # common Spotify paths on Windows
    SPOTIFY_PATHS = [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
        r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
        r"C:\Program Files\Spotify\Spotify.exe",
        r"C:\Program Files (x86)\Spotify\Spotify.exe",
    ]

    print("  Spotify - No devices found — launching Spotify...")

    for path in SPOTIFY_PATHS:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            subprocess.Popen(expanded)
            print(f"  [Spotify] Launched from: {expanded}")
            break
    else:
        # fallback - let Windows find it
        subprocess.Popen("start spotify", shell=True)

    # Wait for Spotify to launch and register with the cloud API.
    # Checks every 3 seconds, up to 10 times (30 seconds total)
    print("  Spotify - Waiting for Spotify API to sync (this can take up to 30s)...")
    
    for attempt in range(10):
        time.sleep(3)
        try:
            devices = sp.devices().get("devices", [])
            if devices:
                print(f"  Spotify - Device synced with API after {(attempt+1)*3}s ✅")
                return True
            print(f"  Spotify - Still syncing... ({(attempt+1)*3}s)")
        except Exception as e:
           
            pass

    print("  Spotify - Spotify didn't register in time.")
    return False

def play_on_spotify(target: str,content : str ,track_uri: str = None) -> dict:
    if not target  and not content:
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

        if track_uri:
            track_name  = content
            artist_name = target
        else:
            search_query = " ".join(p for p in [target, content] if p)
            result = sp.search(q=search_query, type='track', limit=10)
            tracks = result.get('tracks', {}).get('items', [])
            if not tracks:
                return {"success": False, "message": f"Couldn't find '{search_query}'."}
            best        = pick_best_track(tracks, target, content)
            track_uri   = best["uri"]
            track_name  = best["name"]
            artist_name = best["artists"][0]["name"]

          
        devices = sp.devices()

        if not devices.get('devices'):
            launch_success = ensure_spotify_open(sp)
            if launch_success:
                # Refresh the devices list now that the app is open
                devices = sp.devices()
            else:
                return {"success": False, "message": "Could not open Spotify automatically. Please open it manually."}
            
        print(f"  [Spotify] Devices found: {len(devices.get('devices', []))}")

        active_devices = [d for d in devices.get('devices', []) if d.get('is_active')]

        
        device_id = active_devices[0]['id'] if active_devices else devices['devices'][0]['id']

        sp.start_playback(device_id=device_id, uris=[track_uri])
        print(f"  [Spotify] Playing {track_name}. Fetching radio mix...")
        
        valid_tracks = []
        
       
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

                pl_data = sp.playlist_tracks(radio_uri, limit=30)
                for item in pl_data.get('items', []):
                    track = item.get('track')
                    if track and track.get('uri') and track.get('uri') != track_uri:
                        valid_tracks.append(track)
                        
        except Exception as playlist_err:
            print(f"  [Spotify] API blocked reading playlist. Skipping to fallback.")
            
            
        
        try:
            
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
    

from thefuzz import fuzz

def pick_best_track(tracks: list, target: str,content:str) -> dict:
    """
    Picks the most relevant track from search results using Fuzzy String Matching.
    This handles spelling mistakes from Speech-to-Text (e.g. Kaab vs Khaab).
    """
    best_score = -1
    best_track = tracks[0]  # Fallback to the first track

    target_clean = target.lower()
    content_clean = content.lower()

    for track in tracks:
        song_name   = track["name"].lower()
        artist_name = track["artists"][0]["name"].lower()
        
        
        combined = f"{song_name} {artist_name}"

        score1 = fuzz.token_set_ratio(song_name, content_clean)
        score2 = fuzz.token_set_ratio(artist_name, target_clean)
        final_score = score1+score2

        print(f"  [Fuzzy Match] '{track['name']}' by '{track['artists'][0]['name']}' — score: {final_score}%")

        if final_score > best_score:
            best_score = final_score
            best_track = track

    return best_track



def preview_spotify_match(target: str, content: str) -> dict:
    """
    Does the search and fuzzy match but does NOT start playback.
    Returns the best track info so confirmation can use the real name.
    """
    try:
        scope = "user-read-playback-state,user-modify-playback-state"
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope,
            open_browser=True
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        search_query = " ".join(p for p in [target, content] if p)
        result = sp.search(q=search_query, type='track', limit=10)
        tracks = result.get('tracks', {}).get('items', [])

        if not tracks:
            return {"found": False, "message": f"Couldn't find '{search_query}' on Spotify."}

        best = pick_best_track(tracks, target, content)
        return {
            "found":       True,
            "track_name":  best["name"],
            "artist_name": best["artists"][0]["name"],
            "track_uri":   best["uri"],
        }

    except Exception as e:
        return {"found": False, "message": str(e)}