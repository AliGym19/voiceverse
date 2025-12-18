import os
from openai import OpenAI
import subprocess

def text_to_speech_openai(text, voice):
    """Convert text to speech using OpenAI's high-quality TTS"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n❌ Error: OPENAI_API_KEY not set")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            print("Get your API key from: https://platform.openai.com/api-keys")
            return
        
        client = OpenAI(api_key=api_key)
        
        print(f"\n🎙️  Generating speech with {voice} voice...")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=1.0
        )
        
        filename = "speech_output.mp3"
        response.stream_to_file(filename)
        
        print(f"✓ Audio saved as {filename}")
        
        # Auto-play the audio on Mac
        subprocess.run(["afplay", filename])
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # High-quality voice options
    voices = {
        1: ("alloy", "Neutral, balanced"),
        2: ("echo", "Male, clear"),
        3: ("fable", "British, expressive"),
        4: ("onyx", "Deep, authoritative"),
        5: ("nova", "Female, friendly"),
        6: ("shimmer", "Soft, warm")
    }
    
    print("\n=== OpenAI High-Quality Voices ===")
    for num, (voice, desc) in voices.items():
        print(f"{num}. {voice.capitalize()} - {desc}")
    
    # Get voice choice
    while True:
        try:
            choice = int(input(f"\nSelect a voice (1-6): "))
            if 1 <= choice <= 6:
                selected_voice = voices[choice][0]
                print(f"✓ Selected: {voices[choice][0].capitalize()}")
                break
            else:
                print("Invalid choice, try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Get text to speak
    text = input("\nEnter text to read aloud: ")
    
    text_to_speech_openai(text, selected_voice)


