import wave
import os
from datetime import datetime
from core.state import ui_log

def save_false_wak_audio(audio_bytes: bytes): 
    folder_name = "false_positives"
    os.makedirs(folder_name, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder_name, f"error_{timestamp}.wav")

    try: 
        with wave.open(filename, 'wb') as wf: 
            wf.setnchannels(1)
            wf.setframerate(16000)
            wf.setsampwidth(2)
            wf.writeframes(audio_bytes)
            ui_log(f"Active Learning - Saved false wake to {filename}", "sys")
    except Exception as e:
        ui_log(f"Logger Error - Could not save audio: {e}", "err")