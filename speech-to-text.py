from faster_whisper import WhisperModel
import speech_recognition as sr
import torch , os
from groq import Groq
from dotenv import load_dotenv
import json
import datetime

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

class SpeechToText : 
    def __init__(self,model_size = 'small.en') : 
        self.device ="cuda" if torch.cuda.is_available() else "cpu"
        self.model = WhisperModel(model_size,device = self.device)
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 2.0
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True

    def llm_parser(self,text) : 
            

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        client = Groq(api_key=GROQ_API_KEY)


        system_prompt = f"""
        You are the Natural Language Understanding (NLU) core of a voice assistant.
        Your job is to parse messy, transcribed speech, correct phonetic errors, extract the core intent, and output ONLY valid JSON.
        Do not include conversational filler, markdown formatting (like ```json), or explanations.

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
        chat_completion = client.chat.completions.create(
            messages=[
                {'role' : 'system','content':system_prompt},
                {'role':'user','content':f"Parse this transcript {text} "}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        return json.loads(chat_completion.choices[0].message.content)

    def listen(self) : 
        with sr.Microphone() as source : 
            print("Listening now")

            self.recognizer.adjust_for_ambient_noise(source,duration=0.3)

            try : 
                audio = self.recognizer.listen(source,timeout=10,phrase_time_limit=15)
            except sr.WaitTimeoutError:
                print("no speech detected")
                return None
            
        print("got the speech , Transcribing now")

        try : 
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as f : 
                f.write(audio.get_wav_data())
                temp_path = f.name

            segments, info = self.model.transcribe(temp_path,language="en",beam_size=5,vad_filter=True,  
            vad_parameters=dict(min_silence_duration_ms=500))

            text = "".join([segment.text for segment in segments]).strip()
            print("Transcribed text:", text)

            os.unlink(temp_path)
            if text:
                print("Extracting intent with Groq...")
                parsed_json = self.llm_parser(text)
                return parsed_json
            else:
                return None
        except Exception as e:
            print(f"  Transcription error: {e}")
            return None
        

if __name__=="__main__" : 
    st = SpeechToText()
    text = st.listen()
    print(f"ye rha text {text}")

    


        




