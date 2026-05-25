import os
import json
import tempfile
import datetime
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv
from faster_whisper import WhisperModel
import io
from prompts import NLU_SYSTEM_PROMPT , HINGLISH_PROMPT

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")



class NLUParser:

    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.client     = Groq(api_key=GROQ_API_KEY)
        self.model_name = model_name

    def parse(self, text: str) -> dict | None:
        if not text:
            return None

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        system_prompt = NLU_SYSTEM_PROMPT.format(current_time=current_time)

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': f"Parse this transcript: {text}"}
                ],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"  [NLU Error]: {e}")
            return None


class SpeechToText:

    HING_PROMPT= HINGLISH_PROMPT



    def __init__(self, model_size="small"):
        self.recognizer = sr.Recognizer()
        self.client = Groq(api_key=GROQ_API_KEY)
        # VAD settings
        self.recognizer.pause_threshold    = 0.7
        self.recognizer.energy_threshold   = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen(self,timeout=10,phrase_time_limit = 25) :

        with sr.Microphone() as source:
            print("\n🎤 Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout           = timeout,
                    phrase_time_limit = phrase_time_limit
                )
                return audio.get_wav_data()
            except sr.WaitTimeoutError:
                print("  [STT] No speech detected.")
                return None
                    
            # try:
            #     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            #         f.write(audio.get_wav_data())
            #         return f.name
            # except Exception as e:
            #     print(f"  [STT Error saving audio]: {e}")
            #     return None
         

    def transcribe_audio(self,audio_bytes : bytes) :
           
        try : 
                virtual_file =io.BytesIO(audio_bytes)
                virtual_file.name = "audio.wav"
                result = self.client.audio.transcriptions.create(
                    file = virtual_file,
                    model = "whisper-large-v3",
                    prompt = self.HING_PROMPT,
                    response_format = "text",
                    temperature     = 0.0,
                    language='en'
                        )
            
                text= str(result).strip() if result else None

                    

                if text:
                    print(f"  [STT] Transcript: \"{text}\"")

                return text

        except Exception as e:
            print(f"  [STT Error]: {e}")
            return None

