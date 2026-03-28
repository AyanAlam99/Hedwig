"""
HEDWIG — Fast Server (Fixed Lag)
==================================
Fixes:
  1. pyttsx3 engine created ONCE at startup, not every speak call
  2. SpeechToText created ONCE, shared across all uses
  3. Ambient noise calibration removed from hot path
  4. Wake word audio flush improved
  5. TTS runs in background thread — doesn't block listening
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from speech_to_text import NLUParser, SpeechToText
from action_router import ActionRouter
from contextlib import asynccontextmanager
import uvicorn
import tempfile, os, uuid, threading, time
import pyttsx3
import pyaudio
import numpy as np
from openwakeword.model import Model
import queue



# ─────────────────────────────────────────────
# SPEAKER — init ONCE, reuse forever
# ─────────────────────────────────────────────

import pygame
import tempfile
from gtts import gTTS
import os

class Speaker:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        print("  [Speaker] pygame mixer ready.")

    def _speak_text(self, text: str):
        """Convert text to MP3 via gTTS and play via pygame (no device conflict)."""
        try:
            tts = gTTS(text=text, lang='en', tld='co.in')
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tts.save(f.name)
                tmp = f.name
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            os.unlink(tmp)
        except Exception as e:
            print(f"  [Speaker Error]: {e}")

    def say(self, text: str):
        """Blocking — waits until speech finishes."""
        if not text: return
        print(f"\n Hedwig: {text}")
        self._speak_text(text)

    def say_async(self, text: str):
        """Non-blocking."""
        if not text: return
        print(f"\n Hedwig: {text}")
        threading.Thread(target=self._speak_text, args=(text,), daemon=True).start()

# ─────────────────────────────────────────────
# GLOBAL INSTANCES — created once at startup
# ─────────────────────────────────────────────

nlu     = NLUParser()
router  = ActionRouter()
stt     = SpeechToText()      # model loaded ONCE here
speaker = Speaker()            # pyttsx3 engine created ONCE here

pending_actions = {}


# ─────────────────────────────────────────────
# FAST PC BACKGROUND LOOP
# ─────────────────────────────────────────────

def pc_background_loop():
    print("💻 [PC] Loading wake word model...")

    oww_model = Model(
        wakeword_models     = ["hey_hedwig.onnx"],
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

    # ── pre-calibrate mic ONCE at startup ────────────────────
    # previously this ran inside listen() every time = 0.3s delay
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    recognizer.pause_threshold         = 1.2
    recognizer.energy_threshold        = 300
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("  [PC] Calibrating mic noise... (once)")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print(f"  [PC] Mic calibrated. Energy threshold: {recognizer.energy_threshold:.0f}")

    print("✅ [PC] Ready! Say 'Hey Hedwig'...\n")

    local_session  = {"id": None, "intent": None}
    cooldown_until = 0

    while True:
        try:
            # read audio chunk
            pcm        = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(pcm, dtype=np.int16)

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

            if score > 0.08:
                print(f"\n✨ Wake word detected! (score={score:.3f})")
                stream.stop_stream()

                # Blocking "Yes?" — mic is OFF, no overlap, works every time
                speaker.say("Yes?")

                temp_path = stt.listen()
                command_text = None
                if temp_path:
                    try:
                        command_text = stt.transcribe_file(temp_path)
                    except Exception as e:
                        print(f"  STT error: {e}")

                if command_text:
                    print(f"You: {command_text}")
                    parsed = nlu.parse(command_text)
                    if parsed:
                        confirmation = router.generate_confirmation_prompt(parsed)
                        speaker.say(confirmation)

                        print("Say yes or no...")
                        with sr.Microphone() as source:
                            try:
                                confirm_audio = recognizer.listen(
                                    source, timeout=6, phrase_time_limit=4
                                )
                            except sr.WaitTimeoutError:
                                confirm_audio = None

                        if confirm_audio:
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                                f.write(confirm_audio.get_wav_data())
                                tmp = f.name
                            confirm_text = stt.transcribe_file(tmp)
                            print(f"  You: {confirm_text}")

                            POSITIVE = ["yes","yeah","yep","sure","ok","okay",
                                        "please","haan","bilkul","kar do","do it"]

                            if confirm_text and any(w in confirm_text.lower() for w in POSITIVE):
                                result = router.execute(parsed)
                                speaker.say(result if isinstance(result, str) else "Done.")
                            else:
                                speaker.say("Okay, cancelled.")
                        else:
                            speaker.say("No response. Cancelled.")
                    else:
                        speaker.say("Sorry, I didn't understand.")
                else:
                    speaker.say("I didn't catch that.")

                # Restart in correct order: start → sleep → flush → reset → cooldown
                print("\nBack to sleep...")
                stream.start_stream()
                time.sleep(0.1)
                available = stream.get_read_available()
                if available > 0:
                    stream.read(available, exception_on_overflow=False)
                oww_model.reset()           # reset after flush
                cooldown_until = time.time() + 2.0

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
    """Mobile endpoint — receives audio, returns response."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(await audio.read())
        temp_path = f.name

    text = stt.transcribe_file(temp_path)
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