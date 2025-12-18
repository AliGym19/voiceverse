#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for TTS AI Agents
"""

import os
from tts_agents import create_agent_system

def test_preprocessing():
    """Test text preprocessing agent"""
    print("\n" + "="*60)
    print("Testing: Text Preprocessing Agent")
    print("="*60)

    test_text = """
    Visit   our   website   at   https://example.com   for   more   info.
    The NASA   mission   launched   in   2024.
    Contact: john@example.com or call 555-1234.
    """

    agent = create_agent_system()
    cleaned = agent.preprocess_text(test_text)

    print(f"\nOriginal ({len(test_text)} chars):")
    print(test_text)
    print(f"\nCleaned ({len(cleaned)} chars):")
    print(cleaned)
    print("\n✅ Preprocessing test completed")


def test_smart_chunking():
    """Test smart chunking agent"""
    print("\n" + "="*60)
    print("Testing: Smart Chunking Agent")
    print("="*60)

    # Create a long text (over 4096 chars)
    long_text = """
    Chapter 1: Introduction

    This is a long story that needs to be split into multiple chunks for TTS processing.
    """ + ("This is a test sentence that will be repeated many times. " * 100)

    agent = create_agent_system()
    chunks = agent.smart_chunk(long_text, max_chars=500)

    print(f"\nOriginal text: {len(long_text)} characters")
    print(f"Split into: {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}/{len(chunks)}: {chunk['chars']} characters")
        print(f"Preview: {chunk['text'][:100]}...")

    print("\n✅ Chunking test completed")


def test_metadata_suggestions():
    """Test metadata suggestion agent"""
    print("\n" + "="*60)
    print("Testing: Metadata Suggestion Agent")
    print("="*60)

    test_text = """
    Welcome to our podcast about artificial intelligence and machine learning.
    Today we'll discuss the latest breakthroughs in natural language processing
    and how AI is transforming the way we interact with technology.
    """

    agent = create_agent_system()
    suggestions = agent.suggest_metadata(test_text)

    print(f"\nText preview: {test_text[:100]}...")
    print(f"\n📋 AI Suggestions:")
    print(f"  Filename: {suggestions.get('filename', 'N/A')}")
    print(f"  Category: {suggestions.get('category', 'N/A')}")
    print(f"  Summary: {suggestions.get('summary', 'N/A')}")
    print(f"  Recommended Voice: {suggestions.get('recommended_voice', 'N/A')}")
    print(f"  Content Type: {suggestions.get('content_type', 'N/A')}")

    print("\n✅ Metadata suggestion test completed")


def test_quality_analysis():
    """Test quality analysis agent"""
    print("\n" + "="*60)
    print("Testing: Quality Analysis Agent")
    print("="*60)

    test_text = """
    Check out these URLs: http://example.com http://test.com http://demo.com
    And these numbers: 1234567890 9876543210 1111111111
    Here's some code: function test() { return true; }
    """

    agent = create_agent_system()
    analysis = agent.analyze_quality(test_text)

    print(f"\nText preview: {test_text[:100]}...")
    print(f"\n📊 Quality Analysis:")
    print(f"  Characters: {analysis['character_count']}")
    print(f"  Words: {analysis['word_count']}")
    print(f"  Est. Duration: {analysis['estimated_duration_minutes']} minutes")
    print(f"  Quality Score: {analysis['quality_score']}/100")

    if analysis['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in analysis['warnings']:
            print(f"    - {warning}")

    if analysis['issues']:
        print(f"\n❌ Issues:")
        for issue in analysis['issues']:
            print(f"    - {issue}")

    print("\n✅ Quality analysis test completed")


def test_voice_suggestion():
    """Test voice suggestion agent"""
    print("\n" + "="*60)
    print("Testing: Voice Suggestion Agent")
    print("="*60)

    test_cases = [
        "Welcome to our meditation session. Take a deep breath and relax.",
        "Breaking news: The stock market reached record highs today.",
        "Once upon a time, in a faraway kingdom, there lived a brave knight.",
    ]

    agent = create_agent_system()

    for text in test_cases:
        voice, reason = agent.suggest_voice(text)
        print(f"\nText: {text[:60]}...")
        print(f"🎤 Suggested Voice: {voice}")
        print(f"   Reason: {reason}")

    print("\n✅ Voice suggestion test completed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TTS AI AGENTS TEST SUITE")
    print("="*60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        exit(1)

    try:
        # Run all tests
        test_preprocessing()
        test_smart_chunking()
        test_metadata_suggestions()
        test_quality_analysis()
        test_voice_suggestion()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYour AI agents are ready to use in tts_app19.py")
        print("Start the app with: python3 tts_app19.py")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
