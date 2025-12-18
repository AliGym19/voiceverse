import pyttsx3

def text_to_speech(text, voice_id):
    """Convert text to speech with selected voice"""
    try:
        engine = pyttsx3.init()
        
        # Set speech rate to 100
        engine.setProperty("rate", 100)
        
        # Set the selected voice
        engine.setProperty("voice", voice_id)
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
        print("✓ Speech completed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Initialize engine to get voices
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    
    # Display voice menu
    print("\n=== Available Voices ===")
    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice.name}")
    
    # Get user's voice choice
    while True:
        try:
            choice = int(input(f"\nSelect a voice (1-{len(voices)}): "))
            if 1 <= choice <= len(voices):
                selected_voice = voices[choice - 1]
                print(f"✓ Selected: {selected_voice.name}\n")
                break
            else:
                print("Invalid choice, try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Get text to speak
    text = input("Enter text to read aloud: ")
    text_to_speech(text, selected_voice.id)

    
