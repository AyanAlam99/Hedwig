import spotipy 
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os 

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
    "user-modify-playback-state,"
    "playlist-read-private,"       # ← add this
    "playlist-read-collaborative"  # ← and this
)
        
        auth_manager = SpotifyOAuth(
             client_id=SPOTIFY_CLIENT_ID,
             client_secret=SPOTIFY_CLIENT_SECRET,
             redirect_uri=SPOTIPY_REDIRECT_URI,
             scope=scope,
             open_browser=True
        )

        sp = spotipy.Spotify(auth_manager=auth_manager)
        result = sp.search(q=search_query,type='track',limit=10)
        tracks = result.get('tracks',{}).get('items',[])

        if not tracks : 
             return {"success":False , "message" : f"Could not find the {search_query} on Spotify"}
        track_uri = tracks[0]['uri']
        track_name = tracks[0]['name']
        artist_name = tracks[0]['artists'][0]['name']

        devices = sp.devices()
        print(f'printed the devices {devices}')

        active_devices = [d for d in devices['devices'] if d['is_active']]

        if not devices['devices']:
             return {"success": False, "message": "No Spotify devices found. Open Spotify first."}
        
        device_id = active_devices[0]['id'] if active_devices else devices['devices'][0]['id']


        best_track = pick_best_track(tracks, search_query)
        artist_id   = best_track["artists"][0]["id"]
        artist_info = sp.artist(artist_id)
        genres      = artist_info.get("genres", [])

        print(f"  [Spotify] Genres detected: {genres}")

        # ── Step 3: find a genre playlist ────────────────────
        # try each detected genre until we find a playlist
        # replace your playlist fetch loop with this:
        playlist_uri  = None
        playlist_name = None
        genre_used    = None

        # --- 4. FIND A MATCHING PLAYLIST ---
        for genre in genres:
            print(f"  [Spotify] Searching playlist for: '{genre}'")
            pl_results = sp.search(q=genre, type="playlist", limit=5) 
            playlists  = [p for p in pl_results.get("playlists", {}).get("items", []) if p]

            for pl in playlists:
                if pl.get("public") is False:
                    continue
                try:
                    test = sp.playlist_tracks(pl["uri"], limit=1)
                    if test.get("items"):
                        playlist_uri  = pl["uri"]
                        playlist_name = pl["name"]
                        genre_used    = genre
                        print(f"  [Spotify] Found valid playlist: '{playlist_name}'")
                        break
                except Exception:
                    continue
            
            # If we found a valid playlist in the inner loop, break the outer loop too
            if playlist_uri:
                break 

        # --- 5. EXECUTE PLAYBACK ---
        if playlist_uri:
            # First, start playback of the specific requested song
            sp.start_playback(device_id=device_id, uris=[track_uri])
            
            # Note: Spotify API doesn't easily let you force a playlist into the queue securely 
            # without interrupting the current song. So we play the song, and rely on 
            # Spotify's native "Autoplay" feature to keep the music going.
            
            try:
                sp.shuffle(state=True, device_id=device_id)
            except Exception:
                pass # Some devices (like web player) reject shuffle commands
                
            return {
                "success": True,
                "message": f"Playing {track_name} by {artist_name}. Found {genre_used} vibes."
            }
            
        else:
            # Last resort — just play the single track
            print(f"DIdnt get the plalysit buddy ")
            sp.start_playback(device_id=device_id, uris=[track_uri])
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
