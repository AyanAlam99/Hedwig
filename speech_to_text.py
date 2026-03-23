"""
JARVIS — Updated SpeechToText
================================
Uses Groq's Whisper Large V3 API instead of local small.en model.

Why:
  - small.en can't handle Hinglish / Urdu words at all
  - Groq runs whisper-large-v3 for free (500 mins/day free tier)
  - Faster than local small model
  - Handles: "kaise ho tum", "samjhawan", "Tajdar e Haram",
             mixed English-Hindi sentences perfectly

Drop-in replacement — rest of your code (NLUParser etc.) unchanged.
"""

import os
import json
import tempfile
import datetime
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


class NLUParser:

    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.client     = Groq(api_key=GROQ_API_KEY)
        self.model_name = model_name

    def parse(self, text: str) -> dict | None:
        if not text:
            return None

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        system_prompt = f"""
        You are the Natural Language Understanding (NLU) core of a voice assistant.
        Your job is to parse messy, transcribed speech, extract the core intent, and output ONLY valid JSON.
        
        CRITICAL AUTO-CORRECT RULE: 
        IMPORTANT RULES FOR PARAMETERS:
        - "on Spotify", "on YouTube" = platform identifier, NOT the artist name.
        - target = artist name only. If no artist was mentioned, leave target empty ""
        - NEVER correct, expand, or add explanations to names in parameters.
        - NEVER add parentheses, notes, or extra context to any field.
        - If the user says "Summer Jafri", write "Summer Jafri" — not the corrected version.
        - target and content fields must contain ONLY the raw name, nothing else.
        - Wrong: "Akhtar Chanal Zahri (Corrected Artist Name, formerly known as Summer Jafri)"
        - Right:  "Summer Jafri" — exactly what was spoken, cleaned up only for spelling

        .

        CURRENT SYSTEM TIME: {current_time}

        Expected JSON schema:
        {{
            "intent": "schedule_meeting" | "send_message" | "play_media" | "open_app" | "search" | "unknown",
            "platform": "whatsapp" | "youtube" | "spotify" | "calendar" | "general" | "unknown",
            "parameters": {{
                "target": "Contact name, YouTube channel, or Artist name (Corrected for typos)",
                "content": "The message body, search query, or EXACT Song Name (Corrected for typos)",
                "action_modifier": "Specific instructions like 'latest video', 'shuffle', etc. (if applicable)",
                "date": "YYYY-MM-DD (if specified)",
                "time": "HH:MM (in 24-hour format, if specified)"
            }}
        }}
        """

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
    """
    Records mic audio and transcribes using Groq Whisper Large V3.

    Key changes from previous version:
      - Removed local WhisperModel (faster_whisper)
      - Removed torch dependency for STT
      - Uses Groq's whisper-large-v3-turbo via API
      - Added initial_prompt for Hinglish bias
      - Added language="en" with prompt override for mixed language

    Groq free tier: 7200 seconds (120 mins) audio per day — plenty.
    """

    # Prompt that biases Whisper toward Hinglish transcription
    # Add any words/names it keeps getting wrong here
    HINGLISH_PROMPT = (
        "The user speaks English with occasional Urdu and Hindi words,"
        "The speaker uses Hinglish — mixed Hindi and English in the same sentence. "
        "Transcribe Hindi/Urdu words in Roman script exactly as spoken. "
        "Common words: kaise ho, kya haal hai, yaar, bhai, acha, theek hai, "
        "samjhawan, hoor, khaab, ishq, dil, zindagi, pyaar, mohabbat, "
        "Tajdar e Haram, Atif Aslam, Rahat Fateh Ali Khan, Arijit Singh, "
        "kal milte hain, abhi busy hoon, thoda wait karo. "
        "Do not translate. Transcribe exactly what is said."
    )

    def __init__(self):
        self.client     = Groq(api_key=GROQ_API_KEY)
        self.recognizer = sr.Recognizer()

        # VAD settings
        self.recognizer.pause_threshold    = 1.5
        self.recognizer.energy_threshold   = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen(self) -> str | None:
        """
        Records mic until silence, sends to Groq Whisper, returns transcript.
        """
        # ── Step 1: capture audio ─────────────────────────────
        with sr.Microphone() as source:
            print("\n🎤 Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout          = 10,
                    phrase_time_limit= 25
                )
            except sr.WaitTimeoutError:
                print("  [STT] No speech detected.")
                return None

        print("  [STT] Transcribing via Groq Whisper...")

        # ── Step 2: save to temp WAV ──────────────────────────
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as f:
                f.write(audio.get_wav_data())
                temp_path = f.name

            # ── Step 3: send to Groq Whisper API ──────────────
            with open(temp_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file   = audio_file,
                    model  = "whisper-large-v3-turbo",  # fastest + most accurate

                    # prompt biases toward Hinglish — key fix
                    prompt = self.HINGLISH_PROMPT,

                    # "en" keeps output in Roman script
                    # remove this line if you want Devanagari Hindi output
                    language          = "en",

                    response_format   = "text",
                    temperature       = 0.0,
                )

            os.unlink(temp_path)

            text = transcription.strip() if transcription else None

            if text:
                print(f"  [STT] Transcript: \"{text}\"")

            return text

        except Exception as e:
            print(f"  [STT Error]: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            return None


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    stt = SpeechToText()
    nlu = NLUParser()

    print("Speak something in Hinglish...")
    print("Try: 'Send a WhatsApp to Rahul saying kaise ho tum yaar'")
    print("Or:  'Play Tajdar e Haram on YouTube'\n")

    raw_text = stt.listen()

    if raw_text:
        print(f"\n  Raw Transcript : {raw_text}")
        print("  Parsing intent...")

        parsed = nlu.parse(raw_text)

        print("\n  Final JSON:")
        print(json.dumps(parsed, indent=4))
    else:
        print("\n  No audio captured.")