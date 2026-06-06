import time
import threading
from collections import deque
import pyaudio
import numpy as np
from openwakeword.model import Model

from core.state import ui_log
from core.active_learning import save_false_wak_audio
from audio.speech_to_text import NLUParser, SpeechToText
from core.action_router import ActionRouter
from integrations.spotify_handler import preview_spotify_match
from integrations.whatsapp_handler import resolve_contact
from audio.Speaker import Speaker

nlu = NLUParser()
router = ActionRouter()
stt = SpeechToText()      
speaker = Speaker()            

def back_to_sleep(stream, oww_model): 
    ui_log("Back to sleep...", "sys")
    stream.start_stream()
    time.sleep(0.1)
    available = stream.get_read_available()
    if available > 0:
        stream.read(available, exception_on_overflow=False)
    oww_model.reset()  

        
def pc_background_loop():
    ui_log("PC Loading wake word model...", "sys")

    oww_model = Model(
        wakeword_models=["hey_hedwig.onnx"],
        inference_framework="onnx"
    )

    CHUNK  = 1280
    RATE   = 16000
    audio  = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    ui_log(" Ready! Say 'Hey Hedwig'...", "sys")
    cooldown_until = 0
    audio_history_buffer = deque(maxlen=30)

    while True:
        try:
            pcm        = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(pcm, dtype=np.int16)
            audio_history_buffer.append(pcm)

            if time.time() < cooldown_until:
                continue

            oww_model.predict(audio_data)
            scores = oww_model.prediction_buffer
            score = 0.0
            
            for key in scores:
                if len(scores[key]) > 0:
                    score = float(scores[key][-1])
                    break

            # WAKE WORD DETECTED 
            print(score)
            if score > 0.102:
                ui_log(f"Wake word detected! (score={score:.3f})", "sys")

                false_wake_audio_bytes = b"".join(audio_history_buffer)
                stream.stop_stream()
                
                speaker.play_hedwig_wake("hedwig-scenes-4k-harrypotter-scenepack-hedwig-320-kbps_VMVW05xc.mp3")

                audio_byte = stt.listen()
                
                command_text = None
                if audio_byte:
                    try:
                        command_text = stt.transcribe_audio(audio_byte)
                    except Exception as e:
                        ui_log(f"STT error: {e}", "err")

                if command_text:
                    ui_log(command_text, "you")
                    abort_words = ["abort", "jarvis", "stop", "cancel"]  

                    if any(w in command_text.lower().strip(".!,") for w in abort_words): 
                        speaker.say("Logging false positive.")
                        if false_wake_audio_bytes:
                            threading.Thread(target=save_false_wak_audio, args=(false_wake_audio_bytes,), daemon=True).start()
                        
                        back_to_sleep(stream, oww_model)
                        cooldown_until = time.time() + 6.0
                        continue 
                        
                    parsed = nlu.parse(command_text)
                    print(f"DEBUG NLU OUTPUT: {parsed}")
                    if parsed:
                        intent   = parsed.get("intent", "")
                        platform = parsed.get("platform", "")
                        params   = parsed.get("parameters", {})

                        if intent == "unknown":
                            back_to_sleep(stream, oww_model)
                            cooldown_until = time.time() + 6.0
                            continue

                        if intent == "play_media":
                            spotify_preview = preview_spotify_match(params.get("target", ""), params.get("content", ""))
                            if not spotify_preview["found"]:
                                speaker.say(spotify_preview.get("message", "Couldn't find that song."))
                                back_to_sleep(stream, oww_model)
                                cooldown_until = time.time() + 6.0
                                continue
                            parsed["parameters"]["content"]   = spotify_preview["track_name"]
                            parsed["parameters"]["target"]    = spotify_preview["artist_name"]
                            parsed["parameters"]["track_uri"] = spotify_preview["track_uri"]

                        elif intent == "send_message" or platform == "whatsapp":
                            spoken_name     = params.get("target", "").strip()
                            contact_preview = resolve_contact(spoken_name)

                            if not contact_preview["found"]:
                                speaker.say(contact_preview["message"])
                                back_to_sleep(stream, oww_model)
                                cooldown_until = time.time() + 6.0
                                continue
                            parsed["parameters"]["target"]         = contact_preview["matched_name"]
                            parsed["parameters"]["resolved_phone"] = contact_preview["phone"]

                        elif intent in ("pause", "resume"):
                            result = router.execute(parsed)
                            msg = result if isinstance(result, str) else result.get("message", "Done.") if isinstance(result, dict) else "Done."
                            speaker.say(msg)
                            back_to_sleep(stream, oww_model)
                            cooldown_until = time.time() + 6.0
                            continue
                    
                    
                        confirmation = router.generate_confirmation_prompt(parsed)
                        speaker.say(confirmation)
                        ui_log("Listening for confirmation (yes/no)...", "sys")
                    
                        confirm_audio_bytes = stt.listen(timeout=6, phrase_time_limit=4)
                    
                        if confirm_audio_bytes:
                            confirm_text = stt.transcribe_audio(confirm_audio_bytes)
                            ui_log(confirm_text, "you")
                    
                            POSITIVE = ["yes", "yeah", "yep", "sure", "ok", "okay", "please", "haan", "bilkul", "kar do", "do it"]
                    
                            if confirm_text and any(w in confirm_text.lower() for w in POSITIVE):
                                result = router.execute(parsed)
                                msg = result if isinstance(result, str) else result.get("message", "Done.") if isinstance(result, dict) else "Done."
                                speaker.say(msg)
                            else:
                                speaker.say("Okay, cancelled.")
                        else:
                            speaker.say("No response. Cancelled.")
                    else:
                        speaker.say("Sorry, I didn't understand.")
                else:
                    speaker.say("I didn't catch that.")

                back_to_sleep(stream, oww_model)
                cooldown_until = time.time() + 6.0

        except Exception as e:
            ui_log(f" Loop error: {e}", "err")
            try:
                if not stream.is_active():
                    stream.start_stream()
            except Exception:
                pass
            continue
   