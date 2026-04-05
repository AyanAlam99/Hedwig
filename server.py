import wave
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from speech_to_text import NLUParser, SpeechToText
from action_router import ActionRouter
from contextlib import asynccontextmanager
import uvicorn
import tempfile, os, uuid, threading, time
from collections import deque
import pyaudio
import numpy as np
from openwakeword.model import Model
import queue
import json
from spotify_handler import preview_spotify_match
import pygame
import tempfile
from gtts import gTTS
import os
from  datetime import datetime
from Speaker import Speaker



nlu     = NLUParser()
router  = ActionRouter()
stt     = SpeechToText()      # model loaded ONCE here
speaker = Speaker()            # pyttsx3 engine created ONCE here

pending_actions = {}


def save_false_wak_audio(audio_bytes:bytes) : 
    folder_name ="false_positives"

    if not os.path.exists(folder_name) :
        os.makedirs(folder_name)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder_name, f"error_{timestamp}.wav")

    try : 
        with wave.open(filename,'wb') as wf : 
            wf.setnchannels(1)
            wf.setframerate(16000)
            wf.setsampwidth(2)
            wf.writeframes(audio_bytes)
            print(f"  [Logger] Saved false wake audio to {filename}")
    except Exception as e:
        print(f"  [Logger Error] Could not save audio: {e}")



def back_to_sleep(stream,oww_model) : 
    print("\nBack to sleep...")
   
    stream.start_stream()
    time.sleep(0.1)
    available = stream.get_read_available()
    if available > 0:
        stream.read(available, exception_on_overflow=False)
    oww_model.reset()           # reset after flush
    

