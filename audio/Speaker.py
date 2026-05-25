import pygame
import tempfile
import time
import os
import wave
from piper.voice import PiperVoice
import threading
import io



class Speaker:
    def __init__(self,model_path="en_GB-semaine-medium.onnx", config_path="en_GB-semaine.json"):
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        print("  Speaker - pygame mixer ready.")

        print("LOadinf piper model")
        try : 
            self.voice = PiperVoice.load(model_path,config_path)
            print(" Speaker - Piper TTS ready.")
        except Exception as e:
            print(f" Speaker Error - Could not load Piper model: {e}. Check file paths!")
    
    def play_hedwig_wake(self,filepath : str) :
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"  [Speaker Error] Could not play sound effect {filepath}: {e}")

    def _speak_text(self, text: str):
        """Convert text to WAV inmemory via Piper and play via pygame."""
        try:
            wav_io = io.BytesIO()

            with wave.open(wav_io, 'wb') as wav_file:
                self.voice.synthesize_wav(text, wav_file)
            wav_io.seek(0)

            pygame.mixer.music.load(wav_io)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
                
            pygame.mixer.music.unload()

        except Exception as e:
            print(f"  [Speaker Error]: {e}")
            

    def say(self, text: str):
        """Blocking ,  waits until speech finishes."""
        if not text: return
        print(f"\n Hedwig: {text}")
        self._speak_text(text)

    def say_async(self, text: str):
        """Non-blocking."""
        if not text: return
        print(f"\n Hedwig: {text}")
        threading.Thread(target=self._speak_text, args=(text,), daemon=True).start()
