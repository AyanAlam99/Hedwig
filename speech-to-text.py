import os
import json
import tempfile
import datetime
import speech_recognition as sr
import torch
from faster_whisper import WhisperModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

class NLUParser:

    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model_name = model_name

    def parse(self, text: str) -> dict | None:
        
        if not text:
            return None

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        system_prompt = f"""
        You are the Natural Language Understanding (NLU) core of a voice assistant.
        Your job is to parse messy, transcribed speech, correct phonetic errors, extract the core intent, and output ONLY valid JSON.
        Do not include conversational filler, markdown formatting, or explanations.

        CURRENT SYSTEM TIME: {current_time}
        Use this to accurately resolve relative dates and times.

        Expected JSON schema:
        {{
            "intent": "schedule_meeting" | "send_message" | "play_media" | "open_app" | "search" | "unknown",
            "platform": "whatsapp" | "youtube" | "spotify" | "calendar" | "general" | "unknown",
            "parameters": {{
                "target": "Contact name, YouTube channel, or entity name (if applicable)",
                "content": "The message body, song name, or search query (if applicable)",
                "action_modifier": "Specific instructions like 'latest video', 'shuffle', etc. (if applicable)",
                "date": "YYYY-MM-DD (if specified)",
                "time": "HH:MM (in 24-hour format, if specified)"
            }}
        }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Parse this transcript: {text}"}
                ],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            print(f"  [NLU Error]: {e}")
            return None


class SpeechToText:
    
    def __init__(self, model_size='small.en'):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = WhisperModel(model_size, device=self.device)
        
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8  # Lowered to prevent long silence capture
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True

    def listen(self) -> str | None:
        """Captures audio and returns raw text."""
        with sr.Microphone() as source: 
            print("\nSTT Listening now...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

            try: 
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                print("[STT] No speech detected.")
                return None
            
        print("STT Audio captured, transcribing...")

        try: 
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: 
                f.write(audio.get_wav_data())
                temp_path = f.name

            
            segments, _ = self.model.transcribe(
                temp_path, 
                language="en", 
                beam_size=5,
                vad_filter=True,  
                vad_parameters=dict(min_silence_duration_ms=500)
            )

    
            text = "".join([segment.text for segment in segments]).strip()
            
            os.unlink(temp_path)
            return text if text else None
 
        except Exception as e:
            print(f"[STT Error]: Transcription failed: {e}")
            return None


if __name__ == "__main__": 

    stt = SpeechToText()
    nlu = NLUParser()


    raw_text = stt.listen()
    
    if raw_text:
        print(f"\nRaw Transcript: {raw_text}")
        print("NLU Extracting intent")
        
        parsed_data = nlu.parse(raw_text)
        
        print("\n Final JSON Payload:")
        print(json.dumps(parsed_data, indent=4))
    else:
        print("\nPipeline Cancelled: No audio input.")
