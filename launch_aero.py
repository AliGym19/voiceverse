#!/usr/bin/env python3
"""
Launch script for VoiceVerse with Aero Dashboard
"""

import os
import subprocess
import sys
import time
import signal

def kill_port_5000():
    """Kill any process using port 5000"""
    try:
        result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['kill', '-9', pid])
            print("✅ Cleared port 5000")
    except:
        pass

def launch_app():
    """Launch the TTS app with Aero dashboard"""
    print("🚀 Launching VoiceVerse with Windows Vista/7 Aero UI...")
    print("-" * 50)

    # Kill any existing process on port 5000
    kill_port_5000()
    time.sleep(1)

    # Launch the app
    try:
        process = subprocess.Popen(
            ['python3', 'tts_app19.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        print("✅ Application started!")
        print("📌 Access the Aero Dashboard at: http://localhost:5000/dashboard")
        print("📌 Access the classic interface at: http://localhost:5000/")
        print("-" * 50)
        print("Press Ctrl+C to stop the server")

        # Wait for the process
        while True:
            line = process.stdout.readline()
            if line:
                print(line.strip())

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        process.terminate()
        time.sleep(1)
        kill_port_5000()
        print("✅ Server stopped")

if __name__ == "__main__":
    launch_app()
