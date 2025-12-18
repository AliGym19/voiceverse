import pyttsx3
import os
from openai import OpenAI

# ===== OPTION 1: Using pyttsx3 (offline, free) =====
def text_to_speech_pyttsx3(text):
    """Convert text to speech using pyttsx3 (works offline)"""
    try:
        engine = pyttsx3.init()
        
        # Set speech rate to 100
        engine.setProperty("rate", 100)
        
        # List available voices
        voices = engine.getProperty("voices")
        print(f"Available voices: {len(voices)}")
        for voice in voices:
            print(f"  - {voice.name}")
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
        # Save to file
        engine.save_to_file(text, "pyttsx3_output.mp3")
        engine.runAndWait()
        
        print("✓ pyttsx3 speech generated successfully")
        
    except Exception as e:
        print(f"Error with pyttsx3: {e}")


# ===== OPTION 2: Using OpenAI TTS (online, requires API key) =====
def text_to_speech_openai(text):
    """Convert text to speech using OpenAI's API (requires internet and API key)"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            return
        
        client = OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            speed=1.0
        )
        
        response.stream_to_file("openai_output.mp3")
        print("✓ OpenAI TTS audio saved successfully")
        
    except Exception as e:
        print(f"Error with OpenAI TTS: {e}")


# ===== USAGE =====
if __name__ == "__main__":
    text = input("Enter text to read aloud: ")
    
    # Use pyttsx3 (offline)
    print("\n--- Using pyttsx3 ---")
    text_to_speech_pyttsx3(text)
    
    # Use OpenAI (online, requires API key)
    print("\n--- Using OpenAI TTS ---")
    text_to_speech_openai(text)
