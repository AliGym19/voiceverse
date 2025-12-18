#!/usr/bin/env python3
"""Quick TTS generation test for VoiceVerse"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_tts_generation():
    """Test TTS generation with OpenAI API"""

    # Initialize client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    client = OpenAI(api_key=api_key)

    # Test parameters
    test_text = "Hello from VoiceVerse! This is a quick test of the text to speech system."
    voice = "alloy"
    model = "tts-1"
    output_file = "saved_audio/test_audio.mp3"

    print("🎤 VoiceVerse TTS Test")
    print("=" * 50)
    print(f"Text: {test_text}")
    print(f"Voice: {voice}")
    print(f"Model: {model}")
    print(f"Output: {output_file}")
    print("=" * 50)

    try:
        # Start timer
        start_time = time.time()

        # Generate speech
        print("\n⏳ Generating audio...")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=test_text
        )

        # Save to file
        response.stream_to_file(output_file)

        # Calculate duration
        duration = time.time() - start_time

        # Get file size
        file_size = os.path.getsize(output_file)

        # Results
        print(f"\n✅ SUCCESS!")
        print(f"   Generation time: {duration:.2f}s")
        print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"   Output: {output_file}")

        # Cost estimation
        char_count = len(test_text)
        cost = (char_count / 1000) * 0.015  # TTS-1 pricing
        print(f"   Characters: {char_count}")
        print(f"   Estimated cost: ${cost:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_tts_generation()
    exit(0 if success else 1)