def pc_background_loop():
    print("💻 [PC] Loading wake word model...")

    oww_model = Model(
        wakeword_models     = ["hey_hedwig_v2.onnx"],
        inference_framework = "onnx"
    )

    CHUNK  = 1280
    RATE   = 16000
    audio  = pyaudio.PyAudio()
    stream = audio.open(
        format            = pyaudio.paInt16,
        channels          = 1,
        rate              = RATE,
        input             = True,
        frames_per_buffer = CHUNK
    )

    print("✅ [PC] Ready! Say 'Hey Hedwig'...\n")
    cooldown_until = 0

    audio_history_buffer = deque(maxlen=30)

    while True:
        try:
            # read audio chunk
            pcm        = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(pcm, dtype=np.int16)

            audio_history_buffer.append(pcm)

            # skip prediction during cooldown
            if time.time() < cooldown_until:
                continue

            oww_model.predict(audio_data)
            scores = oww_model.prediction_buffer

            score = 0.0
            for key in scores:
                if len(scores[key]) > 0:
                    score = float(scores[key][-1])
                    break
            print(f"score : {score}")

            if score > 0.102:
                print(f"\n✨ Wake word detected! (score={score:.3f})")

                false_wake_audio_bytes = b"".join(audio_history_buffer)
                stream.stop_stream()
                speaker.play_hedwig_wake("hedwig-scenes-4k-harrypotter-scenepack-hedwig-320-kbps_VMVW05xc.mp3")

                audio_byte =  stt.listen()
                
                command_text = None
                if audio_byte:
                    try:
                        command_text = stt.transcribe_audio(audio_byte)
                    except Exception as e:
                        print(f"  STT error: {e}")

                if command_text:
                    print(f"You: {command_text}")
                    abort_words =["abort","jarvis"]  

                    if any(w in command_text.lower().strip(".!,") for w in abort_words ): 
                        speaker.say("Sorry")

                        if false_wake_audio_bytes:
                            threading.Thread(target=save_false_wak_audio, args=(false_wake_audio_bytes,), daemon=True).start()
                        else : 
                            print(f"no fake byte")

                        back_to_sleep(stream,oww_model)
                        cooldown_until = time.time() + 6.0
                        continue 
                        
                    parsed = nlu.parse(command_text)
                    print(f"Parsed : {parsed}")
                    if parsed:
                        intent   = parsed.get("intent", "")
                        platform = parsed.get("platform", "")
                        params   = parsed.get("parameters", {})
                    
                        if intent == "unknown" or (
                            params.get("target", "") == "" and params.get("content", "") == ""
                        ):
                            back_to_sleep(stream, oww_model)
                            cooldown_until = time.time() + 6.0
                            continue
                    
                        # ── SPOTIFY: resolve real track before confirmation ────────────────────
                        if intent in ["play_media", "play music", "play track"] or platform == "spotify":
                            from spotify_handler import preview_spotify_match
                            spotify_preview = preview_spotify_match(
                                params.get("target", ""),
                                params.get("content", "")
                            )
                            if not spotify_preview["found"]:
                                speaker.say(spotify_preview.get("message", "Couldn't find that song."))
                                back_to_sleep(stream, oww_model)
                                cooldown_until = time.time() + 6.0
                                continue
                    
                            parsed["parameters"]["content"]   = spotify_preview["track_name"]
                            parsed["parameters"]["target"]    = spotify_preview["artist_name"]
                            parsed["parameters"]["track_uri"] = spotify_preview["track_uri"]
                    
                        # ── WHATSAPP: resolve real contact before confirmation ─────────────────
                        elif intent == "send_message" or platform == "whatsapp":
                            from whatsapp_handler import resolve_contact
                            spoken_name      = params.get("target", "").strip()
                            contact_preview  = resolve_contact(spoken_name)
                    
                            if not contact_preview["found"]:
                                speaker.say(contact_preview["message"])
                                back_to_sleep(stream, oww_model)
                                cooldown_until = time.time() + 6.0
                                continue
                    
                            # Overwrite target with the REAL matched contact name
                            # so confirmation says "Send to Sufiyan" not "Send to Sufi"
                            parsed["parameters"]["target"]        = contact_preview["matched_name"]
                            parsed["parameters"]["resolved_phone"] = contact_preview["phone"]
                    
                        # ── CONFIRMATION with real names for all intents ───────────────────────
                        confirmation = router.generate_confirmation_prompt(parsed)
                        speaker.say(confirmation)
                    
                        print("Say yes or no...")
                        confirm_audio_bytes = stt.listen(timeout=6, phrase_time_limit=4)
                    
                        if confirm_audio_bytes:
                            confirm_text = stt.transcribe_audio(confirm_audio_bytes)
                            print(f"  You: {confirm_text}")
                    
                            POSITIVE = ["yes", "yeah", "yep", "sure", "ok", "okay",
                                        "please", "haan", "bilkul", "kar do", "do it"]
                    
                            if confirm_text and any(w in confirm_text.lower() for w in POSITIVE):
                                result = router.execute(parsed)
                                msg = (
                                    result if isinstance(result, str)
                                    else result.get("message", "Done.") if isinstance(result, dict)
                                    else "Done."
                                )
                                speaker.say(msg)
                            else:
                                speaker.say("Okay, cancelled.")
                        else:
                            speaker.say("No response. Cancelled.")
                    else:
                        speaker.say("Sorry, I didn't understand.")
                else:
                    speaker.say("I didn't catch that.")

                back_to_sleep(stream,oww_model)
                cooldown_until = time.time() + 6.0

        except Exception as e:
            print(f"  Loop error: {e}")
            # make sure stream is running
            try:
                if not stream.is_active():
                    stream.start_stream()
            except Exception:
                pass
            continue


# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Hedwig...")
    threading.Thread(target=pc_background_loop, daemon=True).start()
    yield
    print("🛑 Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)


@app.post("/chat-audio")
async def chat_audio(
    audio:      UploadFile = File(...),
    session_id: str        = Form(None)
):
    audio_bytes = await audio.read()

    text = stt.transcribe_file(audio_bytes)
    # transcribe_file handles cleanup internally

    if not text:
        return {"status": "error", "message": "Could not transcribe audio"}

    positive_words = ["yes", "yeah", "yep", "sure", "do it", "ok", "okay", "please"]

    # confirmation flow
    if session_id and session_id in pending_actions:
        if any(w in text.lower() for w in positive_words):
            saved_intent = pending_actions.pop(session_id)
            result       = router.execute(saved_intent)
            return {"status": "executed", "result": result}
        else:
            pending_actions.pop(session_id, None)
            return {"status": "cancelled", "message": "Action cancelled"}

    # new command
    parsed = nlu.parse(text)
    if not parsed:
        return {"status": "error", "message": "Could not parse intent"}

    needs_confirmation = parsed.get("needs_confirmation", False)

    if needs_confirmation:
        new_session_id            = str(uuid.uuid4())
        pending_actions[new_session_id] = parsed
        confirmation              = router.generate_confirmation_prompt(parsed)
        return {
            "status":     "waiting_for_confirmation",
            "message":    confirmation,
            "session_id": new_session_id
        }
    else:
        result = router.execute(parsed)
        return {"status": "executed", "result": result}


@app.get("/status")
async def status():
    return {"running": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)